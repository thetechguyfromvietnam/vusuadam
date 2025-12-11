# Hướng Dẫn Sử Dụng Supabase

## Bước 1: Lấy Connection String từ Supabase

1. Vào [Supabase Dashboard](https://app.supabase.com)
2. Chọn project: **supabase-gray-dog**
3. Vào **Settings** → **Database**
4. Scroll xuống phần **Connection string**
5. Copy **URI** hoặc **Connection pooling** (khuyến nghị dùng Connection pooling)
6. Format sẽ là: `postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres`

## Bước 2: Thêm vào Vercel Environment Variables

1. Vào Vercel Dashboard → Project → **Settings** → **Environment Variables**
2. Thêm biến:
   - **Name**: `DATABASE_URL` hoặc `POSTGRES_URL`
   - **Value**: Connection string từ Supabase (thay [YOUR-PASSWORD] bằng password thật)
3. Click **Save**

## Bước 3: Migrate Dữ Liệu

```bash
# Cài đặt psycopg2
pip install psycopg2-binary

# Set connection string
export DATABASE_URL='postgresql://postgres:password@db.xxx.supabase.co:5432/postgres'

# Chạy migrate
python3 setup_vercel_postgres.py
```

## Bước 4: Deploy

```bash
git push
```

## Lưu Ý

- Supabase dùng PostgreSQL, nên app.py đã hỗ trợ sẵn
- Connection string phải có password thật (không phải [YOUR-PASSWORD])
- Nên dùng Connection pooling cho production
- Database sẽ persistent và không bị mất

