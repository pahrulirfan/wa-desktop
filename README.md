<div align="center">

<img src="docs/images/icon.png" width="96" alt="WA Desktop icon">

# WA Desktop

**WhatsApp on your desktop — in its own window, no browser required.**

For **Linux, Windows and macOS**: a tray icon with an unread badge, native notifications, a PIN lock and a
privacy blur mode. Built with Python and PySide6 (Qt WebEngine).

**[Documentation](https://pahrulirfan.github.io/wa-desktop/) · [About](https://pahrulirfan.github.io/wa-desktop/about.html) · [Donate](https://pahrulirfan.github.io/wa-desktop/donate.html) · [Download](https://github.com/pahrulirfan/wa-desktop/releases/latest)**

[![Tests](https://github.com/pahrulirfan/wa-desktop/actions/workflows/tests.yml/badge.svg)](https://github.com/pahrulirfan/wa-desktop/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/pahrulirfan/wa-desktop)](https://github.com/pahrulirfan/wa-desktop/releases/latest)
![Platform: Linux | Windows | macOS](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-informational)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)
![Built with PySide6](https://img.shields.io/badge/built%20with-PySide6-41CD52)

<img src="docs/images/main-light.png" width="820" alt="WA Desktop main window">

<sub>All screenshots in this document use fictional demo data.</sub>

</div>

> **Unofficial project.** WA Desktop is not affiliated with, endorsed by, or connected to WhatsApp LLC or Meta.
> It simply hosts the official WhatsApp Web client in a dedicated window. See the [disclaimer](#disclaimer).

---

## Table of contents

- [Why WA Desktop?](#why-wa-desktop)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Getting started](#getting-started)
- [Keyboard shortcuts](#keyboard-shortcuts)
- [Settings reference](#settings-reference)
- [Privacy & security notes](#privacy--security-notes)
- [Troubleshooting](#troubleshooting)
- [How it works](#how-it-works)
- [Development](#development)
- [Roadmap](#roadmap)
- [Support](#support)
- [About](#about)
- [Disclaimer](#disclaimer)
- [License](#license)

## Why WA Desktop?

WhatsApp offers no official desktop app for Linux, so most people keep a browser tab open. That tab is easy
to lose, has no tray icon, and gives you no control over who can see your chats. WA Desktop gives WhatsApp
Web a proper home on the desktop — on Linux, and with the same features on Windows and macOS:

- it lives in the **system tray** and shows an **unread badge**,
- it sends **native notifications** you can click to jump to the chat,
- it can **blur sender names** and **lock itself with a PIN** when you step away,
- it installs from a **`.deb`, AppImage, Windows installer or macOS disk image** and keeps your login between
  launches.

## Features

### A real desktop app

- **Persistent login** — scan the QR code once; the session survives restarts.
- **System tray** with an unread-message badge on the tray icon and the taskbar icon (an overlay badge on the
  Windows taskbar, a red badge on the macOS Dock and a template icon in the macOS menu bar). Closing the window
  keeps the app running in the background; on macOS the Dock icon brings it back.
- **Single instance** — launching the app again simply raises the existing window.
- **Launch at login** and **start hidden in the tray**.
- **Light / dark / follow-system theme**, applied live to both the app and WhatsApp Web itself, and following
  the system's own light/dark switch as it changes.
- **Zoom** (Ctrl +/−/0 or Ctrl + mouse wheel), **fullscreen** and an optional **menu bar** (macOS uses its
  global menu bar; Ctrl becomes ⌘ there).
- **Downloads** go to your chosen folder, never overwrite existing files, and show a "Show in folder" action.
- **Links open in your default browser**, not inside the app.
- **Loading screen and offline handling** with automatic retry.

<div align="center">
<img src="docs/images/main-dark.png" width="720" alt="Dark theme">
</div>

### Native notifications

- Uses your system's own notifications: `notify-send` on Linux (with the sender's avatar when WhatsApp provides
  one), Windows notifications and the macOS Notification Center.
- **Click a notification to open the app** and the related chat.
- **Do Not Disturb** mode (Ctrl+Shift+D) and an option to hide the message preview.
- A built-in **test notification** button to check that everything works.

<div align="center">
<img src="docs/images/tray-badges.png" width="640" alt="Tray icon states: idle, unread counts, Do Not Disturb">
</div>

### Privacy blur

Keep your contact list out of sight on a shared or visible screen. Names, photos and message previews in the
chat list are blurred; **hover over a row to reveal it**, or open a chat to read it. Only the chat you open is
readable.

<div align="center">
<img src="docs/images/privacy-chat-list.png" width="720" alt="Chat list blurred; hovered row is revealed">
</div>

- **Blur chat list** (Ctrl+Shift+B toggles it instantly).
- **Blur open conversation** — messages are blurred too and revealed on hover.
- **Blur when window is inactive** — everything is blurred while you work in another application.
- Four blur strengths: Light, Medium, Strong, Maximum.

<div align="center">
<img src="docs/images/privacy-everything.png" width="720" alt="Chat list and conversation both blurred">
</div>

### PIN lock

- Lock the app manually (Ctrl+L) or automatically: **after inactivity** (1 minute – 1 hour), **when the window is
  hidden to the tray**, and/or **on launch**.
- While locked, input to WhatsApp is disabled, Settings cannot be opened, and **notifications show only
  "New message"** — no sender, text or avatar.
- PINs are stored as a salted **PBKDF2-HMAC-SHA256** hash (200,000 iterations), never in plain text.
- Wrong PINs trigger an increasing lockout (30 s, 60 s, 120 s … up to 10 minutes) after five attempts.
- *Forgot your PIN?* It cannot be recovered; the only way out is removing the session and scanning the QR code
  again.

<div align="center">
<img src="docs/images/lock-screen.png" width="720" alt="Lock screen showing a wrong-PIN message">
</div>

### Everything is configurable

A clean settings dialog (Ctrl+,) covers every option. The menu bar is hidden by default — press **Alt** or
**Ctrl+M** to show it.

<div align="center">
<img src="docs/images/settings-overview.png" width="760" alt="Settings: General, Notifications, Privacy and Security pages">
</div>

<div align="center">
<img src="docs/images/menu-tools.png" width="230" alt="Tools menu with keyboard shortcuts">
</div>

## Requirements

| | Linux | Windows | macOS |
|---|---|---|---|
| **Version** | glibc 2.34+ — e.g. Ubuntu 22.04+, Debian 12+, Linux Mint 21+, Fedora 35+ | Windows 10 or 11 | macOS 12 Monterey or newer |
| **Architecture** | x86_64 (packages); x86_64 or aarch64 from source | x64 | Apple silicon or Intel |
| **Disk** | ~420 MB installed (the `.deb` download is ~120 MB) | ~400 MB installed | ~450 MB installed |

The app bundles Qt WebEngine (Chromium), which is why it is large. From source you need Python 3.10 or newer.
On Linux a notification daemon and a system tray are needed (Cinnamon, KDE, XFCE and MATE have them; GNOME
needs an AppIndicator extension).

> **Tested on:** Linux Mint 22 (Cinnamon, X11) by hand, every day. Windows and macOS builds are tested
> automatically on GitHub Actions (Windows Server 2025, macOS on Apple silicon and Intel): every package is
> installed and started with a self-test before it is published, but they have not yet been used day to day on
> real machines. Reports from Windows and macOS users are very welcome.

## Installation

Download the file for your system from the **[latest release](https://github.com/pahrulirfan/wa-desktop/releases/latest)**.
`SHA256SUMS.txt` on the release page lists the checksums.

| System | File | How to install |
|---|---|---|
| Windows 10/11 | `WA-Desktop-<version>-windows-x64-setup.exe` | Run it. No administrator rights needed. |
| Windows (no install) | `WA-Desktop-<version>-windows-x64-portable.zip` | Extract and start `WA Desktop.exe`. |
| macOS, Apple silicon | `WA-Desktop-<version>-macos-apple-silicon.dmg` | Open, drag **WA Desktop** to Applications. |
| macOS, Intel | `WA-Desktop-<version>-macos-intel.dmg` | Open, drag **WA Desktop** to Applications. |
| Ubuntu, Debian, Mint | `wadesk_<version>-1_amd64.deb` | `sudo apt install ./wadesk_*_amd64.deb` |
| Other Linux | `WA-Desktop-<version>-linux-x86_64.AppImage` | `chmod +x` it, then run it. |

### Opening the unsigned packages

The packages are built and tested by GitHub Actions from this repository, but they are **not signed** with a paid
code-signing certificate. Windows and macOS therefore warn the first time you open them:

- **Windows (SmartScreen):** on *"Windows protected your PC"* click **More info**, then **Run anyway**.
- **macOS (Gatekeeper):** in Applications, **right-click** (or Control-click) **WA Desktop → Open**, then **Open**
  again. On macOS 15 and newer, if no *Open* button is offered, go to **System Settings → Privacy & Security** and
  click **Open Anyway**. Alternatively, remove the quarantine flag in Terminal:

  ```bash
  xattr -dr com.apple.quarantine "/Applications/WA Desktop.app"
  ```

  The app is ad-hoc signed, which is enough to run on Apple silicon. When WhatsApp asks for the microphone or
  camera (voice messages, calls), allow it.

### Linux from source with install.sh

An alternative to the `.deb`, and the way to install on aarch64 or to follow the latest code.

```bash
git clone https://github.com/pahrulirfan/wa-desktop.git
cd wa-desktop
./install.sh
```

The installer will:

1. check your Python version, CPU architecture and glibc,
2. offer to install any missing system libraries with `sudo apt` (it asks before doing so),
3. create a private virtual environment in `~/.local/share/wadesk` and install PySide6 + Qt WebEngine,
4. add a launcher (`~/.local/bin/wadesk`), an icon and an **application-menu entry**.

Everything except step 2 is installed **for your user only** — no root access is needed for the app itself.

Then open **WA Desktop** from your application menu, or run `wadesk`.

> If the shell reports `wadesk: command not found`, `~/.local/bin` is not in your `PATH` yet. Run
> `~/.local/bin/wadesk` once, or log out and back in.

**Installer options**

| Option | Meaning |
|---|---|
| `--no-apt` | Do not touch system packages (for non-Debian distributions or when you installed them yourself) |
| `-y`, `--yes` | Do not ask before running `apt-get install` |
| `-h`, `--help` | Show help |

### Other distributions (Fedora, Arch, openSUSE, …)

Install the runtime libraries with your package manager, then run the installer with `--no-apt`.

<details>
<summary>Suggested packages <em>(untested starting points)</em></summary>

| Distribution | Packages |
|---|---|
| **Fedora** | `python3 xcb-util-cursor xcb-util-image xcb-util-keysyms xcb-util-renderutil xcb-util-wm nss alsa-lib libnotify libxkbcommon-x11` |
| **Arch / Manjaro** | `python xcb-util-cursor xcb-util-image xcb-util-keysyms xcb-util-renderutil xcb-util-wm nss alsa-lib libnotify libxkbcommon-x11` |

</details>

```bash
./install.sh --no-apt
```

### Run from source (any system)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
python -m wadesk                   # or simply: wadesk
```

On Debian-based systems you still need the system libraries listed above (at least `libxcb-cursor0`,
`libnss3`, `libasound2` and `libnotify-bin`).

### Updating

Install the new release over the old one (`.deb`, Windows installer, or replace the app in Applications). With
`install.sh`, pull the latest version and run it again. Your login session and settings are kept.

### Uninstalling

- **Windows:** *Settings → Apps → WA Desktop → Uninstall*.
- **macOS:** move **WA Desktop** from Applications to the Bin.
- **`.deb`:** `sudo apt remove wadesk`.
- **install.sh:**

```bash
./uninstall.sh            # remove the app, keep your session and settings
./uninstall.sh --purge    # also delete the session, settings and cache
```

If WA Desktop is running, quit it from its tray icon first.

## Getting started

1. Launch **WA Desktop**.
2. On your phone open **WhatsApp → Settings → Linked devices → Link a device** and scan the QR code. Leave
   **Keep me signed in on this browser** ticked so the session persists.
3. **Turn on notifications inside WhatsApp:** open **Settings (⚙️) → Notifications** in the web interface and
   switch on **Messages** (and **Groups** / **Status** if you want them). The app already grants the browser-level
   permission, but WhatsApp keeps its own separate switch — see [Troubleshooting](#troubleshooting).
4. Optional: open **Settings → Security** to set a PIN, and **Settings → Privacy** to enable blur.

**Command-line options**

| Option | Meaning |
|---|---|
| `wadesk --minimized` | Start hidden in the system tray (menu bar on macOS) |
| `wadesk --version` | Print the version |
| `wadesk --smoke` | Self-test: open the window with a local test page, check it, and exit (exit code 0 = passed). Uses a temporary profile; used by CI |

## Keyboard shortcuts

Shortcuts follow each system's conventions: on macOS, **Ctrl** becomes **⌘ Cmd**.

| Linux and Windows | macOS | Action |
|---|---|---|
| **Ctrl+,** | **⌘,** | Open Settings |
| **Ctrl+L** | **⌘L** | Lock now *(when a PIN is set)* |
| **Ctrl+Shift+B** | **⇧⌘B** | Toggle chat-list blur |
| **Ctrl+Shift+D** | **⇧⌘D** | Toggle Do Not Disturb |
| **Ctrl+W** | **⌘W** | Hide the window (to the tray / menu bar) |
| **Ctrl+Q** | **⌘Q** | Quit |
| **F5** / **Ctrl+R** | **⌘R** | Reload |
| **F11** | **⌃⌘F** | Toggle fullscreen |
| **Ctrl +** / **Ctrl −** / **Ctrl 0** | **⌘+** / **⌘−** / **⌘0** | Zoom in / out / reset (Ctrl or ⌘ + mouse wheel also works) |
| **Alt** / **Ctrl+M** | – | Show or hide the menu bar (macOS always shows its global menu bar) |

The tray icon's menu offers *Open*, *Do Not Disturb*, *Lock now*, *Settings* and *Quit*. On Linux and Windows a
left-click on the tray icon shows or hides the window; on macOS a click opens the menu.

## Settings reference

<details open>
<summary><strong>General</strong></summary>

| Setting | Default | Description |
|---|---|---|
| Close to tray | On | The ✕ button hides the window; WhatsApp keeps receiving messages |
| Start hidden | Off | On launch, go straight to the tray |
| Launch at login | Off | Linux: `~/.config/autostart/wadesk.desktop`; Windows: the `HKCU\…\Run` registry key; macOS: a LaunchAgent in `~/Library/LaunchAgents` |

</details>

<details>
<summary><strong>Notifications</strong></summary>

| Setting | Default | Description |
|---|---|---|
| Desktop notifications | On | Show incoming messages as system notifications |
| Show message preview | On | When off, notifications say only "New message" |
| Do Not Disturb | Off | Silence all notifications |
| Test notification | – | Sends a test notification |

</details>

<details>
<summary><strong>Appearance</strong></summary>

| Setting | Default | Description |
|---|---|---|
| Theme | Follow system | Light, Dark or Follow system — also applied to WhatsApp Web |
| Zoom | 100 % | 50 % – 200 % |
| Menu bar | Off | Always show the menu bar |

</details>

<details>
<summary><strong>Privacy</strong></summary>

| Setting | Default | Description |
|---|---|---|
| Blur chat list | Off | Blur names, photos and previews; hover to reveal |
| Blur open conversation | Off | Blur messages and the contact name in the open chat |
| Blur when window is inactive | Off | Blur everything while another window has focus |
| Blur strength | Medium | Light (4 px), Medium (8 px), Strong (14 px), Maximum (22 px) |

</details>

<details>
<summary><strong>Security</strong></summary>

| Setting | Default | Description |
|---|---|---|
| PIN lock | Off | Create or remove the PIN (4–32 characters) |
| Change PIN | – | Requires the current PIN |
| Lock now | – | Lock immediately |
| Auto-lock | Never | After 1 / 5 / 15 / 30 minutes or 1 hour without activity in the window |
| Lock when hidden | Off | Lock each time the window is closed to the tray |
| Lock on launch | On | Ask for the PIN every time the app starts |

</details>

<details>
<summary><strong>Downloads</strong> and <strong>Advanced</strong></summary>

| Setting | Default | Description |
|---|---|---|
| Download folder | `Downloads` in your home folder | Where files are saved |
| Ask where to save | Off | Show a save dialog for each file |
| Disable GPU acceleration | Off | Try this if the window flickers or stays blank (restart required) |
| Custom user agent | Automatic | Override if WhatsApp rejects the browser (restart required) |
| Clear cache | – | Deletes the network cache; your login is unaffected |
| Data folder | – | Opens the folder with your session (see below) |
| Log out | – | Deletes the session so you must scan the QR code again |

</details>

**Where data is stored**

| What | Linux | Windows | macOS |
|---|---|---|---|
| Settings | `~/.config/wadesk/settings.json` | `%APPDATA%\WA Desktop\settings.json` | `~/Library/Application Support/WA Desktop/settings.json` |
| Login session, cookies, local storage | `~/.local/share/wadesk/webengine/` | `%LOCALAPPDATA%\WA Desktop\webengine\` | `~/Library/Application Support/WA Desktop/webengine/` |
| Cache | `~/.cache/wadesk/` | `%LOCALAPPDATA%\WA Desktop\Cache\` | `~/Library/Caches/WA Desktop/` |
| Launch at login (if enabled) | `~/.config/autostart/wadesk.desktop` | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` | `~/Library/LaunchAgents/io.github.pahrulirfan.wadesk.plist` |

Linux keeps the same folders as earlier versions, so updating does not log you out.

## Privacy & security notes

- WA Desktop contains **no analytics or telemetry** and talks to no server other than WhatsApp's. Your messages
  remain end-to-end encrypted by WhatsApp.
- The **PIN lock is a convenience lock, not encryption.** It covers the window and disables input, but the
  session files (see *Where data is stored*) are not encrypted, WhatsApp keeps receiving messages in the
  background, and the failed-attempt counter lives in memory (it resets when the app restarts). Protect your
  user account and disk (for example with full-disk encryption) if you need stronger guarantees.
- **Privacy blur is cosmetic and best-effort.** It relies on the structure of the WhatsApp Web page; if WhatsApp
  changes its markup, some elements may stop being blurred. If you notice that, please open an issue.
- Anyone with access to your unlocked desktop session can also read the files that hold your session.
  Use **Log out** in Settings → Advanced before giving the machine to someone else.

## Troubleshooting

<details>
<summary><strong><code>wadesk: command not found</code></strong></summary>

`~/.local/bin` is not in your `PATH` for the current terminal. Run `~/.local/bin/wadesk`, or:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

It is added automatically at your next login. The application-menu entry and autostart are not affected.
</details>

<details>
<summary><strong><code>Could not load the Qt platform plugin "xcb"</code></strong></summary>

A system library is missing — usually `libxcb-cursor0`. On Debian/Ubuntu/Mint:

```bash
sudo apt install libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-shape0
```

Re-running `./install.sh` installs them for you.
</details>

<details>
<summary><strong>Sound plays and the unread counter updates, but no desktop notification appears</strong></summary>

WhatsApp Web has its own notification switch, separate from the browser permission. Open
**Settings (⚙️) → Notifications** inside WhatsApp and turn **Messages** (and **Groups** / **Status**) on.

Also note that WhatsApp deliberately suppresses notifications while its window is focused and the sender's chat
is open — test with the window hidden to the tray.

Still nothing? Use **Settings → Notifications → Send test**. If the test notification appears, the desktop side
works and the problem is WhatsApp's own notification setting; if it does not, on Linux check that `notify-send` is
installed (`sudo apt install libnotify-bin`) and that your notification daemon is running, then open an issue.
</details>

<details>
<summary><strong>Windows: "Windows protected your PC" / macOS: "cannot be opened" or "damaged"</strong></summary>

The packages are not signed with a paid certificate. See [Opening the unsigned packages](#opening-the-unsigned-packages).
On macOS, a *"damaged"* message also goes away after `xattr -dr com.apple.quarantine "/Applications/WA Desktop.app"`.
</details>

<details>
<summary><strong>macOS or Windows: no notifications</strong></summary>

First check WhatsApp's own switch (previous item). Then allow notifications for **WA Desktop** in **System Settings →
Notifications** (macOS) or **Settings → System → Notifications** (Windows), and make sure *Do Not Disturb* / *Focus*
is off. On macOS, an app without a paid Apple signature may not be offered notifications at all by some macOS
versions — please report what you see.
</details>

<details>
<summary><strong>No tray icon</strong></summary>

The app needs a system-tray host. Cinnamon, KDE, XFCE and MATE provide one. On **GNOME**, install the
*AppIndicator and KStatusNotifierItem Support* extension. Without a tray the window simply closes normally.
</details>

<details>
<summary><strong>Blank, black or flickering window</strong></summary>

Enable **Settings → Advanced → Disable GPU acceleration** and restart the app. You can also try launching with
`QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu" wadesk`.
</details>

<details>
<summary><strong>WhatsApp says the browser is not supported / asks to update Chrome</strong></summary>

WA Desktop presents itself as a regular Chrome browser. If WhatsApp ever raises its minimum version, set a
current Chrome user agent in **Settings → Advanced → Custom user agent** and restart.
</details>

<details>
<summary><strong>Wayland</strong></summary>

Untested. If you see rendering or tray problems, force X11: `QT_QPA_PLATFORM=xcb wadesk`.
</details>

<details>
<summary><strong>I forgot my PIN</strong></summary>

It cannot be recovered. On the lock screen choose **Forgot PIN?** — this removes the WhatsApp session from the
computer and turns the lock off. You will need to scan the QR code again.
</details>

## How it works

WA Desktop is a thin, focused wrapper around Qt WebEngine (Chromium):

- **Profile** — a persistent profile stores cookies and local storage, so WhatsApp Web keeps you signed in. The
  user agent is presented as plain Chrome; the `Accept-Language` header follows your system locale, so WhatsApp
  appears in your own language while the app's interface is English.
- **Notifications** — Qt delivers web notifications to a Python presenter. On Linux it forwards them to
  `notify-send` with the sender's avatar (when available) and a *click-to-open* action; on Windows and macOS, and
  on Linux without `notify-send`, it shows them through the tray icon (Windows notifications / Notification
  Center), and a click opens the chat. Notification permission for `web.whatsapp.com` is granted automatically.
- **Unread badge** — WhatsApp Web exposes the unread count in the page title (`(3) WhatsApp`); the app reads it
  and renders it onto the tray icon, and shows it natively as a taskbar overlay (Windows) or Dock badge (macOS).
- **Operating-system differences** live in one module, `wadesk/platform.py`; setting `WADESK_OS=windows` (or
  `macos`, `linux`) makes the app behave as if it ran on that system, which the tests use.
- **Privacy blur** — a small stylesheet is injected into the page. Hovering a row removes its blur, so the same
  mechanism reveals names on demand.
- **PIN lock** — an opaque overlay covers the web view, the view is disabled, and idle time is tracked from input
  events delivered to the web view.
- **Links and pop-ups** — navigation away from WhatsApp, and `window.open()`, are handed to your default browser.

## Development

```bash
git clone https://github.com/pahrulirfan/wa-desktop.git
cd wa-desktop
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest          # unit tests, no window needed
python -m wadesk --smoke  # starts the real window with a local test page, then exits
python -m wadesk
```

On Linux, `--smoke` needs a display; on a headless machine use `xvfb-run -a python -m wadesk --smoke` (Qt's
`offscreen` platform crashes Qt WebEngine).

**Building the packages locally**

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm packaging/wadesk.spec     # dist/wadesk, dist/WA Desktop or dist/WA Desktop.app
python packaging/check_bundle.py dist/wadesk      # checks that the Qt WebEngine runtime is complete
packaging/linux/build-deb.sh 1.1.0 dist/wadesk packages
```

The Windows installer uses Inno Setup (`packaging/windows/wadesk.iss`); `tools/make_icons.py` regenerates the
`.ico` and `.icns` icons from `wadesk/assets/icon.svg`.

**Continuous integration**

- [`tests.yml`](.github/workflows/tests.yml) runs on every push and pull request: pytest on Ubuntu (Python 3.10
  and 3.12), Windows and macOS, then `--smoke` from source and through `install.sh`.
- [`release.yml`](.github/workflows/release.yml) builds all packages and smoke-tests each one: the Windows
  installer is installed, started and uninstalled; the `.deb` is installed in fresh Ubuntu 22.04 and 24.04
  containers. A pushed tag `vX.Y.Z` (which must match `__version__`) publishes a GitHub Release;
  *Run workflow* builds the same packages as downloadable artifacts only.

**Project layout**

```
wa-desktop/
├── install.sh / uninstall.sh      Linux installer and uninstaller (user-level, no root for the app)
├── pyproject.toml                 package metadata, entry point, test settings
├── requirements.txt               PySide6 + Qt WebEngine
├── packaging/
│   ├── wadesk.spec                PyInstaller build for all three systems
│   ├── check_bundle.py            verifies the Qt WebEngine runtime in a build
│   ├── linux/                     desktop entry, .deb and AppImage scripts, AppArmor profile
│   ├── windows/                   Inno Setup script and .ico
│   └── macos/                     .icns
├── tests/                         pytest suite (runs in a throw-away home folder)
├── tools/
│   ├── make_screenshots.py        regenerates docs/images from the real UI (demo data only)
│   ├── make_icons.py              renders the .ico and .icns from icon.svg
│   └── demo_chat.html             fictional chat page used for the screenshots
├── docs/                          website (GitHub Pages) and screenshots
└── wadesk/
    ├── app.py                     entry point, wiring, single-instance handling
    ├── platform.py                everything that differs between Linux, Windows and macOS
    ├── window.py                  main window, menus, shortcuts, zoom, lock integration
    ├── webpage.py                 profile, page, permissions, downloads, link handling
    ├── notifier.py                desktop notifications
    ├── privacy.py                 blur CSS injection
    ├── lock.py                    PIN hashing, lock screen, PIN dialogs
    ├── dialogs.py                 settings dialog and About box
    ├── tray.py                    tray icon, badge and macOS template icon
    ├── widgets.py                 toggle switch, loading overlay, toast
    ├── settings.py / paths.py     persistent settings (with migration) and data folders
    ├── theme.py                   light/dark themes
    ├── autostart.py               launch-at-login entry per system
    └── smoke.py                   the --smoke self-test
```

**Regenerating the screenshots** (needs a desktop session; uses a throw-away profile and never touches your
real session):

```bash
python tools/make_screenshots.py
```

**Reporting bugs:** please include the output of `wadesk --version` (or the version in *Help → About*), your
operating system and version, and on Linux your desktop environment and whether you use X11 or Wayland. Start the
app from a terminal and include any error messages it prints (remove personal information first).

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the development setup, a manual test
checklist and the known gotchas. Open an issue to discuss larger changes before sending a pull request.

## Roadmap

These are ideas, not commitments:

- [x] **Windows build** — installer and portable zip, registry-based autostart, tray notifications, taskbar badge.
- [x] **macOS build** — `.dmg` for Apple silicon and Intel, Dock badge, menu bar icon, LaunchAgent autostart.
- [x] **`.deb` package** for Ubuntu, Debian and Mint, plus an AppImage.
- [x] **Automated tests and CI** on Linux, Windows and macOS, with smoke-tested release packages.
- [ ] Code-signed Windows and macOS packages (needs paid certificates — see [Support](#support)).
- [ ] **Snap Store package.** Confinement will need the tray (StatusNotifier over D-Bus), notifications (moving
      from `notify-send` to a D-Bus/portal call) and opening links via the desktop portal.
- [ ] Flatpak.
- [ ] Global shortcut to show/hide the window.
- [ ] Verified spell-check dictionaries and voice/video-call support, depending on what WhatsApp Web allows.

## Support

WA Desktop is free and stays free. If it is useful to you, you can support it:

- **[Donate with PayPal](https://paypal.me/pahrulirfan)** — see the [donation page](https://pahrulirfan.github.io/wa-desktop/donate.html)
  for what donations pay for. Donations do not unlock any feature.
- Star the repository, report bugs (especially from Windows and macOS), and tell others about it.

## About

WA Desktop is made by **Pahrul Irfan**, lecturer and researcher in Informatics at the Faculty of Engineering,
Universitas Mataram (Unram), Lombok, Indonesia.

Most of the code, the tests and the documentation were written with the help of **Claude** (the Opus model), an AI
assistant made by Anthropic, in Claude Code. Pahrul Irfan decides the features, reviews every change and tests it
on real machines; the automated tests run on GitHub for Linux, Windows and macOS. More on the
[About page](https://pahrulirfan.github.io/wa-desktop/about.html).

## Disclaimer

WA Desktop is an independent, community project. **WhatsApp** is a trademark of WhatsApp LLC; this project is
not affiliated with, authorised, maintained, sponsored or endorsed by WhatsApp LLC, Meta Platforms, Inc. or any
of their affiliates. The application icon is original artwork.

The app loads the official WhatsApp Web client and does not use any unofficial messaging API. Even so, you are
responsible for using it in line with WhatsApp's Terms of Service. The software is provided "as is", without
warranty of any kind.

## License

Released under the [MIT License](LICENSE).
