# 🌿 Phần Mềm Quản Lý Cây Xanh - KimBioFarm

Hệ thống quản lý nhập xuất tồn cây xanh với giao diện web hiện đại, dễ sử dụng.

## ✨ Tính Năng

- 📊 **Dashboard**: Tổng quan thống kê tồn kho, nhập xuất trong tháng
- 📦 **Quản Lý Tồn Kho**: Xem danh sách tất cả cây với tìm kiếm và phân trang
- 📥 **Nhập Hàng**: Ghi nhận nhập hàng với giá nhập biến động theo ngày
- 📤 **Xuất Hàng**: Ghi nhận xuất hàng (bán, mất, hỏng...)
- 📜 **Lịch Sử**: Xem lịch sử nhập xuất chi tiết
- 📄 **Import Excel**: Import dữ liệu từ file Excel hiện có

## 🚀 Cài Đặt

### 1. Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Chạy ứng dụng

```bash
python app.py
```

Ứng dụng sẽ chạy tại: `http://localhost:5000`

## 📋 Hướng Dẫn Sử Dụng

### Import dữ liệu từ Excel

1. Vào menu **Import Excel**
2. Chọn file Excel `NHẬP XUẤT TỒN CAY XANH KIMBIOFARM.xlsx`
3. Click **Import Dữ Liệu**
4. Hệ thống sẽ tự động import tất cả cây và lịch sử nhập hàng

### Nhập hàng mới

1. Vào menu **Nhập Hàng**
2. Nhập hoặc chọn mã cây
3. Điền thông tin: số lượng, giá nhập (có thể khác mỗi lần nhập), phí ship
4. Chọn ngày nhập
5. Click **Xác Nhận Nhập Hàng**

### Xuất hàng

1. Vào menu **Xuất Hàng**
2. Chọn cây từ danh sách (chỉ hiển thị cây còn tồn kho)
3. Nhập số lượng xuất
4. Chọn lý do: Bán hàng, Mất, Hỏng, Chuyển kho, Khác
5. Click **Xác Nhận Xuất Hàng**

### Xem tồn kho

1. Vào menu **Tồn Kho**
2. Có thể tìm kiếm theo mã cây hoặc loại cây
3. Xem chi tiết tồn kho của từng loại cây

## 🗄️ Cấu Trúc Database

- **CayXanh**: Thông tin cây (mã cây, loại cây, tồn kho)
- **NhapKho**: Lịch sử nhập hàng (số lượng, giá nhập, ngày nhập)
- **XuatKho**: Lịch sử xuất hàng (số lượng, lý do, ngày xuất)

## 📝 Lưu Ý

- Giá nhập có thể thay đổi theo từng lần nhập
- Tồn kho được tự động cập nhật khi nhập/xuất
- Hệ thống tự động tính tổng tiền nhập = (số lượng × giá nhập) + phí ship
- Khi xuất hàng, hệ thống sẽ kiểm tra tồn kho trước khi cho phép xuất

## 🛠️ Công Nghệ Sử Dụng

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: Bootstrap 5, jQuery
- **Icons**: Bootstrap Icons

## 📞 Hỗ Trợ

Nếu có vấn đề, vui lòng kiểm tra:
- File Excel có đúng format không
- Database đã được tạo chưa (tự động tạo khi chạy lần đầu)
- Port 5000 có bị chiếm không

---

© 2025 KimBioFarm - Quản Lý Cây Xanh

