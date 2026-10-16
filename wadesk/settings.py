"""User settings, stored as JSON in ~/.config/wadesk."""

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
            for key, default in DEFAULTS.items():
                if key in raw and isinstance(raw[key], type(default)):
                    self._data[key] = raw[key]

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
            value = raw.get(key, DEFAULTS[key])
            return value if isinstance(value, type(DEFAULTS[key])) else DEFAULTS[key]
        except (OSError, ValueError, AttributeError):
            return DEFAULTS[key]

    @property
    def download_path(self) -> Path:
        configured = self._data["download_dir"]
        return Path(configured) if configured else Path.home() / "Downloads"
