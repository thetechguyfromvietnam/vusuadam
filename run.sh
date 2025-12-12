#!/bin/bash

echo "🌿 Khởi động Phần Mềm Quản Lý Cây Xanh - KimBioFarm"
echo "=================================================="
echo ""

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 chưa được cài đặt!"
    exit 1
fi

# Kiểm tra pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 chưa được cài đặt!"
    exit 1
fi

# Cài đặt dependencies
echo "📦 Đang cài đặt dependencies..."
pip3 install -r requirements.txt

echo ""
echo "✅ Cài đặt hoàn tất!"
echo ""
echo "🚀 Đang khởi động ứng dụng..."
echo "📍 Truy cập: http://localhost:5000"
echo ""
echo "Nhấn Ctrl+C để dừng ứng dụng"
echo ""

# Chạy ứng dụng
python3 app.py


