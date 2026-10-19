from wadesk.privacy import CHAT_SELECTORS, LIST_SELECTORS, css


def config(**kw):
    base = {"list": False, "chat": False, "away": False, "level": 8}
    base.update(kw)
    return base


def test_nothing_enabled_means_no_css():
    assert css(config()) == ""


def test_chat_list_blur_with_hover_reveal():
    out = css(config(list=True, level=14))
    for sel in LIST_SELECTORS:
        assert sel in out
        assert f"{sel}:hover" in out
    assert "filter: blur(14px)" in out
    assert "filter: none" in out
    assert "#main" not in out


def test_conversation_blur():
    out = css(config(chat=True))
    for sel in CHAT_SELECTORS:
        assert f"{sel}:hover" in out
    assert "#pane-side" not in out


def test_away_blur_uses_the_window_class():
    out = css(config(away=True, level=22))
    assert out.strip() == "html.wadesk-away #app { filter: blur(22px) !important; }"


def test_everything_and_braces_balance():
    out = css(config(list=True, chat=True, away=True, level=4))
    assert out.count("{") == out.count("}") == 5
    assert out.count("blur(4px)") == 3


def test_level_is_forced_to_an_integer():
    assert "blur(8px)" in css(config(list=True, level=8.0))
