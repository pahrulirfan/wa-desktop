# Contributing to WA Desktop

Thanks for your interest! WA Desktop is a small community project, and every kind of help is welcome:
testing on other distributions or desktops, reporting bugs, improving the docs, and sending patches.

## Ways to help

- **Test on your setup.** Day-to-day use so far is on Linux Mint 22 (Cinnamon, X11); the Windows and macOS builds
  are only tested automatically in CI. Reports from **Windows and macOS** users, other distributions,
  GNOME/KDE/XFCE and Wayland sessions are very valuable — including "it works".
- **Report bugs** using the checklist below.
- **Improve the privacy blur.** It relies on WhatsApp Web's markup (see [Known gotchas](#known-gotchas)); if a
  part of the page is not blurred, the selector lists in `wadesk/privacy.py` need to be extended.
- **Packaging.** A Snap and a Flatpak are on the [roadmap](README.md#roadmap); Windows, macOS, `.deb` and AppImage
  builds exist and could use real-world testing.

## Reporting bugs

Please open an issue and include:

- `wadesk --version` (or the version shown in *Help → About*)
- your operating system and version; on Linux also the desktop environment and whether you use **X11 or Wayland**
- how you installed it (Windows installer or portable zip, `.dmg`, `.deb`, AppImage, `install.sh`, from source)
- what you expected and what happened; for crashes, start the app from a terminal and paste what it prints

**Never post screenshots or logs containing real chats, phone numbers or contact names.** Blur or remove them
first.

## Development setup

```bash
git clone https://github.com/pahrulirfan/wa-desktop.git
cd wa-desktop
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m pytest
python -m wadesk
```

On Debian-based systems you also need the Qt WebEngine runtime libraries; running `./install.sh` once installs
them for you (or see the list in the README). The app needs a real desktop session — Qt's `offscreen` platform
crashes Qt WebEngine; on a headless Linux machine use `xvfb-run -a`.

### Tests

- `python -m pytest` runs the unit tests. They need no window and always run in a throw-away home folder
  (`tests/conftest.py`), so they never read your real settings or session.
- `python -m wadesk --smoke` starts the real window and Qt WebEngine on a local test page, checks the user agent,
  the unread badge, the privacy style and the single-instance server, and exits with code 0. It uses a temporary
  profile as well.
- Code that differs per operating system belongs in `wadesk/platform.py`. Set `WADESK_OS=windows` (or `macos`,
  `linux`) to run the app or the tests as if on that system — for example
  `WADESK_OS=macos python -m wadesk --smoke` on Linux exercises the macOS code paths that do not need macOS APIs.
- GitHub Actions runs the tests on Linux, Windows and macOS for every push and pull request
  ([`tests.yml`](.github/workflows/tests.yml)); please keep them green.

### Use a throw-away profile while testing

Your own WhatsApp session lives in `~/.local/share/wadesk` (Linux), `%LOCALAPPDATA%\WA Desktop` (Windows) or
`~/Library/Application Support/WA Desktop` (macOS). On Linux, point the XDG directories at a temporary location to
avoid touching it:

```bash
export XDG_CONFIG_HOME=/tmp/wadesk-dev/config XDG_DATA_HOME=/tmp/wadesk-dev/data XDG_CACHE_HOME=/tmp/wadesk-dev/cache
python -m wadesk
```

### Driving the UI from a script

[`tools/make_screenshots.py`](tools/make_screenshots.py) shows how to
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
- `python -m pytest` passes and `python -m wadesk --smoke` exits with 0
- Shortcuts and menus still make sense on macOS (Ctrl becomes ⌘; the menu bar is global there)

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
- Keep operating-system checks in `wadesk/platform.py` (use `platform.is_macos()` etc., not `sys.platform`), so
  they can be tested on any system.
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
- `QGuiApplication.setBadgeNumber()` is an instance method: call it on `QGuiApplication.instance()`.
- A system quit request (macOS Dock *Quit*, logout, SIGTERM) first closes all windows; close-to-tray would cancel
  it, so `QtApp.event()` marks the window as quitting when `QEvent.Quit` arrives.
- PyInstaller collects every QML plugin because Qt WebEngine links QtQuick; `packaging/wadesk.spec` drops them
  and, on Linux, leaves common system libraries (GTK, NSS, X11, ALSA, …) to the system. After changing the spec,
  check the build with `packaging/check_bundle.py` and `--smoke`.
- Ubuntu 24.04 restricts the user namespaces that Chromium's sandbox needs; the `.deb` installs an AppArmor
  profile (`packaging/linux/apparmor-wadesk`) where AppArmor 4 is present. Its `Depends` list prefers the `t64`
  package names first, otherwise apt may pick an unrelated provider of `libasound2`.

## Commits and pull requests

- Keep commits small and focused, with a short imperative summary line (`Fix lock screen focus on show`).
- Don't commit personal data. Consider using your GitHub `…@users.noreply.github.com` address as the commit
  email (GitHub → Settings → Emails) so that your real address stays private.
- Open an issue to discuss larger changes before sending a pull request.
- By contributing you agree that your work is released under the [MIT License](LICENSE).

## Releasing (maintainers)

1. Bump `__version__` in `wadesk/__init__.py` and commit.
2. Optional: run the **Release** workflow by hand (*Actions → Release → Run workflow*). It builds and tests every
   package and keeps them as downloadable artifacts, without publishing anything.
3. Tag the same commit and push the tag:

   ```bash
   git tag -a vX.Y.Z -m "WA Desktop X.Y.Z"
   git push origin vX.Y.Z
   ```

   The **Release** workflow checks that the tag matches `__version__`, builds the Windows installer and portable
   zip, the macOS disk images, the `.deb` and the AppImage, smoke-tests each of them, and publishes a GitHub Release
   with all files, `SHA256SUMS.txt` and generated notes. The macOS Intel build is best effort and never blocks a
   release.
4. Install one package from the release and start it once.

If a tag must be moved, do it **before** the workflow publishes the release.
