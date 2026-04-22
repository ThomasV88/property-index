# Metodika výpočtu indexu

## Filozofia

**Bodový systém bez hornej hranice.** Index nehnuteľnosti = súčet bodov z jednotlivých pravidiel. Každé pravidlo má maximum (napr. `max_points: 30` pre cenu), ale celkový súčet nie je zhora ohraničený — rôzne nehnuteľnosti sa líšia v tom, koľko parametrov majú vyplnených, a bez hornej hranice je porovnanie priamočiare.

**Priorita váh (podľa diskusie):**

1. **Finančné** — cena (30 bodov)
2. **Lokalita** — vzdialenosť (25 b), MHD (10 b)
3. **Priestor** — plocha (15 b), izby, záhrada, pivnica
4. **Komfort a stav** — parkovanie, stav, výťah, balkón, rok výstavby

Celkový typický maximálny súčet: **~110–120 bodov**.

## Typy pravidiel

### `band_desc` — menšia hodnota = lepšie

Príklad: cena, vzdialenosť.

```python
bands = [[3, 1.0], [6, 0.8], [10, 0.55], [15, 0.3]]  # threshold, multiplier
# value = 4 km → spadne do prvého pásma ≤6 → 25 * 0.8 = 20 bodov
```

Hodnota nad najvyšším prahom → 0.

### `band_asc` — väčšia hodnota = lepšie

Príklad: plocha, rok výstavby.

```python
bands = [[40, 0.3], [55, 0.6], [70, 0.85], [90, 1.0]]
# value = 65 m² → spadne do pásma ≥55 → 15 * 0.6 = 9 bodov
```

Hodnota pod najnižším prahom → 0.

### `enum` — kľúč → body

Priama mapovaná hodnota:

```python
{"turnkey": 6, "standard": 4, "shell": 1}
```

### `bool` — áno/nie

Ak pravda → body, inak 0.

### `bool_plus_area` — základ + bonus za plochu, strop

Používa sa pre záhradu, pivnicu:

```python
{"base": 2, "per_m2": 0.05, "cap": 6}
# garden_m2 = 50 → min(2 + 0.05*50, 6) = min(4.5, 6) = 4.5 bodov
```

### `conditional_bool` — podmienené bool

Výťah prináša body iba ak je byt vysoko (napr. floor > 3).

```python
{"max_points": 5, "condition_field": "floor", "condition_gt": 3, "target_field": "has_elevator"}
```

## Cena — špeciálne: pásma podľa typu

Cena sa líši podľa bytu vs. domu — schéma `bands_by_type`:

```json
"price_pln": {
  "type": "band_desc",
  "max_points": 30,
  "bands_by_type": {
    "apartment": [[400000, 1.0], [600000, 0.75], [800000, 0.50], [1000000, 0.25]],
    "house":     [[800000, 1.0], [1200000, 0.75], [1800000, 0.50], [2500000, 0.25]]
  }
}
```

Engine si vyberie správne pásmo podľa `property.property_type`.

## Predvolené hodnoty (Katowice 2026)

| Parameter | Typ | Max b | Rozpočet / pásma |
|---|---|---|---|
| Cena (byt) | band_desc | 30 | ≤400k=100 %, ≤600k=75 %, ≤800k=50 %, ≤1.0M=25 % |
| Cena (dom) | band_desc | 30 | ≤800k=100 %, ≤1.2M=75 %, ≤1.8M=50 %, ≤2.5M=25 % |
| Vzdialenosť od centra | band_desc | 25 | ≤3=100 %, ≤6=80 %, ≤10=55 %, ≤15=30 % |
| Plocha | band_asc | 15 | ≥40=30 %, ≥55=60 %, ≥70=85 %, ≥90=100 % |
| MHD — najbližšia zastávka | band_desc | 10 | ≤300m=100 %, ≤600=75 %, ≤1000=50 %, ≤1500=25 % |
| Garáž | bool_plus_area | 8 | base=6 + 1/miesto, cap=8 |
| Parkovacie miesto | bool_plus_area | 5 | base=3 + 1/miesto, cap=5 |
| Plocha pozemku (iba dom) | band_asc | 8 | ≥200=30 %, ≥400=60 %, ≥700=85 %, ≥1000=100 % |
| Počet izieb | enum | 8 | 1=2, 2=5, 3=8, 4=7, 5=5, 6=3 |
| Stav nehnuteľnosti | enum | 6 | turnkey=6, standard=4, shell=1 |
| Záhrada | bool_plus_area | 6 | base=2 + 0.05/m², cap=6 |
| Rok výstavby | band_asc | 5 | ≥1960=20 %, ≥1990=50 %, ≥2010=80 %, ≥2020=100 % |
| Výťah (pri poschodí > 3) | conditional_bool | 5 | 5 ak splní podmienku |
| Pivnica | bool_plus_area | 4 | base=1 + 0.1/m², cap=4 |
| Balkón alebo terasa | bool | 3 | |
| Parkovacie miesta | band_asc | 3 | ≥1=50 %, ≥2=100 % |

**Spolu maximum: ~116 bodov.**

## Príklad výpočtu

Byt v Brynowe: 450 000 PLN, 62 m², 3.2 km od centra, 3 izby, poschodie 4 s výťahom, balkón, parkovisko (1 miesto), rok 2015, turnkey stav, tramvajová zastávka 350 m.

| Pravidlo | Výpočet | Body |
|---|---|---|
| `price_pln` (byt) | ≤600k → 30 × 0.75 | 22.5 |
| `distance_km` | ≤6 → 25 × 0.80 | 20.0 |
| `area_m2` | ≥55 → 15 × 0.60 | 9.0 |
| `transit_nearest_m` | ≤600 → 10 × 0.75 | 7.5 |
| `parking_spot` (1 miesto) | base 3 + 1×1 | 4.0 |
| `rooms=3` | enum | 8.0 |
| `condition=turnkey` | enum | 6.0 |
| `garden` | nie | 0.0 |
| `year_built=2015` | ≥2010 → 5 × 0.80 | 4.0 |
| `has_elevator` (floor=4>3) | 5 | 5.0 |
| `balcony_or_terrace` | áno | 3.0 |
| `cellar` | nie | 0.0 |
| `plot_m2` | only_for_type=house, byt → 0 | 0.0 |
| **Spolu** | | **89.0** |

## Pridanie nového parametra

1. Pridaj stĺpec do `properties` v `db/schema.sql` a bumpni schema version.
2. Rozšír `Property` dataclass v `domain/models.py`.
3. Pridaj konverziu v `db/repository.py::_row_to_property` a `_property_params`.
4. Ak je to nový typ pravidla, implementuj funkciu v `scoring/rules.py` a napoj ju v `scoring/engine.py::_apply_rule`.
5. Pridaj default v `scoring/defaults.py`.
6. Pridaj editor podporu v `ui/widgets/rule_card.py`.
7. Pridaj UI pole v `ui/edit_dialog.py` a mapovanie v `_load_from_property` + `_on_accept`.
8. Napíš testy v `tests/test_scoring_*.py`.
