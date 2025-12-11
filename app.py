from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import pandas as pd
import os
from sqlalchemy import func, extract

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kimbiofarm-secret-key-2025'

# Database URI - Vercel uses read-only filesystem except /tmp
if os.environ.get('VERCEL'):
    # Vercel environment - use /tmp for SQLite
    db_path = 'sqlite:////tmp/cayxanh.db'
else:
    # Local development
    db_path = os.environ.get('DATABASE_URL', 'sqlite:///cayxanh.db')
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
            # Đọc file Excel
            df = pd.read_excel(file, sheet_name='NHẬP XUẤT TỒN  T12.2015')
            
            imported = 0
            updated = 0
            
            for _, row in df.iterrows():
                ma_cay = str(row.get('MÃ CÂY', '')).strip()
                loai_cay = str(row.get('LOẠI CÂY', '')).strip()
                ton_kho = float(row.get('TỒN từ 3.12.25', 0) or 0)
                
                if not ma_cay or ma_cay == 'nan':
                    continue
                
                # Tìm hoặc tạo cây
                cay = CayXanh.query.filter_by(ma_cay=ma_cay).first()
                if cay:
                    cay.loai_cay = loai_cay
                    cay.ton_kho = ton_kho
                    updated += 1
                else:
                    cay = CayXanh(ma_cay=ma_cay, loai_cay=loai_cay, ton_kho=ton_kho)
                    db.session.add(cay)
                    imported += 1
                
                # Import nhập kho nếu có (xử lý tên cột có thể có khoảng trắng)
                so_luong_nhap = row.get('SỐ LƯỢNG NHẬP') or row.get('SỐ LƯỢNG NHẬP ')
                gia_nhap = row.get('GIÁ NHẬP')
                phi_ship_raw = row.get('PHÍ SHIP', 0)
                ngay_nhap = row.get('NGÀY NHẬP')
                ghi_chu = str(row.get('GHI CHÚ', '')).strip() if pd.notna(row.get('GHI CHÚ')) else ''
                
                if pd.notna(so_luong_nhap) and pd.notna(gia_nhap) and pd.notna(ngay_nhap):
                    # Xử lý NaN cho phi_ship
                    phi_ship = 0.0
                    if pd.notna(phi_ship_raw):
                        phi_ship = float(phi_ship_raw)
                    
                    tong_tien = (float(so_luong_nhap) * float(gia_nhap)) + phi_ship
                    nhap_kho = NhapKho(
                        cay_xanh_id=cay.id,
                        so_luong=float(so_luong_nhap),
                        gia_nhap=float(gia_nhap),
                        phi_ship=float(phi_ship),
                        tong_tien=tong_tien,
                        ngay_nhap=pd.to_datetime(ngay_nhap).date(),
                        ghi_chu=ghi_chu
                    )
                    db.session.add(nhap_kho)
            
            db.session.commit()
            flash(f'Import thành công! Đã thêm {imported} cây mới, cập nhật {updated} cây.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi import: {str(e)}', 'error')
        
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

