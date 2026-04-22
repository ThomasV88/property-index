# PyInstaller spec — House Index (onedir mode)
# Build: pyinstaller build/house_index.spec --noconfirm --clean
from pathlib import Path

project_root = Path(SPECPATH).parent.resolve()
src_dir = project_root / "src" / "house_index"

block_cipher = None

a = Analysis(
    [str(src_dir / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(src_dir / "db" / "schema.sql"), "house_index/db"),
    ],
    hiddenimports=[
        "house_index.ui.main_window",
        "house_index.scoring.defaults",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="HouseIndex",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(project_root / "build" / "version_info.txt"),
    # icon=str(project_root / "build" / "app.ico"),  # pridaj keď budeš mať
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="HouseIndex",
)
