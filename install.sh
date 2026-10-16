#!/usr/bin/env bash
#
# WA Desktop installer.
#
# Installs the app for the current user only (nothing is written outside your home
# directory). The one exception is installing missing system libraries with apt, which
# needs sudo - and can be skipped with --no-apt.
#
set -euo pipefail

APP_ID=wadesk
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
PREFIX="$DATA_HOME/$APP_ID"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/scalable/apps"

SKIP_APT=0
ASSUME_YES=0

usage() {
    cat <<USAGE
Usage: ./install.sh [options]

Options:
  --no-apt     Do not install system packages (use on non-Debian distributions,
               or if you have already installed the dependencies yourself).
  -y, --yes    Do not ask for confirmation before installing system packages.
  -h, --help   Show this help.

Installs to:  $PREFIX
Launcher:     $BIN_DIR/$APP_ID
USAGE
}

say()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

for arg in "$@"; do
    case "$arg" in
        --no-apt)  SKIP_APT=1 ;;
        -y|--yes)  ASSUME_YES=1 ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; die "Unknown option: $arg" ;;
    esac
done

# --- 0. Sanity checks -------------------------------------------------------------
[[ $EUID -eq 0 ]] && die "Please run this script as a normal user, not as root."

case "$(uname -m)" in
    x86_64|aarch64) ;;
    *) die "Unsupported CPU architecture: $(uname -m). PySide6 provides wheels for x86_64 and aarch64 only." ;;
esac

command -v python3 >/dev/null || die "python3 was not found. Install Python 3.10 or newer."
python3 - <<'PY' || die "Python 3.10 or newer is required (found $(python3 -V 2>&1))."
import sys
sys.exit(0 if sys.version_info >= (3, 10) else 1)
PY

glibc="$(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $2}')"
if [[ -n "$glibc" ]] && [[ "$(printf '%s\n2.34\n' "$glibc" | sort -V | head -n1)" != "2.34" ]]; then
    die "glibc 2.34 or newer is required (found $glibc). Use Ubuntu 22.04 / Debian 12 / Linux Mint 21 or newer."
fi

# --- 1. System packages (Qt WebEngine / Chromium runtime libraries) -----------------
if ((SKIP_APT == 0)); then
    if command -v apt-get >/dev/null && command -v dpkg >/dev/null; then
        # Package names differ slightly between releases (e.g. libasound2 / libasound2t64),
        # so only request packages that actually exist on this system.
        wanted=(python3-venv libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0
                libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libnss3 libxkbfile1
                libxcomposite1 libxdamage1 libxtst6 libegl1 libgl1 libnotify-bin)
        if apt-cache show libasound2t64 >/dev/null 2>&1; then wanted+=(libasound2t64)
        else wanted+=(libasound2); fi

        missing=()
        for pkg in "${wanted[@]}"; do
            dpkg -s "$pkg" >/dev/null 2>&1 && continue
            apt-cache show "$pkg" >/dev/null 2>&1 && missing+=("$pkg")
        done

        if ((${#missing[@]})); then
            say "Missing system packages: ${missing[*]}"
            command -v sudo >/dev/null || die "sudo is not available. Install these packages as root, then re-run with --no-apt."
            if ((ASSUME_YES == 0)); then
                read -r -p "Install them now with 'sudo apt-get install'? [Y/n] " reply
                [[ "${reply:-Y}" =~ ^[Yy]$ ]] || die "Aborted. Install the packages yourself, then re-run with --no-apt."
            fi
            sudo apt-get update
            sudo apt-get install -y "${missing[@]}"
        else
            say "All required system packages are already installed"
        fi
    else
        warn "apt was not found, so system packages cannot be installed automatically."
        warn "Make sure these are available: Python venv module, libxcb-cursor, libxkbcommon-x11, NSS (libnss3),"
        warn "ALSA (libasound2), libnotify (notify-send). Continuing."
    fi
fi

python3 -c "import venv, ensurepip" 2>/dev/null \
    || die "The Python 'venv' module is missing. On Debian/Ubuntu/Mint run: sudo apt install python3-venv"

# --- 2. Copy the app and create a virtual environment -------------------------------
say "Installing the app into $PREFIX"
mkdir -p "$PREFIX/app" "$BIN_DIR" "$APPS_DIR" "$ICON_DIR"
rm -rf "$PREFIX/app/$APP_ID"
cp -r "$SRC/$APP_ID" "$PREFIX/app/"
find "$PREFIX/app" -name __pycache__ -type d -prune -exec rm -rf {} +

if [[ ! -x "$PREFIX/venv/bin/python" ]]; then
    say "Creating a Python virtual environment"
    python3 -m venv "$PREFIX/venv"
fi
say "Installing PySide6 + Qt WebEngine (about 260 MB on the first install)"
"$PREFIX/venv/bin/pip" install --quiet --upgrade pip
"$PREFIX/venv/bin/pip" install --quiet --upgrade -r "$SRC/requirements.txt"

# --- 3. Launcher, icon and application-menu entry ---------------------------------
say "Creating the launcher and application-menu entry"
cat > "$BIN_DIR/$APP_ID" <<LAUNCHER
#!/usr/bin/env bash
export PYTHONPATH="$PREFIX/app\${PYTHONPATH:+:\$PYTHONPATH}"
exec "$PREFIX/venv/bin/python" -m wadesk "\$@"
LAUNCHER
chmod +x "$BIN_DIR/$APP_ID"

cp "$SRC/$APP_ID/assets/icon.svg" "$ICON_DIR/$APP_ID.svg"
sed "s|@EXEC@|$BIN_DIR/$APP_ID|" "$SRC/packaging/$APP_ID.desktop" > "$APPS_DIR/$APP_ID.desktop"
chmod +x "$APPS_DIR/$APP_ID.desktop"

command -v update-desktop-database >/dev/null && update-desktop-database "$APPS_DIR" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null && \
    gtk-update-icon-cache -q -t "$DATA_HOME/icons/hicolor" 2>/dev/null || true

# --- Done ----------------------------------------------------------------------------
say "Done! Open \"WA Desktop\" from your application menu, or run: $APP_ID"
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
        echo
        echo "Note: $BIN_DIR is not in your PATH yet, so the '$APP_ID' command may not be found"
        echo "in this terminal. Either log out and back in, or run it as:  $BIN_DIR/$APP_ID"
        ;;
esac
