# PyInstaller spec for WA Desktop (one-folder build).
#
#   pyinstaller --noconfirm packaging/wadesk.spec
#
# Output: dist/wadesk/ (Linux), dist/WA Desktop/ (Windows) or dist/WA Desktop.app (macOS).
# PyInstaller's PySide6 hooks bring the whole Qt WebEngine runtime along: QtWebEngineProcess,
# resources/*.pak, icudtl.dat and qtwebengine_locales. The build step in CI checks for them.

import re
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent  # noqa: F821 - SPECPATH is provided by PyInstaller
VERSION = re.search(r'__version__ = "([^"]+)"', (ROOT / "wadesk" / "__init__.py").read_text()).group(1)
BUNDLE_ID = "io.github.pahrulirfan.wadesk"
WINDOWS, MACOS = sys.platform == "win32", sys.platform == "darwin"
NAME = "WA Desktop" if WINDOWS or MACOS else "wadesk"
ICON = (str(ROOT / "packaging" / "windows" / "wadesk.ico") if WINDOWS
        else str(ROOT / "packaging" / "macos" / "wadesk.icns") if MACOS else None)

# Qt modules the app never uses; leaving them out saves a lot of space.
EXCLUDES = [
    "tkinter", "unittest", "pydoc_data",
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras", "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic", "PySide6.Qt3DRender", "PySide6.QtBluetooth", "PySide6.QtCharts",
    "PySide6.QtDataVisualization", "PySide6.QtDesigner", "PySide6.QtGraphs", "PySide6.QtHelp",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets", "PySide6.QtNfc", "PySide6.QtPdf",
    "PySide6.QtPdfWidgets", "PySide6.QtQuick3D", "PySide6.QtRemoteObjects", "PySide6.QtScxml",
    "PySide6.QtSensors", "PySide6.QtSerialBus", "PySide6.QtSerialPort", "PySide6.QtSpatialAudio",
    "PySide6.QtSql", "PySide6.QtStateMachine", "PySide6.QtTest", "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools", "PySide6.QtWebSockets", "PySide6.QtHttpServer", "PySide6.QtLocation",
]

a = Analysis(  # noqa: F821
    [str(ROOT / "packaging" / "run_wadesk.py")],
    pathex=[str(ROOT)],
    datas=[(str(ROOT / "wadesk" / "assets"), "wadesk/assets")],
    hiddenimports=["PySide6.QtSvg"],
    excludes=EXCLUDES,
)
# The QtQml/QtQuick hooks pull in every QML plugin and the Qt libraries those use (3D, Charts,
# Multimedia, ...), although Qt WebEngine only links QtQuick/QtQml themselves. Drop them.
UNUSED_QT = re.compile(
    r"(^|[/\\])(lib)?Qt6?(3D|Charts|DataVisualization|Graphs|Quick3D|Labs|Location|Multimedia|"
    r"QuickControls2|QuickDialogs2|QuickTemplates2|QuickLayouts|QuickParticles|QuickShapes|"
    r"QuickEffects|QuickTimeline|QuickVectorImage|QmlDesignSupport|QmlLocalStorage|"
    r"QmlXmlListModel|QmlNetwork|QmlCore|ShaderTools|Sensors|SpatialAudio|TextToSpeech|"
    r"VirtualKeyboard|Pdf|Scxml|StateMachine|RemoteObjects|WebView|WebSockets|Bluetooth|Nfc|"
    r"Serial|Sql|Test|QuickTest|UiTools|Designer|Help|HttpServer|Protobuf|Grpc|WaylandCompositor|"
    r"WebEngineQuick|WebChannelQuick|PositioningQuick)")
# QML plugins, plus Qt plugins for features the app does not use (and whose libraries are gone).
QML_DIRS = re.compile(r"PySide6[/\\]Qt[/\\](qml[/\\]|plugins[/\\](qmltooling|position)[/\\]|"
                      r"plugins[/\\]platforminputcontexts[/\\][^/\\]*virtualkeyboard)")
# Linux: libraries every desktop already has (the .deb depends on them). Using the system's copy
# avoids clashes with system GTK themes, NSS modules and graphics drivers.
SYSTEM_LIBS = re.compile(
    r"^(libgtk-3|libgdk-3|libgdk_pixbuf|libglib-2|libgobject-2|libgio-2|libgmodule-2|"
    r"libgthread-2|libcairo|libpango|libharfbuzz|libfontconfig|libfreetype|libX|libxcb|"
    r"libxkbcommon|libdbus-1|libsystemd|libnss|libsmime3|libssl3|libnspr4|libplc4|"
    r"libplds4|libsoftokn3|libfreebl|libasound|libstdc\+\+|libgcc_s|libEGL|libGL|libOpenGL|"
    r"libdrm|libgbm|libwayland-|libepoxy|libatk|libatspi|libkrb5|libgssapi|libk5crypto|"
    r"libcom_err|libgnutls|libgcrypt|libgpg-error|libp11-kit|libunistring|libtasn1|libnettle|"
    r"libhogweed|libidn2|libgmp|libsqlite3|libpng|libjpeg|libtiff|libwebp|libuuid|libblkid|"
    r"libmount|libselinux|libpcre2|libbrotli|libgraphite2|libpixman|libthai|libdatrie|libfribidi|"
    r"libjbig|libdeflate|libLerc|libsharpyuv|libcap|liblz4|libzstd|libmd\.|libbsd|libelf|"
    r"libcups|libavahi|libcloudproviders|libtracker|libtinysparql|libcolord|libgssapi|"
    r"libkeyutils|libresolv|libz\.|libpulse|libsndfile|libFLAC|libogg|libvorbis|libopus|"
    r"libmp3lame|libmpg123|libasyncns|libapparmor|libudev|libxkbfile)")


def keep(entry) -> bool:
    dest = entry[0]
    if UNUSED_QT.search(dest) or QML_DIRS.search(dest):
        return False
    return not (sys.platform.startswith("linux") and SYSTEM_LIBS.match(Path(dest).name))


a.binaries = [b for b in a.binaries if keep(b)]
a.datas = [d for d in a.datas if keep(d)]

pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz, a.scripts, [],
    exclude_binaries=True,
    name=NAME,
    console=False,
    icon=ICON,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name=NAME, upx=False)  # noqa: F821

if MACOS:
    app = BUNDLE(  # noqa: F821
        coll,
        name=f"{NAME}.app",
        icon=ICON,
        bundle_identifier=BUNDLE_ID,
        version=VERSION,
        info_plist={
            "CFBundleName": NAME,
            "CFBundleDisplayName": NAME,
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "LSApplicationCategoryType": "public.app-category.social-networking",
            "LSMinimumSystemVersion": "12.0",
            "NSHighResolutionCapable": True,
            "NSSupportsAutomaticGraphicsSwitching": True,
            "NSMicrophoneUsageDescription": "WA Desktop needs the microphone to record voice "
                                            "messages and for calls in WhatsApp.",
            "NSCameraUsageDescription": "WA Desktop needs the camera for video calls and photos "
                                        "in WhatsApp.",
            "NSHumanReadableCopyright": "MIT License. Not affiliated with WhatsApp LLC or Meta.",
        },
    )
