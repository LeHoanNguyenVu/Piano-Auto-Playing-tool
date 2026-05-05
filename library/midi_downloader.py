"""
MIDI Downloader — Search and download MIDI files from online sources.

Searches BitMidi and allows direct URL downloads.
"""

import os
import re
import requests
import threading


SEARCH_URL = "https://bitmidi.com/search?q={query}"
BITMIDI_BASE = "https://bitmidi.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class SearchResult:
    """Represents a MIDI file found online."""
    def __init__(self, title="", url="", source="", size=""):
        self.title = title
        self.url = url
        self.source = source
        self.size = size

    def __repr__(self):
        return f"SearchResult('{self.title}', source='{self.source}')"


def search_midi(query, callback=None):
    """
    Search for MIDI files online.

    Args:
        query: Search term
        callback: Optional callback(results: list[SearchResult]) for async use

    Returns:
        List of SearchResult objects (if callback is None)
    """
    def _do_search():
        results = []
        try:
            headers = {"User-Agent": USER_AGENT}
            url = SEARCH_URL.format(query=requests.utils.quote(query))
            resp = requests.get(url, headers=headers, timeout=10)

            if resp.status_code == 200:
                # Parse BitMidi search results using regex
                # Look for links to MIDI files
                pattern = r'<a[^>]*href="(/[^"]+\.mid[^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(pattern, resp.text, re.IGNORECASE)

                seen = set()
                for href, title in matches:
                    if href in seen:
                        continue
                    seen.add(href)
                    clean_title = title.strip() or href.split("/")[-1]
                    results.append(SearchResult(
                        title=clean_title,
                        url=BITMIDI_BASE + href,
                        source="BitMidi",
                    ))

                # Also try pattern for BitMidi's specific page structure
                page_pattern = r'href="(/([^"]+)-mid-[^"]*)"'
                page_matches = re.findall(page_pattern, resp.text)
                for href, name in page_matches:
                    if href in seen:
                        continue
                    seen.add(href)
                    clean_name = name.replace("-", " ").title()
                    results.append(SearchResult(
                        title=clean_name,
                        url=BITMIDI_BASE + href,
                        source="BitMidi",
                    ))

        except Exception as e:
            pass

        if callback:
            callback(results)
        return results

    if callback:
        thread = threading.Thread(target=_do_search, daemon=True)
        thread.start()
        return None
    else:
        return _do_search()


def download_midi(url, save_dir, filename=None, callback=None):
    """
    Download a MIDI file from a URL.

    Args:
        url: Direct URL to the MIDI file, or a BitMidi page URL
        save_dir: Directory to save the file
        filename: Optional filename override
        callback: Optional callback(success: bool, file_path: str, error: str)

    Returns:
        (success, file_path, error) tuple if callback is None
    """
    def _do_download():
        try:
            headers = {"User-Agent": USER_AGENT}

            # If it's a BitMidi page URL (not a direct .mid), try to find the download link
            actual_url = url
            if "bitmidi.com" in url and not url.endswith(('.mid', '.midi')):
                page_resp = requests.get(url, headers=headers, timeout=10)
                if page_resp.status_code == 200:
                    # Look for download link
                    dl_match = re.search(r'href="([^"]*\.mid[^"]*)"', page_resp.text, re.IGNORECASE)
                    if dl_match:
                        dl_href = dl_match.group(1)
                        if dl_href.startswith("/"):
                            actual_url = BITMIDI_BASE + dl_href
                        elif dl_href.startswith("http"):
                            actual_url = dl_href

            # Download the file
            resp = requests.get(actual_url, headers=headers, timeout=30, stream=True)
            if resp.status_code != 200:
                result = (False, "", f"HTTP {resp.status_code}")
                if callback:
                    callback(*result)
                return result

            # Determine filename
            if not filename:
                # Try Content-Disposition header
                cd = resp.headers.get("Content-Disposition", "")
                fn_match = re.search(r'filename[*]?=["\']?([^"\';\n]+)', cd)
                if fn_match:
                    fname = fn_match.group(1).strip()
                else:
                    # Use URL path
                    fname = actual_url.split("/")[-1].split("?")[0]
                    if not fname.lower().endswith(('.mid', '.midi')):
                        fname += ".mid"
            else:
                fname = filename

            # Sanitize filename
            fname = re.sub(r'[<>:"/\\|?*]', '_', fname)

            os.makedirs(save_dir, exist_ok=True)
            file_path = os.path.join(save_dir, fname)

            with open(file_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            result = (True, file_path, "")
            if callback:
                callback(*result)
            return result

        except Exception as e:
            result = (False, "", str(e))
            if callback:
                callback(*result)
            return result

    if callback:
        thread = threading.Thread(target=_do_download, daemon=True)
        thread.start()
        return None
    else:
        return _do_download()
