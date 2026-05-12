<div align="center">
  <img src="AutoPiano.png" width="400" alt="Logo">

  # 🎹 Roblox Piano Auto Player

  **Ứng dụng chơi đàn Piano tự động siêu mượt dành riêng cho Roblox Virtual Piano**

  [![Tải Xuống Ngay](https://img.shields.io/badge/Tải_Về_App_Cho_Windows_(.exe)-2563eb?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/LeHoanNguyenVu/Piano-Auto-Playing-tool/releases/latest/download/RobloxPianoPlayer.exe)
</div>

---

## ✨ Tính năng nổi bật

- 🚀 **Zero-drift Timing**: Engine mô phỏng phím bấm siêu chính xác, không trượt nốt dù ở tốc độ cao (BPM > 200).
- 🌐 **Cloud Database**: Tìm kiếm và tải nhạc trực tiếp từ Supabase siêu tốc, không cần tải file MIDI thủ công.
- 🔥 **Trending & Favorites**: Xem bảng xếp hạng các bài hát thịnh hành nhất và lưu bài hát yêu thích để chơi Offline.
- 🎨 **Giao diện Modern Dark Mode**: Thiết kế hiện đại, tinh tế với CustomTkinter.
- ⚙️ **Tuỳ chỉnh chuyên sâu**: Thay đổi tốc độ (Speed), quãng (Transpose), và độ trễ (Start Delay) trước khi chơi.

## 📥 Hướng dẫn cài đặt và sử dụng

1. **Bấm nút tải về màu xanh ở trên** để tải file `RobloxPianoPlayer.exe`.
2. Chạy file `.exe` vừa tải (Nếu Windows hiện cảnh báo *Windows protected your PC*, chọn **More info** ➜ **Run anyway**).
3. Vào game Roblox, mở một tựa game có Virtual Piano.
4. Mở App, qua tab **🌐 Tìm kiếm**, gõ tên bài bạn thích và bấm **Play**.
5. App sẽ đếm ngược 3 giây (bạn có thể chỉnh lại trong Settings), hãy **nhấp chuột vào cửa sổ game Roblox** và thưởng thức!

## ⌨️ Phím tắt (Hotkeys)

- `F5` : Bắt đầu chơi nhạc (Play)
- `F6` : Tạm dừng (Pause / Resume)
- `F7` : Dừng hẳn (Stop)

## 🛠️ Dành cho Developer (Nếu muốn chạy từ source code)

Clone kho mã nguồn này về và cài đặt các thư viện:

```bash
git clone https://github.com/LeHoanNguyenVu/Piano-Auto-Playing-tool.git
cd Piano-Auto-Playing-tool
pip install -r requirements.txt
python main.py
```

## 📜 Cập nhật (v1.0.0)
- Tối ưu hóa Windows SendInput API, khắc phục hoàn toàn lỗi dính phím Shift khi chơi các nốt đen.
- Bổ sung Local Caching giúp load danh sách nhạc từ Cloud Database < 1ms.
- Tích hợp màn hình Splash Screen chờ tải.

---
*Phát triển bởi LeHoanNguyenVu*
