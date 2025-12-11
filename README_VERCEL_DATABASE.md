# 📊 Hướng Dẫn Upload Database Lên Vercel

## ⚠️ Vấn Đề Với SQLite Trên Vercel

SQLite **KHÔNG PHÙ HỢP** cho Vercel vì:
- Vercel sử dụng serverless functions
- Database trong `/tmp` sẽ **BỊ MẤT** khi function restart
- Mỗi request có thể chạy trên instance khác nhau
- Không có persistence

## ✅ Giải Pháp: Sử Dụng PostgreSQL

### Cách 1: Vercel Postgres (Khuyến nghị)

#### Bước 1: Tạo Postgres Database trên Vercel

1. Vào [Vercel Dashboard](https://vercel.com/dashboard)
2. Chọn project của bạn
3. Vào tab **Storage**
4. Click **Create Database**
5. Chọn **Postgres**
6. Chọn plan (Hobby plan miễn phí)
7. Click **Create**

#### Bước 2: Lấy Connection String

1. Sau khi tạo xong, vào **Storage** → **Postgres**
2. Copy **Connection String** (dạng: `postgres://...`)
3. Vào **Settings** → **Environment Variables**
4. Thêm biến:
   - **Name**: `POSTGRES_URL` hoặc `DATABASE_URL`
   - **Value**: Connection string vừa copy
5. Click **Save**

#### Bước 3: Cài Đặt psycopg2

Thêm vào `requirements.txt`:
```
psycopg2-binary==2.9.9
```

#### Bước 4: Cập Nhật app.py

Thay đổi database configuration:

```python
import os
from urllib.parse import urlparse

# Database URI
if os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL'):
    # Use PostgreSQL
    db_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
    # Vercel Postgres uses postgres://, SQLAlchemy needs postgresql://
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    # Fallback to SQLite (local development)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cayxanh.db'
```

#### Bước 5: Migrate Dữ Liệu

1. Cài đặt psycopg2:
```bash
pip install psycopg2-binary
```

2. Chạy script migrate:
```bash
POSTGRES_URL='your-connection-string' python3 setup_vercel_postgres.py
```

Hoặc set environment variable trong terminal:
```bash
export POSTGRES_URL='your-connection-string'
python3 setup_vercel_postgres.py
```

#### Bước 6: Deploy

```bash
git add .
git commit -m "Switch to PostgreSQL"
git push
```

Vercel sẽ tự động deploy và sử dụng PostgreSQL!

---

### Cách 2: Supabase (PostgreSQL Free Tier)

1. Tạo account tại [supabase.com](https://supabase.com)
2. Tạo project mới
3. Vào **Settings** → **Database**
4. Copy **Connection String**
5. Thêm vào Vercel Environment Variables như trên
6. Chạy script migrate

---

### Cách 3: PlanetScale (MySQL Serverless)

1. Tạo account tại [planetscale.com](https://planetscale.com)
2. Tạo database
3. Lấy connection string
4. Cập nhật app.py để dùng MySQL
5. Migrate dữ liệu

---

## 🔄 Script Migrate

File `setup_vercel_postgres.py` sẽ:
- Đọc dữ liệu từ SQLite local
- Tạo tables trong PostgreSQL
- Migrate tất cả dữ liệu
- Verify kết quả

## 📝 Lưu Ý

- **Local development**: Vẫn dùng SQLite
- **Vercel production**: Dùng PostgreSQL
- Database sẽ được tự động sync khi deploy
- Dữ liệu sẽ persistent và không bị mất

## 🚀 Sau Khi Migrate

1. Deploy lại lên Vercel
2. Kiểm tra logs để đảm bảo kết nối thành công
3. Test các chức năng trên web
4. Dữ liệu sẽ hiển thị đầy đủ!

