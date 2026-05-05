"""
Search Tab — Search and download MIDI files from online sources.
"""

import customtkinter as ctk
from ui import theme as T
from library import cloud_database, song_manager


class SearchTab(ctk.CTkFrame):
    """Online MIDI search and download interface."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self._results = []
        self.db = cloud_database.CloudDatabase()
        self._build_ui()

    def _build_ui(self):
        # ─── Header ───────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="☁ Cloud Database Search", font=T.FONT_TITLE,
                      text_color=T.TEXT_PRIMARY).pack(side="left")

        # ─── Search Bar ──────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        search_frame.pack(fill="x", padx=20, pady=(0, 10))

        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=15, pady=12)

        self._search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            search_inner, textvariable=self._search_var,
            placeholder_text="Search for a song name...",
            height=34, font=T.FONT_BODY, fg_color=T.BG_ELEVATED,
            border_color=T.BORDER, text_color=T.TEXT_PRIMARY
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        search_entry.bind("<Return>", lambda e: self._do_search())

        self._search_btn = ctk.CTkButton(
            search_inner, text="🔍 Search", width=100, height=34,
            font=T.FONT_BODY_BOLD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            corner_radius=T.BUTTON_CORNER, command=self._do_search
        )
        self._search_btn.pack(side="right")

        # ─── Direct URL Download ─────────────────────────
        url_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        url_frame.pack(fill="x", padx=20, pady=(0, 10))

        url_inner = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_inner.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(url_inner, text="Direct URL:", font=T.FONT_SMALL,
                      text_color=T.TEXT_SECONDARY).pack(side="left")

        self._url_var = ctk.StringVar()
        ctk.CTkEntry(
            url_inner, textvariable=self._url_var,
            placeholder_text="Paste MIDI file URL here...",
            height=30, font=T.FONT_SMALL, fg_color=T.BG_ELEVATED,
            border_color=T.BORDER, text_color=T.TEXT_PRIMARY
        ).pack(side="left", fill="x", expand=True, padx=8)

        ctk.CTkButton(
            url_inner, text="⬇ Download", width=100, height=30,
            font=T.FONT_SMALL, fg_color=T.INFO, hover_color="#2563eb",
            corner_radius=T.BUTTON_CORNER, command=self._download_url
        ).pack(side="right")

        # ─── Status ──────────────────────────────────────
        self._status = ctk.CTkLabel(self, text="", font=T.FONT_SMALL,
                                     text_color=T.TEXT_MUTED)
        self._status.pack(anchor="w", padx=25, pady=(0, 5))

        # ─── Results List ─────────────────────────────────
        self._results_frame = ctk.CTkScrollableFrame(
            self, fg_color=T.BG_DARKEST, corner_radius=T.CORNER_RADIUS,
            scrollbar_button_color=T.ACCENT_DIM
        )
        self._results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._result_widgets = []

        # Initial message
        self._show_message("Enter a song name above and click Search to find MIDI files online.")

    def _show_message(self, text):
        self._clear_results()
        lbl = ctk.CTkLabel(self._results_frame, text=text, font=T.FONT_BODY,
                            text_color=T.TEXT_MUTED, wraplength=500)
        lbl.pack(pady=40)
        self._result_widgets.append(lbl)

    def _clear_results(self):
        for w in self._result_widgets:
            w.destroy()
        self._result_widgets.clear()

    def _do_search(self):
        query = self._search_var.get().strip()
        if not query:
            return

        self._status.configure(text="🔄 Searching...", text_color=T.WARNING)
        self._search_btn.configure(state="disabled")
        self._show_message("Searching...")

        import threading
        def _search_thread():
            try:
                results = self.db.search(query)
                self.after(0, self._display_results, results)
            except Exception as e:
                self.after(0, lambda: self._status.configure(text=f"✗ Error: {e}", text_color=T.ERROR))
                
        threading.Thread(target=_search_thread, daemon=True).start()

    def _display_results(self, results):
        self._search_btn.configure(state="normal")
        self._results = results
        self._clear_results()

        if not results:
            self._status.configure(text="No results found", text_color=T.TEXT_MUTED)
            self._show_message("No MIDI files found. Try a different search term.\n\n"
                               "Tip: You can also paste a direct URL to any .mid file above.")
            return

        self._status.configure(text=f"Found {len(results)} result(s)", text_color=T.SUCCESS)

        for i, result in enumerate(results):
            row = ctk.CTkFrame(self._results_frame, fg_color=T.BG_CARD, corner_radius=4)
            row.pack(fill="x", padx=5, pady=2)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=8)

            # Title
            ctk.CTkLabel(inner, text=f"♪ {result['title']}", font=T.FONT_SMALL,
                          text_color=T.TEXT_PRIMARY, anchor="w").pack(side="left", fill="x", expand=True)

            # Source badge
            ctk.CTkLabel(inner, text=result.get('artist', 'Unknown'), font=T.FONT_TINY,
                          text_color=T.TEXT_ACCENT).pack(side="left", padx=10)

            # Download button
            ctk.CTkButton(
                inner, text="⬇ Download", width=90, height=26,
                font=T.FONT_SMALL, fg_color=T.INFO, hover_color="#2563eb",
                corner_radius=4, command=lambda r=result: self._download_result(r)
            ).pack(side="right")

            # Hover
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=T.BG_CARD_HOVER))
            row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=T.BG_CARD))

            self._result_widgets.append(row)

    def _download_result(self, result):
        self._status.configure(text=f"⬇ Downloading: {result['title']}...", text_color=T.WARNING)
        import os
        import threading
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "songs")
        
        def _dl_thread():
            try:
                os.makedirs(save_dir, exist_ok=True)
                file_path = self.db.download_song(result, save_dir)
                self.after(0, self._handle_download, True, file_path, None)
            except Exception as e:
                self.after(0, self._handle_download, False, None, str(e))
                
        threading.Thread(target=_dl_thread, daemon=True).start()

    def _download_url(self):
        url = self._url_var.get().strip()
        if not url:
            return
        self._status.configure(text="⬇ Downloading...", text_color=T.WARNING)
        import os
        import threading
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "songs")
        
        def _dl_url_thread():
            try:
                os.makedirs(save_dir, exist_ok=True)
                # Mock a song object for the direct URL
                song = {"title": "Direct Download", "url": url}
                file_path = self.db.download_song(song, save_dir)
                self.after(0, self._handle_download, True, file_path, None)
            except Exception as e:
                self.after(0, self._handle_download, False, None, str(e))
                
        threading.Thread(target=_dl_url_thread, daemon=True).start()

    def _handle_download(self, success, file_path, error):
        if success:
            # Import into library
            result = song_manager.import_midi(file_path)
            if result:
                self._status.configure(text=f"✓ Downloaded: {result['title']}", text_color=T.SUCCESS)
                # Refresh library tab if it exists
                if hasattr(self.app, 'library_tab'):
                    self.app.library_tab._refresh_list()
            else:
                self._status.configure(text="✗ Failed to import file", text_color=T.ERROR)
        else:
            self._status.configure(text=f"✗ Download failed: {error}", text_color=T.ERROR)
