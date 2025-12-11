#!/usr/bin/env python3
"""
Script để export dữ liệu từ database local (SQLite) ra file Excel
Format đơn giản: Tên hàng, Số lượng, Giá tiền, Ngày
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

def export_to_excel():
    """Export dữ liệu nhập kho ra file Excel với format đơn giản"""
    
    print("="*80)
    print("📤 EXPORT DỮ LIỆU RA FILE EXCEL")
    print("="*80)
    
    # Tìm file SQLite database
    db_paths = [
        'cayxanh.db',
        os.path.join('instance', 'cayxanh.db'),
        os.path.join(os.path.dirname(__file__), 'cayxanh.db'),
        os.path.join(os.path.dirname(__file__), 'instance', 'cayxanh.db')
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("\n❌ Không tìm thấy database SQLite (cayxanh.db)!")
        print("   Vui lòng đảm bảo bạn đã chạy app ít nhất 1 lần để tạo database.")
        return None
    
    print(f"\n📂 Đang đọc database: {db_path}")
    
    # Kết nối SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Lấy dữ liệu nhập kho kết hợp với thông tin cây
        query = """
        SELECT 
            c.loai_cay as ten_hang,
            n.so_luong,
            n.gia_nhap as gia_tien,
            n.ngay_nhap as ngay
        FROM nhapkho n
        JOIN cayxanh c ON n.cay_xanh_id = c.id
        ORDER BY n.ngay_nhap DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            print("\n❌ Không có dữ liệu để export!")
            return None
        
        # Chuẩn bị dữ liệu
        data = []
        for row in rows:
            ten_hang, so_luong, gia_tien, ngay = row
            # Format ngày
            if ngay:
                try:
                    if isinstance(ngay, str):
                        ngay_str = ngay[:10]  # Lấy YYYY-MM-DD
                    else:
                        ngay_str = str(ngay)[:10]
                except:
                    ngay_str = str(ngay)
            else:
                ngay_str = ''
            
            data.append({
                'Tên hàng': ten_hang or '',
                'Số lượng': so_luong or 0,
                'Giá tiền': gia_tien or 0,
                'Ngày': ngay_str
            })
        
        # Tạo DataFrame
        df = pd.DataFrame(data)
        
        # Tạo tên file với timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'DuLieuNhapKho_{timestamp}.xlsx'
        
        # Export ra Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n✅ Export thành công!")
        print(f"📁 File: {filename}")
        print(f"📊 Số dòng: {len(data)}")
        print(f"\n📍 Vị trí file: {os.path.abspath(filename)}")
        
        return filename
        
    finally:
        conn.close()

if __name__ == '__main__':
    # Lưu đường dẫn file script để xóa sau
    script_path = os.path.abspath(__file__)
    
    try:
        filename = export_to_excel()
        
        if filename:
            print("\n" + "="*80)
            print("🗑️  Đang xóa file script...")
            
            # Xóa file script sau khi export xong
            try:
                os.remove(script_path)
                print(f"✅ Đã xóa file: {os.path.basename(script_path)}")
            except Exception as e:
                print(f"⚠️  Không thể xóa file script: {e}")
                print(f"   Vui lòng xóa thủ công: {script_path}")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
