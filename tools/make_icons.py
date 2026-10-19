#!/usr/bin/env python3
"""Generate the Windows and macOS app icons from wadesk/assets/icon.svg.

    python tools/make_icons.py

Writes packaging/windows/wadesk.ico and packaging/macos/wadesk.icns. Only PySide6 is needed: the
SVG is rendered with QtSvg, and both formats are written as containers of PNG images (supported
since Windows Vista and Mac OS X 10.7).
"""

import os
import struct
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # no window is opened

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "wadesk" / "assets" / "icon.svg"
ICO = ROOT / "packaging" / "windows" / "wadesk.ico"
ICNS = ROOT / "packaging" / "macos" / "wadesk.icns"

ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
# icns element types holding PNG data, by pixel size (several types share a size: 1x and 2x).
ICNS_TYPES = ((b"icp4", 16), (b"icp5", 32), (b"icp6", 64), (b"ic07", 128), (b"ic08", 256),
              (b"ic09", 512), (b"ic10", 1024), (b"ic11", 32), (b"ic12", 64), (b"ic13", 256),
              (b"ic14", 512))


def png(size: int) -> bytes:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(str(SVG)).render(p, QRectF(0, 0, size, size))
    p.end()
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return bytes(data)


def write_ico(path: Path) -> None:
    images = [(size, png(size)) for size in ICO_SIZES]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries, blobs = b"", b""
    for size, data in images:
        dim = 0 if size >= 256 else size  # 0 means 256 in an ICONDIRENTRY
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset + len(blobs))
        blobs += data
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + entries + blobs)


def write_icns(path: Path) -> None:
    cache: dict[int, bytes] = {}
    body = b""
    for kind, size in ICNS_TYPES:
        data = cache.setdefault(size, png(size))
        body += kind + struct.pack(">I", 8 + len(data)) + data
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"icns" + struct.pack(">I", 8 + len(body)) + body)


def main() -> int:
    app = QGuiApplication(sys.argv[:1])  # noqa: F841 - QPainter needs a GUI application
    write_ico(ICO)
    write_icns(ICNS)
    for f in (ICO, ICNS):
        print(f"wrote {f.relative_to(ROOT)} ({f.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
