
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from library.cloud_database import CloudDatabase
    print("Đang thử kết nối Supabase...")
    db = CloudDatabase()
    if db.supabase:
        print("✅ Thư viện Supabase đã được nhận diện!")
        # Thử refresh catalog (sẽ in lỗi nếu bảng chưa có dữ liệu hoặc sai tên)
        db.refresh_catalog()
        print(f"✅ Đã kết nối. Số lượng bài hát trong kho: {db.song_count}")
    else:
        print("❌ Chưa cấu hình URL/Key trong file cloud_database.py")
except Exception as e:
    print(f"❌ Lỗi: {e}")
