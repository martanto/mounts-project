# PyInstaller spec for the MOUNTS Desktop Dashboard.
# Build: uv run pyinstaller mounts-dashboard.spec

from PyInstaller.utils.hooks import (
    copy_metadata,
    collect_data_files,
    collect_submodules,
)


DASHBOARD_SCRIPTS = [
    "__init__.py",
    "app.py",
    "components.py",
    "compare.py",
    "data.py",
    "detail.py",
    "desktop.py",
    "images.py",
    "overview.py",
]

datas = []
datas += collect_data_files("streamlit")
datas += copy_metadata("streamlit")
datas += copy_metadata("altair")
datas += [
    (f"src/mounts_project/dashboard/{name}", "mounts_project/dashboard")
    for name in DASHBOARD_SCRIPTS
]

hiddenimports = []
hiddenimports += collect_submodules("streamlit")
hiddenimports += collect_submodules("mounts_project")
hiddenimports += [
    "altair",
    "plotly",
    "plotly.graph_objects",
    "plotly.express",
    "pyarrow",
    "pyarrow.lib",
    "pandas",
    "loguru",
    "openpyxl",
    "click",
    "requests",
    "webview",
    "webview.platforms.winforms",
]


a = Analysis(
    ["src/mounts_project/dashboard/desktop.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="mounts-dashboard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="mounts-dashboard",
)
