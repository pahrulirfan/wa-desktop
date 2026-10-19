"""User settings, stored as JSON in the config folder (see paths.py)."""

import json
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from . import paths

DEFAULTS = {
    "close_to_tray": True,
    "start_minimized": False,
    "autostart": False,
    "notifications": True,
    "notification_preview": True,
    "dnd": False,
    "theme": "system",  # system | light | dark
    "zoom": 1.0,
    "show_menubar": False,
    "download_dir": "",
    "ask_download_location": False,
    "disable_gpu": False,
    "user_agent": "",
    "geometry": "",
    "tray_hint_shown": False,
    "lock_enabled": False,
    "lock_hash": "",
    "lock_auto_minutes": 0,
    "lock_on_hide": False,
    "lock_on_start": True,
    "privacy_blur_list": False,
    "privacy_blur_chat": False,
    "privacy_blur_away": False,
    "privacy_blur_level": 8,
}
THEMES = ("system", "light", "dark")
BLUR_LEVELS = (4, 8, 14, 22)
ZOOM_RANGE = (0.5, 2.0)


def _typed(value, default):
    """The value if it has the default's type, else None. bool is not an int here, an int is a float."""
    if isinstance(default, bool) or isinstance(value, bool):
        return value if isinstance(value, bool) and isinstance(default, bool) else None
    if isinstance(default, float) and isinstance(value, int):
        return float(value)
    return value if isinstance(value, type(default)) else None


def migrate(raw: dict) -> dict:
    """Valid values from a settings file, possibly written by an older version or by hand.
    Unknown keys and values of the wrong type or out of range are dropped (defaults apply)."""
    out = {}
    for key, default in DEFAULTS.items():
        value = _typed(raw.get(key), default) if key in raw else None
        if value is not None:
            out[key] = value
    if out.get("theme") not in (None, *THEMES):
        del out["theme"]
    if "zoom" in out:
        out["zoom"] = round(min(ZOOM_RANGE[1], max(ZOOM_RANGE[0], out["zoom"])), 2)
    if out.get("privacy_blur_level") not in (None, *BLUR_LEVELS):
        del out["privacy_blur_level"]
    if out.get("lock_auto_minutes", 0) < 0:
        del out["lock_auto_minutes"]
    if out.get("lock_enabled") and not out.get("lock_hash"):
        out["lock_enabled"] = False  # a lock without a PIN would lock the user out
    return out


class Settings(QObject):
    changed = Signal(str)

    def __init__(self, path: Path | None = None):
        super().__init__()
        self._path = path or paths.CONFIG_DIR / "settings.json"
        self._data = dict(DEFAULTS)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(300)
        self._save_timer.timeout.connect(self.save)
        self.load()

    def load(self) -> None:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(raw, dict):
            self._data.update(migrate(raw))

    def save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self._path)
        except OSError:
            pass

    def __getitem__(self, key: str):
        return self._data[key]

    def set(self, key: str, value) -> None:
        if key not in DEFAULTS:
            raise KeyError(key)
        if self._data[key] == value:
            return
        self._data[key] = value
        self._save_timer.start()
        self.changed.emit(key)

    @staticmethod
    def peek(key: str):
        """Read a single value straight from the file, before QApplication exists."""
        try:
            raw = json.loads((paths.CONFIG_DIR / "settings.json").read_text(encoding="utf-8"))
            return migrate(raw).get(key, DEFAULTS[key])
        except (OSError, ValueError, AttributeError):
            return DEFAULTS[key]

    @property
    def download_path(self) -> Path:
        configured = self._data["download_dir"]
        return Path(configured) if configured else Path.home() / "Downloads"
