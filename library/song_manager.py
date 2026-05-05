"""
Song Manager — Manages the local MIDI song library.

Songs are stored in the library/songs/ directory with metadata tracked in library.json.
"""

import os
import json
import shutil
import uuid
import time as _time
from core.midi_parser import get_song_info


def _get_library_dir():
    """Get the path to the songs directory, creating it if needed."""
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "songs")
    os.makedirs(base, exist_ok=True)
    return base


def _get_metadata_path():
    """Get the path to the library metadata JSON file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.json")


def _load_metadata():
    """Load library metadata from JSON file."""
    path = _get_metadata_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"songs": []}


def _save_metadata(data):
    """Save library metadata to JSON file."""
    path = _get_metadata_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_all_songs():
    """
    Get all songs in the library.
    Returns list of dicts with: id, title, artist, filename, path, duration,
    note_count, tempo_bpm, difficulty, genre, added_date
    """
    data = _load_metadata()
    songs = data.get("songs", [])
    # Verify files still exist
    valid = []
    for s in songs:
        if os.path.exists(s.get("path", "")):
            valid.append(s)
    if len(valid) != len(songs):
        data["songs"] = valid
        _save_metadata(data)
    return valid


def import_midi(file_path, title=None, artist="Unknown", genre="", difficulty=""):
    """
    Import a MIDI file into the library.
    Copies the file to library/songs/ and adds metadata.

    Returns the song metadata dict, or None on failure.
    """
    if not os.path.exists(file_path):
        return None

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ('.mid', '.midi'):
        return None

    # Generate unique filename
    song_id = str(uuid.uuid4())[:8]
    original_name = os.path.basename(file_path)
    dest_name = f"{song_id}_{original_name}"
    dest_path = os.path.join(_get_library_dir(), dest_name)

    # Copy file
    shutil.copy2(file_path, dest_path)

    # Parse MIDI for metadata
    info = get_song_info(dest_path)

    song = {
        "id": song_id,
        "title": title or info.title or os.path.splitext(original_name)[0],
        "artist": artist,
        "filename": dest_name,
        "path": dest_path,
        "duration": round(info.duration, 1),
        "note_count": info.note_count,
        "tempo_bpm": info.tempo_bpm,
        "track_count": info.track_count,
        "difficulty": difficulty,
        "genre": genre,
        "added_date": _time.strftime("%Y-%m-%d %H:%M"),
    }

    data = _load_metadata()
    data["songs"].append(song)
    _save_metadata(data)

    return song


def delete_song(song_id):
    """Delete a song from the library by its ID."""
    data = _load_metadata()
    songs = data.get("songs", [])
    to_remove = None
    for s in songs:
        if s["id"] == song_id:
            to_remove = s
            break

    if to_remove:
        # Delete file
        try:
            if os.path.exists(to_remove["path"]):
                os.remove(to_remove["path"])
        except OSError:
            pass
        songs.remove(to_remove)
        data["songs"] = songs
        _save_metadata(data)
        return True
    return False


def update_song(song_id, **kwargs):
    """Update song metadata fields (title, artist, genre, difficulty)."""
    data = _load_metadata()
    for s in data.get("songs", []):
        if s["id"] == song_id:
            for key, value in kwargs.items():
                if key in ("title", "artist", "genre", "difficulty"):
                    s[key] = value
            _save_metadata(data)
            return True
    return False


def search_songs(query):
    """Search songs by title or artist (case-insensitive)."""
    query = query.lower().strip()
    if not query:
        return get_all_songs()
    return [
        s for s in get_all_songs()
        if query in s.get("title", "").lower() or query in s.get("artist", "").lower()
    ]
