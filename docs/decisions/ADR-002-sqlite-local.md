# ADR-002: SQLite + lokálna zložka fotiek

## Status
Schválené · 2026-04-22

## Kontext
Aplikácia je single-user desktop nástroj. Treba uložiť štruktúrované dáta (nehnuteľnosti, bodovanie, nastavenia) a binárne dáta (fotky).

Voľby pre štruktúrované dáta:
- **SQLite** — embeded, ACID, žiadne servery.
- **JSON súbory** — jednoduchšie, ale pomalé pri raste a slabé pri filtráciách.
- **Server DB (Postgres, MySQL)** — overkill pre single-user offline app.

Voľby pre fotky:
- **BLOB v DB** — všetko v jednom súbore, ale DB narastie na stovky MB.
- **Súborový systém + DB cesty** — štandardný prístup pre obsah.

## Rozhodnutie
**SQLite** (v `data/house_index.db`, WAL mode) pre štruktúrované dáta, **`data/photos/<uuid>.jpg`** pre fotky. V DB iba `file_name`.

## Dôvody
- Rýchle radenie/filtrovanie (100+ nehnuteľností by s JSON boli pomalé).
- SQL kwery sú čitateľnejšie ako rôzne Python filtračné reťazce.
- Zabezpečená integrita cez FK + CHECK + UNIQUE.
- Fotky oddelené od DB → jednoduchá záloha (`copy` celého `data/`), jednoduchý cleanup, žiadne BLOB-y.
- UUID filenamy = žiadne kolízie, žiadna potreba sanitize.

## Dôsledky
- Potrebné riešiť migrácie pri zmene schémy (`schema_version` tabuľka, v `db/migrations.py`).
- Pri mazaní nehnuteľnosti treba explicitne zmazať aj súbory fotiek (zabezpečuje `photo_service.delete_photo_file`).
- Zálohy sú ZIP obsahujúce DB + photos priečinok (pozri `services/backup_service.py`).
