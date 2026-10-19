#!/usr/bin/env bash
#
# Build an AppImage from a PyInstaller one-folder build.
#
#   packaging/linux/build-appimage.sh <version> <dist/wadesk folder> <output folder> <appimagetool>
#
set -euo pipefail

VERSION="$1"
BUILD="$(cd "$2" && pwd)"
OUT="$3"
TOOL="$4"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
APPDIR="$(mktemp -d)/WA-Desktop.AppDir"

mkdir -p "$APPDIR/usr"
cp -a "$BUILD" "$APPDIR/usr/wadesk"
cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/wadesk/wadesk" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"
sed "s|@EXEC@|wadesk|; /^Actions=/d; /^\[Desktop Action/,\$d" "$HERE/wadesk.desktop" > "$APPDIR/wadesk.desktop"
cp "$ROOT/wadesk/assets/icon.svg" "$APPDIR/wadesk.svg"
ln -s wadesk.svg "$APPDIR/.DirIcon"

mkdir -p "$OUT"
ARCH=x86_64 "$TOOL" --no-appstream "$APPDIR" "$OUT/WA-Desktop-${VERSION}-linux-x86_64.AppImage"
