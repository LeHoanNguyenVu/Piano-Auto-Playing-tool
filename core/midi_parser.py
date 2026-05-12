"""
MIDI Parser Module — Parses .mid/.midi files into a list of timed note events.

Uses the mido library for reliable MIDI parsing with tempo change support.
"""

import os
import mido


class NoteEvent:
    """Represents a single note event with absolute timing."""
    __slots__ = ('time', 'note', 'velocity')

    def __init__(self, time, note, velocity):
        self.time = time        # Absolute time in seconds
        self.note = note        # MIDI note number (0-127)
        self.velocity = velocity  # 0 = note off, >0 = note on

    def __repr__(self):
        state = "ON" if self.velocity > 0 else "OFF"
        return f"NoteEvent({self.time:.3f}s, note={self.note}, {state})"


class SongInfo:
    """Metadata about a parsed MIDI file."""
    def __init__(self):
        self.filename = ""
        self.title = ""
        self.duration = 0.0       # Total duration in seconds
        self.note_count = 0       # Number of note_on events
        self.track_count = 0
        self.min_note = 127
        self.max_note = 0
        self.tempo_bpm = 120
        self.ticks_per_beat = 480


def parse_midi(file_path, track_index=None):
    """
    Parse a MIDI file and return a sorted list of NoteEvent objects.

    Args:
        file_path: Path to the .mid/.midi file
        track_index: If specified, only parse this track. None = merge all tracks.

    Returns:
        List of NoteEvent sorted by time (ascending).
    """
    mid = mido.MidiFile(file_path)
    events = []
    ticks_per_beat = mid.ticks_per_beat

    if track_index is not None and track_index < len(mid.tracks):
        tracks_to_use = [mid.tracks[track_index]]
    elif mid.type == 2:
        # Type 2 MIDI: each track is independent, use first track
        tracks_to_use = [mid.tracks[0]]
    else:
        tracks_to_use = mid.tracks

    # ── QUAN TRỌNG: Merge tất cả tracks trước khi xử lý ──────
    # Điều này đảm bảo tempo từ Track 0 áp dụng đúng cho MỌI track.
    # Cách cũ (parse từng track riêng) gây lệch tốc độ giữa các track
    # → nghe như 2 luồng nhạc chạy song song.
    if len(tracks_to_use) > 1:
        merged = mido.merge_tracks(tracks_to_use)
    else:
        merged = tracks_to_use[0]

    # Parse merged track với 1 biến tempo duy nhất
    tempo = 500000  # Default: 120 BPM
    abs_time = 0.0

    for msg in merged:
        # Convert delta ticks to seconds
        if msg.time > 0:
            abs_time += mido.tick2second(msg.time, ticks_per_beat, tempo)

        if msg.type == 'set_tempo':
            tempo = msg.tempo
        elif msg.type == 'note_on':
            events.append(NoteEvent(abs_time, msg.note, msg.velocity))
        elif msg.type == 'note_off':
            events.append(NoteEvent(abs_time, msg.note, 0))

    return events


def get_song_info(file_path):
    """
    Get metadata about a MIDI file without full parsing.

    Returns:
        SongInfo object with file metadata.
    """
    info = SongInfo()
    info.filename = os.path.basename(file_path)
    info.title = os.path.splitext(info.filename)[0]

    try:
        mid = mido.MidiFile(file_path)
    except Exception:
        return info

    info.track_count = len(mid.tracks)
    info.ticks_per_beat = mid.ticks_per_beat
    info.duration = mid.length  # mido calculates this

    # Scan for metadata
    tempo = 500000
    note_count = 0
    min_note = 127
    max_note = 0

    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
            elif msg.type == 'note_on' and msg.velocity > 0:
                note_count += 1
                min_note = min(min_note, msg.note)
                max_note = max(max_note, msg.note)
            elif msg.type == 'track_name' and msg.name:
                if not info.title or info.title == os.path.splitext(info.filename)[0]:
                    info.title = msg.name

    info.tempo_bpm = round(mido.tempo2bpm(tempo))
    info.note_count = note_count
    info.min_note = min_note if note_count > 0 else 0
    info.max_note = max_note if note_count > 0 else 0

    return info


def get_piano_tracks(file_path):
    """
    Identify which tracks in a MIDI file contain piano/note data.

    Returns:
        List of (track_index, track_name, note_count) tuples.
    """
    try:
        mid = mido.MidiFile(file_path)
    except Exception:
        return []

    result = []
    for i, track in enumerate(mid.tracks):
        name = f"Track {i}"
        note_count = 0
        for msg in track:
            if msg.type == 'track_name' and msg.name:
                name = msg.name
            elif msg.type == 'note_on' and msg.velocity > 0:
                note_count += 1
        if note_count > 0:
            result.append((i, name, note_count))

    return result
