"""Privacy mode: blurs the chat list / conversation via CSS injected into the page."""

import json

from PySide6.QtCore import QObject
from PySide6.QtWebEngineCore import QWebEngineScript


SCRIPT_NAME = "wadesk-privacy"
KEYS = ("privacy_blur_list", "privacy_blur_chat", "privacy_blur_away", "privacy_blur_level")

# Selectors are deliberately layered: WhatsApp often renames CSS classes, but ids and
# role/data-testid attributes are comparatively stable. Hovering a row removes its blur
# (and the blur of its ancestors, since :hover propagates upwards).
JS_FUNCTION = r"""
window.__wadeskPrivacy = function (c) {
  var el = document.getElementById('wadesk-privacy');
  if (!el) {
    el = document.createElement('style');
    el.id = 'wadesk-privacy';
    document.documentElement.appendChild(el);
  }
  var b = c.level + 'px', t = 'transition: filter .15s ease;', css = '';
  var LIST = '#pane-side [role="listitem"], #pane-side [role="row"], #pane-side [data-testid="cell-frame-container"]';
  var CHAT = '#main header, #main [role="row"], #main .message-in, #main .message-out';
  function rule(sel) {
    var hover = sel.split(',').map(function (s) { return s.trim() + ':hover'; }).join(', ');
    return sel + ' { filter: blur(' + b + '); ' + t + ' } ' + hover + ' { filter: none; } ';
  }
  if (c.list) css += rule(LIST);
  if (c.chat) css += rule(CHAT);
  if (c.away) css += 'html.wadesk-away #app { filter: blur(' + b + ') !important; } ';
  el.textContent = css;
};
"""



class Privacy(QObject):
    def __init__(self, page, settings, parent=None):
        super().__init__(parent or page)
        self._page = page
        self._settings = settings
        self._away = False
        settings.changed.connect(self._on_setting)
        page.loadFinished.connect(lambda ok: self._push_away())
        self.apply()

    def config(self) -> dict:
        s = self._settings
        return {"list": s["privacy_blur_list"], "chat": s["privacy_blur_chat"],
                "away": s["privacy_blur_away"], "level": s["privacy_blur_level"]}

    def apply(self) -> None:
        """Register the script for every future page load and apply it to the current page right away."""
        source = JS_FUNCTION + f"\nwindow.__wadeskPrivacy({json.dumps(self.config())});"
        scripts = self._page.scripts()
        for old in scripts.find(SCRIPT_NAME):
            scripts.remove(old)
        script = QWebEngineScript()
        script.setName(SCRIPT_NAME)
        script.setSourceCode(source)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        scripts.insert(script)
        self._page.runJavaScript(source)

    def set_away(self, away: bool) -> None:
        self._away = away
        self._push_away()

    def _push_away(self) -> None:
        flag = "true" if self._away else "false"
        self._page.runJavaScript(f"document.documentElement.classList.toggle('wadesk-away', {flag})")

    def _on_setting(self, key: str) -> None:
        if key in KEYS:
            self.apply()
