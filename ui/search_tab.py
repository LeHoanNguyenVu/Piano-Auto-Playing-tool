"""
Search Tab — Online song search and discovery via Supabase.
"""

import threading
import customtkinter as ctk
from ui import theme as T
from library import cloud_database, song_manager


class SearchTab(ctk.CTkFrame):
    """Cloud song search interface."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self.db = None
        self._result_widgets = []
        self._search_timer = None
        self._build_ui()
        self.after(200, self._init_db)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header, text="🌐 " + T.L("search"), font=T.FONT_TITLE, text_color=T.TEXT_PRIMARY).pack(side="left")

        search_bar = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        search_bar.pack(fill="x", padx=20, pady=(0, 15))
        
        # Search variable for tracing (Suggestions)
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_type)

        self._search_entry = ctk.CTkEntry(search_bar, placeholder_text="Search songs or artists...", 
                                          textvariable=self._search_var,
                                          height=40, font=T.FONT_BODY, fg_color="transparent", border_width=0)
        self._search_entry.pack(side="left", fill="x", expand=True, padx=15)
        
        self._search_btn = ctk.CTkButton(search_bar, text="🔍", width=50, height=32, fg_color=T.ACCENT, command=self._search)
        self._search_btn.pack(side="right", padx=10)

        self._results_frame = ctk.CTkScrollableFrame(self, fg_color=T.BG_DARKEST, corner_radius=T.CORNER_RADIUS)
        self._results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _init_db(self):
        def _worker(): self.db = cloud_database.CloudDatabase()
        threading.Thread(target=_worker, daemon=True).start()

    def _on_type(self, *args):
        """Suggestions logic: debounce search while typing."""
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(400, self._search)

    def _search(self):
        query = self._search_var.get().strip()
        if not self.db: return
        if not query:
            self._display_results(self.db.catalog[:50]) # Show initial catalog
            return
            
        def _worker():
            results = self.db.search(query)
            self.after(0, self._display_results, results)
        threading.Thread(target=_worker, daemon=True).start()

    def _display_results(self, songs):
        self._clear_results()
        if not songs:
            self._show_message(T.L("no_results"))
            return
        favs = cloud_database.load_favorites()
        for s in songs: self._create_row(s, favs)

    def _create_row(self, song, favs):
        song_id = str(song.get('id'))
        already_fav = song_id in favs
        row = ctk.CTkFrame(self._results_frame, fg_color=T.BG_CARD, corner_radius=8)
        row.pack(fill="x", padx=5, pady=4)
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        
        title_text = f"{song.get('title', 'Unknown')} - {song.get('artist', 'Unknown')}"
        ctk.CTkLabel(inner, text=title_text, font=T.FONT_BODY_BOLD, text_color=T.TEXT_PRIMARY).pack(side="left")
        
        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(side="right")
        
        fav_text = "❤" if already_fav else "🤍"
        ctk.CTkButton(btns, text=fav_text, width=40, height=32, fg_color="#be185d" if already_fav else T.BG_ELEVATED,
                       command=lambda s=song: self._toggle_favorite(s)).pack(side="left", padx=5)
        ctk.CTkButton(btns, text=T.L("play"), width=80, height=32, fg_color=T.SUCCESS,
                       command=lambda s=song: self._play_song(s)).pack(side="left")
        self._result_widgets.append(row)

    def _play_song(self, song):
        self._show_message(T.L("searching"))
        def _worker():
            try:
                path = self.db.download_to_temp(song)
                if path: self.after(0, lambda: self._start_playback(path, song.get('id')))
            except Exception as e:
                self.after(0, lambda: self._show_message(f"Error: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _start_playback(self, path, song_id):
        if hasattr(self.app, 'player_tab'):
            self.app.player_tab.load_file(path, song_id)
            self.app.show_frame("player")
            self.app.player_tab._play()

    def _toggle_favorite(self, song):
        sid = str(song.get('id'))
        favs = cloud_database.load_favorites()
        if sid in favs:
            cloud_database.remove_favorite(sid)
        else:
            def _worker():
                try:
                    self.db.download_to_favorites(song)
                    self.after(0, self._search)
                except: pass
            threading.Thread(target=_worker, daemon=True).start()
        self._search()

    def _show_message(self, text):
        self._clear_results()
        lbl = ctk.CTkLabel(self._results_frame, text=text, font=T.FONT_BODY, text_color=T.TEXT_MUTED)
        lbl.pack(pady=40)
        self._result_widgets.append(lbl)

    def _clear_results(self):
        for w in self._result_widgets: w.destroy()
        self._result_widgets.clear()
