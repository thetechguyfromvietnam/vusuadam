# 🚀 Hướng Dẫn Upload Database Lên Vercel

## ⚠️ Vấn Đề

SQLite **KHÔNG hoạt động tốt** trên Vercel vì:
- Database trong `/tmp` sẽ **BỊ MẤT** khi function restart
- Mỗi request có thể chạy trên instance khác nhau
- Không có persistence

## ✅ Giải Pháp: Vercel Postgres

### Bước 1: Tạo Postgres Database

1. Vào [Vercel Dashboard](https://vercel.com/dashboard)
2. Chọn project → **Storage** tab
3. Click **Create Database** → Chọn **Postgres**
4. Chọn plan **Hobby** (miễn phí)
5. Click **Create**

### Bước 2: Lấy Connection String

1. Vào **Storage** → Click vào database vừa tạo
2. Copy **Connection String** (dạng: `postgres://...`)
3. Vào **Settings** → **Environment Variables**
4. Thêm:
   - **Name**: `POSTGRES_URL`
   - **Value**: Connection string vừa copy
5. Click **Save**

### Bước 3: Migrate Dữ Liệu

1. Cài đặt psycopg2:
```bash
pip install psycopg2-binary
```

2. Chạy script migrate:
```bash
# Set environment variable
export POSTGRES_URL='your-connection-string-here'

# Chạy script
python3 setup_vercel_postgres.py
```

Script sẽ:
- Đọc dữ liệu từ SQLite local (`instance/cayxanh.db`)
- Tạo tables trong PostgreSQL
- Migrate tất cả dữ liệu (cây, nhập, xuất)
- Verify kết quả

### Bước 4: Deploy

```bash
git add .
git commit -m "Setup PostgreSQL"
git push
```

Vercel sẽ tự động:
- Cài đặt `psycopg2-binary` từ `requirements.txt`
- Sử dụng `POSTGRES_URL` environment variable
- Kết nối với PostgreSQL
- Dữ liệu sẽ persistent!

## 📊 Kiểm Tra

Sau khi deploy:
1. Vào Vercel Dashboard → **Functions** → View Logs
2. Kiểm tra xem có lỗi kết nối không
3. Truy cập web và kiểm tra dữ liệu

## 🔄 Cập Nhật Dữ Liệu

Khi có dữ liệu mới từ Excel:
1. Chạy `update_data.py` để cập nhật SQLite local
2. Chạy `setup_vercel_postgres.py` để sync lên PostgreSQL
3. Hoặc cập nhật trực tiếp trên web (nhập/xuất hàng)

## 💡 Lưu Ý

- **Local**: Vẫn dùng SQLite (`instance/cayxanh.db`)
- **Vercel**: Dùng PostgreSQL (persistent)
- Database sẽ không bị mất khi function restart
- Có thể scale tốt hơn SQLite

