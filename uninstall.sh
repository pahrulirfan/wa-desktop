#!/usr/bin/env bash
#
# WA Desktop uninstaller.
#
#   ./uninstall.sh           remove the app but keep your login session and settings
#   ./uninstall.sh --purge   also delete the session, settings and cache
#
set -euo pipefail

APP_ID=wadesk
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"

case "${1:-}" in
    ""|--purge) ;;
    -h|--help) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1 (try --help)" >&2; exit 1 ;;
esac

rm -rf "$DATA_HOME/$APP_ID/app" "$DATA_HOME/$APP_ID/venv"
rm -f "$HOME/.local/bin/$APP_ID" \
      "$DATA_HOME/applications/$APP_ID.desktop" \
      "$DATA_HOME/icons/hicolor/scalable/apps/$APP_ID.svg" \
      "$CONFIG_HOME/autostart/$APP_ID.desktop"

if [[ "${1:-}" == "--purge" ]]; then
    rm -rf "$DATA_HOME/$APP_ID" "$CONFIG_HOME/$APP_ID" "$CACHE_HOME/$APP_ID"
    echo "WA Desktop was removed, including your session, settings and cache."
else
    echo "WA Desktop was removed. Your login session and settings were kept"
    echo "(run '$0 --purge' to delete them as well)."
fi

command -v update-desktop-database >/dev/null && update-desktop-database "$DATA_HOME/applications" 2>/dev/null || true
echo "If WA Desktop is still running, quit it from its tray icon."
