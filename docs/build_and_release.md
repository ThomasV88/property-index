# Build a release

## Požiadavky

- **Python 3.11+** (testované 3.12)
- **Windows 10/11** (primárny target pre `.exe`)

## Setup dev prostredia

```powershell
cd C:\Users\tomas\projects\house-index
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Spustenie z zdrojákov

```powershell
python -m house_index
```

Dáta sa vytvoria v `data/` v repozitári.

## Testy

```powershell
python -m pytest -v
```

Aktuálne coverage: scoring engine 95 %+, repository 100 %, photo service 100 %, backup 100 %. UI testy manuálne podľa checklistu v `user_guide.md`.

## Build `.exe`

```powershell
pyinstaller build\house_index.spec --noconfirm --clean
```

Výstup v `dist\HouseIndex\HouseIndex.exe`. **Onedir mode.**

**Dáta** bežiacej aplikácie idú do `%APPDATA%\HouseIndex\` (od v0.3.0). Rebuild `.exe` je bezpečný — user dáta sa nestrácajú. Portable mód (dáta vedľa exe) sa zapína prázdnym súborom `portable.txt` vedľa `HouseIndex.exe`.

### Bezpečný rebuild po zmenách

```powershell
# 1. (voliteľné) Preventívna záloha user dát
Compress-Archive -Path $env:APPDATA\HouseIndex -DestinationPath $HOME\house-index-pre-rebuild.zip

# 2. Rebuild — bezpečné, nestratíš žiadne user data
Remove-Item -Recurse -Force dist, build\HouseIndex, build\house_index
pyinstaller build\house_index.spec --noconfirm --clean
```

### Poznámky k buildu

- `paths.py::data_dir()` detekuje `sys.frozen` a prítomnosť `portable.txt`; frozen bez markeru → AppData.
- `schema.sql` je priamo zabalený do `house_index/db/` cez `Analysis.datas`.
- Zo závislostí sú `PySide6`, `Pillow` a `pydantic` automaticky detekované.

### Pridanie ikony

1. Pripravte `build/app.ico` (256×256).
2. V `build/house_index.spec` odkomentujte `icon=...` riadok v EXE sekcii.

## Release checklist

1. **Bumpni verziu** v troch miestach:
   - `pyproject.toml::version`
   - `src/house_index/__init__.py::__version__`
   - `build/version_info.txt::filevers` a `prodvers`
2. `python -m pytest` — musí prejsť 77+ testov.
3. Manuálny smoke test: `python -m house_index` → pridaj, uprav, zmaž, porovnaj, exportuj zálohu, obnov zálohu.
4. `pyinstaller build/house_index.spec --noconfirm --clean`.
5. Na čistom Windows stroji (VM) otestuj `dist/HouseIndex/HouseIndex.exe` — všetky kroky z `user_guide.md`.
6. Zabal: `Compress-Archive dist\HouseIndex HouseIndex-0.1.0-win64.zip`.
7. Commitni tag `v0.1.0`, pushni.

## Ladenie buildu

Ak `.exe` padne pri štarte:

```powershell
pyinstaller build\house_index.spec --noconfirm --clean --debug all
dist\HouseIndex\HouseIndex.exe
```

Najčastejšie chyby:
- **`ModuleNotFoundError: house_index.ui.XYZ`** — pridaj do `hiddenimports` v `.spec`.
- **`FileNotFoundError: schema.sql`** — overi že je v `datas` v `.spec`.
- **Chýbajúce Qt pluginy** — PyInstaller ich obvykle nájde; ak nie, `pyinstaller --collect-all PySide6`.

## CI (budúcnosť)

Nie je nastavené. Keď bude pripravený GitHub repo, odporúčam:
- GitHub Actions matrix pre `3.11` a `3.12` na Windows.
- `pytest` + `ruff check` + `black --check`.
- Release workflow: tag `v*.*.*` → build → upload `HouseIndex-*.zip` do GitHub Releases.
