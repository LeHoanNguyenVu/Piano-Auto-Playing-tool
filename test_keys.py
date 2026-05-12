"""
Test Key Simulator — Chơi 1 đoạn nhạc ngắn để kiểm tra phím có đúng không.
Chạy xong chuyển sang Roblox Piano trong vòng 5 giây.
"""
import time
from core.key_simulator import press_key, release_key, release_all
from core.key_mapping import MIDI_TO_KEY

print("🎹 Test chơi gam Đô trưởng (C Major Scale)")
print("⏳ Bạn có 5 giây để chuyển sang cửa sổ Roblox Piano...")

for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

print("🎵 Đang chơi...")

# Gam C Major: C4 D4 E4 F4 G4 A4 B4 C5
scale_notes = [60, 62, 64, 65, 67, 69, 71, 72]
note_names = ['C4(t)', 'D4(y)', 'E4(u)', 'F4(i)', 'G4(o)', 'A4(p)', 'B4(a)', 'C5(s)']

for note, name in zip(scale_notes, note_names):
    key = MIDI_TO_KEY.get(note)
    if key:
        print(f"  Bấm: {name} → phím '{key}'")
        press_key(key)
        time.sleep(0.3)
        release_key(key)
        time.sleep(0.1)

print()

# Test phím đen (black keys - cần Shift)
print("🎵 Test phím ĐEN (cần Shift)...")
time.sleep(1)

black_notes = [61, 63, 66, 68, 70, 73]
black_names = ['C#4(T)', 'D#4(Y)', 'F#4(I)', 'G#4(O)', 'A#4(P)', 'C#5(S)']

for note, name in zip(black_notes, black_names):
    key = MIDI_TO_KEY.get(note)
    if key:
        print(f"  Bấm: {name} → phím '{key}' (Shift+{key.lower()})")
        press_key(key)
        time.sleep(0.3)
        release_key(key)
        time.sleep(0.1)

release_all()
print("\n✅ Test xong! Bạn có nghe đúng các nốt không?")
print("   - Nếu phím TRẮNG đúng, phím ĐEN sai → Lỗi Shift")
print("   - Nếu cả hai đều sai → Lỗi key simulator hoặc UniKey đang bật")
print("   - Nếu cả hai đều đúng → File MIDI hoặc DB có vấn đề")
