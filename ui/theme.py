"""
Theme Module — Dark theme colors, fonts, and styling constants.
"""

# ─── Color Palette ─────────────────────────────────────────────────
BG_DARKEST = "#0b0b14"      # Deepest background
BG_DARK = "#0f0f1a"         # Main background
BG_SECONDARY = "#161625"    # Sidebar / secondary panels
BG_CARD = "#1c1c2e"         # Cards / input fields
BG_CARD_HOVER = "#242440"   # Card hover state
BG_ELEVATED = "#22223a"     # Elevated surfaces

ACCENT = "#7c3aed"          # Primary accent (purple)
ACCENT_HOVER = "#6d28d9"    # Accent hover
ACCENT_LIGHT = "#a78bfa"    # Light accent for text
ACCENT_DIM = "#4c1d95"      # Dimmed accent

SUCCESS = "#22c55e"         # Green for success states
WARNING = "#f59e0b"         # Amber for warnings
ERROR = "#ef4444"           # Red for errors
INFO = "#3b82f6"            # Blue for info

TEXT_PRIMARY = "#e2e8f0"    # Primary text (near white)
TEXT_SECONDARY = "#94a3b8"  # Secondary text (muted)
TEXT_MUTED = "#64748b"      # Very muted text
TEXT_ACCENT = "#c4b5fd"     # Accent-colored text

BORDER = "#2d2d4a"          # Subtle border
BORDER_FOCUS = "#7c3aed"    # Focus border

# ─── Semantic Colors ───────────────────────────────────────────────
SIDEBAR_BG = BG_SECONDARY
SIDEBAR_BTN = "transparent"
SIDEBAR_BTN_HOVER = "#1e1e35"
SIDEBAR_BTN_ACTIVE = ACCENT_DIM

PLAYER_BG = BG_DARK
CONSOLE_BG = "#0a0a12"

PROGRESS_BG = "#1a1a30"
PROGRESS_FILL = ACCENT

# ─── Fonts ─────────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_HEADING = (FONT_FAMILY, 16, "bold")
FONT_SUBHEADING = (FONT_FAMILY, 14, "bold")
FONT_BODY = (FONT_FAMILY, 13)
FONT_BODY_BOLD = (FONT_FAMILY, 13, "bold")
FONT_SMALL = (FONT_FAMILY, 11)
FONT_TINY = (FONT_FAMILY, 10)
FONT_MONO = ("Consolas", 11)
FONT_MONO_SMALL = ("Consolas", 10)

# ─── Dimensions ────────────────────────────────────────────────────
SIDEBAR_WIDTH = 180
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 580
CORNER_RADIUS = 8
BUTTON_HEIGHT = 36
BUTTON_CORNER = 6
