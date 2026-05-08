"""
Settings Tab — Application settings, keymap config, and hotkey management.
"""

import json
import os
import customtkinter as ctk
from ui import theme as T


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")

DEFAULT_CONFIG = {
    "start_delay": 3.0,
    "default_speed": 100,
    "default_transpose": 0,
    "always_on_top": True,
    "hotkey_play": "F1",
    "hotkey_stop": "F2",
}


def load_config():
    """Load config from file, or return defaults."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
                # Merge with defaults
                merged = {**DEFAULT_CONFIG, **cfg}
                return merged
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config):
    """Save config to file."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


class SettingsTab(ctk.CTkFrame):
    """Application settings panel."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self.config = load_config()
        self._build_ui()

    def _build_ui(self):
        # ─── Header ───────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 15))

        ctk.CTkLabel(header, text="⚙ Settings", font=T.FONT_TITLE,
                      text_color=T.TEXT_PRIMARY).pack(side="left")

        # ─── Cloud Database ─────────────────────────────
        self._section("Cloud Database")

        cloud_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._setting_row("Supabase Status", "Connection status to the cloud catalog", cloud_frame)
        
        import library.cloud_database as cdb
        temp_db = cdb.CloudDatabase()
        status_text = "Connected ✅" if temp_db.is_connected else "Disconnected ❌"
        status_color = T.ACCENT if temp_db.is_connected else "#e74c3c"

        ctk.CTkLabel(cloud_frame, text=status_text, font=T.FONT_BODY_BOLD,
                      text_color=status_color).pack(side="left")

        # ─── General Settings ─────────────────────────────
        self._section("General")

        # Always on top
        self._aot_var = ctk.BooleanVar(value=self.config.get("always_on_top", True))
        self._setting_row("Always on Top", "Keep window above other windows",
                          self._create_switch(self._aot_var, self._on_aot_change))

        # Default start delay
        delay_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._setting_row("Start Delay", "Seconds to wait before playback starts", delay_frame)
        self._delay_var = ctk.StringVar(value=str(self.config.get("start_delay", 3.0)))
        ctk.CTkEntry(delay_frame, textvariable=self._delay_var, width=60, height=28,
                      font=T.FONT_SMALL, fg_color=T.BG_ELEVATED, border_color=T.BORDER).pack(side="left")
        ctk.CTkLabel(delay_frame, text="seconds", font=T.FONT_TINY,
                      text_color=T.TEXT_MUTED).pack(side="left", padx=5)

        # Default speed
        speed_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._setting_row("Default Speed", "Default playback speed percentage", speed_frame)
        self._speed_var = ctk.StringVar(value=str(self.config.get("default_speed", 100)))
        ctk.CTkEntry(speed_frame, textvariable=self._speed_var, width=60, height=28,
                      font=T.FONT_SMALL, fg_color=T.BG_ELEVATED, border_color=T.BORDER).pack(side="left")
        ctk.CTkLabel(speed_frame, text="%", font=T.FONT_TINY,
                      text_color=T.TEXT_MUTED).pack(side="left", padx=5)

        # ─── Hotkeys ─────────────────────────────────────
        self._section("Hotkeys")

        hotkey_info = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        hotkey_info.pack(fill="x", padx=20, pady=(0, 10))
        info_inner = ctk.CTkFrame(hotkey_info, fg_color="transparent")
        info_inner.pack(fill="x", padx=15, pady=12)

        for key, desc in [("F5", "Play"), ("F6", "Pause / Resume"), ("F7", "Stop")]:
            row = ctk.CTkFrame(info_inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=key, font=T.FONT_BODY_BOLD, text_color=T.TEXT_ACCENT,
                          width=60).pack(side="left")
            ctk.CTkLabel(row, text=desc, font=T.FONT_BODY, text_color=T.TEXT_SECONDARY).pack(side="left")

        # ─── Key Layout Info ──────────────────────────────
        self._section("Piano Key Layout")

        layout_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        layout_frame.pack(fill="x", padx=20, pady=(0, 10))

        layout_inner = ctk.CTkFrame(layout_frame, fg_color="transparent")
        layout_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(layout_inner, text="Roblox Virtual Piano — 61 Keys (C2 → C7)",
                      font=T.FONT_BODY_BOLD, text_color=T.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(layout_inner, text="White: 1 2 3 4 5 6 7 8 9 0 q w e r t y u i o p a s d f g h j k l z x c v b n m",
                      font=T.FONT_MONO_SMALL, text_color=T.TEXT_SECONDARY, wraplength=600).pack(anchor="w", pady=(5, 0))
        ctk.CTkLabel(layout_inner, text="Black: ! @ $ % ^ * ( Q W E T Y I O P S D G H J L Z C V B",
                      font=T.FONT_MONO_SMALL, text_color=T.TEXT_ACCENT, wraplength=600).pack(anchor="w", pady=(2, 0))

        # ─── Save Button ─────────────────────────────────
        ctk.CTkButton(
            self, text="💾 Save Settings", width=160, height=36,
            font=T.FONT_BODY_BOLD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            corner_radius=T.BUTTON_CORNER, command=self._save
        ).pack(pady=(10, 20))

        # ─── App Info ─────────────────────────────────────
        ctk.CTkLabel(self, text="RobloxPianoPlayer v1.0.0 — Built with ❤",
                      font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(side="bottom", pady=10)

    def _section(self, title):
        ctk.CTkLabel(self, text=title, font=T.FONT_HEADING, text_color=T.TEXT_PRIMARY).pack(
            anchor="w", padx=20, pady=(15, 8))

    def _setting_row(self, label, description, widget):
        frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        frame.pack(fill="x", padx=20, pady=(0, 6))
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=10)

        text_frame = ctk.CTkFrame(inner, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_frame, text=label, font=T.FONT_BODY_BOLD,
                      text_color=T.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=description, font=T.FONT_TINY,
                      text_color=T.TEXT_MUTED).pack(anchor="w")

        if isinstance(widget, ctk.CTkBaseClass):
            widget.pack(in_=inner, side="right")
        elif isinstance(widget, ctk.CTkFrame):
            widget.pack(in_=inner, side="right")

    def _create_switch(self, var, command):
        switch = ctk.CTkSwitch(self, variable=var, text="", width=46,
                                fg_color=T.BG_ELEVATED, progress_color=T.ACCENT,
                                button_color=T.TEXT_PRIMARY, command=command)
        return switch

    def _on_aot_change(self):
        val = self._aot_var.get()
        self.app.wm_attributes("-topmost", val)
        self.config["always_on_top"] = val

    def _save(self):
        try:
            self.config["start_delay"] = float(self._delay_var.get())
        except ValueError:
            pass
        try:
            self.config["default_speed"] = int(self._speed_var.get())
        except ValueError:
            pass
        # Save local config
        self.config["always_on_top"] = self._aot_var.get()
        save_config(self.config)
