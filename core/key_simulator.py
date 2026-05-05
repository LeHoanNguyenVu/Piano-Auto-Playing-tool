"""
Key Simulator — Simulates keyboard input using the 'pynput' library.

Adapted to use the exact same input mechanism as nanoMIDIPlayer for 
perfect Roblox Virtual Piano compatibility.
"""

from pynput.keyboard import Controller, Key
import time

keyboard = Controller()

# ─── Shifted key → base key mapping ───────────────────────────────
# Black keys in Roblox VP require Shift + base key
SHIFT_MAP = {
    # Shift + number = special character
    '!': '1', '@': '2', '$': '4', '%': '5',
    '^': '6', '*': '8', '(': '9',
    # Shift + letter = uppercase
    'Q': 'q', 'W': 'w', 'E': 'e', 'T': 't', 'Y': 'y',
    'I': 'i', 'O': 'o', 'P': 'p', 'S': 's', 'D': 'd',
    'G': 'g', 'H': 'h', 'J': 'j', 'L': 'l', 'Z': 'z',
    'C': 'c', 'V': 'v', 'B': 'b',
}

VALID_KEYS = set('1234567890qwertyuiopasdfghjklzxcvbnm') | set(SHIFT_MAP.keys())


def press_key(key_char):
    """
    Press down a key. Handles Shift for black keys.
    Mirrors nanoMIDIPlayer logic: hold shift, press base key, release shift immediately.
    The base key is kept held down.
    """
    if key_char not in VALID_KEYS:
        return

    if key_char in SHIFT_MAP:
        base = SHIFT_MAP[key_char]
        keyboard.press(Key.shift)
        keyboard.press(base)
        keyboard.release(Key.shift)
    else:
        keyboard.press(key_char)


def release_key(key_char):
    """
    Release a key.
    For black keys, only the base key needs to be released since shift was already released.
    """
    if key_char not in VALID_KEYS:
        return

    if key_char in SHIFT_MAP:
        base = SHIFT_MAP[key_char]
        keyboard.release(base)
    else:
        keyboard.release(key_char)


def release_all():
    """Safety function to release all possible pressed keys."""
    try:
        keyboard.release(Key.shift)
        for key in '1234567890qwertyuiopasdfghjklzxcvbnm':
            keyboard.release(key)
    except Exception:
        pass
