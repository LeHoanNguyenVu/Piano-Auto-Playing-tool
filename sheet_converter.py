"""
Sheet to MIDI Converter v2 — Chuyển đổi Virtual Piano Sheet thành file MIDI có cảm xúc.
Tính năng Humanize: mô phỏng cách chơi piano của người thật.
"""

import mido
import os
import random
from core.key_mapping import MIDI_TO_KEY

# ĐẢO NGƯỢC MAPPING: Key Character -> MIDI Note
KEY_TO_MIDI = {v: k for k, v in MIDI_TO_KEY.items()}


def humanize_velocity(base=75, is_chord=False, position_in_phrase=0, phrase_len=1):
    """
    Tạo velocity tự nhiên:
    - Hợp âm: mạnh hơn (85-100)
    - Nốt đầu câu: mạnh vừa (75-90)
    - Nốt giữa câu: nhẹ hơn (60-80)
    - Nốt cuối câu: nhẹ nhất (55-70)
    - Thêm dao động ngẫu nhiên ±5
    """
    if is_chord:
        v = random.randint(82, 100)
    elif phrase_len > 0:
        ratio = position_in_phrase / max(phrase_len, 1)
        if ratio < 0.2:      # Đầu câu
            v = random.randint(75, 90)
        elif ratio < 0.7:    # Giữa câu
            v = random.randint(60, 80)
        else:                # Cuối câu
            v = random.randint(55, 72)
    else:
        v = base + random.randint(-8, 8)

    return max(30, min(127, v))


def humanize_timing(base_ticks, swing=True):
    """
    Thêm dao động nhẹ vào timing:
    - ±8% để không bị đều như máy
    - Swing nhẹ cho nhịp phách tự nhiên
    """
    variation = int(base_ticks * random.uniform(-0.08, 0.08))
    return max(60, base_ticks + variation)


def parse_phrase(line_text):
    """
    Parse một dòng text thành danh sách các phần tử nhạc.
    Mỗi phần tử là: ('single', 'a') hoặc ('chord', ['a', 's', 'd'])
    """
    elements = []
    i = 0
    while i < len(line_text):
        ch = line_text[i]
        if ch == '[':
            # Hợp âm
            chord = []
            i += 1
            while i < len(line_text) and line_text[i] != ']':
                chord.append(line_text[i])
                i += 1
            if chord:
                elements.append(('chord', chord))
        elif ch in KEY_TO_MIDI:
            elements.append(('single', ch))
        elif ch == ' ':
            elements.append(('space', None))
        i += 1
    return elements


def text_sheet_to_midi(text, output_filename, bpm=120):
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Tên bài hát
    song_name = os.path.splitext(output_filename)[0]
    track.append(mido.MetaMessage('track_name', name=song_name))

    # Thiết lập nhịp độ
    tempo = mido.bpm2tempo(bpm)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo))

    # Đơn vị thời gian cơ bản
    base_ticks = 240  # 1/8 note at 480 ticks/beat

    # Tách theo dòng → mỗi dòng là một câu nhạc
    lines = text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            # Dòng trống = nghỉ dài (giữa đoạn)
            track.append(mido.Message('note_on', note=60, velocity=0, time=base_ticks * 2))
            continue

        elements = parse_phrase(line)
        note_elements = [e for e in elements if e[0] != 'space']
        phrase_len = len(note_elements)
        note_idx = 0

        for elem_type, data in elements:
            if elem_type == 'space':
                # Khoảng trắng = nghỉ ngắn giữa các nốt
                track.append(mido.Message('note_on', note=60, velocity=0,
                                          time=humanize_timing(base_ticks // 3)))
                continue

            is_chord = (elem_type == 'chord')

            if is_chord:
                chars = data
                vel = humanize_velocity(is_chord=True,
                                        position_in_phrase=note_idx,
                                        phrase_len=phrase_len)
                # Bật tất cả nốt trong hợp âm
                first_note = True
                for c in chars:
                    if c in KEY_TO_MIDI:
                        # Nốt đầu tiên trong hợp âm có thể lệch nhẹ (strum effect)
                        strum_delay = 0 if first_note else random.randint(0, 15)
                        track.append(mido.Message('note_on',
                                                  note=KEY_TO_MIDI[c],
                                                  velocity=vel + random.randint(-3, 3),
                                                  time=strum_delay))
                        first_note = False

                # Giữ nốt rồi tắt
                hold = humanize_timing(base_ticks)
                first_off = True
                for c in chars:
                    if c in KEY_TO_MIDI:
                        track.append(mido.Message('note_off',
                                                  note=KEY_TO_MIDI[c],
                                                  velocity=0,
                                                  time=hold if first_off else 0))
                        first_off = False
            else:
                # Nốt đơn
                char = data
                if char in KEY_TO_MIDI:
                    vel = humanize_velocity(is_chord=False,
                                            position_in_phrase=note_idx,
                                            phrase_len=phrase_len)
                    note = KEY_TO_MIDI[char]
                    hold = humanize_timing(base_ticks)

                    track.append(mido.Message('note_on', note=note, velocity=vel, time=0))
                    track.append(mido.Message('note_off', note=note, velocity=0, time=hold))

            note_idx += 1

        # Cuối dòng = nghỉ lấy hơi (ngắt câu)
        track.append(mido.Message('note_on', note=60, velocity=0,
                                  time=humanize_timing(base_ticks)))

    # Kết thúc
    track.append(mido.MetaMessage('end_of_track'))

    # Lưu file
    os.makedirs("upload_queue", exist_ok=True)
    full_path = os.path.join("upload_queue", output_filename)
    mid.save(full_path)
    return full_path


if __name__ == "__main__":
    print("═══════════════════════════════════════════")
    print("  🎹 SHEET TEXT → MIDI CONVERTER v2")
    print("  ✨ Với tính năng Humanize (chơi tự nhiên)")
    print("═══════════════════════════════════════════")

    song_name = input("\n🎵 Nhập tên bài hát: ").strip()
    if not song_name:
        print("❌ Bạn chưa nhập tên bài.")
        exit()

    artist = input("🎤 Nhập tên tác giả (Enter để bỏ qua): ").strip()

    try:
        bpm_input = input("⏱  Nhập BPM / nhịp độ (Enter = 120): ").strip()
        bpm = int(bpm_input) if bpm_input else 120
    except ValueError:
        bpm = 120

    print("\n📝 Dán đoạn Text Sheet vào đây (nhấn Enter 2 lần để kết thúc):")

    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)

    full_text = "\n".join(lines)

    if full_text.strip():
        filename = f"{song_name}.mid"
        path = text_sheet_to_midi(full_text, filename, bpm)
        print(f"\n✅ Đã tạo xong: {path}")
        print(f"   🎵 Tên: {song_name}")
        print(f"   🎤 Tác giả: {artist or 'Unknown'}")
        print(f"   ⏱  BPM: {bpm}")
        print(f"\n👉 Chạy 'python bulk_uploader.py' để upload lên Supabase!")
    else:
        print("❌ Bạn chưa nhập nội dung sheet.")
