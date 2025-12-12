from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import pandas as pd
import os
from urllib.parse import quote_plus, urlparse, urlunparse
from sqlalchemy import func, extract
from sqlalchemy.engine.url import URL
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kimbiofarm-secret-key-2025'

# Cấu hình upload ảnh
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Cấu hình instance_path cho Vercel (read-only filesystem)
# Trên Vercel, chỉ có thể ghi vào /tmp
# Phải set trước khi khởi tạo SQLAlchemy để tránh lỗi read-only filesystem
if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
    app.instance_path = '/tmp'
    # Trên Vercel, lưu ảnh vào /tmp
    UPLOAD_FOLDER = '/tmp/uploads/images'
else:
    # Local development: lưu trong static/uploads/images
    UPLOAD_FOLDER = 'static/uploads/images'

# Tạo thư mục upload nếu chưa có (chỉ khi không phải trên Vercel hoặc nếu là /tmp)
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError:
    # Nếu không thể tạo thư mục (read-only), bỏ qua
    pass

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    """Kiểm tra file có phải là ảnh hợp lệ không"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def fix_postgres_url(url):
    """Fix PostgreSQL connection string by properly encoding password and handling special characters"""
    if not url or 'postgres' not in url.lower():
        return url
    
    # Vercel Postgres uses postgres://, SQLAlchemy needs postgresql://
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    
    # Try using SQLAlchemy's URL parser first (most reliable)
    try:
        # SQLAlchemy's make_url can parse connection strings properly
        from sqlalchemy.engine.url import make_url
        parsed = make_url(url)
        
        # Rebuild using SQLAlchemy's URL.create which handles encoding automatically
        if parsed.password:
            # URL.create will properly encode special characters
            # Don't include query parameters as they might cause issues with psycopg2
            fixed_url = URL.create(
                drivername='postgresql',
                username=parsed.username,
                password=parsed.password,  # SQLAlchemy handles encoding
                host=parsed.host,
                port=parsed.port,
                database=parsed.database.lstrip('/') if parsed.database else None
                # Explicitly exclude query parameters
            )
            return str(fixed_url)
    except Exception as e:
        print(f"Warning: SQLAlchemy URL parsing failed: {e}, trying manual parsing...")
    
    # Fallback: manual parsing with urllib
    try:
        parsed = urlparse(url)
        
        if parsed.username and parsed.password:
            # URL encode the password to handle special characters
            encoded_password = quote_plus(parsed.password)
            encoded_username = quote_plus(parsed.username)
            
            # Reconstruct the URL with encoded credentials
            netloc = f"{encoded_username}:{encoded_password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            
            # Clean up database path (remove leading /)
            db_path = parsed.path.lstrip('/') if parsed.path else ''
            
            # Don't include query parameters, params, or fragment as they might cause issues
            fixed_url = urlunparse((
                'postgresql',
                netloc,
                '/' + db_path if db_path else '/',
                '',  # No params
                '',  # No query parameters
                ''   # No fragment
            ))
            return fixed_url
        elif parsed.username:
            # No password case
            encoded_username = quote_plus(parsed.username)
            netloc = f"{encoded_username}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            
            db_path = parsed.path.lstrip('/') if parsed.path else ''
            # Don't include query parameters, params, or fragment
            fixed_url = urlunparse((
                'postgresql',
                netloc,
                '/' + db_path if db_path else '/',
                '',  # No params
                '',  # No query parameters
                ''   # No fragment
            ))
            return fixed_url
    except Exception as e:
        print(f"Warning: Manual URL parsing also failed: {e}")
    
    # Last resort: return original URL (might work if already properly formatted)
    return url

# Database Configuration
# - Production (Vercel/Supabase): Sử dụng PostgreSQL khi có DATABASE_URL hoặc POSTGRES_URL
# - Local Development: Sử dụng SQLite
db_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL', '')

if db_url and 'postgres' in db_url.lower():
    # Production: Sử dụng PostgreSQL
    try:
        db_path = fix_postgres_url(db_url)
        if '@' in db_path:
            masked = db_path.split('@')[0].split(':')[0] + ':***@' + '@'.join(db_path.split('@')[1:])
            print(f"Using PostgreSQL (Production): {masked}")
    except Exception as e:
        print(f"Error parsing PostgreSQL connection string: {e}")
        db_path = 'sqlite:///cayxanh.db'
        print("Falling back to SQLite")
else:
    # Local Development: Sử dụng SQLite
    db_path = 'sqlite:///cayxanh.db'
    print("Using SQLite (Local Development)")

app.config['SQLALCHEMY_DATABASE_URI'] = db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class CayXanh(db.Model):
    __tablename__ = 'cayxanh'
    
    id = db.Column(db.Integer, primary_key=True)
    ma_cay = db.Column(db.String(50), unique=True, nullable=False, index=True)
    loai_cay = db.Column(db.String(200), nullable=False)
    ton_kho = db.Column(db.Float, default=0.0, nullable=False)
    hinh_anh = db.Column(db.String(500), nullable=True)  # Đường dẫn ảnh
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    nhap_khos = db.relationship('NhapKho', backref='cay_xanh', lazy=True, cascade='all, delete-orphan')
    xuat_khos = db.relationship('XuatKho', backref='cay_xanh', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CayXanh {self.ma_cay}: {self.loai_cay}>'

class NhapKho(db.Model):
    __tablename__ = 'nhapkho'
    
    id = db.Column(db.Integer, primary_key=True)
    cay_xanh_id = db.Column(db.Integer, db.ForeignKey('cayxanh.id'), nullable=False)
    so_luong = db.Column(db.Float, nullable=False)
    gia_nhap = db.Column(db.Float, nullable=False)
    phi_ship = db.Column(db.Float, default=0.0)
    tong_tien = db.Column(db.Float, nullable=False)
    ngay_nhap = db.Column(db.Date, nullable=False, default=date.today)
    ghi_chu = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<NhapKho {self.cay_xanh_id}: {self.so_luong} cây - {self.ngay_nhap}>'

class XuatKho(db.Model):
    __tablename__ = 'xuatkho'
    
    id = db.Column(db.Integer, primary_key=True)
    cay_xanh_id = db.Column(db.Integer, db.ForeignKey('cayxanh.id'), nullable=False)
    so_luong = db.Column(db.Float, nullable=False)
    ngay_xuat = db.Column(db.Date, nullable=False, default=date.today)
    ly_do = db.Column(db.String(200))  # Bán, mất, hỏng, etc.
    ghi_chu = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<XuatKho {self.cay_xanh_id}: {self.so_luong} cây - {self.ngay_xuat}>'

# Routes
@app.route('/')
def index():
    # Ensure database tables exist
    try:
        db.create_all()
    except Exception as e:
        print(f"Warning: Could not ensure tables exist: {e}")
    
    # Dashboard statistics
    try:
        total_cay = CayXanh.query.count()
    except Exception as e:
        print(f"Error querying total_cay: {e}")
        total_cay = 0
    
    try:
        total_ton_kho = db.session.query(func.sum(CayXanh.ton_kho)).scalar() or 0
    except Exception as e:
        print(f"Error querying total_ton_kho: {e}")
        total_ton_kho = 0
    
    # Tổng giá trị tồn kho (lấy giá nhập mới nhất của mỗi cây)
    tong_gia_tri = 0
    try:
        for cay in CayXanh.query.all():
            nhap_moi_nhat = NhapKho.query.filter_by(cay_xanh_id=cay.id).order_by(NhapKho.ngay_nhap.desc()).first()
            if nhap_moi_nhat and nhap_moi_nhat.gia_nhap and cay.ton_kho:
                tong_gia_tri += float(cay.ton_kho) * float(nhap_moi_nhat.gia_nhap)
    except Exception as e:
        print(f"Error calculating tong_gia_tri: {e}")
        tong_gia_tri = 0
    
    # Nhập xuất trong tháng
    thang_hien_tai = datetime.now().month
    nam_hien_tai = datetime.now().year
    
    try:
        tong_nhap_thang = db.session.query(func.sum(NhapKho.so_luong)).filter(
            extract('month', NhapKho.ngay_nhap) == thang_hien_tai,
            extract('year', NhapKho.ngay_nhap) == nam_hien_tai
        ).scalar() or 0
    except Exception as e:
        print(f"Error querying tong_nhap_thang: {e}")
        tong_nhap_thang = 0
    
    try:
        tong_xuat_thang = db.session.query(func.sum(XuatKho.so_luong)).filter(
            extract('month', XuatKho.ngay_xuat) == thang_hien_tai,
            extract('year', XuatKho.ngay_xuat) == nam_hien_tai
        ).scalar() or 0
    except Exception as e:
        print(f"Error querying tong_xuat_thang: {e}")
        tong_xuat_thang = 0
    
    # Top 10 cây có tồn kho cao nhất
    top_ton_kho = CayXanh.query.order_by(CayXanh.ton_kho.desc()).limit(10).all()
    
    # Lịch sử nhập xuất gần đây
    lich_su_nhap = NhapKho.query.order_by(NhapKho.ngay_nhap.desc(), NhapKho.created_at.desc()).limit(10).all()
    lich_su_xuat = XuatKho.query.order_by(XuatKho.ngay_xuat.desc(), XuatKho.created_at.desc()).limit(10).all()
    
    return render_template('index.html',
                         total_cay=total_cay,
                         total_ton_kho=total_ton_kho,
                         tong_gia_tri=tong_gia_tri,
                         tong_nhap_thang=tong_nhap_thang,
                         tong_xuat_thang=tong_xuat_thang,
                         top_ton_kho=top_ton_kho,
                         lich_su_nhap=lich_su_nhap,
                         lich_su_xuat=lich_su_xuat)

@app.route('/ton-kho')
def ton_kho():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    query = CayXanh.query
    
    if search:
        query = query.filter(
            db.or_(
                CayXanh.ma_cay.ilike(f'%{search}%'),
                CayXanh.loai_cay.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(CayXanh.ton_kho.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('ton_kho.html', pagination=pagination, search=search)

@app.route('/nhap-hang', methods=['GET', 'POST'])
def nhap_hang():
    if request.method == 'POST':
        data = request.get_json()
        
        ma_cay = data.get('ma_cay')
        loai_cay = data.get('loai_cay')
        so_luong = float(data.get('so_luong', 0))
        gia_nhap = float(data.get('gia_nhap', 0))
        phi_ship = float(data.get('phi_ship', 0))
        ngay_nhap = datetime.strptime(data.get('ngay_nhap'), '%Y-%m-%d').date()
        ghi_chu = data.get('ghi_chu', '')
        
        tong_tien = (so_luong * gia_nhap) + phi_ship
        
        # Tìm hoặc tạo cây
        cay = CayXanh.query.filter_by(ma_cay=ma_cay).first()
        if not cay:
            cay = CayXanh(ma_cay=ma_cay, loai_cay=loai_cay, ton_kho=0)
            db.session.add(cay)
            db.session.flush()
        
        # Cập nhật loại cây nếu thay đổi
        if loai_cay and loai_cay != cay.loai_cay:
            cay.loai_cay = loai_cay
        
        # Tạo phiếu nhập
        nhap_kho = NhapKho(
            cay_xanh_id=cay.id,
            so_luong=so_luong,
            gia_nhap=gia_nhap,
            phi_ship=phi_ship,
            tong_tien=tong_tien,
            ngay_nhap=ngay_nhap,
            ghi_chu=ghi_chu
        )
        db.session.add(nhap_kho)
        
        # Cập nhật tồn kho
        cay.ton_kho += so_luong
        cay.updated_at = datetime.now()
        
        try:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Nhập hàng thành công!'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})
    
    # GET: Hiển thị form
    danh_sach_cay = CayXanh.query.order_by(CayXanh.loai_cay).all()
    return render_template('nhap_hang.html', danh_sach_cay=danh_sach_cay, today=date.today().strftime('%Y-%m-%d'))

@app.route('/xuat-hang', methods=['GET', 'POST'])
def xuat_hang():
    if request.method == 'POST':
        data = request.get_json()
        
        ma_cay = data.get('ma_cay')
        so_luong = float(data.get('so_luong', 0))
        ngay_xuat = datetime.strptime(data.get('ngay_xuat'), '%Y-%m-%d').date()
        ly_do = data.get('ly_do', '')
        ghi_chu = data.get('ghi_chu', '')
        
        # Tìm cây
        cay = CayXanh.query.filter_by(ma_cay=ma_cay).first()
        if not cay:
            return jsonify({'success': False, 'message': 'Không tìm thấy mã cây!'})
        
        # Kiểm tra tồn kho
        ton_kho_hien_tai = cay.ton_kho or 0
        if ton_kho_hien_tai < so_luong:
            return jsonify({'success': False, 'message': f'Tồn kho không đủ! Hiện có: {ton_kho_hien_tai}'})
        
        # Tạo phiếu xuất
        xuat_kho = XuatKho(
            cay_xanh_id=cay.id,
            so_luong=so_luong,
            ngay_xuat=ngay_xuat,
            ly_do=ly_do,
            ghi_chu=ghi_chu
        )
        db.session.add(xuat_kho)
        
        # Cập nhật tồn kho
        cay.ton_kho -= so_luong
        cay.updated_at = datetime.now()
        
        try:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Xuất hàng thành công!'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})
    
    # GET: Hiển thị form
    danh_sach_cay = CayXanh.query.filter(
        db.or_(CayXanh.ton_kho > 0, CayXanh.ton_kho.is_(None))
    ).order_by(CayXanh.loai_cay).all()
    # Lọc lại trong Python để xử lý None
    danh_sach_cay = [c for c in danh_sach_cay if (c.ton_kho or 0) > 0]
    return render_template('xuat_hang.html', danh_sach_cay=danh_sach_cay, today=date.today().strftime('%Y-%m-%d'))

@app.route('/lich-su')
def lich_su():
    loai = request.args.get('loai', 'all')  # all, nhap, xuat
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    if loai == 'nhap':
        pagination = NhapKho.query.order_by(
            NhapKho.ngay_nhap.desc(), NhapKho.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        return render_template('lich_su_nhap.html', pagination=pagination, loai=loai)
    elif loai == 'xuat':
        pagination = XuatKho.query.order_by(
            XuatKho.ngay_xuat.desc(), XuatKho.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        return render_template('lich_su_xuat.html', pagination=pagination, loai=loai)
    else:
        # Hiển thị cả hai
        return render_template('lich_su.html', loai=loai)

@app.route('/api/cay/<ma_cay>')
def api_cay(ma_cay):
    cay = CayXanh.query.filter_by(ma_cay=ma_cay).first()
    if cay:
        nhap_moi_nhat = NhapKho.query.filter_by(cay_xanh_id=cay.id).order_by(NhapKho.ngay_nhap.desc()).first()
        return jsonify({
            'success': True,
            'ma_cay': cay.ma_cay,
            'loai_cay': cay.loai_cay,
            'ton_kho': cay.ton_kho,
            'gia_nhap_moi_nhat': nhap_moi_nhat.gia_nhap if nhap_moi_nhat else None
        })
    return jsonify({'success': False, 'message': 'Không tìm thấy!'})

@app.route('/cay/<ma_cay>')
def chi_tiet_cay(ma_cay):
    cay = CayXanh.query.filter_by(ma_cay=ma_cay).first()
    if not cay:
        flash('Không tìm thấy cây!', 'error')
        return redirect(url_for('ton_kho'))
    
    # Lấy lịch sử nhập
    lich_su_nhap = NhapKho.query.filter_by(cay_xanh_id=cay.id).order_by(
        NhapKho.ngay_nhap.desc(), NhapKho.created_at.desc()
    ).all()
    
    # Lấy lịch sử xuất
    lich_su_xuat = XuatKho.query.filter_by(cay_xanh_id=cay.id).order_by(
        XuatKho.ngay_xuat.desc(), XuatKho.created_at.desc()
    ).all()
    
    # Tính tổng tiền nhập
    tong_tien_nhap = db.session.query(func.sum(NhapKho.tong_tien)).filter_by(cay_xanh_id=cay.id).scalar() or 0
    
    # Tính tổng số lượng nhập
    tong_so_luong_nhap = db.session.query(func.sum(NhapKho.so_luong)).filter_by(cay_xanh_id=cay.id).scalar() or 0
    
    # Tính tổng số lượng xuất
    tong_so_luong_xuat = db.session.query(func.sum(XuatKho.so_luong)).filter_by(cay_xanh_id=cay.id).scalar() or 0
    
    return render_template('chi_tiet_cay.html',
                         cay=cay,
                         lich_su_nhap=lich_su_nhap,
                         lich_su_xuat=lich_su_xuat,
                         tong_tien_nhap=tong_tien_nhap,
                         tong_so_luong_nhap=tong_so_luong_nhap,
                         tong_so_luong_xuat=tong_so_luong_xuat)

@app.route('/cay/<ma_cay>/xoa', methods=['POST'])
def xoa_cay(ma_cay):
    """Xóa cây và tất cả lịch sử nhập xuất liên quan"""
    cay = CayXanh.query.filter_by(ma_cay=ma_cay).first()
    if not cay:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Không tìm thấy cây!'})
        flash('Không tìm thấy cây!', 'error')
        return redirect(url_for('ton_kho'))
    
    # Lưu tên cây để hiển thị thông báo
    ten_cay = cay.loai_cay
    ma_cay_value = cay.ma_cay
    
    try:
        # Xóa ảnh nếu có
        if cay.hinh_anh:
            old_filename = os.path.basename(cay.hinh_anh)
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass
        
        # Xóa cây (cascade sẽ tự động xóa lịch sử nhập xuất)
        db.session.delete(cay)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': f'Đã xóa cây {ma_cay_value} ({ten_cay}) thành công!'})
        
        flash(f'Đã xóa cây {ma_cay_value} ({ten_cay}) thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        error_msg = f'Lỗi khi xóa cây: {str(e)}'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg, 'error')
    
    return redirect(url_for('ton_kho'))

@app.route('/cay/<ma_cay>/upload-anh', methods=['POST'])
def upload_anh_cay(ma_cay):
    """Upload ảnh cho cây"""
    cay = CayXanh.query.filter_by(ma_cay=ma_cay).first()
    if not cay:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Không tìm thấy cây!'})
        flash('Không tìm thấy cây!', 'error')
        return redirect(url_for('ton_kho'))
    
    if 'file' not in request.files:
        flash('Không có file được chọn!', 'error')
        return redirect(url_for('chi_tiet_cay', ma_cay=ma_cay))
    
    file = request.files['file']
    if file.filename == '':
        flash('Không có file được chọn!', 'error')
        return redirect(url_for('chi_tiet_cay', ma_cay=ma_cay))
    
    if file and allowed_file(file.filename):
        try:
            # Tạo tên file an toàn: ma_cay_timestamp.extension
            filename = secure_filename(file.filename)
            extension = filename.rsplit('.', 1)[1].lower()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{ma_cay}_{timestamp}.{extension}"
            
            # Xóa ảnh cũ nếu có
            if cay.hinh_anh:
                old_filename = os.path.basename(cay.hinh_anh)
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except:
                        pass
            
            # Lưu file mới
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(file_path)
            
            # Lưu đường dẫn vào database (relative path)
            if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
                # Trên Vercel, có thể cần lưu vào cloud storage
                cay.hinh_anh = f"/uploads/images/{new_filename}"
            else:
                cay.hinh_anh = f"uploads/images/{new_filename}"
            
            cay.updated_at = datetime.now()
            db.session.commit()
            
            flash('Upload ảnh thành công!', 'success')
        except RequestEntityTooLarge:
            flash('File quá lớn! Kích thước tối đa là 5MB.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi upload ảnh: {str(e)}', 'error')
    else:
        flash('File không hợp lệ! Chỉ chấp nhận file ảnh (PNG, JPG, JPEG, GIF, WEBP).', 'error')
    
    return redirect(url_for('chi_tiet_cay', ma_cay=ma_cay))

@app.route('/uploads/images/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    upload_folder = app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    
    if os.path.exists(file_path):
        return send_from_directory(upload_folder, filename)
    else:
        # Fallback: trả về 404 hoặc placeholder
        return "Image not found", 404

@app.route('/import-excel', methods=['GET', 'POST'])
def import_excel():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Không có file được chọn!', 'error')
            return redirect(url_for('import_excel'))
        
        file = request.files['file']
        if file.filename == '':
            flash('Không có file được chọn!', 'error')
            return redirect(url_for('import_excel'))
        
        try:
            # Đọc file Excel - format đơn giản: Tên hàng, Số lượng, Giá tiền, Ngày
            df = pd.read_excel(file)
            
            # Tìm các cột (hỗ trợ nhiều tên cột khác nhau)
            ten_hang_col = None
            so_luong_col = None
            gia_tien_col = None
            phi_ship_col = None
            ngay_col = None
            
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'tên' in col_lower or 'hàng' in col_lower or 'loại' in col_lower or 'cây' in col_lower:
                    ten_hang_col = col
                elif 'số lượng' in col_lower or 'sl' in col_lower or 'quantity' in col_lower:
                    so_luong_col = col
                elif 'giá' in col_lower or 'price' in col_lower or 'giá tiền' in col_lower:
                    gia_tien_col = col
                elif 'phí' in col_lower and 'ship' in col_lower:
                    phi_ship_col = col
                elif 'ngày' in col_lower or 'date' in col_lower:
                    ngay_col = col
            
            if not ten_hang_col or not so_luong_col or not gia_tien_col or not ngay_col:
                flash('File Excel phải có các cột: Tên hàng, Số lượng, Giá tiền, Ngày (Phí ship là tùy chọn)', 'error')
                return redirect(url_for('import_excel'))
            
            imported = 0
            
            for _, row in df.iterrows():
                ten_hang = str(row.get(ten_hang_col, '')).strip()
                so_luong = row.get(so_luong_col)
                gia_tien = row.get(gia_tien_col)
                phi_ship = row.get(phi_ship_col) if phi_ship_col else None
                ngay_nhap = row.get(ngay_col)
                
                # Bỏ qua dòng trống
                if pd.isna(ten_hang) or ten_hang == '' or ten_hang == 'nan':
                    continue
                
                # Xử lý số lượng, giá và phí ship (cho phép số lượng = 0)
                try:
                    so_luong = float(so_luong) if pd.notna(so_luong) else 0.0
                    gia_tien = float(gia_tien) if pd.notna(gia_tien) else 0.0
                    phi_ship = float(phi_ship) if pd.notna(phi_ship) and phi_ship_col else 0.0
                    ngay_nhap = pd.to_datetime(ngay_nhap).date() if pd.notna(ngay_nhap) else date.today()
                except:
                    # Nếu không parse được, đặt giá trị mặc định
                    so_luong = 0.0
                    gia_tien = 0.0
                    phi_ship = 0.0
                    ngay_nhap = date.today()
                
                # Tạo mã cây tự động từ tên hàng (hoặc tìm nếu đã có)
                # Sử dụng tên hàng làm mã cây nếu chưa có mã
                ma_cay = ten_hang[:50]  # Giới hạn độ dài mã cây
                
                # Tìm hoặc tạo cây
                cay = CayXanh.query.filter_by(ma_cay=ma_cay).first()
                if not cay:
                    cay = CayXanh(ma_cay=ma_cay, loai_cay=ten_hang, ton_kho=0)
                    db.session.add(cay)
                    db.session.flush()
                    imported += 1
                else:
                    # Cập nhật tên nếu khác
                    if cay.loai_cay != ten_hang:
                        cay.loai_cay = ten_hang
                
                # Chỉ tạo phiếu nhập nếu số lượng > 0
                if so_luong > 0 and gia_tien > 0:
                    tong_tien = (so_luong * gia_tien) + phi_ship
                    nhap_kho = NhapKho(
                        cay_xanh_id=cay.id,
                        so_luong=so_luong,
                        gia_nhap=gia_tien,
                        phi_ship=phi_ship,
                        tong_tien=tong_tien,
                        ngay_nhap=ngay_nhap,
                        ghi_chu='Import từ Excel'
                    )
                    db.session.add(nhap_kho)
                
                # Cập nhật tồn kho (kể cả số lượng = 0)
                cay.ton_kho = so_luong
                cay.updated_at = datetime.now()
            
            db.session.commit()
            flash(f'Import thành công! Đã import {imported} hàng mới và cập nhật tồn kho.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi import: {str(e)}', 'error')
            import traceback
            traceback.print_exc()
        
        return redirect(url_for('import_excel'))
    
    return render_template('import_excel.html')

# Initialize database - lazy initialization in api/index.py for Vercel
# For local development, initialize here
if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
    app.run(debug=True, host='0.0.0.0', port=5000)

