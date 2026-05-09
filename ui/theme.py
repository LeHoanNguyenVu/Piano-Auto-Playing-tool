import customtkinter as ctk

class Theme:
    def __init__(self):
        self.current_theme = "Dark"
        # Window constants
        self.WINDOW_WIDTH = 900
        self.WINDOW_HEIGHT = 600
        self.SIDEBAR_WIDTH = 200
        self._set_midnight()

    def set_theme(self, name):
        self.current_theme = name
        if name == "Light": self._set_snowy()
        elif name == "Pink": self._set_sakura()
        elif name == "Blue": self._set_ocean()
        else: self._set_midnight()

    def _set_midnight(self):
        self.BG_DARK = "#0f172a"
        self.PLAYER_BG = "#121212"
        self.SIDEBAR_BG = "#1a1a1a"
        self.BG_DARKEST = "#0a0a0a"
        self.BG_CARD = "#242424"
        self.BG_CARD_HOVER = "#2a2a2a"
        self.BG_ELEVATED = "#333333"
        self.SIDEBAR_BTN_HOVER = "#2d2d2d"
        self.SIDEBAR_BTN_ACTIVE = "#333333"
        self.CONSOLE_BG = "#000000"
        self.ACCENT = "#7c3aed"
        self.ACCENT_HOVER = "#6d28d9"
        self.ACCENT_DIM = "#4c1d95"
        self.ACCENT_LIGHT = "#a78bfa"
        self.PROGRESS_BG = "#1e1e1e"
        self.TEXT_PRIMARY = "#ffffff"
        self.TEXT_SECONDARY = "#e2e8f0"
        self.TEXT_MUTED = "#94a3b8"
        self.TEXT_ACCENT = "#a78bfa"
        self.BORDER = "#3f3f46"
        self.SUCCESS = "#22c55e"
        self.ERROR = "#ef4444"
        self.WARNING = "#f59e0b"
        ctk.set_appearance_mode("dark")

    def _set_snowy(self):
        self.BG_DARK = "#f8fafc"
        self.PLAYER_BG = "#f8fafc"
        self.SIDEBAR_BG = "#f1f5f9"
        self.BG_DARKEST = "#e2e8f0"
        self.BG_CARD = "#ffffff"
        self.BG_CARD_HOVER = "#f1f5f9"
        self.BG_ELEVATED = "#cbd5e1"
        self.SIDEBAR_BTN_HOVER = "#e2e8f0"
        self.SIDEBAR_BTN_ACTIVE = "#cbd5e1"
        self.CONSOLE_BG = "#f1f5f9"
        self.ACCENT = "#3b82f6"
        self.ACCENT_HOVER = "#2563eb"
        self.ACCENT_DIM = "#bfdbfe"
        self.ACCENT_LIGHT = "#60a5fa"
        self.PROGRESS_BG = "#e2e8f0"
        self.TEXT_PRIMARY = "#1e293b"
        self.TEXT_SECONDARY = "#475569"
        self.TEXT_MUTED = "#64748b"
        self.TEXT_ACCENT = "#2563eb"
        self.BORDER = "#e2e8f0"
        self.SUCCESS = "#10b981"
        self.ERROR = "#ef4444"
        self.WARNING = "#f59e0b"
        ctk.set_appearance_mode("light")

    def _set_sakura(self):
        self.BG_DARK = "#fff1f2"
        self.PLAYER_BG = "#fff1f2"
        self.SIDEBAR_BG = "#ffe4e6"
        self.BG_DARKEST = "#fecdd3"
        self.BG_CARD = "#ffffff"
        self.BG_CARD_HOVER = "#fff1f2"
        self.BG_ELEVATED = "#fda4af"
        self.SIDEBAR_BTN_HOVER = "#fecdd3"
        self.SIDEBAR_BTN_ACTIVE = "#fda4af"
        self.CONSOLE_BG = "#fff1f2"
        self.ACCENT = "#fb7185"
        self.ACCENT_HOVER = "#f43f5e"
        self.ACCENT_DIM = "#fff1f2"
        self.ACCENT_LIGHT = "#fda4af"
        self.PROGRESS_BG = "#ffe4e6"
        self.TEXT_PRIMARY = "#881337"
        self.TEXT_SECONDARY = "#9f1239"
        self.TEXT_MUTED = "#be123c"
        self.TEXT_ACCENT = "#e11d48"
        self.BORDER = "#fecdd3"
        self.SUCCESS = "#10b981"
        self.ERROR = "#e11d48"
        self.WARNING = "#fbbf24"
        ctk.set_appearance_mode("light")

    def _set_ocean(self):
        self.BG_DARK = "#f0f9ff"
        self.PLAYER_BG = "#f0f9ff"
        self.SIDEBAR_BG = "#e0f2fe"
        self.BG_DARKEST = "#bae6fd"
        self.BG_CARD = "#ffffff"
        self.BG_CARD_HOVER = "#f0f9ff"
        self.BG_ELEVATED = "#7dd3fc"
        self.SIDEBAR_BTN_HOVER = "#bae6fd"
        self.SIDEBAR_BTN_ACTIVE = "#7dd3fc"
        self.CONSOLE_BG = "#f0f9ff"
        self.ACCENT = "#0284c7"
        self.ACCENT_HOVER = "#0369a1"
        self.ACCENT_DIM = "#e0f2fe"
        self.ACCENT_LIGHT = "#7dd3fc"
        self.PROGRESS_BG = "#bae6fd"
        self.TEXT_PRIMARY = "#0c4a6e"
        self.TEXT_SECONDARY = "#075985"
        self.TEXT_MUTED = "#0369a1"
        self.TEXT_ACCENT = "#0284c7"
        self.BORDER = "#bae6fd"
        self.SUCCESS = "#059669"
        self.ERROR = "#e11d48"
        self.WARNING = "#d97706"
        ctk.set_appearance_mode("light")

class Strings:
    def __init__(self):
        self.lang = "vi"
        self._data = {
            "vi": {
                "player": "Người chơi",
                "library": "Thư viện",
                "search": "Tìm kiếm",
                "trends": "Xu hướng",
                "settings": "Cài đặt",
                "open_midi": "📂 Mở MIDI",
                "duration": "Thời lượng",
                "notes": "Số nốt",
                "tempo": "Nhịp độ",
                "range": "Quãng",
                "delay": "Độ trễ (s)",
                "speed": "Tốc độ",
                "transpose": "Dịch tone",
                "play": "Chơi",
                "pause": "Tạm dừng",
                "stop": "Dừng",
                "btn_play": "▶ Chơi",
                "btn_pause": "⏸ Tạm dừng",
                "btn_stop": "⏹ Dừng",
                "save": "💾 Lưu cài đặt",
                "always_on_top": "Luôn hiện trên cùng",
                "theme": "Màu giao diện",
                "language": "Ngôn ngữ",
                "hotkeys": "Phím tắt",
                "refresh": "🔄 Làm mới",
                "searching": "Đang tìm kiếm...",
                "no_results": "Không tìm thấy kết quả.",
                "favorite": "❤ Yêu thích",
                "unfavorite": "🤍 Bỏ thích",
                "rank": "Hạng",
                "play_count": "lượt chơi",
                "delete_all": "🗑 Xoá tất cả",
                "confirm_delete": "Bạn có chắc muốn xóa sạch toàn bộ thư viện nhạc không?",
                "confirm": "Xác nhận"
            },
            "en": {
                "player": "Player",
                "library": "Library",
                "search": "Search",
                "trends": "Trends",
                "settings": "Settings",
                "open_midi": "📂 Open MIDI",
                "duration": "Duration",
                "notes": "Notes",
                "tempo": "Tempo",
                "range": "Range",
                "delay": "Delay (s)",
                "speed": "Speed",
                "transpose": "Transpose",
                "play": "Play",
                "pause": "Pause",
                "stop": "Stop",
                "btn_play": "▶ Play",
                "btn_pause": "⏸ Pause",
                "btn_stop": "⏹ Stop",
                "save": "💾 Save Settings",
                "always_on_top": "Always on Top",
                "theme": "Theme Color",
                "language": "Language",
                "hotkeys": "Hotkeys",
                "refresh": "🔄 Refresh",
                "searching": "Searching...",
                "no_results": "No results found.",
                "favorite": "❤ Favorite",
                "unfavorite": "🤍 Unfav",
                "rank": "Rank",
                "play_count": "plays",
                "delete_all": "🗑 Delete All",
                "confirm_delete": "Are you sure you want to delete all songs from library?",
                "confirm": "Confirm"
            }
        }

    def set_lang(self, lang):
        self.lang = lang

    def get(self, key):
        return self._data.get(self.lang, self._data["en"]).get(key, key)

# Typography
FONT_TITLE = ("Inter Bold", 26)
FONT_HEADING = ("Inter Bold", 20)
FONT_BODY = ("Inter Medium", 15)
FONT_BODY_BOLD = ("Inter Bold", 15)
FONT_SMALL = ("Inter Medium", 13)
FONT_TINY = ("Inter Medium", 11)
FONT_MONO_SMALL = ("JetBrains Mono", 12)

# Global instances
theme = Theme()
lang = Strings()

# Helpers
def __getattr__(name):
    if name == "lang": return lang
    return getattr(theme, name)

def L(key):
    return lang.get(key)

CORNER_RADIUS = 12
BUTTON_CORNER = 8
