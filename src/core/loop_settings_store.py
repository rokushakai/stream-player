import json
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
SETTINGS_FILE = os.path.join(_PROJECT_ROOT, "loop_settings.json")

# Query params to strip for URL normalization
_STRIP_PARAMS = {"t", "feature", "si"}


def normalize_url(url: str) -> str:
    """Normalize URL by stripping transient query params and sorting the rest."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    for p in _STRIP_PARAMS:
        params.pop(p, None)
    sorted_query = urlencode(
        {k: v[0] if len(v) == 1 else v for k, v in sorted(params.items())},
        doseq=True,
    )
    return urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, sorted_query, "",
    ))


class LoopSettingsStore:
    """Persists loop settings (markers, segments, loop_mode) per URL."""

    def __init__(self):
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
        except Exception:
            self._data = {}

    def _save(self) -> None:
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[LoopSettingsStore] save error: {e}")

    def save_for_url(self, url: str, markers: list[dict],
                     segments: list[dict], loop_mode: str) -> None:
        key = normalize_url(url)
        if not markers and not segments:
            if key in self._data:
                del self._data[key]
                self._save()
            return
        self._data[key] = {
            "markers": markers,
            "segments": segments,
            "loop_mode": loop_mode,
        }
        self._save()

    def load_for_url(self, url: str) -> dict | None:
        key = normalize_url(url)
        return self._data.get(key)
