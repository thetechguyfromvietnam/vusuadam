#!/usr/bin/env python3
"""
Script để migrate database từ SQLite sang PostgreSQL (Vercel Postgres)
và upload dữ liệu lên Vercel
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

def migrate_to_postgres():
    """Migrate dữ liệu từ SQLite sang PostgreSQL"""
    
    print("="*80)
    print("🔄 MIGRATE DATABASE TỪ SQLITE SANG POSTGRESQL")
    print("="*80)
    
    # Đọc connection string từ environment variable
    postgres_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
    
    if not postgres_url:
        print("\n❌ THIẾU POSTGRES CONNECTION STRING!")
        print("\nCách lấy:")
        print("1. Vào Vercel Dashboard → Project → Storage → Create Database")
        print("2. Chọn 'Postgres'")
        print("3. Copy connection string")
        print("4. Thêm vào Vercel Environment Variables:")
        print("   - POSTGRES_URL hoặc DATABASE_URL")
        print("\nHoặc chạy script với:")
        print("   POSTGRES_URL='your-connection-string' python3 setup_vercel_postgres.py")
        return False
    
    # Đọc SQLite database
    sqlite_path = 'instance/cayxanh.db'
    if not os.path.exists(sqlite_path):
        sqlite_path = 'cayxanh.db'
    
    if not os.path.exists(sqlite_path):
        print(f"\n❌ Không tìm thấy SQLite database: {sqlite_path}")
        return False
    
    print(f"\n📖 Đang đọc SQLite: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Kết nối PostgreSQL
    print("🔗 Đang kết nối PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(postgres_url)
        pg_cursor = pg_conn.cursor()
        print("✅ Kết nối thành công!")
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return False
    
    try:
        # Tạo tables trong PostgreSQL
        print("\n📝 Đang tạo tables...")
        
        pg_cursor.execute('''
            CREATE TABLE IF NOT EXISTS cayxanh (
                id SERIAL PRIMARY KEY,
                ma_cay VARCHAR(50) UNIQUE NOT NULL,
                loai_cay VARCHAR(200) NOT NULL,
                ton_kho FLOAT NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        pg_cursor.execute('''
            CREATE TABLE IF NOT EXISTS nhapkho (
                id SERIAL PRIMARY KEY,
                cay_xanh_id INTEGER NOT NULL,
                so_luong FLOAT NOT NULL,
                gia_nhap FLOAT NOT NULL,
                phi_ship FLOAT DEFAULT 0.0,
                tong_tien FLOAT NOT NULL,
                ngay_nhap DATE NOT NULL,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cay_xanh_id) REFERENCES cayxanh(id) ON DELETE CASCADE
            )
        ''')
        
        pg_cursor.execute('''
            CREATE TABLE IF NOT EXISTS xuatkho (
                id SERIAL PRIMARY KEY,
                cay_xanh_id INTEGER NOT NULL,
                so_luong FLOAT NOT NULL,
                ngay_xuat DATE NOT NULL,
                ly_do VARCHAR(200),
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cay_xanh_id) REFERENCES cayxanh(id) ON DELETE CASCADE
            )
        ''')
        
        pg_conn.commit()
        print("✅ Tables đã được tạo!")
        
        # Migrate dữ liệu cayxanh
        print("\n📦 Đang migrate dữ liệu cayxanh...")
        sqlite_cursor.execute('SELECT ma_cay, loai_cay, ton_kho, created_at, updated_at FROM cayxanh')
        cay_data = sqlite_cursor.fetchall()
        
        if cay_data:
            # Clear existing data (optional)
            pg_cursor.execute('DELETE FROM nhapkho')  # Delete first due to foreign key
            pg_cursor.execute('DELETE FROM xuatkho')
            pg_cursor.execute('DELETE FROM cayxanh')
            
            execute_values(
                pg_cursor,
                '''INSERT INTO cayxanh (ma_cay, loai_cay, ton_kho, created_at, updated_at)
                   VALUES %s ON CONFLICT (ma_cay) DO UPDATE SET
                   loai_cay = EXCLUDED.loai_cay,
                   ton_kho = EXCLUDED.ton_kho,
                   updated_at = EXCLUDED.updated_at''',
                cay_data
            )
            print(f"  ✅ Đã migrate {len(cay_data)} cây")
        
        # Migrate dữ liệu nhapkho
        print("\n📥 Đang migrate dữ liệu nhapkho...")
        sqlite_cursor.execute('''
            SELECT n.cay_xanh_id, n.so_luong, n.gia_nhap, n.phi_ship, 
                   n.tong_tien, n.ngay_nhap, n.ghi_chu, n.created_at
            FROM nhapkho n
            JOIN cayxanh c ON n.cay_xanh_id = c.id
        ''')
        nhap_data = sqlite_cursor.fetchall()
        
        if nhap_data:
            # Map SQLite cay_xanh_id to PostgreSQL id
            sqlite_cursor.execute('SELECT id, ma_cay FROM cayxanh')
            id_map = {row[0]: row[1] for row in sqlite_cursor.fetchall()}
            
            pg_cursor.execute('SELECT id, ma_cay FROM cayxanh')
            pg_id_map = {row[1]: row[0] for row in pg_cursor.fetchall()}
            
            nhap_data_mapped = []
            for row in nhap_data:
                sqlite_id = row[0]
                ma_cay = id_map.get(sqlite_id)
                pg_id = pg_id_map.get(ma_cay)
                if pg_id:
                    nhap_data_mapped.append((pg_id,) + row[1:])
            
            if nhap_data_mapped:
                execute_values(
                    pg_cursor,
                    '''INSERT INTO nhapkho (cay_xanh_id, so_luong, gia_nhap, phi_ship, 
                                          tong_tien, ngay_nhap, ghi_chu, created_at)
                       VALUES %s''',
                    nhap_data_mapped
                )
                print(f"  ✅ Đã migrate {len(nhap_data_mapped)} phiếu nhập")
        
        # Migrate dữ liệu xuatkho
        print("\n📤 Đang migrate dữ liệu xuatkho...")
        sqlite_cursor.execute('''
            SELECT x.cay_xanh_id, x.so_luong, x.ngay_xuat, x.ly_do, x.ghi_chu, x.created_at
            FROM xuatkho x
            JOIN cayxanh c ON x.cay_xanh_id = c.id
        ''')
        xuat_data = sqlite_cursor.fetchall()
        
        if xuat_data:
            # Map IDs
            sqlite_cursor.execute('SELECT id, ma_cay FROM cayxanh')
            id_map = {row[0]: row[1] for row in sqlite_cursor.fetchall()}
            
            pg_cursor.execute('SELECT id, ma_cay FROM cayxanh')
            pg_id_map = {row[1]: row[0] for row in pg_cursor.fetchall()}
            
            xuat_data_mapped = []
            for row in xuat_data:
                sqlite_id = row[0]
                ma_cay = id_map.get(sqlite_id)
                pg_id = pg_id_map.get(ma_cay)
                if pg_id:
                    xuat_data_mapped.append((pg_id,) + row[1:])
            
            if xuat_data_mapped:
                execute_values(
                    pg_cursor,
                    '''INSERT INTO xuatkho (cay_xanh_id, so_luong, ngay_xuat, ly_do, ghi_chu, created_at)
                       VALUES %s''',
                    xuat_data_mapped
                )
                print(f"  ✅ Đã migrate {len(xuat_data_mapped)} phiếu xuất")
        
        pg_conn.commit()
        
        # Verify
        pg_cursor.execute('SELECT COUNT(*) FROM cayxanh')
        cay_count = pg_cursor.fetchone()[0]
        pg_cursor.execute('SELECT COUNT(*) FROM nhapkho')
        nhap_count = pg_cursor.fetchone()[0]
        pg_cursor.execute('SELECT COUNT(*) FROM xuatkho')
        xuat_count = pg_cursor.fetchone()[0]
        
        print("\n" + "="*80)
        print("✅ MIGRATE THÀNH CÔNG!")
        print("="*80)
        print(f"  📦 Cây: {cay_count}")
        print(f"  📥 Phiếu nhập: {nhap_count}")
        print(f"  📤 Phiếu xuất: {xuat_count}")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()
        pg_conn.rollback()
        return False
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == '__main__':
    success = migrate_to_postgres()
    if not success:
        sys.exit(1)

