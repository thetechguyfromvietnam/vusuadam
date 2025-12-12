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
- **Database**: PostgreSQL (Supabase/Vercel) hoặc SQLite (local development)
- **Frontend**: Bootstrap 5, jQuery
- **Icons**: Bootstrap Icons

## ⚙️ Cấu Hình Database

### ⚠️ QUAN TRỌNG: Database trên Vercel

**Trên Vercel, bạn PHẢI cấu hình PostgreSQL database. SQLite KHÔNG THỂ lưu trữ dữ liệu trên Vercel vì filesystem là read-only và dữ liệu sẽ bị mất sau mỗi lần deploy.**

### Local Development (SQLite)
Mặc định sử dụng SQLite, không cần cấu hình gì thêm.

### Production (PostgreSQL) - BẮT BUỘC trên Vercel

#### Cách 1: Sử dụng Vercel Postgres
1. Vào Vercel Dashboard → Project → Storage
2. Tạo Vercel Postgres database
3. Vercel sẽ tự động thêm `POSTGRES_URL` vào environment variables
4. Redeploy ứng dụng

#### Cách 2: Sử dụng Supabase hoặc PostgreSQL khác
1. Tạo PostgreSQL database (Supabase, Neon, Railway, etc.)
2. **Lấy Database Password từ Supabase:**
   - Vào Supabase Dashboard → Project Settings → Database
   - Tìm phần "Database Password" hoặc "Connection string"
   - Nếu chưa có password, click "Reset database password" để tạo mới
   - Copy password (lưu ý: password có thể chứa ký tự đặc biệt)
3. **Tạo Connection String:**
   - Format: `postgresql://postgres:[YOUR_PASSWORD]@db.[project-ref].supabase.co:5432/postgres`
   - Thay `[YOUR_PASSWORD]` bằng password thực tế từ Supabase
   - Ví dụ: `postgresql://postgres:your_actual_password@db.qflrmqlsgkxxqopetolg.supabase.co:5432/postgres`
4. **Thêm vào Vercel:**
   - Vào Vercel Dashboard → Project → Settings → Environment Variables
   - Click "Add New"
   - **Key**: `DATABASE_URL` hoặc `POSTGRES_URL`
   - **Value**: Dán connection string đã tạo (với password thực tế)
   - **Environment**: Chọn tất cả (Production, Preview, Development)
   - Click "Save"
5. **Redeploy ứng dụng:**
   - Vào Deployments tab
   - Click "Redeploy" trên deployment mới nhất
   - Hoặc push code mới để trigger auto-deploy

#### Kiểm tra Database đã được cấu hình
- Ứng dụng sẽ tự động phát hiện và sử dụng PostgreSQL
- Nếu không có database URL, ứng dụng sẽ báo lỗi rõ ràng
- Check logs trong Vercel để xem thông báo: "✓ Using PostgreSQL (Production)"

### Lưu ý
- **KHÔNG** sử dụng SQLite trên Vercel - dữ liệu sẽ bị mất
- Database connection string phải có format: `postgresql://user:password@host:port/database`
- Ứng dụng tự động xử lý URL encoding cho password có ký tự đặc biệt

## 📸 Cấu Hình Vercel Blob Storage (Ảnh)

Ứng dụng hỗ trợ lưu trữ ảnh trên Vercel Blob storage cho production.

### Production (Vercel Blob)
1. Tạo Vercel Blob store trong Vercel Dashboard
2. Lấy `BLOB_READ_WRITE_TOKEN` từ Vercel Dashboard
3. Thêm vào environment variables trong Vercel:
   ```
   BLOB_READ_WRITE_TOKEN=your_token_here
   ```
4. Ứng dụng sẽ tự động sử dụng Blob storage khi có `BLOB_READ_WRITE_TOKEN`
5. Nếu không có token, sẽ fallback về local storage (hoặc `/tmp` trên Vercel)

### Local Development
Mặc định lưu ảnh trong `static/uploads/images/` khi không có `BLOB_READ_WRITE_TOKEN`

## 📞 Hỗ Trợ

Nếu có vấn đề, vui lòng kiểm tra:
- File Excel có đúng format không
- Database đã được tạo chưa (tự động tạo khi chạy lần đầu)
- Port 5000 có bị chiếm không

---

© 2025 KimBioFarm - Quản Lý Cây Xanh



