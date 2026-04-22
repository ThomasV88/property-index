# Architektúra

Aplikácia je rozdelená do vrstiev s jasnými hranicami. Dáta tečú **UI → Service → Repository → SQLite**, scoring je čistá knižnica bez externých závislostí.

## Vrstvy

```
┌────────────────────────────────────────────────────────────────┐
│  UI (PySide6)                                                  │
│  main_window, cards_view, edit_dialog, detail_view,            │
│  compare_view, settings_panel, widgets/*                       │
└───────────────┬────────────────────────────────────────────────┘
                │ Property dataclasses
                ▼
┌────────────────────────────────────────────────────────────────┐
│  Services                                                      │
│  property_service   (CRUD + auto-scoring)                      │
│  photo_service      (import, resize, delete)                   │
│  backup_service     (ZIP export/import)                        │
└───────────────┬────────────────────────────────────────────────┘
                │
                ▼
┌────────────────┬────────────────────────┬──────────────────────┐
│ Scoring        │ Repository             │ Domain               │
│ rules, engine, │ CRUD SQL               │ dataclasses, enums   │
│ defaults       │ open_connection()      │                      │
└────────────────┴───────────┬────────────┴──────────────────────┘
                             ▼
                    ┌──────────────────┐
                    │  SQLite (WAL)    │
                    │  data/*.db       │
                    └──────────────────┘
```

## Kľúčové moduly

| Modul | Účel |
|---|---|
| `paths.py` | Resolver pre `app_dir()`, `data_dir()` — detekuje `sys.frozen` a lokalizuje `data/` vedľa `.exe` |
| `db/schema.sql` | DDL definícia, idempotentná (IF NOT EXISTS) |
| `db/migrations.py` | Verzie schémy, aplikuje pri štarte |
| `db/repository.py` | Čisto-funkcionálne CRUD operácie nad SQLite |
| `domain/models.py` | Dataclasses (`Property`, `Link`, `Photo`, `TransitStop`) |
| `domain/enums.py` | `PropertyType`, `Condition`, `Status`, `ParkingKind`, `TransitKind` |
| `scoring/rules.py` | Čisté funkcie: `band_desc`, `band_asc`, `enum_score`, `bool_score`, `bool_plus_area_score`, `conditional_bool_score` |
| `scoring/engine.py` | `compute(property, config) -> IndexResult` |
| `scoring/defaults.py` | `DEFAULT_SCORING_CONFIG` (pásma pre Katowice 2026) |
| `scoring/recompute.py` | Batch prepočet všetkých nehnuteľností |
| `services/property_service.py` | CRUD fasáda + automatický prepočet indexu pri `save()` |
| `services/photo_service.py` | Import fotky (Pillow → JPEG max 1920 px) |
| `services/backup_service.py` | Export/import ZIP (SQLite backup API + fotky) |

## Thread model

Hlavný Qt thread obsluhuje UI. SQLite sa otvára **per-operation** (context manager `open_connection`), takže neexistuje zdieľaná dlhožijúca connection medzi vláknami.

**Prepočet indexu po zmene configu** beží v samostatnom `QThread` (`ui/settings_panel.py::RecomputeWorker`) s progress dialogom — pri 100+ nehnuteľnostiach by blokovanie UI bolo badateľné.

## Tok dát: pridanie nehnuteľnosti

1. User klikne **Pridať** → `MainWindow._on_add_property`
2. Otvorí sa `PropertyEditDialog` (tabuľkový formulár, 6 tabov)
3. User vyplní → Save → dialog konštruuje `Property` dataclass
4. `MainWindow` volá `service.save(prop)`:
   - `PropertyService.save()` zavolá `compute(prop, config)` → vráti `IndexResult`
   - Uloží `index_score` + `index_breakdown` do dataclass-u
   - Otvorí DB connection, volá `repository.save_property(conn, prop)`
   - Repo spraví INSERT + nahradí vzťahy (links, photos, transit_stops, tags)
5. `MainWindow.reload()` → znova vylistuje + prekreslí karty

## Tok dát: zmena bodovania

1. User otvorí **Nastavenia** → `SettingsPanel`
2. Panel vykreslí `RuleCard` pre každé pravidlo v `scoring_config`
3. User upraví hodnoty → **Save**
4. `_collect_config()` zbiera zmeny z kariet → `dict`
5. `service.save_config(config)` → INSERT do `scoring_config`, prednastaví `is_active=1`
6. `RecomputeWorker` v `QThread` iteruje nad všetkými properties, volá `compute()` a `repository.update_index_cache()`
7. Po dokončení → progress dialog close → `MainWindow.reload()`

## Perzistencia

- **SQLite** v `data/house_index.db` (WAL mode) pre štruktúrované dáta.
- **Fotky** ako JPEG v `data/photos/<uuid>.jpg`, v DB iba relatívny `file_name`.
- **Scoring config** v tabuľke `scoring_config` ako JSON blob, vždy jeden `is_active=1`.
- **Settings** (jazyk, UI preferencie) v KV tabuľke `settings`.

## Build vrstvy

Projekt sa balí cez **PyInstaller onedir** (nie onefile). Dôvod: `data/` musí byť perzistentný vedľa `.exe`. `paths.app_dir()` deteguje `sys.frozen` a lokalizuje správne.
