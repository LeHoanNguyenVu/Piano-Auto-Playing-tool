"""
Bulk Uploader Tool — Tự động hóa việc thêm hàng ngàn bài nhạc lên Supabase.
Cách dùng: 
1. Để các file .mid vào một thư mục (mặc định là 'upload_queue')
2. Chạy lệnh: python bulk_uploader.py
"""

import os
import sys
import mido
from supabase import create_client, Client
from library.cloud_database import SUPABASE_URL, SUPABASE_KEY

# THƯ MỤC CHỨA NHẠC CẦN UPLOAD
SOURCE_FOLDER = "upload_queue"
# BUCKET TRÊN SUPABASE
STORAGE_BUCKET = "songs"
# BẢNG TRÊN SUPABASE
TABLE_NAME = "songs_catalog"

def get_midi_title(file_path):
    """Lấy tên bài hát từ metadata của file MIDI hoặc từ tên file."""
    try:
        mid = mido.MidiFile(file_path)
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'track_name' and msg.name.strip():
                    return msg.name.strip()
    except:
        pass
    return os.path.splitext(os.path.basename(file_path))[0]

def upload_folder():
    if not os.path.exists(SOURCE_FOLDER):
        os.makedirs(SOURCE_FOLDER)
        print(f"❌ Thư mục '{SOURCE_FOLDER}' không tồn tại. Đã tạo mới cho bạn.")
        print("Hãy chép các file .mid vào đó rồi chạy lại script này.")
        return

    # Khởi tạo Supabase Client
    # Lưu ý: Nên dùng Service Role Key nếu bị lỗi RLS (không có quyền chèn dữ liệu)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.mid', '.midi'))]
    if not files:
        print(f"ℹ️ Không tìm thấy file MIDI nào trong '{SOURCE_FOLDER}'.")
        return

    print(f"🚀 Bắt đầu upload {len(files)} bài nhạc...")

    for filename in files:
        file_path = os.path.join(SOURCE_FOLDER, filename)
        title = get_midi_title(file_path)
        # Giả định artist là tên file nếu không có metadata (bạn có thể sửa logic này)
        artist = "Unknown Artist"
        if " - " in title:
            parts = title.split(" - ", 1)
            artist, title = parts[0], parts[1]

        print(f"\n──────────────────────────────────────────")
        print(f"📦 Đang xử lý: {filename}")
        
        try:
            # 1. Upload lên Storage
            with open(file_path, 'rb') as f:
                # Ghi đè nếu đã tồn tại bằng upsert=True
                res = supabase.storage.from_(STORAGE_BUCKET).upload(
                    path=filename,
                    file=f,
                    file_options={"content-type": "audio/midi", "x-upsert": "true"}
                )
            
            # 2. Lấy Public URL
            file_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)
            
            # 3. Chèn vào Database
            song_data = {
                "title": title,
                "artist": artist,
                "file_url": file_url,
                "play_count": 0
            }
            
            # Kiểm tra xem bài hát đã tồn tại chưa để tránh trùng lặp (dựa trên file_url)
            check = supabase.table(TABLE_NAME).select("id").eq("file_url", file_url).execute()
            
            if check.data:
                print(f"🔄 Bài hát đã tồn tại trên DB. Đang cập nhật thông tin...")
                supabase.table(TABLE_NAME).update(song_data).eq("file_url", file_url).execute()
            else:
                print(f"✨ Đang thêm mới vào Database...")
                supabase.table(TABLE_NAME).insert(song_data).execute()
            
            print(f"✅ Thành công: {title}")
            
        except Exception as e:
            print(f"❌ Lỗi khi xử lý {filename}: {e}")

    print(f"\n🏁 Đã hoàn thành tất cả!")

if __name__ == "__main__":
    upload_folder()
