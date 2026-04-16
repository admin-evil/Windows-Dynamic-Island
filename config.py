"""Persistent configuration."""
import json
from pathlib import Path

CONFIG_DIR  = Path.home() / ".dynamic_island"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "width":    140,
    "y_offset": 10,
    "expand_on": "hover",
    "font_scale": 1.0,
}

class Config:
    def __init__(self):
        self._d = {}
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self._d = {**DEFAULTS, **loaded}
                return
            except Exception:
                pass
        self._d = dict(DEFAULTS)

    def save(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps(self._d, indent=2), encoding="utf-8")
        except Exception:
            pass

    def get(self, key, default=None):
        return self._d.get(key, default)

    def set(self, key, value):
        self._d[key] = value
        self.save()

    def get_font_scale(self) -> float:
        return float(self._d.get("font_scale", 1.0))

    def set_font_scale(self, v: float):
        self._d["font_scale"] = round(v, 2)
        self.save()
