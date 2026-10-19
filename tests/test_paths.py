from pathlib import Path

from wadesk import APP_ID, APP_NAME, paths, platform


def test_linux_uses_xdg_defaults(force_os, isolated_home):
    force_os("linux")
    assert platform.app_dirs() == (isolated_home / ".config" / APP_ID,
                                   isolated_home / ".local/share" / APP_ID,
                                   isolated_home / ".cache" / APP_ID)


def test_linux_honours_xdg_variables(force_os, isolated_home, monkeypatch):
    force_os("linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(isolated_home / "cfg"))
    monkeypatch.setenv("XDG_DATA_HOME", str(isolated_home / "dat"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(isolated_home / "tmp"))
    config, data, cache = platform.app_dirs()
    assert (config, data, cache) == (isolated_home / "cfg" / APP_ID, isolated_home / "dat" / APP_ID,
                                     isolated_home / "tmp" / APP_ID)


def test_windows_uses_appdata(force_os, isolated_home):
    force_os("windows")
    config, data, cache = platform.app_dirs()
    assert config == isolated_home / "AppData" / "Roaming" / APP_NAME
    assert data == isolated_home / "AppData" / "Local" / APP_NAME
    assert cache == data / "Cache"


def test_windows_without_variables_falls_back_to_the_profile(force_os, isolated_home):
    force_os("windows")
    config, data, _ = platform.app_dirs(env={})
    assert config == isolated_home / "AppData" / "Roaming" / APP_NAME
    assert data == isolated_home / "AppData" / "Local" / APP_NAME


def test_macos_uses_library(force_os, isolated_home):
    force_os("macos")
    config, data, cache = platform.app_dirs()
    assert config == data == isolated_home / "Library" / "Application Support" / APP_NAME
    assert cache == isolated_home / "Library" / "Caches" / APP_NAME


def test_data_and_cache_never_share_a_folder(force_os):
    for name in ("linux", "windows", "macos"):
        force_os(name)
        _, data, cache = platform.app_dirs()
        assert data != cache


def test_use_root_redirects_everything(tmp_path, monkeypatch):
    for name in ("CONFIG_DIR", "DATA_DIR", "CACHE_DIR"):
        monkeypatch.setattr(paths, name, getattr(paths, name))
    paths.use_root(tmp_path / "smoke")
    paths.ensure_dirs()
    for d in (paths.CONFIG_DIR, paths.DATA_DIR, paths.CACHE_DIR):
        assert d.is_dir() and tmp_path in d.parents


def test_icon_is_shipped():
    assert paths.ICON_SVG.is_file()
    assert Path(paths.ASSETS_DIR).name == "assets"
