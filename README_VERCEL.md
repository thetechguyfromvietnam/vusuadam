# Deploy lên Vercel

## Cấu hình đã thêm

1. **vercel.json** - Cấu hình Vercel để chạy Flask app
2. **api/index.py** - Entry point cho Vercel serverless function
3. **Database path** - Tự động sử dụng `/tmp` trên Vercel (read-only filesystem)

## Lưu ý quan trọng

⚠️ **SQLite trên Vercel có hạn chế:**
- Vercel sử dụng serverless functions, mỗi request có thể chạy trên instance khác nhau
- Database SQLite trong `/tmp` sẽ bị mất khi function restart
- **Khuyến nghị:** Sử dụng database bên ngoài (PostgreSQL, MySQL) cho production

## Giải pháp đề xuất

1. **Sử dụng Vercel Postgres** (miễn phí tier)
2. Hoặc **PlanetScale** (MySQL serverless)
3. Hoặc **Supabase** (PostgreSQL)

## Cách deploy

```bash
# Cài Vercel CLI
npm i -g vercel

# Deploy
vercel

# Deploy production
vercel --prod
```

## Environment Variables (nếu dùng database bên ngoài)

Thêm vào Vercel Dashboard:
- `DATABASE_URL` - Connection string cho database
- `VERCEL=1` - Để app biết đang chạy trên Vercel

