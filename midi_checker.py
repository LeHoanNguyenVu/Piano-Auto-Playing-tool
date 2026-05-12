"""
MIDI Checker — Kiểm tra file MIDI có phải Piano thuần hay không.

Cách dùng:
  1. Kiểm tra 1 file:  python midi_checker.py "tên_file.mid"
  2. Kiểm tra cả folder: python midi_checker.py
"""

import os
import sys
import mido

# Bảng tên nhạc cụ theo chuẩn General MIDI
GM_INSTRUMENTS = {
    0: "🎹 Acoustic Grand Piano", 1: "🎹 Bright Acoustic Piano",
    2: "🎹 Electric Grand Piano", 3: "🎹 Honky-tonk Piano",
    4: "🎹 Electric Piano 1", 5: "🎹 Electric Piano 2",
    6: "🎹 Harpsichord", 7: "🎹 Clavinet",
    8: "Celesta", 9: "Glockenspiel", 10: "Music Box",
    11: "Vibraphone", 12: "Marimba", 13: "Xylophone",
    14: "Tubular Bells", 15: "Dulcimer",
    16: "Drawbar Organ", 17: "Percussive Organ", 18: "Rock Organ",
    19: "Church Organ", 20: "Reed Organ", 21: "Accordion",
    22: "Harmonica", 23: "Tango Accordion",
    24: "🎸 Acoustic Guitar (nylon)", 25: "🎸 Acoustic Guitar (steel)",
    26: "🎸 Electric Guitar (jazz)", 27: "🎸 Electric Guitar (clean)",
    28: "🎸 Electric Guitar (muted)", 29: "🎸 Overdriven Guitar",
    30: "🎸 Distortion Guitar", 31: "🎸 Guitar Harmonics",
    32: "🎸 Acoustic Bass", 33: "🎸 Electric Bass (finger)",
    34: "🎸 Electric Bass (pick)", 35: "🎸 Fretless Bass",
    36: "🎸 Slap Bass 1", 37: "🎸 Slap Bass 2",
    38: "🎸 Synth Bass 1", 39: "🎸 Synth Bass 2",
    40: "🎻 Violin", 41: "🎻 Viola", 42: "🎻 Cello", 43: "🎻 Contrabass",
    44: "Tremolo Strings", 45: "Pizzicato Strings",
    46: "Orchestral Harp", 47: "Timpani",
    48: "String Ensemble 1", 49: "String Ensemble 2",
    56: "🎺 Trumpet", 57: "🎺 Trombone", 58: "Tuba", 59: "Muted Trumpet",
    60: "French Horn", 61: "Brass Section",
    64: "Soprano Sax", 65: "Alto Sax", 66: "Tenor Sax", 67: "Baritone Sax",
    68: "Oboe", 69: "English Horn", 70: "Bassoon", 71: "Clarinet",
    72: "Piccolo", 73: "🎵 Flute", 74: "Recorder",
}

PIANO_PROGRAMS = set(range(0, 8))  # Program 0-7 đều là Piano


def check_midi(file_path):
    """Kiểm tra chi tiết nội dung file MIDI."""
    try:
        mid = mido.MidiFile(file_path)
    except Exception as e:
        print(f"  ❌ Không đọc được file: {e}")
        return

    channels_used = {}  # channel -> set of programs
    has_drums = False
    note_counts = {}    # channel -> note count
    instruments = {}    # channel -> program name

    for track in mid.tracks:
        for msg in track:
            if msg.type == 'program_change':
                ch = msg.channel
                if ch not in channels_used:
                    channels_used[ch] = set()
                channels_used[ch].add(msg.program)
                instruments[ch] = GM_INSTRUMENTS.get(msg.program, f"Instrument #{msg.program}")
            
            if msg.type == 'note_on' and msg.velocity > 0:
                ch = msg.channel
                note_counts[ch] = note_counts.get(ch, 0) + 1
                if ch == 9:  # Channel 10 (0-indexed = 9) = Drums
                    has_drums = True

    # Phân tích kết quả
    total_notes = sum(note_counts.values())
    piano_notes = 0
    other_notes = 0

    print(f"\n  📊 Tổng số nốt: {total_notes}")
    print(f"  🎼 Số track: {len(mid.tracks)}")
    print(f"  ⏱️ Thời lượng: {mid.length:.1f} giây")
    print(f"  📡 Số kênh (channel) sử dụng: {len(note_counts)}")
    print()

    for ch in sorted(note_counts.keys()):
        count = note_counts[ch]
        if ch == 9:
            name = "🥁 TRỐNG (Drums/Percussion)"
            other_notes += count
        elif ch in instruments:
            name = instruments[ch]
            prog = list(channels_used.get(ch, set()))
            if prog and prog[0] in PIANO_PROGRAMS:
                piano_notes += count
            else:
                other_notes += count
        else:
            name = "🎹 Piano (mặc định)"
            piano_notes += count
        
        print(f"  Channel {ch+1:2d}: {name} — {count} nốt")

    # Kết luận
    print()
    if other_notes == 0 and not has_drums:
        print(f"  ✅ KẾT LUẬN: PIANO THUẦN — Chơi sẽ rất hay!")
    elif has_drums and other_notes == note_counts.get(9, 0):
        print(f"  ⚠️ KẾT LUẬN: Piano + Trống — Có thể nghe hơi lạ do tiếng trống.")
    else:
        pct = (piano_notes / total_notes * 100) if total_notes > 0 else 0
        print(f"  ⚠️ KẾT LUẬN: NHIỀU NHẠC CỤ — Chỉ {pct:.0f}% là Piano.")
        print(f"     → Bài này có thể nghe 'kì kì' khi chơi trên Roblox Piano.")


def main():
    if len(sys.argv) > 1:
        # Kiểm tra 1 file cụ thể
        file_path = sys.argv[1]
        if os.path.isfile(file_path):
            print(f"\n🔍 Đang kiểm tra: {os.path.basename(file_path)}")
            check_midi(file_path)
        else:
            print(f"❌ Không tìm thấy file: {file_path}")
    else:
        # Kiểm tra tất cả file trong upload_queue
        folder = "upload_queue"
        if not os.path.exists(folder):
            print(f"❌ Không tìm thấy thư mục '{folder}'")
            return
        
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.mid', '.midi'))]
        if not files:
            print(f"✨ Thư mục '{folder}' đang trống.")
            return

        print(f"\n🔍 Đang kiểm tra {len(files)} file MIDI...\n")
        print("=" * 60)
        
        for f in files:
            path = os.path.join(folder, f)
            print(f"\n📦 {f}")
            check_midi(path)
            print("─" * 60)


if __name__ == "__main__":
    main()
