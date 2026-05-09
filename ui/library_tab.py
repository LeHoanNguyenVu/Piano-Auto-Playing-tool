"""
Library Tab — Manage locally downloaded MIDI files and favorites.
"""

import os
import customtkinter as ctk
from ui import theme as T
from library import song_manager, cloud_database


class LibraryTab(ctk.CTkFrame):
    """Local song library interface."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self._song_widgets = []
        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header, text="📚 " + T.L("library"), font=T.FONT_TITLE, text_color=T.TEXT_PRIMARY).pack(side="left")
        
        # Bổ sung nút Xóa tất cả
        ctk.CTkButton(header, text="🗑 Xoá tất cả", width=100, height=28, font=T.FONT_TINY,
                       fg_color=T.ERROR, hover_color="#dc2626", command=self._delete_all).pack(side="right", padx=5)

        ctk.CTkButton(header, text=T.L("refresh"), width=90, height=28, font=T.FONT_SMALL,
                       fg_color=T.BG_ELEVATED, command=self.refresh_list).pack(side="right")

    def refresh_list(self):
        for w in self._song_widgets: w.destroy()
        self._song_widgets.clear()
        
        # Merge local manual imports and cloud favorites
        songs = song_manager.get_all_songs()
        favs = cloud_database.get_all_favorites()
        
        all_songs = songs + favs
        
        if not all_songs:
            lbl = ctk.CTkLabel(self._scroll, text=T.L("no_results"), font=T.FONT_BODY, text_color=T.TEXT_MUTED)
            lbl.pack(pady=40)
            self._song_widgets.append(lbl)
            return
            
        for s in all_songs: self._create_row(s)

    def _create_row(self, song):
        row = ctk.CTkFrame(self._scroll, fg_color=T.BG_CARD, corner_radius=8)
        row.pack(fill="x", padx=5, pady=4)
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        
        title = song.get('title', 'Unknown')
        artist = song.get('artist', '')
        display_text = f"♪ {title}" + (f" - {artist}" if artist else "")
        
        ctk.CTkLabel(inner, text=display_text, font=T.FONT_BODY_BOLD, text_color=T.TEXT_PRIMARY).pack(side="left")
        
        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(side="right")
        
        ctk.CTkButton(btns, text="🗑", width=32, height=32, fg_color=T.ERROR, 
                       command=lambda s=song: self._delete(s)).pack(side="left", padx=5)
        ctk.CTkButton(btns, text=T.L("play"), width=80, height=32, fg_color=T.SUCCESS,
                       command=lambda s=song: self._play(s)).pack(side="left")
        self._song_widgets.append(row)

    @property
    def _scroll(self):
        if not hasattr(self, '_scroll_frame'):
            self._scroll_frame = ctk.CTkScrollableFrame(self, fg_color=T.BG_DARKEST, corner_radius=T.CORNER_RADIUS)
            self._scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        return self._scroll_frame

    def _play(self, song):
        path = song.get('path') or song.get('local_path')
        if path and hasattr(self.app, 'player_tab'):
            self.app.player_tab.load_file(path, song.get('id'))
            self.app.show_frame("player")
            self.app.player_tab._play()

    def _delete(self, song):
        sid = song.get('id')
        # Check if it's a favorite or a manual import
        if 'local_path' in song:
            cloud_database.remove_favorite(sid)
        else:
            song_manager.delete_song(sid)
        self.refresh_list()

    def _delete_all(self):
        from tkinter import messagebox
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sạch toàn bộ thư viện nhạc không?"):
            song_manager.clear_all_songs()
            cloud_database.clear_all_favorites()
            self.refresh_list()
