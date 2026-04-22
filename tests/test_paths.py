from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from house_index import paths


@pytest.fixture()
def fake_frozen(monkeypatch, tmp_path):
    """Simulates a frozen .exe located at tmp_path/HouseIndex.exe."""
    exe_path = tmp_path / "HouseIndex.exe"
    exe_path.write_bytes(b"fake")
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys.executable", str(exe_path))

    appdata = tmp_path / "AppData_Roaming"
    monkeypatch.setenv("APPDATA", str(appdata))
    return tmp_path


def test_portable_mode_dev(monkeypatch):
    monkeypatch.delattr("sys.frozen", raising=False)
    assert paths.is_portable_mode() is True


def test_portable_mode_frozen_no_marker(fake_frozen):
    assert paths.is_portable_mode() is False


def test_portable_mode_frozen_with_marker(fake_frozen):
    (fake_frozen / paths.PORTABLE_MARKER).write_text("")
    assert paths.is_portable_mode() is True


def test_appdata_dir_uses_env(fake_frozen):
    d = paths.appdata_dir()
    assert d == fake_frozen / "AppData_Roaming" / paths.APP_FOLDER_NAME


def test_data_dir_frozen_goes_to_appdata(fake_frozen):
    d = paths.data_dir()
    assert d.parent.name == "AppData_Roaming"
    assert d.name == paths.APP_FOLDER_NAME
    assert (d / "photos").is_dir()
    assert (d / "backups").is_dir()


def test_data_dir_portable_next_to_exe(fake_frozen):
    (fake_frozen / paths.PORTABLE_MARKER).write_text("")
    d = paths.data_dir()
    assert d.parent == fake_frozen
    assert d.name == "data"


def test_migrate_legacy_data_moves_db_and_photos(fake_frozen):
    legacy = fake_frozen / "data"
    (legacy / "photos").mkdir(parents=True)
    (legacy / "backups").mkdir()

    conn = sqlite3.connect(str(legacy / "house_index.db"))
    conn.execute("CREATE TABLE test (x INTEGER)")
    conn.execute("INSERT INTO test VALUES (42)")
    conn.commit()
    conn.close()

    (legacy / "photos" / "abc.jpg").write_bytes(b"fakeimage")

    target = paths.migrate_legacy_data()
    assert target is not None
    assert target == paths.appdata_dir()
    assert (target / "house_index.db").exists()
    assert (target / "photos" / "abc.jpg").exists()
    assert not (legacy / "house_index.db").exists()
    assert not (legacy / "photos" / "abc.jpg").exists()

    conn = sqlite3.connect(str(target / "house_index.db"))
    row = conn.execute("SELECT x FROM test").fetchone()
    assert row[0] == 42
    conn.close()


def test_migrate_legacy_data_noop_if_target_has_db(fake_frozen):
    legacy = fake_frozen / "data"
    legacy.mkdir()
    (legacy / "house_index.db").write_bytes(b"legacy")

    target = paths.appdata_dir()
    target.mkdir(parents=True)
    (target / "house_index.db").write_bytes(b"already-there")

    result = paths.migrate_legacy_data()
    assert result is None
    assert (legacy / "house_index.db").read_bytes() == b"legacy"
    assert (target / "house_index.db").read_bytes() == b"already-there"


def test_migrate_legacy_data_noop_in_portable_mode(fake_frozen):
    (fake_frozen / paths.PORTABLE_MARKER).write_text("")
    legacy = fake_frozen / "data"
    legacy.mkdir()
    (legacy / "house_index.db").write_bytes(b"legacy")

    assert paths.migrate_legacy_data() is None
    assert (legacy / "house_index.db").exists()


def test_migrate_legacy_data_noop_if_no_legacy(fake_frozen):
    assert paths.migrate_legacy_data() is None
