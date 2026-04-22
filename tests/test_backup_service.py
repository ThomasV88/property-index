from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from PIL import Image

from house_index.domain.enums import PropertyType
from house_index.domain.models import Property
from house_index.services.backup_service import (
    BackupError,
    create_backup,
    restore_backup,
)
from house_index.services.photo_service import import_photo
from house_index.services.property_service import PropertyService


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture()
def env(tmp_path):
    photos = tmp_path / "photos"
    photos.mkdir()
    db = tmp_path / "house.db"
    yield tmp_path, db, photos


def _seed(db, photos):
    service = PropertyService(db)
    raw = db.parent / "raw.jpg"
    Image.new("RGB", (400, 300), (200, 100, 50)).save(raw, "JPEG")
    f1 = import_photo(raw, photos)
    service.save(
        Property(
            title="Test Brynow",
            property_type=PropertyType.APARTMENT,
            price_pln=450_000,
            area_m2=62,
            distance_km=3.2,
            rooms=3,
        )
    )
    return service


def test_create_backup_contains_db_and_photos(env):
    tmp, db, photos = env
    _seed(db, photos)

    zip_path = tmp / "backup.zip"
    count = create_backup(zip_path, db, photos)
    assert zip_path.exists()
    assert count == 1


def test_restore_round_trip_preserves_data(env):
    tmp, db, photos = env
    svc = _seed(db, photos)
    original = svc.list_all()
    photo_files_before = sorted(p.name for p in photos.iterdir() if p.is_file())
    hash_before = _hash(photos / photo_files_before[0])

    zip_path = tmp / "backup.zip"
    create_backup(zip_path, db, photos)

    # Simuluj stratu dát
    db.unlink()
    for f in photos.iterdir():
        if f.is_file():
            f.unlink()

    success, n_photos = restore_backup(zip_path, db, photos)
    assert success
    assert n_photos == 1

    svc2 = PropertyService(db)
    restored = svc2.list_all()
    assert len(restored) == len(original)
    assert restored[0].title == original[0].title

    photo_files_after = sorted(p.name for p in photos.iterdir() if p.is_file())
    assert photo_files_after == photo_files_before
    assert _hash(photos / photo_files_after[0]) == hash_before


def test_restore_missing_file_raises(env):
    tmp, db, photos = env
    with pytest.raises(BackupError):
        restore_backup(tmp / "missing.zip", db, photos)


def test_restore_invalid_zip_raises(env):
    import zipfile

    tmp, db, photos = env
    bad = tmp / "bad.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("note.txt", "no db here")
    with pytest.raises(BackupError):
        restore_backup(bad, db, photos)
