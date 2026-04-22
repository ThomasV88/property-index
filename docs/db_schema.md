# Databázová schéma

SQLite, WAL mode, `PRAGMA foreign_keys = ON`. Verzia schémy v tabuľke `schema_version` (aktuálne 1). Migrácie v `src/house_index/db/migrations.py`.

## Tabuľky

### `properties` — jadro nehnuteľnosti

| Stĺpec | Typ | Poznámka |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `title` | TEXT NOT NULL | zobrazovaný názov |
| `primary_link` | TEXT | hlavný odkaz na inzerát |
| `property_type` | TEXT NOT NULL | `apartment` \| `house` |
| `multi_floor` | INTEGER (bool) | viacpodlažná nehnuteľnosť |
| `price_pln` | INTEGER | cena v PLN |
| `area_m2` | REAL | plocha v m² |
| `distance_km` | REAL | vzdialenosť od centra Katowíc (manuálne) |
| `rooms` | INTEGER | počet izieb |
| `floor` | INTEGER | poschodie |
| `has_elevator` | INTEGER (bool) | |
| `has_balcony` / `balcony_m2` | INTEGER (bool) / REAL | |
| `has_terrace` / `terrace_m2` | | |
| `has_garden` / `garden_m2` | | |
| `has_garage` / `garage_spots` | INTEGER (bool) / INTEGER | garáž + počet miest v nej |
| `has_parking_spot` / `parking_spot_count` | INTEGER (bool) / INTEGER | parkovacie miesto mimo garáže + počet |
| `plot_m2` | REAL | plocha pozemku (relevantné iba pre dom) |
| `year_built` | INTEGER | |
| `has_cellar` / `cellar_m2` | | |
| `condition` | TEXT | `shell` \| `standard` \| `turnkey` |
| `status` | TEXT NOT NULL | `interested` \| `visited` \| `rejected` \| `reserved` |
| `notes` | TEXT | |
| `index_score` | REAL | cached; recompute pri save alebo zmene configu |
| `index_breakdown` | TEXT (JSON) | per-parameter body |
| `created_at`, `updated_at` | TEXT (ISO datetime) | auto |

Indexy: `(status)`, `(index_score DESC)`.

### `transit_stops` — 1:N

`id, property_id → properties.id CASCADE, kind (bus|tram|train), distance_m, name`.

### `links` — 1:N (dodatočné odkazy okrem `primary_link`)

`id, property_id CASCADE, url, label`.

### `photos` — 1:N

`id, property_id CASCADE, file_name (uuid.jpg v data/photos/), is_primary, sort_order`.

### `tags` + `property_tags` — M:N

```sql
tags (id, name UNIQUE)
property_tags (property_id, tag_id) PRIMARY KEY (property_id, tag_id)
```

### `scoring_config` — verzionované konfigurácie

```sql
id, name, is_active (0/1), config_json, updated_at
UNIQUE INDEX on (is_active) WHERE is_active = 1
```

Vždy jeden aktívny riadok; history zostáva pre možnosť vrátenia sa.

### `settings` — KV store

`key PRIMARY KEY, value`. Používa sa pre jazyk, default triedenie a podobné UI nastavenia.

## Migrácia

```python
# db/migrations.py
CURRENT_VERSION = 1

def migrate(conn):
    current = _get_version(conn)
    if current == 0:
        conn.executescript(schema_sql)   # CREATE TABLE IF NOT EXISTS ...
    _set_version(conn, CURRENT_VERSION)
```

Pri každom budúcom bumpe verzie pridaj `if current < N: conn.executescript(migration_N_sql)` a bumpni `CURRENT_VERSION`.

## Integrita dát

- `ON DELETE CASCADE` pre všetky child tabuľky (`transit_stops`, `links`, `photos`, `property_tags`) — zmazanie `properties` odstráni aj ich relácie.
- `CHECK` constraints na enum stĺpce (`property_type`, `status`, `condition`, `transit_stops.kind`).
- Filenamy fotiek sú generované UUID, takže kolízie nehrozia.

## Príklady dotazov

```sql
-- Top 5 nehnuteľností podľa indexu
SELECT title, index_score, price_pln FROM properties
ORDER BY index_score DESC LIMIT 5;

-- Byty do 500k PLN s vzdialenosťou <5km od centra
SELECT * FROM properties
WHERE property_type = 'apartment'
  AND price_pln <= 500000
  AND distance_km < 5
ORDER BY index_score DESC;

-- Všetky fotky nehnuteľnosti s id=42
SELECT file_name, is_primary FROM photos
WHERE property_id = 42 ORDER BY is_primary DESC, sort_order;
```
