"""
Key Simulator — Uses Windows SendInput API for reliable Roblox input.
Sends press+release atomically in a single SendInput call to prevent
Shift key state from bleeding across rapid notes.
"""

import ctypes
from ctypes import wintypes

# ─── Windows API ─────────────────────────────────────────────────
user32 = ctypes.windll.user32

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_SHIFT = 0x10

# ─── ctypes structures ──────────────────────────────────────────
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         wintypes.WORD),
        ("wScan",       wintypes.WORD),
        ("dwFlags",     wintypes.DWORD),
        ("time",        wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 28)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", INPUTUNION)]

# ─── Virtual Key Code map ───────────────────────────────────────
VK = {
    '0':0x30,'1':0x31,'2':0x32,'3':0x33,'4':0x34,
    '5':0x35,'6':0x36,'7':0x37,'8':0x38,'9':0x39,
    'a':0x41,'b':0x42,'c':0x43,'d':0x44,'e':0x45,
    'f':0x46,'g':0x47,'h':0x48,'i':0x49,'j':0x4A,
    'k':0x4B,'l':0x4C,'m':0x4D,'n':0x4E,'o':0x4F,
    'p':0x50,'q':0x51,'r':0x52,'s':0x53,'t':0x54,
    'u':0x55,'v':0x56,'w':0x57,'x':0x58,'y':0x59,
    'z':0x5A,
}

# Black keys → base key (cần Shift)
SHIFT_MAP = {
    '!': '1', '@': '2', '$': '4', '%': '5',
    '^': '6', '*': '8', '(': '9',
    'Q': 'q', 'W': 'w', 'E': 'e', 'T': 't', 'Y': 'y',
    'I': 'i', 'O': 'o', 'P': 'p', 'S': 's', 'D': 'd',
    'G': 'g', 'H': 'h', 'J': 'j', 'L': 'l', 'Z': 'z',
    'C': 'c', 'V': 'v', 'B': 'b',
}

VALID_KEYS = set('1234567890qwertyuiopasdfghjklzxcvbnm') | set(SHIFT_MAP.keys())

# ─── Internal helpers ────────────────────────────────────────────
_extra = ctypes.c_ulong(0)

def _inp(vk, flags=0):
    i = INPUT()
    i.type = INPUT_KEYBOARD
    i.u.ki.wVk = vk
    i.u.ki.wScan = user32.MapVirtualKeyW(vk, 0)
    i.u.ki.dwFlags = flags
    i.u.ki.time = 0
    i.u.ki.dwExtraInfo = ctypes.pointer(_extra)
    return i


def _send(*inputs_list):
    n = len(inputs_list)
    arr = (INPUT * n)(*inputs_list)
    user32.SendInput(n, arr, ctypes.sizeof(INPUT))


# ─── Public API ──────────────────────────────────────────────────
def press_key(key_char):
    """
    TAP a key — bấm rồi thả ngay trong 1 lệnh SendInput duy nhất.
    Phím đen: Shift↓ → Key↓ → Key↑ → Shift↑ (tất cả atomic).
    Phím trắng: Key↓ → Key↑ (atomic).
    """
    if key_char not in VALID_KEYS:
        return

    if key_char in SHIFT_MAP:
        base_vk = VK.get(SHIFT_MAP[key_char])
        if base_vk:
            # GỬI 4 SỰ KIỆN CÙNG LÚC — Shift không bao giờ "dính" sang nốt khác
            _send(
                _inp(VK_SHIFT),                       # Shift ↓
                _inp(base_vk),                        # Key ↓
                _inp(base_vk, KEYEVENTF_KEYUP),       # Key ↑
                _inp(VK_SHIFT, KEYEVENTF_KEYUP),      # Shift ↑
            )
    else:
        vk = VK.get(key_char)
        if vk:
            # GỬI 2 SỰ KIỆN CÙNG LÚC — bấm rồi thả ngay
            _send(
                _inp(vk),                             # Key ↓
                _inp(vk, KEYEVENTF_KEYUP),            # Key ↑
            )


def release_key(key_char):
    """Không cần làm gì — press_key đã tự thả rồi."""
    pass


def release_all():
    """Safety: thả tất cả phím phòng trường hợp kẹt."""
    try:
        _send(_inp(VK_SHIFT, KEYEVENTF_KEYUP))
        for ch in '1234567890qwertyuiopasdfghjklzxcvbnm':
            vk = VK.get(ch)
            if vk:
                _send(_inp(vk, KEYEVENTF_KEYUP))
    except Exception:
        pass
