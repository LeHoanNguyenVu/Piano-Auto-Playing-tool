"""
Search Tab — Cloud Database Search.

Luồng:
- Khởi động: kết nối Cloud, hiển thị trạng thái + số bài.
- Search: tìm trong Cloud catalog.
- [▶ Play]: tải .mid tạm thời, chuyển sang Player tab ngay.
- [❤ Yêu thích]: tải về + lưu vào Favorites.
"""

import os
import threading
import unicodedata
import customtkinter as ctk
from ui import theme as T
from library import cloud_database


def remove_accents(input_str):
    """Loại bỏ dấu tiếng Việt để tìm kiếm không dấu."""
    if not input_str: return ""
    s = unicodedata.normalize('NFD', input_str)
    return "".join(c for c in s if unicodedata.category(c) != 'Mn').replace('đ', 'd').replace('Đ', 'D')


class SearchTab(ctk.CTkFrame):
    """Cloud Database search interface."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self._results = []
        # CloudDatabase khởi tạo kết nối trong background
        self.db = None
        self._build_ui()
        # Kết nối cloud sau khi UI sẵn sàng
        self.after(200, self._init_cloud)

    def _build_ui(self):
        # ─── Header ───────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="☁ Cloud Database", font=T.FONT_TITLE,
                      text_color=T.TEXT_PRIMARY).pack(side="left")

        self._refresh_btn = ctk.CTkButton(
            header, text="🔄 Refresh", width=90, height=28,
            font=T.FONT_SMALL, fg_color=T.BG_ELEVATED, hover_color=T.BG_CARD_HOVER,
            text_color=T.TEXT_SECONDARY, corner_radius=T.BUTTON_CORNER,
            command=self._refresh_cloud
        )
        self._refresh_btn.pack(side="right")

        # ─── Cloud Status Banner ──────────────────────────
        self._status_banner = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        self._status_banner.pack(fill="x", padx=20, pady=(0, 8))
        self._banner_label = ctk.CTkLabel(
            self._status_banner, text="⏳ Đang kết nối Cloud Database...",
            font=T.FONT_SMALL, text_color=T.WARNING
        )
        self._banner_label.pack(padx=15, pady=8, anchor="w")

        # ─── Search Bar ──────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        search_frame.pack(fill="x", padx=20, pady=(0, 10))

        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=15, pady=12)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *args: self._on_input_change("title"))
        
        self._search_entry = ctk.CTkEntry(
            search_inner, textvariable=self._search_var,
            placeholder_text="Nhập tên bài hát cần tìm...",
            height=36, font=T.FONT_BODY, fg_color=T.BG_ELEVATED,
            border_color=T.BORDER, text_color=T.TEXT_PRIMARY
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._search_entry.bind("<Return>", lambda e: self._do_search())
        self._search_entry.bind("<FocusOut>", lambda e: self.after(200, self._hide_suggestions))

        self._search_btn = ctk.CTkButton(
            search_inner, text="🔍 Tìm bài hát", width=110, height=36,
            font=T.FONT_BODY_BOLD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            corner_radius=T.BUTTON_CORNER, command=self._do_search
        )
        self._search_btn.pack(side="right")

        # ─── Suggestions Overlay ─────────────────────────
        self._suggest_frame = ctk.CTkFrame(self, fg_color=T.BG_ELEVATED, 
                                            border_width=1, border_color=T.ACCENT_DIM,
                                            corner_radius=4, width=545, height=1) # Sẽ co giãn theo nội dung
        # Sẽ được pack/forget tùy lúc gõ

        # ─── Artist Filter ──────────────────────────────
        artist_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        artist_frame.pack(fill="x", padx=20, pady=(0, 8))

        artist_inner = ctk.CTkFrame(artist_frame, fg_color="transparent")
        artist_inner.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(artist_inner, text="Tìm theo Tác giả:", font=T.FONT_SMALL,
                      text_color=T.TEXT_SECONDARY).pack(side="left")

        self._artist_var = ctk.StringVar()
        self._artist_var.trace_add("write", lambda *args: self._on_input_change("artist"))
        
        self._artist_entry = ctk.CTkEntry(
            artist_inner, textvariable=self._artist_var,
            placeholder_text="Tên ca sĩ, nhạc sĩ...",
            height=30, font=T.FONT_SMALL, fg_color=T.BG_ELEVATED,
            border_color=T.BORDER, text_color=T.TEXT_PRIMARY
        )
        self._artist_entry.pack(side="left", fill="x", expand=True, padx=8)
        self._artist_entry.bind("<Return>", lambda e: self._do_search())
        self._artist_entry.bind("<FocusOut>", lambda e: self.after(200, self._hide_suggestions))

        ctk.CTkButton(
            artist_inner, text="👥 Lọc tác giả", width=90, height=30,
            font=T.FONT_SMALL, fg_color=T.BG_ELEVATED, hover_color=T.BG_CARD_HOVER,
            text_color=T.TEXT_PRIMARY, corner_radius=T.BUTTON_CORNER, 
            command=self._do_search
        ).pack(side="right")

        # ─── Result Status ────────────────────────────────
        self._result_status = ctk.CTkLabel(self, text="", font=T.FONT_SMALL,
                                            text_color=T.TEXT_MUTED)
        self._result_status.pack(anchor="w", padx=25, pady=(0, 4))

        # ─── Results List ─────────────────────────────────
        self._results_frame = ctk.CTkScrollableFrame(
            self, fg_color=T.BG_DARKEST, corner_radius=T.CORNER_RADIUS,
            scrollbar_button_color=T.ACCENT_DIM
        )
        self._results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._result_widgets = []
        self._show_message("Đang kết nối Cloud Database, vui lòng chờ...")

    # ─── Cloud Connection ─────────────────────────────────

    def _init_cloud(self):
        """Khởi tạo kết nối Cloud trong background thread."""
        def _worker():
            self.db = cloud_database.CloudDatabase()
            self.after(0, self._on_cloud_ready)
        threading.Thread(target=_worker, daemon=True).start()

    def _on_cloud_ready(self):
        """Callback khi CloudDatabase đã sẵn sàng."""
        if self.db.is_connected:
            self._banner_label.configure(
                text=f"✅ Đã kết nối Cloud — {self.db.song_count} bài hát",
                text_color=T.SUCCESS
            )
        else:
            self._banner_label.configure(
                text=f"⚠ Không kết nối được Cloud. Đang dùng dữ liệu mẫu ({self.db.song_count} bài).",
                text_color=T.WARNING
            )
        self._show_message("Gõ tên bài hát và bấm Tìm kiếm.")

    def _refresh_cloud(self):
        self._banner_label.configure(text="⏳ Đang kết nối lại...", text_color=T.WARNING)
        self._show_message("Đang tải lại danh sách từ Cloud...")
        def _worker():
            if self.db:
                self.db.refresh_catalog()
            else:
                self.db = cloud_database.CloudDatabase()
            self.after(0, self._on_cloud_ready)
        threading.Thread(target=_worker, daemon=True).start()

    # ─── Search ───────────────────────────────────────────

    def _do_search(self):
        if not self.db:
            self._result_status.configure(text="⏳ Đang kết nối, vui lòng đợi...", text_color=T.WARNING)
            return

        self._hide_suggestions()
        title_q = remove_accents(self._search_var.get().strip().lower())
        artist_q = remove_accents(self._artist_var.get().strip().lower())
        
        self._result_status.configure(text="🔄 Đang tìm kiếm...", text_color=T.WARNING)
        self._search_btn.configure(state="disabled")
        self._show_message("Đang tìm kiếm...")

        def _worker():
            # Tìm kiếm kết hợp cả 2 ô
            all_songs = self.db.catalog
            results = []
            for s in all_songs:
                title = remove_accents(str(s.get('title', ''))).lower()
                artist = remove_accents(str(s.get('artist', ''))).lower()
                
                match_title = not title_q or title_q in title
                match_artist = not artist_q or artist_q in artist
                
                if match_title and match_artist:
                    results.append(s)
                    
            self.after(0, self._display_results, results)
        threading.Thread(target=_worker, daemon=True).start()

    def _display_results(self, results):
        self._search_btn.configure(state="normal")
        self._results = results
        self._clear_results()

        if not results:
            self._result_status.configure(text="Không tìm thấy kết quả.", text_color=T.TEXT_MUTED)
            self._show_message("Không tìm thấy bài nào.\nThử từ khoá khác hoặc dán URL trực tiếp.")
            return

        self._result_status.configure(text=f"Tìm thấy {len(results)} bài hát", text_color=T.SUCCESS)

        favs = cloud_database.load_favorites()

        for result in results:
            self._create_result_row(result, favs)

    def _create_result_row(self, result, favs):
        song_id = result.get('id', result.get('title', ''))
        already_fav = song_id in favs

        row = ctk.CTkFrame(self._results_frame, fg_color=T.BG_CARD, corner_radius=6)
        row.pack(fill="x", padx=5, pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        # Info block
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(info, text=f"♪  {result.get('title', 'Unknown')}",
                      font=T.FONT_BODY_BOLD, text_color=T.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text=result.get('artist', ''),
                      font=T.FONT_TINY, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")

        # Buttons block
        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(side="right")

        # Nút Yêu thích
        fav_text = "❤ Đã lưu" if already_fav else "🤍 Yêu thích"
        fav_color = "#be185d" if already_fav else T.BG_ELEVATED
        fav_hover = "#9d174d" if already_fav else T.BG_CARD_HOVER
        fav_btn = ctk.CTkButton(
            btns, text=fav_text, width=100, height=30,
            font=T.FONT_SMALL, fg_color=fav_color, hover_color=fav_hover,
            text_color=T.TEXT_PRIMARY, corner_radius=4
        )
        fav_btn.pack(side="left", padx=(0, 6))

        # Nút Play
        play_btn = ctk.CTkButton(
            btns, text="▶ Play", width=80, height=30,
            font=T.FONT_SMALL, fg_color=T.SUCCESS, hover_color="#16a34a",
            corner_radius=4
        )
        play_btn.pack(side="left")

        # Bind commands sau khi có widget references
        play_btn.configure(command=lambda r=result, b=play_btn: self._play_song(r, b))
        fav_btn.configure(command=lambda r=result, b=fav_btn: self._toggle_favorite(r, b))

        # Hover
        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=T.BG_CARD_HOVER))
        row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=T.BG_CARD))

        self._result_widgets.append(row)

    # ─── Play ─────────────────────────────────────────────

    def _play_song(self, song, btn):
        """Tải tạm về temp và chuyển sang Player tab để chơi ngay."""
        btn.configure(text="⏳...", state="disabled")
        self._result_status.configure(text=f"⬇ Đang tải: {song['title']}...", text_color=T.WARNING)

        def _worker():
            try:
                tmp_path = self.db.download_to_temp(song)
                self.after(0, self._on_play_ready, song, tmp_path, btn)
            except Exception as e:
                self.after(0, self._on_play_error, str(e), btn)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_play_ready(self, song, file_path, btn):
        btn.configure(text="▶ Play", state="normal")
        self._result_status.configure(text=f"▶ Đang chơi: {song['title']}", text_color=T.SUCCESS)
        # Lưu song metadata vào temp file để dùng cho chức năng Yêu thích sau
        self._last_played = {"song": song, "path": file_path}
        # Chuyển sang Player tab
        if hasattr(self.app, 'player_tab'):
            self.app.player_tab.load_file(file_path)
        self.app.show_frame("player")

    def _on_play_error(self, error, btn):
        btn.configure(text="▶ Play", state="normal")
        self._result_status.configure(text=f"✗ Tải thất bại: {error}", text_color=T.ERROR)

    def _play_url(self):
        """Tải và chơi bài hát từ URL trực tiếp."""
        url = self._url_var.get().strip()
        if not url:
            return
        song = {"id": "direct_url", "title": "Direct URL", "artist": "", "url": url}
        self._result_status.configure(text="⬇ Đang tải từ URL...", text_color=T.WARNING)

        def _worker():
            try:
                tmp_path = self.db.download_to_temp(song) if self.db else None
                if tmp_path:
                    self.after(0, self._on_play_ready, song, tmp_path, None)
            except Exception as e:
                self.after(0, lambda: self._result_status.configure(
                    text=f"✗ Lỗi: {e}", text_color=T.ERROR))

        threading.Thread(target=_worker, daemon=True).start()

    # ─── Favorites ────────────────────────────────────────

    def _toggle_favorite(self, song, btn):
        """Thêm/xóa bài khỏi Favorites."""
        song_id = song.get('id', song.get('title', ''))
        if cloud_database.is_favorite(song_id):
            # Xóa yêu thích
            cloud_database.remove_favorite(song_id)
            btn.configure(text="🤍 Yêu thích", fg_color=T.BG_ELEVATED, hover_color=T.BG_CARD_HOVER)
            self._result_status.configure(text=f"Đã bỏ yêu thích: {song['title']}", text_color=T.TEXT_MUTED)
            self._refresh_library_tab()
        else:
            # Thêm yêu thích — cần tải file về
            btn.configure(text="⏳...", state="disabled")
            self._result_status.configure(text=f"💾 Đang lưu: {song['title']}...", text_color=T.WARNING)

            def _worker():
                try:
                    meta = self.db.download_to_favorites(song)
                    self.after(0, self._on_fav_saved, song, btn, meta)
                except Exception as e:
                    self.after(0, self._on_fav_error, str(e), btn)

            threading.Thread(target=_worker, daemon=True).start()

    def _on_fav_saved(self, song, btn, meta):
        btn.configure(text="❤ Đã lưu", fg_color="#be185d", hover_color="#9d174d", state="normal")
        self._result_status.configure(
            text=f"❤ Đã lưu '{song['title']}' vào Yêu thích!", text_color="#f472b6")
        self._refresh_library_tab()

    def _on_fav_error(self, error, btn):
        btn.configure(text="🤍 Yêu thích", state="normal")
        self._result_status.configure(text=f"✗ Lưu thất bại: {error}", text_color=T.ERROR)

    def _refresh_library_tab(self):
        """Báo cho Library Tab refresh danh sách Favorites."""
        if hasattr(self.app, 'library_tab'):
            try:
                self.app.library_tab._refresh_list()
            except Exception:
                pass

    # ─── Suggestions Logic ────────────────────────────────

    def _on_input_change(self, mode):
        """Xử lý khi người dùng gõ vào một trong hai ô tìm kiếm."""
        if mode == "title":
            var = self._search_var
            field = "title"
            y_pos = 160
        else:
            var = self._artist_var
            field = "artist"
            y_pos = 220 # Vị trí dưới ô Tác giả

        query = remove_accents(var.get().strip().lower())
        if not query or len(query) < 1 or not self.db:
            self._hide_suggestions()
            return

        # Lấy tối đa 5 gợi ý
        matches = []
        seen = set() # Tránh gợi ý lặp (đặc biệt cho artist)
        
        for s in self.db.catalog:
            val = str(s.get(field, ''))
            clean_val = remove_accents(val).lower()
            
            if query in clean_val and val not in seen:
                matches.append(s)
                seen.add(val)
                if len(matches) >= 5: break

        if matches:
            self._show_suggestions(matches, field, y_pos)
        else:
            self._hide_suggestions()

    def _show_suggestions(self, matches, field, y_pos):
        # Dọn dẹp frame cũ
        for w in self._suggest_frame.winfo_children():
            w.destroy()

        for s in matches:
            display_text = s['title'] if field == "title" else s['artist']
            sub_text = f" - {s['artist']}" if field == "title" else ""
            
            btn = ctk.CTkButton(
                self._suggest_frame, text=f"♪ {display_text}{sub_text}",
                anchor="w", font=T.FONT_SMALL, fg_color="transparent",
                text_color=T.TEXT_SECONDARY, hover_color=T.BG_CARD_HOVER,
                height=28, corner_radius=0,
                command=lambda val=display_text, f=field: self._select_suggestion(val, f)
            )
            btn.pack(fill="x", padx=2, pady=1)

        # Hiển thị tại vị trí tương ứng
        self._suggest_frame.place(x=35, y=y_pos)
        self._suggest_frame.lift()

    def _select_suggestion(self, value, field):
        if field == "title":
            self._search_var.set(value)
        else:
            self._artist_var.set(value)
        self._hide_suggestions()
        self._do_search()

    def _hide_suggestions(self):
        self._suggest_frame.place_forget()

    # ─── Helpers ──────────────────────────────────────────

    def _show_message(self, text):
        self._clear_results()
        lbl = ctk.CTkLabel(self._results_frame, text=text, font=T.FONT_BODY,
                            text_color=T.TEXT_MUTED, wraplength=500)
        lbl.pack(pady=50)
        self._result_widgets.append(lbl)

    def _clear_results(self):
        for w in self._result_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self._result_widgets.clear()
