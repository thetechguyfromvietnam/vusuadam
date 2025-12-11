#!/usr/bin/env python3
"""
Script để cập nhật dữ liệu từ Excel lên database web
- Đọc BẢNG GIÁ SALER - TẤT CẢ SẢN PHẨM.xlsx
- Đọc NHẬP XUẤT TỒN CAY XANH KIMBIOFARM.xlsx
- Kết hợp và cập nhật database
- Tự động xóa file sau khi xong
"""

import sys
import os
import pandas as pd
from datetime import datetime
import sqlite3

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Database path
db_path = 'cayxanh.db'
if not os.path.exists(db_path):
    # Try instance folder
    db_path = os.path.join('instance', 'cayxanh.db')
    if not os.path.exists(db_path):
        db_path = 'cayxanh.db'  # Will create new

def update_database():
    """Cập nhật database từ 2 file Excel"""
    
    print("="*80)
    print("🔄 BẮT ĐẦU CẬP NHẬT DỮ LIỆU")
    print("="*80)
    
    try:
        # Đọc file 1: Bảng giá saler
        print("\n📖 Đang đọc: BẢNG GIÁ SALER - TẤT CẢ SẢN PHẨM.xlsx")
        df_saler = pd.read_excel("BẢNG GIÁ SALER - TẤT CẢ SẢN PHẨM.xlsx", sheet_name=0, header=3)
        df_saler = df_saler[df_saler['TÊN SẢN PHẨM'].notna()].copy()
        df_saler = df_saler[df_saler['LOẠI'] == 'Cây Giống'].copy()  # Chỉ lấy Cây Giống
        print(f"  ✅ Đã đọc {len(df_saler)} sản phẩm từ bảng giá saler")
        
        # Đọc file 2: Nhập xuất tồn
        print("\n📖 Đang đọc: NHẬP XUẤT TỒN CAY XANH KIMBIOFARM.xlsx")
        df_nxt = pd.read_excel("NHẬP XUẤT TỒN CAY XANH KIMBIOFARM.xlsx", sheet_name='NHẬP XUẤT TỒN  T12.2015')
        print(f"  ✅ Đã đọc {len(df_nxt)} dòng từ nhập xuất tồn")
        
        # Kết nối database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Đảm bảo tables tồn tại
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cayxanh (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ma_cay VARCHAR(50) UNIQUE NOT NULL,
                loai_cay VARCHAR(200) NOT NULL,
                ton_kho FLOAT NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nhapkho (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cay_xanh_id INTEGER NOT NULL,
                so_luong FLOAT NOT NULL,
                gia_nhap FLOAT NOT NULL,
                phi_ship FLOAT DEFAULT 0.0,
                tong_tien FLOAT NOT NULL,
                ngay_nhap DATE NOT NULL,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cay_xanh_id) REFERENCES cayxanh(id)
            )
        ''')
        
        print("\n📝 Đang cập nhật database...")
        
        imported = 0
        updated = 0
        nhap_imported = 0
        
        for _, row in df_nxt.iterrows():
            ma_cay = str(row.get('MÃ CÂY', '')).strip()
            loai_cay = str(row.get('LOẠI CÂY', '')).strip()
            ton_kho = float(row.get('TỒN từ 3.12.25', 0) or 0)
            
            if not ma_cay or ma_cay == 'nan' or ma_cay.lower() == 'none':
                continue
            
            # Tìm hoặc tạo cây
            cursor.execute('SELECT id FROM cayxanh WHERE ma_cay = ?', (ma_cay,))
            result = cursor.fetchone()
            
            if result:
                cay_id = result[0]
                cursor.execute('''
                    UPDATE cayxanh 
                    SET loai_cay = ?, ton_kho = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (loai_cay, ton_kho, cay_id))
                updated += 1
            else:
                cursor.execute('''
                    INSERT INTO cayxanh (ma_cay, loai_cay, ton_kho)
                    VALUES (?, ?, ?)
                ''', (ma_cay, loai_cay, ton_kho))
                cay_id = cursor.lastrowid
                imported += 1
            
            # Import nhập kho nếu có
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
                
                so_luong = float(so_luong_nhap)
                gia = float(gia_nhap)
                tong_tien = (so_luong * gia) + phi_ship
                ngay = pd.to_datetime(ngay_nhap).strftime('%Y-%m-%d')
                
                # Kiểm tra xem đã có phiếu nhập này chưa
                cursor.execute('''
                    SELECT id FROM nhapkho 
                    WHERE cay_xanh_id = ? AND so_luong = ? AND gia_nhap = ? AND ngay_nhap = ?
                ''', (cay_id, so_luong, gia, ngay))
                
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO nhapkho (cay_xanh_id, so_luong, gia_nhap, phi_ship, tong_tien, ngay_nhap, ghi_chu)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (cay_id, so_luong, gia, phi_ship, tong_tien, ngay, ghi_chu))
                    nhap_imported += 1
        
        conn.commit()
        conn.close()
        
        print("\n" + "="*80)
        print("✅ CẬP NHẬT THÀNH CÔNG!")
        print("="*80)
        print(f"  📦 Đã thêm: {imported} cây mới")
        print(f"  🔄 Đã cập nhật: {updated} cây")
        print(f"  📥 Đã import: {nhap_imported} phiếu nhập")
        print("="*80)
        
        return True
            
    except Exception as e:
        print(f"\n❌ LỖI: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_files():
    """Xóa file sau khi cập nhật xong"""
    print("\n🗑️  Đang xóa file...")
    
    files_to_delete = [
        "BẢNG GIÁ SALER - TẤT CẢ SẢN PHẨM.xlsx",
        "NHẬP XUẤT TỒN CAY XANH KIMBIOFARM.xlsx"
    ]
    
    deleted = 0
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  ✅ Đã xóa: {file}")
                deleted += 1
            except Exception as e:
                print(f"  ⚠️  Không thể xóa {file}: {e}")
    
    print(f"\n  ✅ Đã xóa {deleted}/{len(files_to_delete)} files")

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 SCRIPT CẬP NHẬT DỮ LIỆU TỪ EXCEL")
    print("="*80)
    print(f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Kiểm tra file tồn tại
    files_required = [
        "BẢNG GIÁ SALER - TẤT CẢ SẢN PHẨM.xlsx",
        "NHẬP XUẤT TỒN CAY XANH KIMBIOFARM.xlsx"
    ]
    
    missing_files = []
    for file in files_required:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("\n❌ THIẾU FILE:")
        for file in missing_files:
            print(f"  - {file}")
        print("\n⚠️  Vui lòng đảm bảo các file Excel có trong thư mục!")
        sys.exit(1)
    
    # Cập nhật database
    success = update_database()
    
    if success:
        # Xóa file sau khi thành công
        cleanup_files()
        
        print("\n" + "="*80)
        print("✅ HOÀN TẤT!")
        print("="*80)
        print("  Dữ liệu đã được cập nhật lên database web")
        print("  Các file Excel đã được xóa")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ CẬP NHẬT THẤT BẠI!")
        print("="*80)
        print("  Các file Excel vẫn được giữ lại để kiểm tra")
        print("="*80)
        sys.exit(1)
