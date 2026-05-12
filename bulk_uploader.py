"""
Bulk Uploader Tool — Tự động hóa việc thêm bài nhạc và ảnh bìa lên Supabase.
"""

import os
import sys
import mido
import shutil
from supabase import create_client, Client
from library.cloud_database import SUPABASE_URL, SUPABASE_KEY

# CẤU HÌNH
SOURCE_FOLDER = "upload_queue"
STORAGE_BUCKET = "Songs"
TABLE_NAME = "songs_catalog"

def clean_string(s):
    if not s: return ""
    return "".join(ch for ch in str(s) if ch.isprintable()).strip().replace("\x00", "")

def safe_filename(filename):
    import unicodedata
    import hashlib
    name, ext = os.path.splitext(filename)
    name = unicodedata.normalize('NFD', name)
    name = "".join(ch for ch in name if unicodedata.category(ch) != 'Mn')
    name = name.replace('đ', 'd').replace('Đ', 'D')
    safe = "".join(ch if (ch.isascii() and (ch.isalnum() or ch in '-_ ')) else '_' for ch in name)
    safe = safe.replace(' ', '_')
    while '__' in safe: safe = safe.replace('__', '_')
    return safe.strip('_') + ext

def get_midi_title(file_path):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    return clean_string(filename.replace("_", " "))

def upload_folder():
    if not os.path.exists(SOURCE_FOLDER): os.makedirs(SOURCE_FOLDER)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    all_files = os.listdir(SOURCE_FOLDER)
    unique_names = set(os.path.splitext(f)[0] for f in all_files if os.path.isfile(os.path.join(SOURCE_FOLDER, f)))
    
    if not unique_names:
        print(f"✨ Thư mục '{SOURCE_FOLDER}' đang trống.")
        return

    print(f"🚀 Bắt đầu xử lý {len(unique_names)} bài nhạc...")

    for name_only in unique_names:
        midi_file = None
        image_file = None
        for f in all_files:
            if os.path.splitext(f)[0] == name_only:
                ext = f.lower()
                if ext.endswith(('.mid', '.midi')): midi_file = f
                if ext.endswith(('.jpg', '.jpeg', '.png', '.webp')): image_file = f

        if not midi_file and not image_file: continue
        print(f"\n──────────────────────────────────────────\n📦 Đang xử lý: {name_only}")
        
        cover_url = None
        if image_file:
            print(f"🖼️ Uploading ảnh bìa...")
            storage_name = safe_filename(image_file)
            with open(os.path.join(SOURCE_FOLDER, image_file), 'rb') as f:
                supabase.storage.from_(STORAGE_BUCKET).upload(path=storage_name, file=f, file_options={"x-upsert": "true"})
            cover_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_name)

        file_url = None
        title = name_only.replace("_", " ")
        artist = "Unknown Artist"
        if midi_file:
            print(f"🎹 Uploading MIDI...")
            midi_path = os.path.join(SOURCE_FOLDER, midi_file)
            title = get_midi_title(midi_path)
            if " - " in title: artist, title = title.split(" - ", 1)
            storage_name = safe_filename(midi_file)
            with open(midi_path, 'rb') as f:
                supabase.storage.from_(STORAGE_BUCKET).upload(path=storage_name, file=f, file_options={"content-type": "audio/midi", "x-upsert": "true"})
            file_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_name)

        try:
            search_title = clean_string(title)
            # 1. Thử tìm khớp hoàn toàn
            check = supabase.table(TABLE_NAME).select("id").eq("title", search_title).execute()
            
            # 2. Nếu không thấy, thử tìm bỏ qua gạch dưới/khoảng trắng
            if not check.data:
                alt_title = search_title.replace("_", " ").strip()
                check = supabase.table(TABLE_NAME).select("id").eq("title", alt_title).execute()

            song_data = {"title": search_title, "artist": clean_string(artist)}
            if file_url: song_data["url"] = file_url
            if cover_url: song_data["cover_url"] = cover_url
            
            success_op = False
            if check.data:
                supabase.table(TABLE_NAME).update(song_data).eq("id", check.data[0]['id']).execute()
                print(f"✅ Đã cập nhật xong!")
                success_op = True
            elif midi_file:
                song_data["play_count"] = 0
                supabase.table(TABLE_NAME).insert(song_data).execute()
                print(f"✅ Đã thêm mới xong!")
                success_op = True
            else:
                print(f"⚠️ KHÔNG TÌM THẤY bài '{search_title}' trên DB. Hãy kiểm tra lại tên file ảnh!")

            # CHỈ XÓA KHI THỰC SỰ THÀNH CÔNG
            if success_op:
                if midi_file: os.remove(os.path.join(SOURCE_FOLDER, midi_file))
                if image_file: os.remove(os.path.join(SOURCE_FOLDER, image_file))
            else:
                print(f"ℹ️ Giữ lại file trong upload_queue để bạn sửa tên.")
        except Exception as e:
            print(f"❌ Lỗi: {e}")

    print(f"\n🏁 Xong!")

if __name__ == "__main__":
    upload_folder()
