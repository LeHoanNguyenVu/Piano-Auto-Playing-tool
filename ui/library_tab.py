"""
Library Tab — My Favorites (Nhạc của tôi).

Chỉ hiển thị các bài hát user đã bấm ❤ Yêu thích trong tab Search.
Các bài này đã được tải về máy và lưu trong thư mục library/favorites/.
"""

import os
import customtkinter as ctk
from ui import theme as T
from library import cloud_database


class ConfirmationDialog(ctk.CTkToplevel):
    """Custom premium-looking confirmation dialog."""
    def __init__(self, parent, title, message, on_confirm):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x200")
        self.on_confirm = on_confirm
        
        # Center the window
        self.after(10, self._center_window)
        
        self.configure(fg_color=T.BG_CARD)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # UI
        ctk.CTkLabel(self, text=title, font=T.FONT_HEADING, text_color=T.TEXT_ACCENT).pack(pady=(20, 10))
        ctk.CTkLabel(self, text=message, font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY, wraplength=350).pack(pady=10)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=20)
        
        ctk.CTkButton(btn_frame, text="Hủy", width=100, height=32, 
                       fg_color=T.BG_ELEVATED, hover_color=T.BG_CARD_HOVER,
                       command=self.destroy).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="Xác nhận xóa", width=120, height=32,
                       fg_color=T.ERROR, hover_color="#dc2626",
                       command=self._confirm).pack(side="left", padx=10)

    def _confirm(self):
        self.on_confirm()
        self.destroy()

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')


class LibraryTab(ctk.CTkFrame):
    """Màn hình Nhạc Yêu thích — hiển thị các bài đã lưu từ Cloud."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # ─── Header ───────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="❤ Nhạc Yêu Thích", font=T.FONT_TITLE,
                      text_color=T.TEXT_PRIMARY).pack(side="left")

        ctk.CTkButton(
            header, text="🗑 Xóa tất cả", width=120, height=32,
            font=T.FONT_SMALL, fg_color=T.BG_ELEVATED, hover_color=T.ERROR,
            text_color=T.TEXT_SECONDARY, corner_radius=T.BUTTON_CORNER,
            command=self._clear_all
        ).pack(side="right")

        # ─── Info Banner ─────────────────────────────────
        banner = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        banner.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(
            banner,
            text="Các bài bạn đã bấm ❤ trong tab Search sẽ xuất hiện ở đây.\n"
                 "Bài yêu thích được lưu trên máy — có thể chơi mà không cần Internet.",
            font=T.FONT_SMALL, text_color=T.TEXT_MUTED, justify="left"
        ).pack(padx=15, pady=8, anchor="w")

        # ─── Search Bar ──────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        search_frame.pack(fill="x", padx=20, pady=(0, 10))

        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(search_inner, text="🔍", font=T.FONT_BODY).pack(side="left")
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_list())
        ctk.CTkEntry(
            search_inner, textvariable=self._search_var,
            placeholder_text="Tìm trong danh sách yêu thích...",
            height=30, font=T.FONT_BODY, fg_color=T.BG_ELEVATED,
            border_color=T.BORDER, text_color=T.TEXT_PRIMARY
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

        # ─── Song Count ──────────────────────────────────
        self._count_label = ctk.CTkLabel(self, text="", font=T.FONT_TINY,
                                          text_color=T.TEXT_MUTED)
        self._count_label.pack(anchor="w", padx=25, pady=(0, 5))

        # ─── Song List ───────────────────────────────────
        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color=T.BG_DARKEST, corner_radius=T.CORNER_RADIUS,
            scrollbar_button_color=T.ACCENT_DIM
        )
        self._list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._song_widgets = []
        self._refresh_list()

    def _refresh_list(self):
        """Làm mới danh sách bài yêu thích."""
        for w in self._song_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self._song_widgets.clear()

        query = self._search_var.get().lower().strip()

        # Lấy danh sách từ Favorites (Cloud only)
        all_favs = cloud_database.get_all_favorites()

        # Gộp và filter theo query
        songs = []
        for s in all_favs:
            if not query or query in s.get('title', '').lower() or query in s.get('artist', '').lower():
                songs.append({"source": "cloud", **s})

        self._count_label.configure(
            text=f"Đang có {len(songs)} bài hát trong kho yêu thích"
        )

        if not songs:
            empty = ctk.CTkLabel(
                self._list_frame,
                text="Chưa có bài nào.\n\n"
                     "Vào tab ☁ Search → tìm bài → bấm ❤ Yêu thích để lưu bài vào đây.",
                font=T.FONT_BODY, text_color=T.TEXT_MUTED, justify="center"
            )
            empty.pack(pady=60)
            self._song_widgets.append(empty)
            return

        for song in songs:
            row = self._create_song_row(song)
            if row:
                self._song_widgets.append(row)

    def _create_song_row(self, song):
        """Tạo một hàng hiển thị bài hát."""
        is_fav = song.get("source") == "cloud"
        local_path = song.get("local_path") or song.get("path", "")
        if not local_path or not os.path.exists(local_path):
            return None

        row = ctk.CTkFrame(self._list_frame, fg_color=T.BG_CARD, corner_radius=6, height=52)
        row.pack(fill="x", padx=5, pady=3)
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=6)

        # Icon yêu thích / local
        icon = "❤" if is_fav else "📁"
        ctk.CTkLabel(inner, text=icon, font=T.FONT_BODY,
                      text_color="#f472b6" if is_fav else T.TEXT_MUTED).pack(side="left", padx=(0, 8))

        # Thông tin bài
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(info, text=song.get("title", "Unknown"), font=T.FONT_SMALL,
                      text_color=T.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        artist = song.get("artist", "")
        added = song.get("added_date", "")
        sub = f"{artist}  •  Đã lưu: {added}" if artist else f"Đã lưu: {added}"
        ctk.CTkLabel(info, text=sub, font=T.FONT_TINY,
                      text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")

        # Nút Play
        ctk.CTkButton(
            inner, text="▶", width=34, height=32, font=T.FONT_BODY_BOLD,
            fg_color=T.SUCCESS, hover_color="#16a34a", corner_radius=4,
            command=lambda s=song: self._play_song(s)
        ).pack(side="right", padx=(4, 0))

        # Nút xóa
        ctk.CTkButton(
            inner, text="✕", width=34, height=32, font=T.FONT_SMALL,
            fg_color=T.ERROR, hover_color="#dc2626", corner_radius=4,
            command=lambda s=song: self._remove_song(s)
        ).pack(side="right", padx=(4, 0))

        # Hover
        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=T.BG_CARD_HOVER))
        row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=T.BG_CARD))

        return row

    def _play_song(self, song):
        """Load bài vào Player và chuyển sang tab Player."""
        path = song.get("local_path") or song.get("path", "")
        if os.path.exists(path):
            if hasattr(self.app, 'player_tab'):
                self.app.player_tab.load_file(path)
            self.app.show_frame("player")

    def _remove_song(self, song):
        """Xóa bài khỏi danh sách."""
        # Lấy ID chính xác (ưu tiên id từ Supabase, fallback về title)
        song_id = song.get("id")
        if song_id is None:
            song_id = song.get("title", "")
        
        # Ép kiểu về string để khớp với keys trong favorites.json
        cloud_database.remove_favorite(str(song_id))
        self._refresh_list()

    def _clear_all(self):
        """Xóa sạch sành sanh mọi thứ trong kho với Custom Popup."""
        if not cloud_database.get_all_favorites():
            return
            
        ConfirmationDialog(
            self, 
            title="Dọn dẹp Thư viện",
            message="Bạn có chắc muốn xóa toàn bộ danh sách nhạc yêu thích không? Hành động này sẽ xóa vĩnh viễn các file đã tải.",
            on_confirm=lambda: [cloud_database.clear_all_favorites(), self._refresh_list()]
        )

    def _import_midi(self):
        # Chức năng này đã được chuyển sang tab Player
        pass
