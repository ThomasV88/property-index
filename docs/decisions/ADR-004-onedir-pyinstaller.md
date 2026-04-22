# ADR-004: PyInstaller onedir (nie onefile)

## Status
Schválené · 2026-04-22

## Kontext
PyInstaller ponúka dva základné režimy:

- **onefile** — jeden `.exe` súbor, pri spustení sa extrahuje do `%TEMP%\_MEIxxxx`.
- **onedir** — `.exe` + adresár s DLL/knižnicami, všetko vedľa seba v `dist/HouseIndex/`.

## Rozhodnutie
**onedir.**

## Dôvody
- **`data/` musí byť perzistentné a vedľa `.exe`.** `paths.app_dir()` používa `sys.executable.parent`. Pri onefile režime by sa `sys.executable` ukázal na `_MEIxxxx` v TEMP a aplikácia by si nezapamätala uložené dáta medzi spustiami.
- **Rýchlejší štart** — onefile má overhead ~1–3 s na extrahovanie pri každom spustení.
- **Menej false-positive v antivírusoch** — onefile je self-extracting archív, čo niektoré AV označujú podozrivo.
- **Jednoduchšie podpisovanie** (v budúcnosti) a patch releases — pri zmene jedného `.pyc` netreba rebuildovať celý archív.
- **Prehľadnejšie pre konkurencionálneho používateľa** — vidí priečinok s `HouseIndex.exe` + `_internal/` + `data/`, dá sa zálohovať copy-paste.

## Dôsledky
- Distribuuje sa celý priečinok (typicky ZIP). Nie je to jeden `.exe`, ale `HouseIndex-<ver>-win64.zip` (~125 MB).
- Užívateľ nesmie premiestniť iba `.exe` bez priečinka — preto v `user_guide.md` zdôrazňujeme *„nechaj priečinok ako je”*.

## Aktualizácia (v0.3.0)

**Pôvodná verzia tohto ADR** odporúčala mať `data/` vedľa `.exe`, ale pri preinstale / rebuilde sa tento priečinok prepisoval a **užívateľské dáta sa strácali** (reálny incident v dev prostredí). Preto sme zmenili default:

- **Default:** dáta idú do `%APPDATA%\HouseIndex\` (Windows štandardný user-data priečinok). Rebuild a update `.exe` sú teraz bezpečné.
- **Portable mód:** ak existuje `portable.txt` vedľa `.exe`, správanie sa vráti k pôvodnému „data vedľa exe". Pre USB kľúče a prenos.
- **Auto-migrácia:** pri prvom štarte novej verzie sa obsah legacy `data/` presunie do AppData.
- **Auto-backup:** 1× denne sa robí ZIP záloha do `data/backups/`, 7-dňová retencia.

Implementácia v `src/house_index/paths.py::is_portable_mode()`, `migrate_legacy_data()` a `services/backup_service.py::auto_backup_on_start()`.
