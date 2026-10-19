import pytest

from wadesk import platform
from wadesk.webpage import build_user_agent

QT_DEFAULTS = {
    "linux": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
             "QtWebEngine/6.12.0 Chrome/140.0.7339.207 Safari/537.36",
    "windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
               "QtWebEngine/6.12.0 Chrome/140.0.7339.207 Safari/537.36",
    "macos": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
             "QtWebEngine/6.12.0 Chrome/140.0.7339.207 Safari/537.36",
}


@pytest.mark.parametrize("os_name", ["linux", "windows", "macos"])
def test_looks_like_plain_chrome(force_os, os_name):
    force_os(os_name)
    ua = build_user_agent(QT_DEFAULTS[os_name])
    assert "QtWebEngine" not in ua
    assert ua == (f"Mozilla/5.0 ({platform.UA_PLATFORMS[os_name]}) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")


def test_platform_token_matches_the_os_not_the_qt_default(force_os):
    force_os("windows")
    assert "Windows NT 10.0" in build_user_agent(QT_DEFAULTS["linux"])
    force_os("macos")
    assert "Macintosh" in build_user_agent(QT_DEFAULTS["windows"])


def test_follows_the_chromium_version(force_os):
    force_os("linux")
    assert "Chrome/146.0.0.0" in build_user_agent(QT_DEFAULTS["linux"].replace("140.0.7339.207", "146.0.1.2"))
    assert "Chrome/140.0.0.0" in build_user_agent("something odd")


def test_custom_user_agent_wins(force_os):
    force_os("windows")
    assert build_user_agent(QT_DEFAULTS["windows"], "  MyAgent/1.0  ") == "MyAgent/1.0"
    assert "Chrome/" in build_user_agent(QT_DEFAULTS["windows"], "   ")
