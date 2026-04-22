# House Index

Desktop aplikácia pre hodnotenie nehnuteľností v Katowiciach podľa osobných preferencií. Pridávaš byty/domy, vypĺňaš dotazník a pre každú nehnuteľnosť dostaneš numerický **Index Ideálneho Bývania** (napr. 97) na základe konfigurovateľného bodovacieho systému.

## Obsah

- [Funkcie](#funkcie)
- [Ako funguje index](#ako-funguje-index)
- [Rýchly štart](#rýchly-štart)
- [Build `.exe`](#build-exe)
- [Dokumentácia](#dokumentácia)
- [Štruktúra projektu](#štruktúra-projektu)
- [Testy](#testy)
- [Licencia](#licencia)

## Funkcie

- **Pridávanie nehnuteľností** (byt / dom) s dotazníkom: cena, plocha, vzdialenosť od centra Katowíc, počet izieb, poschodie, výťah, balkón/terasa/záhrada, parkovanie, rok výstavby, pivnica, MHD v okolí, stav (holý / v štandarde / na kľúč).
- **Automatický výpočet indexu** — súčet bodov zo 14 pravidiel (bez hornej hranice, typicky ~116 max).
- **Karty s fotkami** — hlavná obrazovka zobrazuje nehnuteľnosti ako dlaždice s primárnou fotkou, cenou, m², vzdialenosťou a farebným index badge.
- **Detail** — kompletné parametre, rozpis indexu (bar chart per parameter), galéria fotiek, klikateľné odkazy.
- **Side-by-side porovnanie** 2–3 nehnuteľností; najlepší stĺpec zelený, najhorší červený.
- **Radenie a filtrovanie** — podľa indexu, ceny, plochy, ceny/m², dátumu; filter podľa statusu (záujem / po obhliadke / rezervované / odmietnuté).
- **Konfigurovateľné bodovanie** — Settings panel umožňuje meniť pásma, max body a enum mapovania; po Save sa index automaticky prepočíta všetkým nehnuteľnostiam.
- **Status tracking, poznámky, tagy** — vedieš si stav rozhodovania a voľný text.
- **Záloha a obnova** — export ZIP (DB + fotky), neskôr import na inom PC.
- **Windows `.exe`** cez PyInstaller (onedir).

## Ako funguje index

**Bodový systém bez hornej hranice.** Každé pravidlo pripočíta body podľa hodnoty parametra. Pravidlá sú 6 typov:

- `band_desc` — menšia = lepšie (cena, vzdialenosť)
- `band_asc` — väčšia = lepšie (plocha, rok výstavby)
- `enum` — kľúč → body (parkovanie, stav, izby)
- `bool` — áno/nie (balkón)
- `bool_plus_area` — základ + bonus za m² s cap (záhrada, pivnica)
- `conditional_bool` — podmienené (výťah iba pri poschodí > 3)

**Priorita váh:** finančné (cena 30 b) + lokalita (vzdialenosť 25 b, MHD 10 b) — tak ako požadoval autor. Cena má oddelené pásma pre byt vs. dom.

**Príklad** — byt 450 000 PLN, 62 m², 3.2 km od centra, 3 izby, poschodie 4 s výťahom, parkovisko, rok 2015, turnkey, tramvaj 350 m:

| Pravidlo | Body |
|---|---|
| Cena (≤600k = 75 %) | 22.5 |
| Vzdialenosť (≤6 = 80 %) | 20.0 |
| Plocha (≥55 = 60 %) | 9.0 |
| MHD (≤600 m = 75 %) | 7.5 |
| Parkovanie (lot) | 5.0 |
| 3 izby | 8.0 |
| Turnkey stav | 6.0 |
| Rok 2015 (≥2010 = 80 %) | 4.0 |
| Výťah (poschodie 4) | 5.0 |
| Balkón | 3.0 |
| Parkovacie miesto | 1.5 |
| **Spolu** | **91.0** |

Detailnejšie v [`docs/scoring_methodology.md`](./docs/scoring_methodology.md).

## Rýchly štart

Vyžaduje **Python 3.11+** na Windows 10/11.

```powershell
cd C:\Users\tomas\projects\house-index
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m house_index
```

Pri prvom spustení sa v `data/` vytvorí prázdna databáza a default bodovacia konfigurácia. Klikni **Pridať** a vyplň nehnuteľnosť.

Podrobný workflow v [`docs/user_guide.md`](./docs/user_guide.md).

## Build `.exe`

```powershell
pyinstaller build\house_index.spec --noconfirm --clean
```

Výstup: `dist\HouseIndex\HouseIndex.exe` + `_internal\` priečinok. **Onedir mode** — celý adresár je portable, `data/` sa vytvorí vedľa `.exe` pri prvom spustení. Typická veľkosť distribúcie: ~125 MB.

Detaily + release checklist v [`docs/build_and_release.md`](./docs/build_and_release.md).

## Dokumentácia

Všetko v [`docs/`](./docs/):

| Súbor | Obsah |
|---|---|
| [`architecture.md`](./docs/architecture.md) | Vrstvy, tok dát, thread model |
| [`db_schema.md`](./docs/db_schema.md) | Tabuľky, indexy, migračná stratégia |
| [`scoring_methodology.md`](./docs/scoring_methodology.md) | Filozofia bodovania, pásma, príklady |
| [`user_guide.md`](./docs/user_guide.md) | Používateľská príručka s workflow |
| [`build_and_release.md`](./docs/build_and_release.md) | Setup, PyInstaller, release proces |
| [`decisions/ADR-*.md`](./docs/decisions/) | Architektonické rozhodnutia (PySide6, SQLite, bodový systém, onedir) |

## Štruktúra projektu

```
src/house_index/
├── app.py, __main__.py, paths.py       # bootstrap + path resolver
├── db/                                  # schema.sql, migrations, repository
├── domain/                              # dataclasses + enums
├── scoring/                             # rules, engine, defaults, recompute
├── services/                            # property, photo, backup
└── ui/                                  # main_window + views + widgets
docs/                                    # dokumentácia (sk)
tests/                                   # pytest
build/                                   # house_index.spec, version_info.txt
```

## Testy

```powershell
python -m pytest -q
```

Aktuálne **77 testov** (scoring 49, repository 10, property service 8, photo service 6, backup 4). UI sa testuje manuálne podľa checklistu v používateľskej príručke.

## Licencia

Proprietary. Autor: Tomas Voslar.