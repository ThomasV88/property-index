from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from house_index.services.backup_service import (
    AUTO_PREFIX,
    auto_backup_on_start,
)


@pytest.fixture()
def env(tmp_path: Path):
    db = tmp_path / "house.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()

    photos = tmp_path / "photos"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"fake")

    backups = tmp_path / "backups"
    backups.mkdir()
    return db, photos, backups


def test_auto_backup_creates_first_zip(env):
    db, photos, backups = env
    out = auto_backup_on_start(db, photos, backups)
    assert out is not None
    assert out.exists()
    assert out.name.startswith(AUTO_PREFIX)


def test_auto_backup_skips_if_today_exists(env):
    db, photos, backups = env
    now = datetime(2026, 4, 22, 10, 0)
    out1 = auto_backup_on_start(db, photos, backups, now=now)
    assert out1 is not None

    out2 = auto_backup_on_start(db, photos, backups, now=now + timedelta(hours=3))
    assert out2 is None
    assert len(list(backups.glob(f"{AUTO_PREFIX}*.zip"))) == 1


def test_auto_backup_prunes_old(env):
    db, photos, backups = env
    old1 = backups / f"{AUTO_PREFIX}2026-04-10_100000.zip"
    old2 = backups / f"{AUTO_PREFIX}2026-04-05_100000.zip"
    recent = backups / f"{AUTO_PREFIX}2026-04-21_100000.zip"
    for p in (old1, old2, recent):
        p.write_bytes(b"dummy")

    now = datetime(2026, 4, 22, 10, 0)
    auto_backup_on_start(db, photos, backups, keep_days=7, now=now)

    assert not old1.exists()
    assert not old2.exists()
    assert recent.exists()


def test_auto_backup_no_db_returns_none(tmp_path):
    missing = tmp_path / "nothing.db"
    photos = tmp_path / "photos"
    photos.mkdir()
    backups = tmp_path / "backups"
    backups.mkdir()
    assert auto_backup_on_start(missing, photos, backups) is None


def test_auto_backup_ignores_malformed_filenames(env):
    db, photos, backups = env
    (backups / f"{AUTO_PREFIX}garbage.zip").write_bytes(b"x")
    now = datetime(2026, 4, 22, 10, 0)
    auto_backup_on_start(db, photos, backups, keep_days=7, now=now)
    assert (backups / f"{AUTO_PREFIX}garbage.zip").exists()
