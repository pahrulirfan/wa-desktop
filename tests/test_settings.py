import json

import pytest

from wadesk import paths, settings
from wadesk.settings import DEFAULTS, Settings, migrate


@pytest.fixture
def config_file(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_DIR", tmp_path / "config")
    return tmp_path / "config" / "settings.json"


def write(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_defaults_without_a_file(qapp, config_file):
    s = Settings()
    for key, value in DEFAULTS.items():
        assert s[key] == value
    assert s.download_path.name == "Downloads"


def test_save_and_load_round_trip(qapp, config_file):
    s = Settings()
    s.set("theme", "dark")
    s.set("zoom", 1.3)
    s.save()
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert data["theme"] == "dark" and data["zoom"] == 1.3
    assert Settings()["theme"] == "dark"


def test_set_emits_changed_only_on_a_real_change(qapp, config_file):
    s = Settings()
    seen = []
    s.changed.connect(seen.append)
    s.set("dnd", True)
    s.set("dnd", True)
    assert seen == ["dnd"]
    with pytest.raises(KeyError):
        s.set("no_such_key", 1)


def test_broken_file_falls_back_to_defaults(qapp, config_file):
    config_file.parent.mkdir(parents=True)
    config_file.write_text("{not json", encoding="utf-8")
    assert Settings()["theme"] == "system"
    write(config_file, ["a", "list"])
    assert Settings()["theme"] == "system"


def test_migrate_drops_wrong_types_and_unknown_keys():
    out = migrate({"dnd": "yes", "zoom": "big", "old_option": 1, "notifications": False})
    assert out == {"notifications": False}


def test_migrate_bool_is_not_an_int_but_int_is_a_float():
    out = migrate({"privacy_blur_level": True, "lock_auto_minutes": False, "zoom": 1})
    assert "privacy_blur_level" not in out and "lock_auto_minutes" not in out
    assert out["zoom"] == 1.0 and isinstance(out["zoom"], float)


def test_migrate_fixes_out_of_range_values():
    out = migrate({"theme": "blue", "zoom": 9.0, "privacy_blur_level": 99, "lock_auto_minutes": -5})
    assert out == {"zoom": settings.ZOOM_RANGE[1]}
    assert migrate({"zoom": 0.1})["zoom"] == settings.ZOOM_RANGE[0]
    assert migrate({"theme": "light", "privacy_blur_level": 14}) == {"theme": "light",
                                                                   "privacy_blur_level": 14}


def test_migrate_turns_off_a_lock_without_pin():
    assert migrate({"lock_enabled": True, "lock_hash": ""})["lock_enabled"] is False
    stored = "pbkdf2_sha256$1$00$00"
    assert migrate({"lock_enabled": True, "lock_hash": stored})["lock_enabled"] is True


def test_load_applies_migration(qapp, config_file):
    write(config_file, {"theme": "sepia", "zoom": 1, "lock_enabled": True, "close_to_tray": False})
    s = Settings()
    assert s["theme"] == "system"
    assert s["zoom"] == 1.0
    assert s["lock_enabled"] is False
    assert s["close_to_tray"] is False


def test_peek_reads_without_qt(config_file):
    assert Settings.peek("disable_gpu") is False
    write(config_file, {"disable_gpu": True, "zoom": "x"})
    assert Settings.peek("disable_gpu") is True
    assert Settings.peek("zoom") == DEFAULTS["zoom"]
