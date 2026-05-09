"""
Cloud Database — Cloud-First MIDI catalog system.

Luồng hoạt động:
1. App kết nối Cloud URL (mặc định là file JSON trên Github). 
   Lưu ý: File này chứa metadata công khai. Đảm bảo không để thông tin nhạy cảm ở đây.
2. User search trên catalog Cloud.
3. Khi user bấm Play: tải .mid về thư mục temp, kiểm tra tính hợp lệ (header MThd), chơi ngay.
4. Khi user bấm Yêu thích (❤): tải file về và lưu vào Local Library (thư mục favorites/).
"""

import json
import os
import tempfile
import requests
from pathlib import Path

# Default cloud URL — bạn có thể đổi thành link Github của riêng bạn trong Settings
DEFAULT_CLOUD_URL = "https://raw.githubusercontent.com/LeHoanNguyenVu/Piano-Auto-Playing-tool/main/cloud_database.json"

# Fallback database dùng để test khi chưa có Cloud URL thật
FALLBACK_DATABASE = [
    {
        "id": "demo_1",
        "title": "River Flows In You",
        "artist": "Yiruma",
        "url": "https://bitmidi.com/uploads/15410.mid"
    },
    {
        "id": "demo_2",
        "title": "Faded",
        "artist": "Alan Walker",
        "url": "https://bitmidi.com/uploads/98711.mid"
    },
    {
        "id": "demo_3",
        "title": "Fur Elise",
        "artist": "Beethoven",
        "url": "https://bitmidi.com/uploads/23281.mid"
    }
]

# Thư mục lưu bài yêu thích (nằm trong library/favorites/)
def _get_favorites_dir():
    base = Path(__file__).parent / "favorites"
    base.mkdir(parents=True, exist_ok=True)
    return base

# File lưu metadata yêu thích
def _get_favorites_meta_path():
    return Path(__file__).parent / "favorites.json"

# File cấu hình cloud URL
def _get_config_path():
    config_dir = Path(os.environ.get('APPDATA', Path.home())) / 'RobloxPianoPlayer'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'settings.json'


def load_cloud_url():
    """Load cloud URL từ cài đặt người dùng."""
    try:
        p = _get_config_path()
        if p.exists():
            data = json.loads(p.read_text(encoding='utf-8'))
            return data.get('cloud_url', DEFAULT_CLOUD_URL)
    except Exception:
        pass
    return DEFAULT_CLOUD_URL


def save_cloud_url(url):
    """Lưu cloud URL vào cài đặt người dùng."""
    p = _get_config_path()
    try:
        data = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
        data['cloud_url'] = url
        p.write_text(json.dumps(data, indent=4), encoding='utf-8')
    except Exception:
        pass


# ─── Favorites (Local Storage) ─────────────────────────────

def load_favorites():
    """Trả về dict {song_id: song_metadata} của các bài đã yêu thích."""
    p = _get_favorites_meta_path()
    try:
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {}


def _save_favorites(data: dict):
    p = _get_favorites_meta_path()
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def is_favorite(song_id: str) -> bool:
    return song_id in load_favorites()


def add_favorite(song: dict, midi_path: str) -> dict:
    """
    Lưu bài hát vào danh sách yêu thích.
    Sao chép file .mid từ midi_path vào thư mục favorites/.
    Trả về metadata đã lưu.
    """
    import shutil, time as _time

    favs = load_favorites()
    song_id = str(song.get('id', song.get('title', 'unknown')))

    # Đảm bảo bài hát có dữ liệu hợp lệ
    if not os.path.exists(midi_path):
        raise FileNotFoundError(f"Không tìm thấy file MIDI tại {midi_path}")

    # Sao chép file vào thư mục favorites với tên file an toàn và duy nhất
    title = song.get('title', 'song')
    safe_title = "".join(c for c in title if c.isalnum() or c in ' _-').strip()
    if not safe_title: safe_title = "unnamed_song"
    
    # Để tránh trùng tên file, ta có thể thêm ID vào tên file nếu cần
    dest_filename = f"{safe_title}.mid"
    dest = _get_favorites_dir() / dest_filename
    try:
        shutil.copy2(midi_path, dest)
    except Exception as e:
        # Nếu copy lỗi (ví dụ file đang mở), thử ghi đè hoặc báo lỗi
        pass

    meta = {
        **song,
        "local_path": str(dest),
        "added_date": _time.strftime("%Y-%m-%d %H:%M"),
        "favorite": True
    }
    favs[song_id] = meta
    _save_favorites(favs)
    return meta


def remove_favorite(song_id: str):
    """Xóa bài hát khỏi danh sách yêu thích (và file .mid nếu có)."""
    favs = load_favorites()
    if song_id in favs:
        local_path = favs[song_id].get('local_path', '')
        try:
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
        except OSError:
            pass
        del favs[song_id]
        _save_favorites(favs)


def clear_all_favorites():
    """Xóa toàn bộ danh sách yêu thích (bao gồm cả file vật lý)."""
    favs = load_favorites()
    for song_id in list(favs.keys()):
        remove_favorite(song_id)


def get_all_favorites() -> list:
    """Trả về danh sách các bài yêu thích (chỉ những bài còn file trên máy)."""
    favs = load_favorites()
    valid = []
    changed = False
    for song_id, meta in list(favs.items()):
        path = meta.get('local_path', '')
        if path and os.path.exists(path):
            valid.append(meta)
        else:
            # File bị xóa bên ngoài → dọn metadata
            del favs[song_id]
            changed = True
    if changed:
        _save_favorites(favs)
    return valid


# ─── Cloud Catalog ─────────────────────────────────────────

from supabase import create_client, Client

def load_env():
    """Đọc file .env để lấy thông tin bảo mật."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

# Load configuration
ENV = load_env()
SUPABASE_URL = ENV.get("SUPABASE_URL", "https://your-project-id.supabase.co")
SUPABASE_KEY = ENV.get("SUPABASE_KEY", "your-anon-key")

class CloudDatabase:
    """
    Quản lý Cloud Catalog thông qua Supabase:
    - Truy vấn danh sách bài hát từ bảng songs_catalog
    - Tải .mid từ Supabase Storage
    """

    def __init__(self):
        self.catalog = []
        self._connected = False
        self.supabase: Client = None
        
        if SUPABASE_URL != "https://your-project-id.supabase.co":
            try:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                self.refresh_catalog()
            except Exception as e:
                print(f"Lỗi kết nối Supabase: {e}")

    def refresh_catalog(self):
        """Tải danh sách bài hát từ Supabase Table."""
        if not self.supabase:
            self.catalog = list(FALLBACK_DATABASE)
            return False
            
        try:
            # Truy vấn bảng songs_catalog
            response = self.supabase.table("songs_catalog").select("*").execute()
            self.catalog = response.data
            self._connected = True
            return True
        except Exception as e:
            print(f"Lỗi tải catalog: {e}")
            self.catalog = list(FALLBACK_DATABASE)
            self._connected = False
            return False

    @property
    def is_connected(self):
        return self._connected

    @property
    def song_count(self):
        return len(self.catalog)

    def _remove_accents(self, s):
        """Loại bỏ dấu tiếng Việt để tìm kiếm linh hoạt."""
        import unicodedata
        if not s: return ""
        s = unicodedata.normalize('NFD', str(s))
        s = ''.join([c for c in s if unicodedata.category(c) != 'Mn'])
        return s.replace('đ', 'd').replace('Đ', 'D').lower()

    def search(self, query: str) -> list:
        """Tìm kiếm thông minh: không phân biệt hoa thường, không phân biệt dấu."""
        if not query or not query.strip():
            return list(self.catalog)
        
        q = self._remove_accents(query)
        results = []
        for s in self.catalog:
            title = self._remove_accents(s.get('title', ''))
            artist = self._remove_accents(s.get('artist', ''))
            if q in title or q in artist:
                results.append(s)
        return results

    def download_to_temp(self, song: dict) -> str:
        """Tải file .mid về thư mục temp."""
        url = song.get('url')
        if not url:
            raise ValueError("Bài hát này không có link tải.")

        safe_title = "".join(c for c in str(song.get('title', 'song')) if c.isalnum() or c in ' _-').strip()
        tmp_path = Path(tempfile.gettempdir()) / f"piano_tmp_{safe_title}.mid"

        resp = requests.get(url, stream=True, timeout=15)
        resp.raise_for_status()
        
        # Kiểm tra header MIDI
        content = b""
        for chunk in resp.iter_content(chunk_size=8192):
            content += chunk
            if len(content) >= 4 and not content.startswith(b'MThd'):
                raise ValueError("File từ Supabase không phải là định dạng MIDI hợp lệ.")
        
        with open(tmp_path, 'wb') as f:
            f.write(content)
        return str(tmp_path)

    def download_to_favorites(self, song: dict) -> dict:
        """Tải và lưu vào Favorites."""
        tmp_path = self.download_to_temp(song)
        return add_favorite(song, tmp_path)

    def increment_play_count(self, song_id):
        """Tăng lượt chơi của bài hát trên Supabase."""
        if not self.supabase or not self._connected:
            return
            
        try:
            # Chuyển ID sang int để khớp với cột int8 của Supabase
            sid = int(song_id)
            self.supabase.rpc('increment_play_count', {'row_id': sid}).execute()
        except Exception:
            try:
                sid = int(song_id)
                res = self.supabase.table("songs_catalog").select("play_count").eq("id", sid).execute()
                if res.data:
                    current = res.data[0].get('play_count', 0) or 0
                    self.supabase.table("songs_catalog").update({"play_count": current + 1}).eq("id", sid).execute()
            except Exception as e:
                print(f"Lỗi tăng lượt chơi: {e}")

    def get_trending_songs(self, limit=20):
        """Lấy danh sách bài hát có lượt chơi cao nhất."""
        if not self.supabase or not self._connected:
            # Fallback nếu không có kết nối: trả về catalog hiện tại sắp xếp theo tên
            return sorted(self.catalog, key=lambda x: x.get('title', ''))[:limit]
            
        try:
            res = self.supabase.table("songs_catalog")\
                .select("*")\
                .order("play_count", desc=True)\
                .limit(limit)\
                .execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Lỗi lấy xu hướng: {e}")
            return []
