#!/usr/bin/env bash
#
# Build the .deb from a PyInstaller one-folder build.
#
#   packaging/linux/build-deb.sh <version> <dist/wadesk folder> <output folder>
#
# Layout: /opt/wadesk (the app), /usr/bin/wadesk (symlink), desktop entry and icon in /usr/share.
#
set -euo pipefail

VERSION="$1"
BUILD="$(cd "$2" && pwd)"
OUT="$3"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
PKG="wadesk_${VERSION}-1_amd64"
STAGE="$(mktemp -d)/$PKG"

mkdir -p "$STAGE/DEBIAN" "$STAGE/opt" "$STAGE/usr/bin" "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/icons/hicolor/scalable/apps" "$STAGE/usr/share/doc/wadesk"
cp -a "$BUILD" "$STAGE/opt/wadesk"
ln -s /opt/wadesk/wadesk "$STAGE/usr/bin/wadesk"
sed "s|@EXEC@|/usr/bin/wadesk|" "$HERE/wadesk.desktop" > "$STAGE/usr/share/applications/wadesk.desktop"
cp "$ROOT/wadesk/assets/icon.svg" "$STAGE/usr/share/icons/hicolor/scalable/apps/wadesk.svg"
cp "$ROOT/LICENSE" "$STAGE/usr/share/doc/wadesk/copyright"
cp "$HERE/apparmor-wadesk" "$STAGE/opt/wadesk/apparmor-profile"
install -m 755 "$HERE/deb/postinst" "$HERE/deb/postrm" "$STAGE/DEBIAN/"

SIZE_KB="$(du -sk "$STAGE" | cut -f1)"
cat > "$STAGE/DEBIAN/control" <<CONTROL
Package: wadesk
Version: ${VERSION}-1
Section: net
Priority: optional
Architecture: amd64
Installed-Size: ${SIZE_KB}
Maintainer: Pahrul Irfan <7369642+pahrulirfan@users.noreply.github.com>
Homepage: https://pahrulirfan.github.io/wa-desktop/
Depends: libc6 (>= 2.35), libstdc++6, libgcc-s1, zlib1g, libzstd1, libbrotli1,
 libasound2t64 | libasound2, libglib2.0-0t64 | libglib2.0-0, libdbus-1-3, libudev1,
 libnss3, libnspr4, libgssapi-krb5-2, libfontconfig1, libfreetype6,
 libegl1, libgl1, libgbm1, libdrm2, libwayland-client0, libwayland-cursor0,
 libx11-6, libx11-xcb1, libxext6, libxfixes3, libxrandr2, libxtst6, libxcomposite1,
 libxdamage1, libxkbfile1, libxkbcommon0, libxkbcommon-x11-0, libxcb1, libxcb-cursor0,
 libxcb-dri3-0, libxcb-glx0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-randr0,
 libxcb-render0, libxcb-render-util0, libxcb-shape0, libxcb-shm0, libxcb-sync1,
 libxcb-util1, libxcb-xfixes0, libxcb-xkb1
Recommends: libnotify-bin, libgtk-3-0t64 | libgtk-3-0
Description: Unofficial desktop client for WhatsApp Web
 WA Desktop hosts the official WhatsApp Web client in its own window, with a tray
 icon and unread badge, native notifications, a PIN lock and a privacy blur mode.
 .
 Not affiliated with, endorsed by or connected to WhatsApp LLC or Meta.
CONTROL

chmod -R go-w "$STAGE"
mkdir -p "$OUT"
dpkg-deb --root-owner-group --build -Zxz "$STAGE" "$OUT/$PKG.deb"
echo "Built $OUT/$PKG.deb"
