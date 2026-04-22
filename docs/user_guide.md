# Používateľská príručka

## Prvé spustenie

Po prvom spustení sa v `data/` adresári automaticky vytvorí prázdna databáza a default bodovacia konfigurácia. Okno zobrazí prázdny zoznam.

## Pridanie nehnuteľnosti

1. V toolbare klikni **Pridať**.
2. V záložke **Základ** vyplň minimum: **Názov** (povinné), typ (byt/dom), cena, plocha, počet izieb.
3. V záložke **Dotazník** dopln parametre rozloženia (poschodie, výťah, balkón/terasa/záhrada, pivnica) a vybavenia (parkovanie, rok výstavby, stav).
4. V záložke **Lokalita** zadaj vzdialenosť od centra Katowíc v km (manuálne zmeriaš v Google Maps) a pridaj MHD zastávky v okolí.
5. **Odkazy** — pridaj ďalšie URL (mapa, plán bytu, fotogaléria). Hlavný odkaz je v Základe.
6. **Fotky** — pridaj fotky cez **+ Pridať fotku**, nastav primárnu fotku.
7. **Poznámky** — voľný text + tagy oddelené čiarkou (napr. `centrum, novostavba, svetle`).
8. Klikni **Save**. Index sa automaticky vypočíta.

## Úprava nehnuteľnosti

- **Dvojklik na kartu** → otvorí sa **Detail**.
- V detaile tlačidlo **Upraviť** alebo v toolbare vyber kartu a klikni **Upraviť**.

## Porovnanie nehnuteľností

1. Klikni na prvú kartu, **Ctrl + klik** na ďalšie 1–2 karty (max 3 spolu).
2. V toolbare klikni **Porovnať**.
3. Tabuľka zobrazí každý parameter v riadku; najlepší stĺpec zelený, najhorší červený.

## Radenie a filtrovanie

V pravej časti toolbara:

- **Status filter:** zobraz iba nehnuteľnosti s vybraným statusom (Záujem, Po obhliadke, Rezervované, Odmietnuté).
- **Radiť:** Index (default DESC), Cena (ASC/DESC), Plocha, Dátum pridania, Cena/m².

## Nastavenia bodovania

Toolbar → **Nastavenia**.

- Pre každé pravidlo uprav **Max body** a **pásma** (threshold, násobič 0–1).
- Pre cenu sú dve záložky (byt / dom) — rôzne pásma pre rôzne typy.
- Pre enum (parkovanie, stav, izby) uprav mapovanie kľúč → body.
- **Obnoviť defaulty** — vráti predvolené hodnoty (zmeny stratíš až po Save).
- **Save** — uloží config a automaticky prepočíta index všetkým nehnuteľnostiam (progress dialog).

## Záloha a obnova

**Toolbar → Záloha ▾ → Exportovať ZIP…**
- Vyber cieľový ZIP súbor. Obsahuje kompletnú DB + všetky fotky.
- Zálohy ukladaj pred veľkými zmenami nastavení.

**Toolbar → Záloha ▾ → Obnoviť zo ZIP…**
- Vyber ZIP súbor. Aktuálna DB sa uloží ako `.db.bak` a prepíše sa zálohou.
- Reštartuj aplikáciu ak sa zmeny nepremietnu.

## Stavy nehnuteľnosti

- **Záujem** (default) — zváženie v dlhom zozname
- **Po obhliadke** — videl si ju naživo, zvažuješ
- **Rezervované** — podpísaná rezervácia, v procese
- **Odmietnuté** — nie je vhodná

Status meň v edit dialógu (záložka Základ). Filter v toolbare potom zobrazí iba vybraný status.

## Kde sa ukladajú dáta

V predvolenom móde sú dáta v **`%APPDATA%\HouseIndex\`** (konkrétne `C:\Users\<user>\AppData\Roaming\HouseIndex\`):

```
%APPDATA%\HouseIndex\
├── house_index.db           # hlavná databáza
├── photos\                  # všetky fotky (JPEG)
└── backups\                 # auto-zálohy
    ├── auto-2026-04-22_...  # prvé spustenie daného dňa
    └── ...                  # uchovávané 7 dní, potom sa auto-mažú
```

Keď aktualizuješ `.exe` alebo preinstaluješ, dáta zostávajú nedotknuté.

### Portable mód (USB kľúč, prenos)

Ak chceš mať dáta priamo vedľa `.exe` (napr. na USB kľúči alebo keď nechceš stopu v AppData), vytvor prázdny súbor `portable.txt` vedľa `HouseIndex.exe`:

```
HouseIndex\
├── HouseIndex.exe
├── portable.txt             ← vytvor prázdny súbor
├── _internal\
└── data\                    ← dáta idú sem, nie do AppData
```

### Auto-zálohy pri štarte

Prvé spustenie každého dňa automaticky uloží ZIP zálohu do `backups/auto-<date>.zip`. Zálohy staršie ako 7 dní sa automaticky mažú. Ručnú zálohu urob cez **Záloha ▾ → Exportovať ZIP…** (odporúčame pred výraznými zmenami scoring konfigurácie).

## Tipy

- **Ctrl + klik** na viacero kariet = viac vybraných.
- **Dvojklik** na kartu = detail.
- Pri nastavovaní cenových pásem pre dom vs byt dvaj značne — domy sú výrazne drahšie.
