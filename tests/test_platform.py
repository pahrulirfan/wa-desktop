import sys

import pytest

from wadesk import APP_ID, platform


def test_detects_the_real_os():
    expected = {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")
    assert platform.current() == expected


def test_forced_os(force_os):
    for name in ("linux", "windows", "macos"):
        force_os(name)
        assert platform.current() == name
    force_os("haiku")  # unknown values are ignored
    assert platform.current() in ("linux", "windows", "macos")


@pytest.mark.parametrize("user, expected", [
    ("irfan", f"{APP_ID}-irfan"),
    ("Jane Doe", f"{APP_ID}-Jane_Doe"),
    ("CORP\\jane", f"{APP_ID}-CORP_jane"),
    ("a/b:c", f"{APP_ID}-a_b_c"),
])
def test_socket_name_is_per_user_and_safe(monkeypatch, user, expected):
    monkeypatch.setattr(platform.getpass, "getuser", lambda: user)
    assert platform.socket_name() == expected


def test_socket_name_without_a_user(monkeypatch):
    def fail():
        raise OSError("no user")
    monkeypatch.setattr(platform.getpass, "getuser", fail)
    assert platform.socket_name() == f"{APP_ID}-user"


def test_root_policy(force_os, monkeypatch):
    monkeypatch.setattr(platform.os, "geteuid", lambda: 0, raising=False)
    force_os("linux")
    assert platform.root_policy() == "no-sandbox"
    force_os("macos")
    assert platform.root_policy() == "refuse"
    force_os("windows")
    assert platform.root_policy() == "ok"
    monkeypatch.setattr(platform.os, "geteuid", lambda: 1000, raising=False)
    for name in ("linux", "macos"):
        force_os(name)
        assert platform.root_policy() == "ok"


def test_notifier_backend(force_os):
    found = lambda name: f"/usr/bin/{name}"  # noqa: E731
    missing = lambda name: None  # noqa: E731
    force_os("linux")
    assert platform.notifier_backend(found) == ("notify-send", "/usr/bin/notify-send")
    assert platform.notifier_backend(missing) == ("tray", "")
    for name in ("windows", "macos"):
        force_os(name)
        assert platform.notifier_backend(found) == ("tray", "")


def test_restore_library_path(force_os, monkeypatch):
    force_os("linux")
    env = {"LD_LIBRARY_PATH": "/opt/wadesk/_internal", "LD_LIBRARY_PATH_ORIG": "/usr/local/lib"}
    platform.restore_library_path(env)
    assert env["LD_LIBRARY_PATH"] == "/opt/wadesk/_internal"  # from source: untouched
    monkeypatch.setattr(platform.sys, "frozen", True, raising=False)
    platform.restore_library_path(env)
    assert env == {"LD_LIBRARY_PATH": "/usr/local/lib"}
    env = {"LD_LIBRARY_PATH": "/opt/x", "A": "1"}
    platform.restore_library_path(env)
    assert env == {"A": "1"}
    force_os("windows")
    env = {"LD_LIBRARY_PATH": "/opt/x"}
    platform.restore_library_path(env)
    assert env == {"LD_LIBRARY_PATH": "/opt/x"}


def test_tray_place(force_os):
    force_os("macos")
    assert platform.tray_place() == "menu bar"
    force_os("windows")
    assert platform.tray_place() == "system tray"
