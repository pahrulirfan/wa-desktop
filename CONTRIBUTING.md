# Contributing to WA Desktop

Thanks for your interest! WA Desktop is a small community project, and every kind of help is welcome:
testing on other distributions or desktops, reporting bugs, improving the docs, and sending patches.

## Ways to help

- **Test on your setup.** The app has only been verified on Linux Mint 22 (Cinnamon, X11). Reports from other
  distributions, GNOME/KDE/XFCE, and Wayland sessions are very valuable — including "it works".
- **Report bugs** using the checklist below.
- **Improve the privacy blur.** It relies on WhatsApp Web's markup (see [Known gotchas](#known-gotchas)); if a
  part of the page is not blurred, the selector lists in `wadesk/privacy.py` need to be extended.
- **Packaging.** A Windows build, a Snap, a `.deb`, Flatpak or AppImage are all on the [roadmap](README.md#roadmap).

## Reporting bugs

Please open an issue and include:

- `wadesk --version`
- your distribution and version, desktop environment, and whether you use **X11 or Wayland**
- how you installed it (`install.sh`, from source, …)
- what you expected and what happened; for crashes, start the app from a terminal and paste what it prints

**Never post screenshots or logs containing real chats, phone numbers or contact names.** Blur or remove them
first.

## Development setup

```bash
git clone https://github.com/pahrulirfan/wa-desktop.git
cd wa-desktop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m wadesk
```

On Debian-based systems you also need the Qt WebEngine runtime libraries; running `./install.sh` once installs
them for you (or see the list in the README). The app needs a real desktop session — Qt's `offscreen` platform
crashes Qt WebEngine.

### Use a throw-away profile while testing

Your own WhatsApp session lives in `~/.local/share/wadesk`. To avoid touching it, point the XDG directories at a
temporary location:

```bash
export XDG_CONFIG_HOME=/tmp/wadesk-dev/config XDG_DATA_HOME=/tmp/wadesk-dev/data XDG_CACHE_HOME=/tmp/wadesk-dev/cache
python -m wadesk
```

### Driving the UI from a script

There is no automated test suite yet. [`tools/make_screenshots.py`](tools/make_screenshots.py) shows how to
drive the real UI from a script: it uses a disposable profile, loads the fictional page
[`tools/demo_chat.html`](tools/demo_chat.html) instead of WhatsApp, waits with a nested `QEventLoop`, hovers by
sending a `QMouseEvent` to `view.focusProxy()`, and grabs widgets with `widget.grab()`. Use the same pattern for
any scripted check, and always run `app.exec()` — without an event loop `aboutToQuit` never fires.

Screenshots in this repository must only ever show **fictional demo data**.

### Manual checklist before a pull request

- App starts, loads WhatsApp Web, and keeps you logged in after a restart
- Tray icon appears; closing the window keeps the app running; the tray menu works
- *Settings → Notifications → Send test* shows a notification
- Toggling every setting you touched works, in both light and dark theme
- If you changed the lock or privacy code: lock/unlock, wrong-PIN lockout, blur on/off
- `python -m compileall -q wadesk` reports no errors

## Code guidelines

- **English only** in the UI, scripts, comments and documentation.
- Match the surrounding code style: small functions, type hints where they help, short comments that explain
  *why*, not *what*.
- New persistent options go in `DEFAULTS` in `wadesk/settings.py` (values are type-checked when loaded) and need
  a control in `wadesk/dialogs.py` plus a row in the README's settings reference.
- **Do not install an application-wide Python event filter** (`QApplication.installEventFilter`). With Qt
  WebEngine it segfaults, because PySide tries to wrap Chromium-internal objects that are still being
  constructed. Filter specific, fully built widgets instead (the app hooks `view.focusProxy()`).
- Don't add telemetry, analytics or network calls to servers other than WhatsApp's.
- Keep the app lean: avoid adding diagnostic flags or log files to the shipped app; use a throw-away script
  while investigating and remove it afterwards.

## Known gotchas

Things that cost time to discover (PySide6 / Qt WebEngine 6.12):

- Qt WebEngine is a **separate wheel** since 6.12: `PySide6-WebEngine`.
- `QWebEnginePermission.PermissionType` has no `ClipboardSanitizedWrite`; `queryPermission()` is on
  `QWebEngineProfile`, not on the page.
- `QWebEnginePage.createStandardContextMenu` does not exist; use `QWebEngineView.createStandardContextMenu`.
- The default user agent contains `QtWebEngine/x.y`; WhatsApp Web may reject it, so it is stripped.
- Changing `QStyleHints.setColorScheme` does **not** update `prefers-color-scheme` in an already loaded page.
  Touching any web setting does (see `Application._setting_changed`).
- `runJavaScript` does not await Promises and returns arrays as empty lists; return `JSON.stringify(...)`
  strings and store asynchronous results on `window`.
- **WhatsApp Web only sends notifications when `Notification.permission` is `granted` *and* WhatsApp's own
  *Settings → Notifications* switches (Messages / Groups / Status) are on.** Sound and the unread counter work
  even when those switches are off, which makes "no notifications" look like an app bug.
- The lock screen must be raised above the loading/error overlay whenever the overlay changes
  (`MainWindow._keep_lock_on_top`); toasts are suppressed while locked.

## Commits and pull requests

- Keep commits small and focused, with a short imperative summary line (`Fix lock screen focus on show`).
- Don't commit personal data. Consider using your GitHub `…@users.noreply.github.com` address as the commit
  email (GitHub → Settings → Emails) so that your real address stays private.
- Open an issue to discuss larger changes before sending a pull request.
- By contributing you agree that your work is released under the [MIT License](LICENSE).

## Releasing (maintainers)

1. Bump `__version__` in `wadesk/__init__.py` and commit.
2. Tag the same commit: `git tag -a vX.Y.Z -m "WA Desktop X.Y.Z"` and `git push origin vX.Y.Z`.
3. Create a GitHub Release from that tag and paste the notes; the auto-generated source archive is the
   Linux download (it contains `install.sh`).
4. Download that archive, extract it, run `./install.sh` and start the app once to check the release.

If a tag must be moved, do it **before** publishing the Release.
