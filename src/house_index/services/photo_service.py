from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from PIL import Image, ImageOps

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_DIMENSION = 1920
THUMB_DIMENSION = 480


class PhotoImportError(Exception):
    pass


def import_photo(source: Path, photos_dir: Path) -> str:
    """Skopíruje fotku do photos_dir, zmenší ju na rozumný max rozmer a vráti relatívny názov."""
    source = Path(source)
    if not source.exists():
        raise PhotoImportError(f"Súbor neexistuje: {source}")
    ext = source.suffix.lower()
    if ext not in SUPPORTED_EXT:
        raise PhotoImportError(f"Nepodporovaný formát: {ext}")

    photos_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"{uuid.uuid4().hex}.jpg"
    out_path = photos_dir / out_name

    try:
        with Image.open(source) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            img.save(out_path, "JPEG", quality=88, optimize=True)
    except Exception as exc:
        if out_path.exists():
            out_path.unlink()
        raise PhotoImportError(f"Chyba pri spracovaní fotky: {exc}") from exc

    return out_name


def delete_photo_file(file_name: str, photos_dir: Path) -> None:
    path = photos_dir / file_name
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


def thumbnail_path(file_name: str, photos_dir: Path) -> Path:
    """Vráti cestu k fotke — delegate si ju potom škáluje cez QPixmap."""
    return photos_dir / file_name


def copy_photo_as_is(source: Path, photos_dir: Path) -> str:
    """Fallback: ak Pillow zlyhá, skopíruje súbor bez úpravy."""
    source = Path(source)
    photos_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"{uuid.uuid4().hex}{source.suffix.lower()}"
    shutil.copyfile(source, photos_dir / out_name)
    return out_name
