import plistlib
import sys
import types

import pytest

from wadesk import APP_NAME, autostart, platform


@pytest.fixture
def frozen_exe(monkeypatch, tmp_path):
    """Pretend to run from a PyInstaller build installed in a folder with a space."""
    exe = tmp_path / "Program Files" / APP_NAME / f"{APP_NAME}.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    return exe


class FakeKey:
    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeWinreg(types.ModuleType):
    """Just enough of the winreg module for autostart.py, backed by a dict."""

    HKEY_CURRENT_USER = "HKCU"
    KEY_SET_VALUE = 2
    REG_SZ = 1

    def __init__(self):
        super().__init__("winreg")
        self.keys = {}

    def CreateKeyEx(self, root, sub, reserved=0, access=0):  # noqa: N802 - winreg's names
        return FakeKey(self.keys.setdefault((root, sub), {}))

    def SetValueEx(self, key, name, reserved, kind, value):  # noqa: N802
        assert kind == self.REG_SZ
        key.store[name] = value

    def DeleteValue(self, key, name):  # noqa: N802
        if name not in key.store:
            raise FileNotFoundError(name)
        del key.store[name]


@pytest.fixture
def winreg(monkeypatch):
    fake = FakeWinreg()
    monkeypatch.setitem(sys.modules, "winreg", fake)
    return fake


def test_linux_desktop_entry(force_os, isolated_home, monkeypatch):
    force_os("linux")
    monkeypatch.setattr(platform, "launch_command", lambda: ["/home/u/My Apps/wadesk"])
    autostart.set_enabled(True)
    entry = isolated_home / ".config" / "autostart" / "wadesk.desktop"
    text = entry.read_text(encoding="utf-8")
    assert text.startswith("[Desktop Entry]\n")
    assert 'Exec="/home/u/My Apps/wadesk" --minimized\n' in text
    assert f"Name={APP_NAME}\n" in text and "Icon=wadesk\n" in text
    autostart.set_enabled(False)
    assert not entry.exists()
    autostart.set_enabled(False)  # disabling twice is fine


def test_linux_honours_xdg_config_home(force_os, isolated_home, monkeypatch):
    force_os("linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(isolated_home / "cfg"))
    assert autostart.desktop_file() == isolated_home / "cfg" / "autostart" / "wadesk.desktop"


def test_linux_prefers_the_install_sh_launcher(force_os, isolated_home):
    force_os("linux")
    launcher = isolated_home / ".local" / "bin" / "wadesk"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#!/bin/sh\n")
    assert autostart.command() == [str(launcher), "--minimized"]


def test_linux_appimage(force_os, frozen_exe, monkeypatch):
    force_os("linux")
    monkeypatch.setenv("APPIMAGE", "/home/u/Apps/WA-Desktop.AppImage")
    assert autostart.command() == ["/home/u/Apps/WA-Desktop.AppImage", "--minimized"]


def test_windows_registry_points_at_the_exe(force_os, frozen_exe, winreg):
    force_os("windows")
    autostart.set_enabled(True)
    values = winreg.keys[("HKCU", autostart.RUN_KEY)]
    assert values == {APP_NAME: f'"{frozen_exe}" --minimized'}
    autostart.set_enabled(False)
    assert values == {}
    autostart.set_enabled(False)


def test_windows_from_source_uses_pythonw(force_os, winreg, monkeypatch, tmp_path):
    force_os("windows")
    python = tmp_path / "py" / "python.exe"
    python.parent.mkdir()
    python.write_text("")
    (python.parent / "pythonw.exe").write_text("")
    monkeypatch.setattr(sys, "executable", str(python))
    assert autostart.command() == [str(python.parent / "pythonw.exe"), "-m", "wadesk", "--minimized"]


def test_macos_launch_agent(force_os, frozen_exe, isolated_home):
    force_os("macos")
    autostart.set_enabled(True)
    plist = isolated_home / "Library" / "LaunchAgents" / f"{platform.BUNDLE_ID}.plist"
    data = plistlib.loads(plist.read_bytes())
    assert data["Label"] == platform.BUNDLE_ID
    assert data["ProgramArguments"] == [str(frozen_exe), "--minimized"]
    assert data["RunAtLoad"] is True
    autostart.set_enabled(False)
    assert not plist.exists()


def test_other_systems_files_are_left_alone(force_os, frozen_exe, isolated_home, winreg):
    force_os("windows")
    autostart.set_enabled(True)
    assert not autostart.desktop_file().exists()
    assert not autostart.launch_agent_file().exists()
