"""File locations: XDG on Linux, %APPDATA% / %LOCALAPPDATA% on Windows, ~/Library on macOS."""

from pathlib import Path

from . import platform

CONFIG_DIR, DATA_DIR, CACHE_DIR = platform.app_dirs()

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ICON_SVG = ASSETS_DIR / "icon.svg"


def use_root(root: Path) -> None:
    """Keep everything below one folder (used by --smoke so real data is never touched)."""
    global CONFIG_DIR, DATA_DIR, CACHE_DIR
    CONFIG_DIR, DATA_DIR, CACHE_DIR = root / "config", root / "data", root / "cache"


def ensure_dirs() -> None:
    for d in (CONFIG_DIR, DATA_DIR, CACHE_DIR):
        d.mkdir(parents=True, exist_ok=True)
