#!/usr/bin/env bash
#
# Install a .deb on a fresh Debian/Ubuntu system (e.g. a container) and run the self-test.
#
#   packaging/linux/test-deb.sh path/to/wadesk_X.Y.Z-1_amd64.deb
#
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq "$(readlink -f "$1")" xvfb xauth >/dev/null
test -x /usr/bin/wadesk
test -f /usr/share/applications/wadesk.desktop
xvfb-run -a -s "-screen 0 1280x800x24" wadesk --smoke
apt-get remove -y -qq wadesk >/dev/null
test ! -e /usr/bin/wadesk
echo "deb test passed"
