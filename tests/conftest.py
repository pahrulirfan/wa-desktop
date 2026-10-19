"""Every test runs against a throw-away home folder, never the runner's real configuration."""

import os
import tempfile
from pathlib import Path

import pytest

ISOLATED_VARS = ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA",
                 "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME")


def _point_home_at(root: Path, env) -> None:
    env["HOME"] = env["USERPROFILE"] = str(root)
    env["APPDATA"] = str(root / "AppData" / "Roaming")
    env["LOCALAPPDATA"] = str(root / "AppData" / "Local")
    for var in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME"):
        env.pop(var, None)


# Before wadesk is imported: paths.py resolves its folders at import time.
_point_home_at(Path(tempfile.mkdtemp(prefix="wadesk-tests-")), os.environ)
os.environ.pop("WADESK_OS", None)


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch) -> Path:
    for var in ISOLATED_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.delenv("WADESK_OS", raising=False)
    monkeypatch.delenv("APPIMAGE", raising=False)
    env = {}
    _point_home_at(tmp_path, env)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    return tmp_path


@pytest.fixture
def force_os(monkeypatch):
    def force(name: str) -> None:
        monkeypatch.setenv("WADESK_OS", name)
    return force


@pytest.fixture(scope="session")
def qapp():
    """A QCoreApplication for tests that need Qt objects (no window, no display)."""
    from PySide6.QtCore import QCoreApplication
    return QCoreApplication.instance() or QCoreApplication([])
