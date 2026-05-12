"""
Trends Tab — Top Trending Songs from Cloud Database.
"""

import threading
import customtkinter as ctk
from ui import theme as T
from library import cloud_database


class TrendsTab(ctk.CTkFrame):
    """Trending songs interface."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self.db = None
        self._result_widgets = []
        self._build_ui()
        self.after(200, self._init_and_load)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="🔥 " + T.L("trends"), font=T.FONT_TITLE,
                      text_color=T.TEXT_PRIMARY).pack(side="left")

        self._refresh_btn = ctk.CTkButton(
            header, text=T.L("refresh"), width=90, height=28,
            font=T.FONT_SMALL, fg_color=T.BG_ELEVATED, hover_color=T.BG_CARD_HOVER,
            text_color=T.TEXT_PRIMARY, corner_radius=T.BUTTON_CORNER,
            command=self._load_trends
        )
        self._refresh_btn.pack(side="right")

        self._results_frame = ctk.CTkScrollableFrame(
            self, fg_color=T.BG_DARKEST, corner_radius=T.CORNER_RADIUS,
            scrollbar_button_color=T.ACCENT_DIM
        )
        self._results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._show_message("...")

    def _init_and_load(self):
        def _worker():
            from library.cloud_database import get_cloud_db
            self.db = get_cloud_db()
            self._load_trends()
        threading.Thread(target=_worker, daemon=True).start()

    def _load_trends(self):
        if not hasattr(self, '_refresh_btn'): return
        self._refresh_btn.configure(state="disabled")
        
        def _worker():
            if self.db:
                self.db.refresh_catalog()
                songs = self.db.get_trending_songs(limit=20)
                self.after(0, self._display_trends, songs)
            else:
                self.after(0, lambda: self._refresh_btn.configure(state="normal"))
        threading.Thread(target=_worker, daemon=True).start()

    def _display_trends(self, songs):
        self._refresh_btn.configure(state="normal")
        self._clear_results()
        if not songs:
            self._show_message(T.L("no_results"))
            return
        favs = cloud_database.load_favorites()
        for i, song in enumerate(songs):
            self._create_trend_row(i + 1, song, favs)

    def _create_trend_row(self, rank, song, favs):
        song_id = str(song.get('id'))
        already_fav = song_id in favs
        row = ctk.CTkFrame(self._results_frame, fg_color=T.BG_CARD, corner_radius=8)
        row.pack(fill="x", padx=5, pady=4)
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        rank_color = T.ACCENT if rank <= 3 else T.BG_ELEVATED
        ctk.CTkLabel(inner, text=str(rank), width=30, height=30, font=T.FONT_BODY_BOLD, 
                      fg_color=rank_color, text_color="#ffffff", corner_radius=15).pack(side="left", padx=(0, 15))

        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(info, text=song.get('title', 'Unknown'), font=T.FONT_BODY_BOLD, text_color=T.TEXT_PRIMARY, anchor="w").pack(anchor="w")
        meta = f"{song.get('artist', 'Unknown')}  •  🔥 {song.get('play_count', 0)} {T.L('play_count')}"
        ctk.CTkLabel(info, text=meta, font=T.FONT_TINY, text_color=T.TEXT_ACCENT).pack(anchor="w")

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(side="right")
        
        fav_text = "❤" if already_fav else "🤍"
        ctk.CTkButton(btns, text=fav_text, width=40, height=32, 
                       fg_color="#be185d" if already_fav else T.BG_ELEVATED,
                       command=lambda s=song: self._toggle_favorite(s)).pack(side="left", padx=5)
        
        ctk.CTkButton(btns, text=T.L("play"), width=80, height=32, font=T.FONT_SMALL, fg_color=T.SUCCESS,
                       command=lambda s=song: self._play_song(s)).pack(side="left")
        self._result_widgets.append(row)

    def _play_song(self, song):
        if hasattr(self.app, 'search_tab'):
            self.app.search_tab._play_song(song)

    def _toggle_favorite(self, song):
        if hasattr(self.app, 'search_tab'):
            self.app.search_tab._toggle_favorite(song)
            # Delay refresh to allow file system/DB to update
            self.after(600, self._load_trends)

    def _show_message(self, text):
        self._clear_results()
        lbl = ctk.CTkLabel(self._results_frame, text=text, font=T.FONT_BODY, text_color=T.TEXT_MUTED)
        lbl.pack(pady=50)
        self._result_widgets.append(lbl)

    def _clear_results(self):
        for w in self._result_widgets: w.destroy()
        self._result_widgets.clear()
