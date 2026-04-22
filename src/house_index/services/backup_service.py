from __future__ import annotations

import shutil
import sqlite3
import zipfile
from datetime import datetime, timedelta
from pathlib import Path


class BackupError(Exception):
    pass


AUTO_PREFIX = "auto-"
DATE_FORMAT = "%Y-%m-%d"
TIMESTAMP_FORMAT = "%Y-%m-%d_%H%M%S"


def create_backup(zip_path: Path, db_path: Path, photos_dir: Path) -> int:
    """Vytvorí ZIP zálohu s DB (ako plný vacuum) a všetkými fotkami. Vráti počet zabalených fotiek."""
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        raise BackupError(f"DB neexistuje: {db_path}")

    snapshot = zip_path.parent / f".{zip_path.stem}.db.tmp"
    _snapshot_db(db_path, snapshot)

    photo_count = 0
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(snapshot, arcname="house_index.db")
            if photos_dir.exists():
                for p in sorted(photos_dir.iterdir()):
                    if p.is_file() and not p.name.startswith("."):
                        zf.write(p, arcname=f"photos/{p.name}")
                        photo_count += 1
    finally:
        if snapshot.exists():
            snapshot.unlink()
    return photo_count


def _snapshot_db(src: Path, dst: Path) -> None:
    """Uložia konzistentnú kópiu SQLite DB cez backup API."""
    src_conn = sqlite3.connect(str(src))
    try:
        dst_conn = sqlite3.connect(str(dst))
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()


def restore_backup(zip_path: Path, db_path: Path, photos_dir: Path) -> tuple[bool, int]:
    """Nahradí aktuálnu DB a fotky obsahom zálohy. Vráti (success, photo_count)."""
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise BackupError(f"Záloha neexistuje: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if "house_index.db" not in names:
            raise BackupError("Záloha neobsahuje house_index.db")

        if db_path.exists():
            shutil.copy2(db_path, db_path.with_suffix(".db.bak"))
        if photos_dir.exists():
            for p in photos_dir.iterdir():
                if p.is_file() and not p.name.startswith("."):
                    p.unlink()
        photos_dir.mkdir(parents=True, exist_ok=True)

        zf.extract("house_index.db", db_path.parent)
        extracted = db_path.parent / "house_index.db"
        if extracted != db_path:
            shutil.move(str(extracted), str(db_path))

        photo_count = 0
        for name in names:
            if name.startswith("photos/") and not name.endswith("/"):
                data = zf.read(name)
                out = photos_dir / Path(name).name
                out.write_bytes(data)
                photo_count += 1
        return True, photo_count


def auto_backup_on_start(
    db_path: Path,
    photos_dir: Path,
    backups_dir: Path,
    keep_days: int = 7,
    now: datetime | None = None,
) -> Path | None:
    """Vytvorí zálohu ak dnes ešte neexistuje a prune-ne staršie ako keep_days.

    Volá sa raz pri štarte. Ak DB neexistuje alebo už existuje dnešná záloha,
    vráti None. Inak vráti cestu k novej zálohe.
    """
    if not db_path.exists():
        return None

    now = now or datetime.now()
    backups_dir.mkdir(parents=True, exist_ok=True)

    today = now.strftime(DATE_FORMAT)
    existing_today = list(backups_dir.glob(f"{AUTO_PREFIX}{today}_*.zip"))
    if existing_today:
        _prune_old_backups(backups_dir, keep_days, now=now)
        return None

    backup_path = backups_dir / f"{AUTO_PREFIX}{now.strftime(TIMESTAMP_FORMAT)}.zip"
    try:
        create_backup(backup_path, db_path, photos_dir)
    except BackupError:
        return None

    _prune_old_backups(backups_dir, keep_days, now=now)
    return backup_path


def _prune_old_backups(
    backups_dir: Path, keep_days: int, now: datetime | None = None
) -> int:
    """Zmaže auto-* zálohy staršie ako keep_days dní. Vráti počet zmazaných."""
    now = now or datetime.now()
    cutoff = now - timedelta(days=keep_days)
    removed = 0
    for p in backups_dir.glob(f"{AUTO_PREFIX}*.zip"):
        try:
            date_str = p.stem.replace(AUTO_PREFIX, "").split("_")[0]
            d = datetime.strptime(date_str, DATE_FORMAT)
        except ValueError:
            continue
        if d < cutoff:
            try:
                p.unlink()
                removed += 1
            except OSError:
                pass
    return removed
