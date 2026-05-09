"""
Main Application Window — Sidebar navigation with tab switching and global hotkeys.
"""

import ctypes
import threading
import time
import customtkinter as ctk
from ui import theme as T
from ui.player_tab import PlayerTab
from ui.library_tab import LibraryTab
from ui.search_tab import SearchTab
from ui.trends_tab import TrendsTab
from ui.settings_tab import SettingsTab


# Win32 Virtual Key codes for hotkeys
VK_F5 = 0x74
VK_F6 = 0x75
VK_F7 = 0x76


class App(ctk.CTk):
    """Main application window with sidebar navigation."""

    def __init__(self):
        super().__init__()
        
        # Load initial config
        from ui.settings_tab import load_config
        self.config = load_config()
        
        # Set theme and language
        T.theme.set_theme(self.config.get("theme", "Dark"))
        T.lang.set_lang(self.config.get("language", "vi"))

        # ── Window setup ──────────────────────────────────
        self.title("RobloxPianoPlayer")
        self.geometry(f"{T.WINDOW_WIDTH}x{T.WINDOW_HEIGHT}")
        self.minsize(800, 500)
        self.configure(fg_color=T.BG_DARK)

        try:
            self.wm_attributes("-topmost", self.config.get("always_on_top", True))
        except Exception:
            pass

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────
        self._build_sidebar()

        # ── Content area ──────────────────────────────────
        self.content = ctk.CTkFrame(self, fg_color=T.PLAYER_BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # ── Create tabs ──────────────────────────────────
        self.player_tab = PlayerTab(self.content, self)
        self.library_tab = LibraryTab(self.content, self)
        self.search_tab = SearchTab(self.content, self)
        self.trends_tab = TrendsTab(self.content, self)
        self.settings_tab = SettingsTab(self.content, self)

        self._frames = {
            "player": self.player_tab,
            "library": self.library_tab,
            "search": self.search_tab,
            "trends": self.trends_tab,
            "settings": self.settings_tab,
        }

        self._current_page = None
        self.show_frame("player")

        # ── Global hotkeys ────────────────────────────────
        self._hotkey_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        self._hotkey_thread.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=T.SIDEBAR_WIDTH, fg_color=T.SIDEBAR_BG, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(6, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=10, pady=(18, 20), sticky="ew")

        ctk.CTkLabel(logo_frame, text="🎹", font=("Segoe UI", 26)).pack(side="left", padx=(8, 6))
        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="RobloxPiano", font=("Segoe UI", 15, "bold"),
                      text_color=T.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Player v1.0", font=T.FONT_TINY,
                      text_color=T.TEXT_MUTED).pack(anchor="w")

        # Navigation buttons
        self._nav_buttons = {}
        nav_items = [
            ("player", "🎹  " + T.L("player"), 1),
            ("library", "📚  " + T.L("library"), 2),
            ("search", "🌐  " + T.L("search"), 3),
            ("trends", "🔥  " + T.L("trends"), 4),
            ("settings", "⚙  " + T.L("settings"), 5),
        ]

        for name, text, row in nav_items:
            btn = ctk.CTkButton(
                sidebar, text=text, height=40, anchor="w",
                font=T.FONT_BODY, corner_radius=0,
                fg_color="transparent", text_color=T.TEXT_SECONDARY,
                hover_color=T.SIDEBAR_BTN_HOVER,
                command=lambda n=name: self.show_frame(n)
            )
            btn.grid(row=row, column=0, sticky="ew", padx=0)
            self._nav_buttons[name] = btn

        # Hotkeys hint — clean, no duplicate icons
        hint_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        hint_frame.grid(row=7, column=0, sticky="sew", padx=10, pady=10)
        ctk.CTkLabel(hint_frame, text=T.L("hotkeys"), font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(anchor="w")
        ctk.CTkLabel(hint_frame, text="F5  " + T.L("play"), font=T.FONT_TINY, text_color=T.TEXT_ACCENT).pack(anchor="w")
        ctk.CTkLabel(hint_frame, text="F6  " + T.L("pause"), font=T.FONT_TINY, text_color=T.TEXT_ACCENT).pack(anchor="w")
        ctk.CTkLabel(hint_frame, text="F7  " + T.L("stop"), font=T.FONT_TINY, text_color=T.TEXT_ACCENT).pack(anchor="w")

    def show_frame(self, name):
        """Switch to a tab by name."""
        if name == self._current_page:
            return

        self._current_page = name
        for frame in self._frames.values():
            frame.grid_forget()

        if name == "trends" and hasattr(self, 'trends_tab'):
            self.trends_tab._load_trends()

        self._frames[name].grid(row=0, column=0, sticky="nsew")

        for btn_name, btn in self._nav_buttons.items():
            if btn_name == name:
                btn.configure(fg_color=T.SIDEBAR_BTN_ACTIVE, text_color=T.TEXT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=T.TEXT_SECONDARY)

    def refresh_theme(self):
        """Rebuild everything for theme or language change."""
        self.configure(fg_color=T.BG_DARK)
        self.content.configure(fg_color=T.PLAYER_BG)
        for w in self.grid_slaves(column=0):
            w.destroy()
        self._build_sidebar()
        old_page = self._current_page
        for f in self._frames.values():
            f.destroy()
        self.player_tab = PlayerTab(self.content, self)
        self.library_tab = LibraryTab(self.content, self)
        self.search_tab = SearchTab(self.content, self)
        self.trends_tab = TrendsTab(self.content, self)
        self.settings_tab = SettingsTab(self.content, self)
        self._frames = {
            "player": self.player_tab,
            "library": self.library_tab,
            "search": self.search_tab,
            "trends": self.trends_tab,
            "settings": self.settings_tab,
        }
        self._current_page = None
        self.show_frame(old_page or "player")

    def _hotkey_listener(self):
        user32 = ctypes.windll.user32
        prev_f5, prev_f6, prev_f7 = False, False, False
        while True:
            try:
                s5 = user32.GetAsyncKeyState(VK_F5) & 0x8000
                if s5 and not prev_f5: self.after(0, self._hotkey_start)
                prev_f5 = bool(s5)
                s6 = user32.GetAsyncKeyState(VK_F6) & 0x8000
                if s6 and not prev_f6: self.after(0, self._hotkey_pause)
                prev_f6 = bool(s6)
                s7 = user32.GetAsyncKeyState(VK_F7) & 0x8000
                if s7 and not prev_f7: self.after(0, self._hotkey_stop)
                prev_f7 = bool(s7)
                time.sleep(0.010)
            except Exception:
                time.sleep(0.05)

    def _hotkey_start(self):
        if hasattr(self, 'player_tab'): self.player_tab._play()
    def _hotkey_pause(self):
        if hasattr(self, 'player_tab'): self.player_tab._pause()
    def _hotkey_stop(self):
        if hasattr(self, 'player_tab'): self.player_tab._stop()

    def _on_close(self):
        try: self.player_tab.engine.stop()
        except Exception: pass
        self.destroy()
