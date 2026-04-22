from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from house_index.services import photo_service


@pytest.fixture()
def photos_dir(tmp_path: Path) -> Path:
    d = tmp_path / "photos"
    d.mkdir()
    return d


@pytest.fixture()
def sample_jpeg(tmp_path: Path) -> Path:
    p = tmp_path / "sample.jpg"
    Image.new("RGB", (3000, 2000), (200, 50, 100)).save(p, "JPEG")
    return p


def test_import_jpeg_resizes_to_max_dimension(sample_jpeg, photos_dir):
    name = photo_service.import_photo(sample_jpeg, photos_dir)
    assert name.endswith(".jpg")
    out = photos_dir / name
    assert out.exists()

    with Image.open(out) as img:
        assert max(img.size) == photo_service.MAX_DIMENSION


def test_import_unsupported_format_raises(tmp_path, photos_dir):
    bogus = tmp_path / "file.txt"
    bogus.write_text("not an image")
    with pytest.raises(photo_service.PhotoImportError):
        photo_service.import_photo(bogus, photos_dir)


def test_import_missing_file_raises(tmp_path, photos_dir):
    with pytest.raises(photo_service.PhotoImportError):
        photo_service.import_photo(tmp_path / "nothing.jpg", photos_dir)


def test_delete_photo_file(sample_jpeg, photos_dir):
    name = photo_service.import_photo(sample_jpeg, photos_dir)
    assert (photos_dir / name).exists()

    photo_service.delete_photo_file(name, photos_dir)
    assert not (photos_dir / name).exists()


def test_delete_missing_file_is_noop(photos_dir):
    photo_service.delete_photo_file("does_not_exist.jpg", photos_dir)


def test_import_png_converts_to_jpeg(tmp_path, photos_dir):
    png = tmp_path / "pic.png"
    Image.new("RGBA", (500, 400), (10, 200, 30, 255)).save(png, "PNG")

    name = photo_service.import_photo(png, photos_dir)
    assert name.endswith(".jpg")
    with Image.open(photos_dir / name) as img:
        assert img.format == "JPEG"
