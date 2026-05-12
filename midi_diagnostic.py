"""
Diagnostic Tool — So sánh file MIDI gốc vs file tải từ Supabase.
Cách dùng: python midi_diagnostic.py "tên bài" "đường dẫn file gốc"
Ví dụ:    python midi_diagnostic.py "Blue Yung Kai" "upload_queue/Blue Yung Kai.mid"
"""

import sys
import os
import tempfile
import requests
from core.midi_parser import parse_midi
from core.key_mapping import MIDI_TO_KEY, get_note_name
from library.cloud_database import CloudDatabase

def show_notes(events, label, count=30):
    print(f"\n{'='*50}")
    print(f"📋 {label} — Hiển thị {count} nốt đầu tiên:")
    print(f"{'='*50}")
    note_on_events = [e for e in events if e.velocity > 0]
    for i, e in enumerate(note_on_events[:count]):
        key = MIDI_TO_KEY.get(e.note, '?')
        name = get_note_name(e.note)
        print(f"  #{i+1:3d} | t={e.time:7.3f}s | MIDI={e.note:3d} | {name:4s} | Key='{key}'")
    print(f"\n  Tổng note_on: {len(note_on_events)}")

def main():
    if len(sys.argv) < 2:
        print("Cách dùng: python midi_diagnostic.py \"tên bài\" [đường dẫn file gốc]")
        return

    song_title = sys.argv[1]
    local_file = sys.argv[2] if len(sys.argv) > 2 else None

    # 1. Tìm bài trên Supabase
    print(f"🔍 Đang tìm '{song_title}' trên Supabase...")
    db = CloudDatabase()
    results = db.search(song_title)
    
    if not results:
        print(f"❌ Không tìm thấy bài '{song_title}' trên Supabase!")
        return

    # Hiển thị tất cả kết quả (phát hiện trùng lặp)
    print(f"\n📊 Tìm thấy {len(results)} kết quả:")
    for r in results:
        url_status = "✅ Có URL" if r.get('url') else "❌ KHÔNG CÓ URL"
        print(f"  ID={r.get('id')} | '{r.get('title')}' | {url_status}")
    
    if len(results) > 1:
        print(f"\n  ⚠️ CẢNH BÁO: Có {len(results)} bản trùng! Chỉ giữ 1 bản thôi!")

    # Lấy bản có URL
    song = None
    for r in results:
        if r.get('url'):
            song = r
            break
    
    if not song:
        print("❌ Không có bản nào có URL!")
        return

    # 2. Tải file từ Supabase
    print(f"\n📥 Đang tải MIDI từ Supabase (ID={song['id']})...")
    print(f"   URL: {song['url'][:80]}...")
    
    try:
        tmp_path = db.download_to_temp(song)
        print(f"   ✅ Đã tải: {tmp_path}")
        cloud_size = os.path.getsize(tmp_path)
        print(f"   📦 Kích thước: {cloud_size} bytes")
    except Exception as e:
        print(f"   ❌ Lỗi tải: {e}")
        return

    # 3. Parse file từ Supabase
    cloud_events = parse_midi(tmp_path)
    show_notes(cloud_events, "FILE TỪ SUPABASE")

    # 4. So sánh với file gốc (nếu có)
    if local_file and os.path.exists(local_file):
        local_size = os.path.getsize(local_file)
        print(f"\n📁 File gốc: {local_file} ({local_size} bytes)")
        
        if local_size == cloud_size:
            print("   ✅ Kích thước KHỚP!")
        else:
            print(f"   ❌ KÍCH THƯỚC KHÁC NHAU! Gốc={local_size} vs Cloud={cloud_size}")

        local_events = parse_midi(local_file)
        show_notes(local_events, "FILE GỐC (LOCAL)")

        # So sánh chi tiết
        local_on = [e for e in local_events if e.velocity > 0]
        cloud_on = [e for e in cloud_events if e.velocity > 0]
        
        print(f"\n{'='*50}")
        print(f"🔍 SO SÁNH KẾT QUẢ:")
        print(f"{'='*50}")
        print(f"  Số nốt gốc:      {len(local_on)}")
        print(f"  Số nốt Supabase:  {len(cloud_on)}")
        
        if len(local_on) == len(cloud_on):
            mismatches = 0
            for i, (l, c) in enumerate(zip(local_on, cloud_on)):
                if l.note != c.note or abs(l.time - c.time) > 0.001:
                    mismatches += 1
                    if mismatches <= 5:
                        print(f"  ❌ Nốt #{i+1}: Gốc=MIDI{l.note}@{l.time:.3f}s vs Cloud=MIDI{c.note}@{c.time:.3f}s")
            if mismatches == 0:
                print("  ✅ HAI FILE HOÀN TOÀN GIỐNG NHAU!")
            else:
                print(f"  ❌ Có {mismatches} nốt khác nhau!")
        else:
            print("  ❌ SỐ NỐT KHÁC NHAU — File bị thay đổi!")
    else:
        if local_file:
            print(f"\n⚠️ Không tìm thấy file gốc: {local_file}")
        print("💡 Để so sánh, chạy lại với đường dẫn file gốc:")
        print(f'   python midi_diagnostic.py "{song_title}" "đường_dẫn_file.mid"')

if __name__ == "__main__":
    main()
