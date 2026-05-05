"""
Key Mapping Module — Maps MIDI note numbers to Roblox Virtual Piano keys.

Roblox Virtual Piano Layout (61 keys, C2-C7):
  White keys: 1 2 3 4 5 6 7 8 9 0 q w e r t y u i o p a s d f g h j k l z x c v b n m
  Black keys: ! @ $ % ^ * ( Q W E T Y I O P S D G H J L Z C V B
"""

# MIDI note number → Roblox Virtual Piano key character
# Range: MIDI 36 (C2) to MIDI 96 (C7)
MIDI_TO_KEY = {
    # Octave 2: C2-B2
    36: '1',   # C2
    37: '!',   # C#2
    38: '2',   # D2
    39: '@',   # D#2
    40: '3',   # E2
    41: '4',   # F2
    42: '$',   # F#2
    43: '5',   # G2
    44: '%',   # G#2
    45: '6',   # A2
    46: '^',   # A#2
    47: '7',   # B2
    # Octave 3: C3-B3
    48: '8',   # C3
    49: '*',   # C#3
    50: '9',   # D3
    51: '(',   # D#3
    52: '0',   # E3
    53: 'q',   # F3
    54: 'Q',   # F#3
    55: 'w',   # G3
    56: 'W',   # G#3
    57: 'e',   # A3
    58: 'E',   # A#3
    59: 'r',   # B3
    # Octave 4: C4-B4 (Middle C)
    60: 't',   # C4 (Middle C)
    61: 'T',   # C#4
    62: 'y',   # D4
    63: 'Y',   # D#4
    64: 'u',   # E4
    65: 'i',   # F4
    66: 'I',   # F#4
    67: 'o',   # G4
    68: 'O',   # G#4
    69: 'p',   # A4
    70: 'P',   # A#4
    71: 'a',   # B4
    # Octave 5: C5-B5
    72: 's',   # C5
    73: 'S',   # C#5
    74: 'd',   # D5
    75: 'D',   # D#5
    76: 'f',   # E5
    77: 'g',   # F5
    78: 'G',   # F#5
    79: 'h',   # G5
    80: 'H',   # G#5
    81: 'j',   # A5
    82: 'J',   # A#5
    83: 'k',   # B5
    # Octave 6: C6-B6
    84: 'l',   # C6
    85: 'L',   # C#6
    86: 'z',   # D6
    87: 'Z',   # D#6
    88: 'x',   # E6
    89: 'c',   # F6
    90: 'C',   # F#6
    91: 'v',   # G6
    92: 'V',   # G#6
    93: 'b',   # A6
    94: 'B',   # A#6
    95: 'n',   # B6
    # Octave 7
    96: 'm',   # C7
}

# Minimum and maximum supported MIDI notes
MIN_NOTE = 36
MAX_NOTE = 96

# Note names for display
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def get_note_name(midi_note):
    """Get human-readable note name (e.g., 'C4', 'F#5')."""
    octave = (midi_note // 12) - 1
    name = NOTE_NAMES[midi_note % 12]
    return f"{name}{octave}"


def get_key_for_note(midi_note, transpose=0):
    """
    Get the Roblox VP key for a MIDI note, with optional transpose.
    Returns the key character or None if note is out of range.
    """
    adjusted = midi_note + transpose
    return MIDI_TO_KEY.get(adjusted)


def clamp_to_range(midi_note, transpose=0):
    """
    Clamp a MIDI note to the playable range, adjusting by octaves if needed.
    Returns the clamped note number.
    """
    adjusted = midi_note + transpose
    while adjusted < MIN_NOTE:
        adjusted += 12
    while adjusted > MAX_NOTE:
        adjusted -= 12
    return adjusted
