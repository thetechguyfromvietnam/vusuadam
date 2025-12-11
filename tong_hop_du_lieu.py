#!/usr/bin/env python3
"""
Script tổng hợp dữ liệu từ các file Excel:
- BẢNG TÍNH GIÁ BÁN SẢN PHẨM (1).xlsx (lấy giá nhập) - Bảng Tính Giá Cây Xanh
- Tồn T12.20155.xlsx (lấy tồn kho và giá nhập) - Tồn T1220155

Tổng hợp: Tên hàng, Số lượng tồn kho hiện tại, Giá nhập, Ngày

CÁCH SỬ DỤNG:
1. Đảm bảo có 2 file Excel trong cùng thư mục:
   - BẢNG TÍNH GIÁ BÁN SẢN PHẨM (1).xlsx
   - Tồn T12.20155.xlsx

2. Chạy script:
   python3 tong_hop_du_lieu.py

3. File output sẽ được tạo: DuLieuTongHop_YYYYMMDD_HHMMSS.xlsx

4. Upload file Excel đó lên production qua giao diện Import Excel

LƯU Ý:
- Script sẽ tự động tìm và khớp tên hàng giữa 2 file
- Ưu tiên lấy giá từ BẢNG TÍNH GIÁ BÁN SẢN PHẨM (1).xlsx
- Export tất cả sản phẩm (kể cả tồn kho = 0)
"""

import os
import pandas as pd
from datetime import datetime, date

def doc_bang_tinh_gia():
    """Đọc file BẢNG TÍNH GIÁ BÁN SẢN PHẨM (1).xlsx để lấy giá"""
    print("📖 Đang đọc BẢNG TÍNH GIÁ BÁN SẢN PHẨM (1).xlsx...")
    
    file_paths = [
        'BẢNG TÍNH GIÁ BÁN SẢN PHẨM (1).xlsx',
        'BẢNG TÍNH GIÁ BÁN SẢN PHẨM.xlsx',
        'BANG TINH GIA BAN SAN PHAM.xlsx'
    ]
    
    file_path = None
    for path in file_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if not file_path:
        print("⚠️  Không tìm thấy file BẢNG TÍNH GIÁ BÁN SẢN PHẨM (1).xlsx")
        return {}
    
    try:
        # Đọc tất cả các sheet
        excel_file = pd.ExcelFile(file_path)
        gia_dict = {}
        
        print(f"   Tìm thấy {len(excel_file.sheet_names)} sheet(s)")
        
        for sheet_name in excel_file.sheet_names:
            try:
                # Đọc với header=1 (dòng thứ 2)
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
                
                # Đọc với header=0 để kiểm tra giá trị trong dòng đầu
                df_header = pd.read_excel(file_path, sheet_name=sheet_name, header=0, nrows=2)
                
                # Tìm các cột
                ten_col = None
                gia_col = None
                
                # Tìm cột tên bằng cách kiểm tra giá trị trong dòng header
                for col_idx, col in enumerate(df.columns):
                    # Kiểm tra giá trị trong dòng header (dòng 1 của df_header)
                    if col_idx < len(df_header.columns):
                        header_val = str(df_header.iloc[1, col_idx]).lower() if len(df_header) > 1 and col_idx < len(df_header.columns) else ''
                        col_str = str(col).lower().strip()
                        
                        # Tìm cột "TÊN SẢN PHẨM"
                        if not ten_col:
                            if 'tên sản phẩm' in header_val or ('tên' in header_val and 'sản phẩm' in header_val):
                                ten_col = col
                            elif 'tên' in col_str and 'sản phẩm' in col_str:
                                ten_col = col
                            elif 'tên' in col_str or 'sản phẩm' in col_str:
                                # Kiểm tra xem cột này có chứa text không
                                sample = df[col].dropna().head(3)
                                if len(sample) > 0 and any(isinstance(v, str) and len(str(v).strip()) > 2 for v in sample):
                                    if not ten_col:
                                        ten_col = col
                        
                        # Tìm cột "GIÁ NHẬP" (ưu tiên "GIÁ NHẬP" thuần, không có số phía trước)
                        if not gia_col:
                            # Ưu tiên 1: "GIÁ NHẬP" thuần (không có số, không có "kho")
                            if header_val == 'giá nhập' or (header_val.startswith('giá nhập') and 'kho' not in header_val and not any(c.isdigit() for c in header_val[:5])):
                                gia_col = col
                            # Ưu tiên 2: "giá nhập" trong header (không có "kho")
                            elif 'giá nhập' in header_val and 'kho' not in header_val:
                                if not gia_col or 'giá nhập kho' in str(gia_col).lower():
                                    gia_col = col
                            # Ưu tiên 3: "giá nhập kho"
                            elif 'giá nhập kho' in header_val:
                                if not gia_col:
                                    gia_col = col
                            # Ưu tiên 4: tìm trong tên cột
                            elif 'giá nhập' in col_str and 'kho' not in col_str and not any(c.isdigit() for c in col_str[:5]):
                                if not gia_col:
                                    gia_col = col
                            elif 'giá nhập kho' in col_str:
                                if not gia_col:
                                    gia_col = col
                
                # Nếu không tìm thấy bằng header, tìm bằng tên cột
                if not ten_col:
                    for col in df.columns:
                        col_str = str(col).lower().strip()
                        if 'tên' in col_str and 'sản phẩm' in col_str:
                            ten_col = col
                            break
                        elif any(keyword in col_str for keyword in ['tên', 'hàng', 'sản phẩm']):
                            sample = df[col].dropna().head(3)
                            if len(sample) > 0 and any(isinstance(v, str) and len(str(v).strip()) > 2 for v in sample):
                                if not ten_col:
                                    ten_col = col
                
                if not gia_col:
                    for col in df.columns:
                        col_str = str(col).lower().strip()
                        if 'giá nhập' in col_str and 'kho' not in col_str:
                            gia_col = col
                            break
                        elif 'giá nhập kho' in col_str:
                            gia_col = col
                            break
                        elif any(keyword in col_str for keyword in ['giá mua', 'giá gốc', 'giá vốn']):
                            if not gia_col:
                                gia_col = col
                
                # Nếu không tìm thấy giá nhập, tìm cột giá (nhưng ưu tiên không phải giá bán)
                if not gia_col:
                    for col in df.columns:
                        col_str = str(col).lower().strip()
                        # Ưu tiên: có "giá" nhưng không phải "giá bán"
                        if 'giá' in col_str and 'bán' not in col_str:
                            gia_col = col
                            break
                
                # Nếu vẫn không tìm thấy, lấy cột có "giá" (kể cả giá bán - nhưng sẽ ưu tiên giá nhập từ nguồn khác)
                if not gia_col:
                    for col in df.columns:
                        col_str = str(col).lower().strip()
                        if 'giá' in col_str:
                            gia_col = col
                            break
                
                # Nếu không tìm thấy tên, thử các cột đầu tiên (bỏ qua Unnamed)
                if not ten_col:
                    for i in range(min(10, len(df.columns))):
                        col = df.columns[i]
                        col_str = str(col).lower().strip()
                        if 'unnamed' not in col_str and col_str != 'nan':
                            # Kiểm tra xem cột này có chứa text không
                            sample_vals = df[col].dropna().head(3)
                            if len(sample_vals) > 0:
                                # Nếu có ít nhất 1 giá trị là text dài > 2 ký tự
                                if any(isinstance(v, str) and len(str(v).strip()) > 2 for v in sample_vals):
                                    ten_col = col
                                    break
                
                # Nếu vẫn không tìm thấy, thử cột đầu tiên không phải Unnamed
                if not ten_col:
                    for col in df.columns:
                        if 'unnamed' not in str(col).lower():
                            ten_col = col
                            break
                
                if not ten_col and len(df.columns) > 0:
                    ten_col = df.columns[0]
                
                print(f"   Sheet '{sheet_name}': Tên={ten_col}, Giá={gia_col}")
                
                # Đọc dữ liệu
                for _, row in df.iterrows():
                    ten_hang = None
                    gia_nhap = None
                    
                    if ten_col:
                        ten_val = row.get(ten_col)
                        if pd.notna(ten_val):
                            ten_hang = str(ten_val).strip()
                            # Bỏ qua nếu tên chỉ là số hoặc rỗng
                            if not ten_hang or ten_hang == 'nan' or ten_hang.replace(' ', '').isdigit():
                                continue
                    
                    if gia_col:
                        gia_val = row.get(gia_col)
                        if pd.notna(gia_val):
                            try:
                                if isinstance(gia_val, str):
                                    gia_val = gia_val.replace(',', '').replace(' ', '').replace('.', '').strip()
                                gia_nhap = float(gia_val)
                            except:
                                pass
                    
                    # Lưu nếu có cả tên và giá hợp lệ
                    if ten_hang and ten_hang != 'nan' and len(ten_hang) > 1 and pd.notna(gia_nhap) and gia_nhap > 0:
                        # Lưu giá (nếu có nhiều, lấy giá lớn hơn hoặc giá mới nhất)
                        if ten_hang not in gia_dict:
                            gia_dict[ten_hang] = gia_nhap
                        else:
                            # Giữ giá lớn hơn (có thể là giá mới hơn)
                            if gia_nhap > gia_dict[ten_hang]:
                                gia_dict[ten_hang] = gia_nhap
                            
            except Exception as e:
                print(f"   ⚠️  Lỗi khi đọc sheet '{sheet_name}': {e}")
                continue
        
        print(f"✅ Đã đọc {len(gia_dict)} sản phẩm từ BẢNG TÍNH GIÁ")
        return gia_dict
        
    except Exception as e:
        print(f"⚠️  Lỗi khi đọc BẢNG TÍNH GIÁ: {e}")
        import traceback
        traceback.print_exc()
        return {}

def doc_nhap_xuat_ton():
    """Đọc file Tồn T12.20155.xlsx để lấy tồn kho"""
    print("📖 Đang đọc Tồn T12.20155.xlsx...")
    
    file_paths = [
        'Tồn T12.20155.xlsx',
        'Tồn T12.2015.xlsx',
        'Ton T12.20155.xlsx',
        'NHẬP XUẤT TỒN CAY XANH KIMBIOFARM.xlsx',
        'NHẬP XUẤT TỒN CAY XANH KIMBIOFARM.xlsx'
    ]
    
    file_path = None
    for path in file_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if not file_path:
        print("⚠️  Không tìm thấy file Tồn T12.20155.xlsx")
        return {}
    
    try:
        # Thử đọc sheet cụ thể trước
        sheet_names = ['NHẬP XUẤT TỒN  T12.2015', 'NHẬP XUẤT TỒN  T12.20155', 'Sheet1', None]
        df = None
        
        for sheet_name in sheet_names:
            try:
                if sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                else:
                    df = pd.read_excel(file_path)
                break
            except:
                continue
        
        if df is None:
            print("⚠️  Không thể đọc file Excel")
            return {}
        
        ton_kho_dict = {}
        gia_dict = {}
        phi_ship_dict = {}
        
        # Tìm các cột
        ma_cay_col = None
        ten_cay_col = None
        ton_kho_col = None
        gia_nhap_col = None
        phi_ship_col = None
        
        # Tìm tất cả các cột tồn trước, sau đó chọn cột có dữ liệu
        ton_cols = []
        for col in df.columns:
            col_str = str(col).lower().strip()
            if 'mã' in col_str and 'cây' in col_str:
                ma_cay_col = col
            elif 'loại' in col_str and 'cây' in col_str:
                ten_cay_col = col
            elif 'tồn' in col_str or 'ton' in col_str:
                ton_cols.append(col)
            elif 'giá' in col_str and 'nhập' in col_str:
                gia_nhap_col = col
            elif 'phí' in col_str and 'ship' in col_str:
                phi_ship_col = col
        
        # Chọn cột tồn có nhiều dữ liệu nhất
        if ton_cols:
            best_col = None
            best_count = 0
            for col in ton_cols:
                count = df[col].notna().sum()
                if count > best_count:
                    best_col = col
                    best_count = count
            if best_col:
                ton_kho_col = best_col
        
        # Nếu không tìm thấy, thử tìm theo tên khác
        if not ten_cay_col:
            for col in df.columns:
                col_str = str(col).lower().strip()
                if any(keyword in col_str for keyword in ['tên', 'hàng', 'sản phẩm']):
                    ten_cay_col = col
                    break
        
        if not ton_kho_col:
            for col in df.columns:
                col_str = str(col).lower().strip()
                if 'số lượng' in col_str or 'sl' in col_str:
                    ton_kho_col = col
                    break
        
        # Nếu vẫn không tìm thấy, thử tìm cột có chứa "tồn" hoặc "ton"
        if not ton_kho_col:
            for col in df.columns:
                col_str = str(col).lower().strip()
                if 'tồn' in col_str or 'ton' in col_str or 'tồn kho' in col_str:
                    ton_kho_col = col
                    break
        
        print(f"   Cột tìm thấy: Mã cây={ma_cay_col}, Tên={ten_cay_col}, Tồn={ton_kho_col}, Giá={gia_nhap_col}, Phí ship={phi_ship_col}")
        if ton_kho_col:
            count = df[ton_kho_col].notna().sum()
            non_zero = (df[ton_kho_col].fillna(0) > 0).sum()
            print(f"   Cột tồn '{ton_kho_col}' có {count} giá trị (trong đó {non_zero} > 0)")
        
        # Đọc dữ liệu
        for _, row in df.iterrows():
            ten_hang = None
            ton_kho = 0
            gia_nhap = None
            phi_ship = 0
            
            if ten_cay_col:
                ten_hang = str(row.get(ten_cay_col, '')).strip()
            
            if ton_kho_col:
                try:
                    ton_kho_val = row.get(ton_kho_col, 0)
                    if pd.notna(ton_kho_val):
                        # Thử convert sang số
                        if isinstance(ton_kho_val, str):
                            # Loại bỏ khoảng trắng và ký tự đặc biệt
                            ton_kho_val = ton_kho_val.strip().replace(',', '').replace(' ', '')
                        ton_kho = float(ton_kho_val) if ton_kho_val else 0
                    else:
                        ton_kho = 0
                except:
                    ton_kho = 0
            else:
                # Nếu không tìm thấy cột tồn, thử tìm trong tất cả các cột
                for col in df.columns:
                    col_str = str(col).lower().strip()
                    if 'tồn' in col_str or 'ton' in col_str:
                        try:
                            val = row.get(col)
                            if pd.notna(val):
                                if isinstance(val, str):
                                    val = val.strip().replace(',', '').replace(' ', '')
                                ton_kho = float(val) if val else 0
                                if ton_kho > 0:
                                    break
                        except:
                            pass
            
            if gia_nhap_col:
                try:
                    gia_val = row.get(gia_nhap_col)
                    if pd.notna(gia_val):
                        gia_nhap = float(gia_val)
                except:
                    pass
            
            if phi_ship_col:
                try:
                    phi_ship_val = row.get(phi_ship_col)
                    if pd.notna(phi_ship_val):
                        if isinstance(phi_ship_val, str):
                            phi_ship_val = phi_ship_val.strip().replace(',', '').replace(' ', '')
                        phi_ship = float(phi_ship_val) if phi_ship_val else 0
                except:
                    phi_ship = 0
            
            if ten_hang and ten_hang != 'nan' and ten_hang:
                # Lưu tồn kho (lấy giá trị cuối cùng, kể cả = 0)
                if ten_hang not in ton_kho_dict:
                    ton_kho_dict[ten_hang] = 0
                # Cập nhật tồn kho (ưu tiên giá trị > 0, nhưng vẫn lưu nếu = 0)
                if pd.notna(ton_kho):
                    ton_kho_dict[ten_hang] = ton_kho
                
                # Lưu giá nhập
                if gia_nhap and gia_nhap > 0:
                    if ten_hang not in gia_dict:
                        gia_dict[ten_hang] = gia_nhap
                
                # Lưu phí ship (lấy giá trị cuối cùng)
                if pd.notna(phi_ship):
                    phi_ship_dict[ten_hang] = phi_ship
        
        print(f"✅ Đã đọc {len(ton_kho_dict)} sản phẩm từ NHẬP XUẤT TỒN")
        return ton_kho_dict, gia_dict, phi_ship_dict
        
    except Exception as e:
        print(f"⚠️  Lỗi khi đọc NHẬP XUẤT TỒN: {e}")
        import traceback
        traceback.print_exc()
        return {}, {}, {}

def tong_hop_du_lieu():
    """Tổng hợp dữ liệu từ các file"""
    print("="*80)
    print("📊 TỔNG HỢP DỮ LIỆU TỪ CÁC FILE EXCEL")
    print("="*80)
    print()
    
    # Đọc giá từ BẢNG TÍNH GIÁ
    gia_tu_bang_tinh = doc_bang_tinh_gia()
    print()
    
    # Đọc tồn kho, giá và phí ship từ NHẬP XUẤT TỒN
    ton_kho_dict, gia_tu_nhap_xuat, phi_ship_dict = doc_nhap_xuat_ton()
    print()
    
    # Kết hợp dữ liệu
    print("🔄 Đang tổng hợp dữ liệu...")
    
    # Hàm chuẩn hóa tên để so sánh (bỏ khoảng trắng, chuyển chữ thường)
    def normalize_name(name):
        return str(name).lower().strip().replace(' ', '').replace('_', '').replace('-', '')
    
    # Ưu tiên lấy giá từ BẢNG TÍNH GIÁ (file chính)
    # Tạo mapping tên hàng (chuẩn hóa) - ưu tiên BẢNG TÍNH GIÁ
    gia_normalized = {}
    
    # Đầu tiên lấy từ BẢNG TÍNH GIÁ (ưu tiên cao nhất)
    for ten_hang, gia in gia_tu_bang_tinh.items():
        key = normalize_name(ten_hang)
        if gia > 0:
            gia_normalized[key] = (ten_hang, gia)
    
    # Sau đó bổ sung từ NHẬP XUẤT TỒN (nếu chưa có trong BẢNG TÍNH GIÁ)
    for ten_hang, gia in gia_tu_nhap_xuat.items():
        key = normalize_name(ten_hang)
        if key not in gia_normalized and gia > 0:
            gia_normalized[key] = (ten_hang, gia)
    
    # Tạo danh sách tổng hợp
    data = []
    ngay_hom_nay = date.today().strftime('%Y-%m-%d')
    
    print(f"   Tồn kho: {len(ton_kho_dict)} sản phẩm")
    print(f"   Giá từ NHẬP XUẤT: {len(gia_tu_nhap_xuat)} sản phẩm")
    print(f"   Giá từ BẢNG TÍNH: {len(gia_tu_bang_tinh)} sản phẩm")
    print(f"   Phí ship: {len(phi_ship_dict)} sản phẩm")
    
    # Hàm kiểm tra tên chỉ là số
    def is_only_number(name):
        """Kiểm tra xem tên có phải chỉ là số không"""
        if not name or pd.isna(name):
            return True
        name_str = str(name).strip()
        # Loại bỏ khoảng trắng và kiểm tra
        name_clean = name_str.replace(' ', '').replace(',', '').replace('.', '')
        # Nếu chỉ chứa số thì return True
        return name_clean.isdigit()
    
    # Lấy TẤT CẢ sản phẩm (kể cả tồn kho = 0)
    # Kết hợp tất cả sản phẩm từ cả 2 nguồn
    all_products = set(ton_kho_dict.keys())
    all_products.update(gia_tu_bang_tinh.keys())
    all_products.update(gia_tu_nhap_xuat.keys())
    
    # Lọc bỏ các sản phẩm có tên chỉ là số
    all_products = {p for p in all_products if not is_only_number(p)}
    
    print(f"   Đã lọc bỏ sản phẩm có tên chỉ là số")
    
    for ten_hang in sorted(all_products):  # Đã sorted theo tên
        so_luong = ton_kho_dict.get(ten_hang, 0)  # Mặc định = 0 nếu không có
        
        # Tìm giá tương ứng (so sánh chuẩn hóa)
        ten_normalized = normalize_name(ten_hang)
        gia_tien = 0
        ten_hang_final = ten_hang
        
        # Ưu tiên 1: Tìm chính xác (chuẩn hóa)
        if ten_normalized in gia_normalized:
            ten_goc, gia_tien = gia_normalized[ten_normalized]
            ten_hang_final = ten_goc
        else:
            # Ưu tiên 2: Tìm chính xác (không chuẩn hóa) - BẢNG TÍNH GIÁ trước
            if ten_hang in gia_tu_bang_tinh:
                gia_tien = gia_tu_bang_tinh[ten_hang]
            elif ten_hang in gia_tu_nhap_xuat:
                gia_tien = gia_tu_nhap_xuat[ten_hang]
            else:
                # Ưu tiên 3: Tìm tương đối (một phần tên) - BẢNG TÍNH GIÁ trước
                ten_hang_lower = ten_hang.lower()
                best_match = None
                best_score = 0
                
                for ten_gia, gia in gia_tu_bang_tinh.items():
                    ten_gia_lower = ten_gia.lower()
                    # Tính điểm khớp
                    if ten_hang_lower == ten_gia_lower:
                        best_match = (ten_gia, gia)
                        best_score = 100
                        break
                    elif ten_hang_lower in ten_gia_lower or ten_gia_lower in ten_hang_lower:
                        # Tính độ dài phần khớp
                        score = min(len(ten_hang_lower), len(ten_gia_lower)) / max(len(ten_hang_lower), len(ten_gia_lower))
                        if score > best_score:
                            best_match = (ten_gia, gia)
                            best_score = score
                
                if best_match and best_score > 0.5:  # Khớp ít nhất 50%
                    ten_hang_final, gia_tien = best_match
        
        # Tìm phí ship tương ứng
        phi_ship_tien = phi_ship_dict.get(ten_hang, 0)
        # Nếu không tìm thấy chính xác, thử tìm bằng tên chuẩn hóa
        if phi_ship_tien == 0:
            ten_normalized = normalize_name(ten_hang)
            for ten_phi, phi in phi_ship_dict.items():
                if normalize_name(ten_phi) == ten_normalized:
                    phi_ship_tien = phi
                    break
        
        # Thêm vào danh sách (TẤT CẢ sản phẩm, kể cả số lượng = 0)
        data.append({
            'Tên hàng': ten_hang_final,
            'Số lượng': so_luong,
            'Giá tiền': gia_tien if gia_tien > 0 else 0,
            'Phí ship': phi_ship_tien if phi_ship_tien > 0 else 0,
            'Ngày': ngay_hom_nay
        })
    
    # Đã được sorted ở trên khi lặp qua all_products
    print(f"   Tổng số sản phẩm: {len(data)}")
    print(f"   Sản phẩm có tồn kho > 0: {sum(1 for item in data if item['Số lượng'] > 0)}")
    print(f"   Sản phẩm tồn kho = 0: {sum(1 for item in data if item['Số lượng'] == 0)}")
    
    if not data:
        print("❌ Không có dữ liệu để tổng hợp!")
        return None
    
    # Tạo DataFrame
    df = pd.DataFrame(data)
    
    # Tạo tên file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'DuLieuTongHop_{timestamp}.xlsx'
    
    # Export ra Excel
    df.to_excel(filename, index=False, engine='openpyxl')
    
    # Thống kê
    so_luong_co_gia = sum(1 for item in data if item['Giá tiền'] > 0)
    so_luong_khong_gia = len(data) - so_luong_co_gia
    so_luong_co_phi_ship = sum(1 for item in data if item['Phí ship'] > 0)
    
    print(f"\n✅ Tổng hợp thành công!")
    print(f"📁 File: {filename}")
    print(f"📊 Tổng số sản phẩm: {len(data)}")
    print(f"   - Có giá: {so_luong_co_gia}")
    print(f"   - Chưa có giá: {so_luong_khong_gia}")
    print(f"   - Có phí ship: {so_luong_co_phi_ship}")
    print(f"📅 Ngày: {ngay_hom_nay}")
    print(f"\n📍 Vị trí file: {os.path.abspath(filename)}")
    
    if so_luong_khong_gia > 0:
        print(f"\n⚠️  Lưu ý: Có {so_luong_khong_gia} sản phẩm chưa có giá.")
        print("   Vui lòng mở file Excel và cập nhật giá thủ công nếu cần.")
    
    print("\n" + "="*80)
    print("💡 Mẹo: Bạn có thể chạy lại script này bất cứ lúc nào khi có dữ liệu mới!")
    print("="*80)
    
    return filename

if __name__ == '__main__':
    try:
        filename = tong_hop_du_lieu()
        if filename:
            print("✅ Hoàn tất!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
