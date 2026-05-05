import json
import requests
import os
from pathlib import Path

# Default cloud URL (User can change this in settings)
# For demonstration, we provide a placeholder URL.
DEFAULT_CLOUD_URL = "https://raw.githubusercontent.com/antigravity-mock/roblox-piano-cloud/main/database.json"

# Fallback mock data in case the URL is invalid or the user hasn't set one up yet.
# This ensures the tool works out of the box for testing!
FALLBACK_DATABASE = [
    {
        "id": "1",
        "title": "Em Của Ngày Hôm Qua",
        "artist": "Sơn Tùng M-TP",
        "url": "https://bitmidi.com/uploads/85566.mid"  # Placeholder MIDI link
    },
    {
        "id": "2",
        "title": "River Flows In You",
        "artist": "Yiruma",
        "url": "https://bitmidi.com/uploads/15410.mid"  # Placeholder MIDI link
    },
    {
        "id": "3",
        "title": "Faded",
        "artist": "Alan Walker",
        "url": "https://bitmidi.com/uploads/98711.mid"  # Placeholder MIDI link
    }
]


class CloudDatabase:
    """
    Handles fetching and searching a cloud-hosted JSON catalog of MIDI files.
    """
    def __init__(self):
        self.catalog = []
        self.cloud_url = DEFAULT_CLOUD_URL
        self._load_config()
        self.refresh_catalog()

    def _load_config(self):
        """Load the cloud URL from local settings if available."""
        config_path = Path(os.environ.get('APPDATA', '')) / 'RobloxPianoPlayer' / 'settings.json'
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cloud_url = data.get('cloud_url', DEFAULT_CLOUD_URL)
        except Exception:
            pass

    def save_config(self, new_url):
        self.cloud_url = new_url
        config_path = Path(os.environ.get('APPDATA', '')) / 'RobloxPianoPlayer' / 'settings.json'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {}
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            data['cloud_url'] = new_url
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def refresh_catalog(self):
        """Fetch the latest catalog from the cloud URL."""
        try:
            # Try to fetch from the user's Github JSON URL
            response = requests.get(self.cloud_url, timeout=5)
            if response.status_code == 200:
                self.catalog = response.json()
            else:
                self.catalog = FALLBACK_DATABASE
        except Exception:
            # If no internet or bad URL, use fallback so the user still sees something
            self.catalog = FALLBACK_DATABASE

    def search(self, query):
        """Search the loaded catalog for a query."""
        if not query:
            return self.catalog

        query = query.lower()
        results = []
        for song in self.catalog:
            title = song.get('title', '').lower()
            artist = song.get('artist', '').lower()
            if query in title or query in artist:
                results.append(song)
        return results

    def download_song(self, song, save_dir):
        """Download a song from the cloud catalog to the local library."""
        url = song.get('url')
        if not url:
            raise ValueError("No download URL provided in cloud database.")

        # Clean filename
        safe_title = "".join([c for c in song['title'] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        filename = f"{safe_title}.mid"
        save_path = Path(save_dir) / filename

        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return str(save_path)
