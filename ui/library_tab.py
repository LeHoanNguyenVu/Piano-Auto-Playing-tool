"""
Library Tab — Browse, search, import, and manage local MIDI song library.
"""

import os
import customtkinter as ctk
from tkinter import filedialog
from ui import theme as T
from library import song_manager


class LibraryTab(ctk.CTkFrame):
    """Song library browser with search, import, and management."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # ─── Header ───────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="📚 Song Library", font=T.FONT_TITLE,
                      text_color=T.TEXT_PRIMARY).pack(side="left")

        ctk.CTkButton(
            header, text="📂 Import MIDI", width=130, height=32,
            font=T.FONT_BODY_BOLD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            corner_radius=T.BUTTON_CORNER, command=self._import_midi
        ).pack(side="right")

        # ─── Search Bar ──────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        search_frame.pack(fill="x", padx=20, pady=(0, 10))

        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(search_inner, text="🔍", font=T.FONT_BODY).pack(side="left")
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_list())
        ctk.CTkEntry(
            search_inner, textvariable=self._search_var, placeholder_text="Search songs...",
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

        # Column headers
        header_row = ctk.CTkFrame(self._list_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=5, pady=(5, 5))
        for text, w in [("Title", 250), ("Notes", 60), ("Duration", 70), ("Tempo", 60), ("Added", 100)]:
            ctk.CTkLabel(header_row, text=text, font=T.FONT_TINY, text_color=T.TEXT_MUTED,
                          width=w, anchor="w").pack(side="left", padx=2)

        self._song_widgets = []
        self._refresh_list()

    def _refresh_list(self):
        """Refresh the song list display."""
        # Clear existing
        for w in self._song_widgets:
            w.destroy()
        self._song_widgets.clear()

        query = self._search_var.get()
        songs = song_manager.search_songs(query) if query else song_manager.get_all_songs()
        self._count_label.configure(text=f"{len(songs)} song{'s' if len(songs) != 1 else ''}")

        if not songs:
            empty = ctk.CTkLabel(
                self._list_frame, text="No songs in library.\nClick 'Import MIDI' or use the Search tab to add songs.",
                font=T.FONT_BODY, text_color=T.TEXT_MUTED
            )
            empty.pack(pady=40)
            self._song_widgets.append(empty)
            return

        for song in songs:
            row = self._create_song_row(song)
            self._song_widgets.append(row)

    def _create_song_row(self, song):
        """Create a clickable row for a song."""
        row = ctk.CTkFrame(self._list_frame, fg_color=T.BG_CARD, corner_radius=4, height=40)
        row.pack(fill="x", padx=5, pady=2)
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=4)

        # Title
        title = song.get("title", "Unknown")
        ctk.CTkLabel(inner, text=f"♪ {title}", font=T.FONT_SMALL, text_color=T.TEXT_PRIMARY,
                      width=250, anchor="w").pack(side="left", padx=2)

        # Note count
        ctk.CTkLabel(inner, text=str(song.get("note_count", "—")), font=T.FONT_SMALL,
                      text_color=T.TEXT_SECONDARY, width=60, anchor="w").pack(side="left", padx=2)

        # Duration
        dur = song.get("duration", 0)
        mins, secs = divmod(int(dur), 60)
        ctk.CTkLabel(inner, text=f"{mins}:{secs:02d}", font=T.FONT_SMALL,
                      text_color=T.TEXT_SECONDARY, width=70, anchor="w").pack(side="left", padx=2)

        # Tempo
        ctk.CTkLabel(inner, text=f"{song.get('tempo_bpm', '—')}", font=T.FONT_SMALL,
                      text_color=T.TEXT_SECONDARY, width=60, anchor="w").pack(side="left", padx=2)

        # Added date
        ctk.CTkLabel(inner, text=song.get("added_date", ""), font=T.FONT_TINY,
                      text_color=T.TEXT_MUTED, width=100, anchor="w").pack(side="left", padx=2)

        # Action buttons
        ctk.CTkButton(
            inner, text="▶", width=30, height=26, font=T.FONT_SMALL,
            fg_color=T.SUCCESS, hover_color="#16a34a", corner_radius=4,
            command=lambda s=song: self._play_song(s)
        ).pack(side="right", padx=2)

        ctk.CTkButton(
            inner, text="✕", width=30, height=26, font=T.FONT_SMALL,
            fg_color=T.ERROR, hover_color="#dc2626", corner_radius=4,
            command=lambda s=song: self._delete_song(s)
        ).pack(side="right", padx=2)

        # Hover effect
        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=T.BG_CARD_HOVER))
        row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=T.BG_CARD))

        return row

    def _play_song(self, song):
        """Load song into player and switch to player tab."""
        path = song.get("path", "")
        if os.path.exists(path):
            self.app.player_tab.load_file(path)
            self.app.show_frame("player")

    def _delete_song(self, song):
        """Delete a song from the library."""
        song_manager.delete_song(song["id"])
        self._refresh_list()

    def _import_midi(self):
        """Import MIDI files from disk."""
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
