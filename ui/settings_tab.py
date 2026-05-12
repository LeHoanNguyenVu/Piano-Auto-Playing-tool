"""
Settings Tab — Application settings, keymap config, and hotkey management.
"""

import json
import os
import threading
import customtkinter as ctk
from ui import theme as T


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")

DEFAULT_CONFIG = {
    "start_delay": 3.0,
    "default_speed": 100,
    "default_transpose": 0,
    "always_on_top": True,
    "hotkey_play": "F5",
    "hotkey_stop": "F7",
    "theme": "Dark",
    "language": "vi"
}


def load_config():
    """Load config from file, or return defaults."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
                merged = {**DEFAULT_CONFIG, **cfg}
                return merged
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config):
    """Save config to file."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


class SettingsTab(ctk.CTkScrollableFrame):
    """Application settings panel."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0,
                         scrollbar_button_color=T.ACCENT_DIM)
        self.app = app
        self.config = load_config()
        self._build_ui()

    def _build_ui(self):
        # ─── Header ───────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 15))

        ctk.CTkLabel(header, text="⚙ " + T.L("settings"), font=T.FONT_TITLE,
                      text_color=T.TEXT_PRIMARY).pack(side="left")

        # ─── Cloud Database ─────────────────────────────
        self._section("Cloud Database")

        row_cloud = self._setting_row("Supabase Status", "Connection status to the cloud catalog")
        self._cloud_status_label = ctk.CTkLabel(row_cloud, text="Checking... ⏳", font=T.FONT_BODY_BOLD,
                                                text_color=T.WARNING)
        self._cloud_status_label.pack(side="right")
        
        threading.Thread(target=self._check_cloud_status, daemon=True).start()

        # ─── Appearance Settings ──────────────────────────
        self._section(T.L("theme"))

        # Theme selection
        row_theme = self._setting_row(T.L("theme"), "Choose your favorite UI style")
        self._theme_var = ctk.StringVar(value=self.config.get("theme", "Dark"))
        ctk.CTkOptionMenu(
            row_theme, variable=self._theme_var,
            values=["Dark", "Light", "Pink", "Blue"],
            width=120, height=28, font=T.FONT_SMALL,
            fg_color=T.BG_ELEVATED, button_color=T.ACCENT,
            button_hover_color=T.ACCENT_HOVER,
            command=self._on_theme_change
        ).pack(side="right")

        # Language selection
        row_lang = self._setting_row(T.L("language"), "Set application language")
        self._lang_var = ctk.StringVar(value="Tiếng Việt" if self.config.get("language") == "vi" else "English")
        ctk.CTkOptionMenu(
            row_lang, variable=self._lang_var,
            values=["Tiếng Việt", "English"],
            width=120, height=28, font=T.FONT_SMALL,
            fg_color=T.BG_ELEVATED, button_color=T.ACCENT,
            button_hover_color=T.ACCENT_HOVER,
            command=self._on_lang_change
        ).pack(side="right")

        # ─── General Settings ─────────────────────────────
        self._section("General")

        # Always on top
        self._aot_var = ctk.BooleanVar(value=self.config.get("always_on_top", True))
        row_aot = self._setting_row(T.L("always_on_top"), "Keep window above other windows")
        ctk.CTkSwitch(row_aot, variable=self._aot_var, text="", width=46,
                      fg_color=T.BG_ELEVATED, progress_color=T.ACCENT,
                      button_color=T.TEXT_PRIMARY, command=self._on_aot_change).pack(side="right")

        # ─── Hotkeys ─────────────────────────────────────
        self._section(T.L("hotkeys"))

        hotkey_info = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        hotkey_info.pack(fill="x", padx=20, pady=(0, 10))
        info_inner = ctk.CTkFrame(hotkey_info, fg_color="transparent")
        info_inner.pack(fill="x", padx=15, pady=12)

        for key, desc_key in [("F5", "play"), ("F6", "pause"), ("F7", "stop")]:
            row = ctk.CTkFrame(info_inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=key, font=T.FONT_BODY_BOLD, text_color=T.TEXT_ACCENT,
                          width=60).pack(side="left")
            ctk.CTkLabel(row, text=T.L(desc_key), font=T.FONT_BODY, text_color=T.TEXT_SECONDARY).pack(side="left")

        # ─── Save Button ─────────────────────────────────
        ctk.CTkButton(
            self, text=T.L("save"), width=200, height=40,
            font=T.FONT_BODY_BOLD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            corner_radius=T.BUTTON_CORNER, command=self._save
        ).pack(pady=30)

        # ─── App Info ─────────────────────────────────────
        ctk.CTkLabel(self, text="RobloxPianoPlayer v1.0.0",
                      font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(pady=10)

    def _section(self, title):
        ctk.CTkLabel(self, text=title, font=T.FONT_HEADING, text_color=T.TEXT_PRIMARY).pack(
            anchor="w", padx=20, pady=(15, 8))

    def _setting_row(self, label, description):
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
        return inner

    def _check_cloud_status(self):
        try:
            from library.cloud_database import get_cloud_db
            db = get_cloud_db()
            status_text = "Connected ✅" if db.is_connected else "Disconnected ❌"
            status_color = T.SUCCESS if db.is_connected else T.ERROR
            self.after(0, lambda: self._cloud_status_label.configure(text=status_text, text_color=status_color))
        except Exception:
            self.after(0, lambda: self._cloud_status_label.configure(text="Error ❌", text_color=T.ERROR))

    def _on_theme_change(self, new_theme):
        self.config["theme"] = new_theme
        save_config(self.config)
        T.theme.set_theme(new_theme)
        if hasattr(self.app, 'refresh_theme'):
            self.app.refresh_theme()

    def _on_lang_change(self, val):
        new_lang = "vi" if val == "Tiếng Việt" else "en"
        self.config["language"] = new_lang
        save_config(self.config)
        T.lang.set_lang(new_lang)
        if hasattr(self.app, 'refresh_theme'):
            self.app.refresh_theme()

    def _on_aot_change(self):
        val = self._aot_var.get()
        self.app.wm_attributes("-topmost", val)
        self.config["always_on_top"] = val
        save_config(self.config)

    def _save(self):
        try:
            self.config["theme"] = self._theme_var.get()
            self.config["language"] = "vi" if self._lang_var.get() == "Tiếng Việt" else "en"
            save_config(self.config)
            self.app.wm_attributes("-topmost", self._aot_var.get())
        except Exception:
            pass
