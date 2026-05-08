"""
Library Tab — My Favorites (Nhạc của tôi).

Chỉ hiển thị các bài hát user đã bấm ❤ Yêu thích trong tab Search.
Các bài này đã được tải về máy và lưu trong thư mục library/favorites/.
"""

import os
import customtkinter as ctk
from tkinter import filedialog
from ui import theme as T
from library import cloud_database, song_manager


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
            header, text="📂 Import MIDI", width=130, height=32,
            font=T.FONT_BODY_BOLD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            corner_radius=T.BUTTON_CORNER, command=self._import_midi
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

        # Lấy danh sách từ Favorites
        all_favs = cloud_database.get_all_favorites()
        # Lấy thêm bài từ Local Library (import thủ công)
        local_songs = song_manager.get_all_songs()

        # Gộp và filter theo query
        songs = []
        for s in all_favs:
            if not query or query in s.get('title', '').lower() or query in s.get('artist', '').lower():
                songs.append({"source": "cloud", **s})
        for s in local_songs:
            if not query or query in s.get('title', '').lower() or query in s.get('artist', '').lower():
                songs.append({"source": "local", **s})

        self._count_label.configure(
            text=f"{len(songs)} bài — {len(all_favs)} từ Cloud, {len(local_songs)} import thủ công"
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
        """Xóa bài khỏi danh sách (Favorites hoặc Local Library)."""
        if song.get("source") == "cloud":
            song_id = song.get("id", song.get("title", ""))
            cloud_database.remove_favorite(song_id)
        else:
            song_manager.delete_song(song.get("id", ""))
        self._refresh_list()

    def _import_midi(self):
        """Import MIDI file thủ công vào Local Library."""
        paths = filedialog.askopenfilenames(
            title="Import MIDI Files",
            filetypes=[("MIDI Files", "*.mid *.midi"), ("All Files", "*.*")]
        )
        count = 0
        for path in paths:
            result = song_manager.import_midi(path)
            if result:
                count += 1
        if count > 0:
            self._refresh_list()
