from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_FOLDER_NAME = "HouseIndex"
PORTABLE_MARKER = "portable.txt"


def app_dir() -> Path:
    """Adresár kde beží aplikácia — vedľa .exe (frozen) alebo koreň repozitára (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def is_portable_mode() -> bool:
    """Dev mód je vždy portable; frozen mód je portable iba ak existuje marker vedľa .exe."""
    if not _is_frozen():
        return True
    return (app_dir() / PORTABLE_MARKER).exists()


def appdata_dir() -> Path:
    """%APPDATA%/HouseIndex (Windows) alebo ~/.local/share/HouseIndex (iné OS)."""
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_FOLDER_NAME
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / APP_FOLDER_NAME
    return Path.home() / ".local" / "share" / APP_FOLDER_NAME


def data_dir() -> Path:
    d = app_dir() / "data" if is_portable_mode() else appdata_dir()
    (d / "photos").mkdir(parents=True, exist_ok=True)
    (d / "backups").mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return data_dir() / "house_index.db"


def photos_dir() -> Path:
    p = data_dir() / "photos"
    p.mkdir(parents=True, exist_ok=True)
    return p


def backups_dir() -> Path:
    b = data_dir() / "backups"
    b.mkdir(parents=True, exist_ok=True)
    return b


def logs_dir() -> Path:
    p = data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def migrate_legacy_data() -> Path | None:
    """Ak je v exe_dir/data DB a cieľ (AppData) ešte nemá DB, presunie ju tam.

    Volá sa pred prvou inicializáciou PropertyService. Vracia cieľový adresár
    ak sa migrovalo, inak None. V portable móde nič nerobí.
    """
    if is_portable_mode():
        return None

    legacy = app_dir() / "data"
    legacy_db = legacy / "house_index.db"
    if not legacy_db.exists():
        return None

    target = appdata_dir()
    if (target / "house_index.db").exists():
        return None

    target.mkdir(parents=True, exist_ok=True)
    (target / "photos").mkdir(exist_ok=True)
    (target / "backups").mkdir(exist_ok=True)

    shutil.move(str(legacy_db), str(target / "house_index.db"))
    for suffix in ("-wal", "-shm", "-journal"):
        src = legacy / f"house_index.db{suffix}"
        if src.exists():
            shutil.move(str(src), str(target / f"house_index.db{suffix}"))

    legacy_photos = legacy / "photos"
    if legacy_photos.exists():
        target_photos = target / "photos"
        for f in legacy_photos.iterdir():
            if f.is_file() and not f.name.startswith("."):
                shutil.move(str(f), str(target_photos / f.name))
        try:
            legacy_photos.rmdir()
        except OSError:
            pass

    try:
        legacy.rmdir()
    except OSError:
        pass

    return target
