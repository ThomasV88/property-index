# ADR-001: PySide6 ako Qt wrapper

## Status
Schválené · 2026-04-22

## Kontext
Potrebujeme desktop GUI toolkit pre Python. Hlavné voľby:

- **PySide6** — oficiálny wrapper od Qt Company, LGPL.
- **PyQt6** — starší wrapper od Riverbank Computing, GPL (alebo komerčná licencia).
- **Tkinter** — štandardná knižnica, ale vizuálne obmedzená a nemoderná.
- **Kivy / wxPython** — menej populárne pre klasické desktop aplikácie.

## Rozhodnutie
**PySide6.**

## Dôvody
- **Licencia:** LGPL je priateľskejšia k proprietárnym/uzavretým projektom než GPL. Pre súkromný projekt to nie je blokujúce, ale uľahčuje budúce komerčné zdieľanie.
- **Oficiálny wrapper:** update cadence matches Qt releases.
- **Rozsiahla knižnica widgetov** — `QListView` s custom delegátom presne podporuje kartový layout, `QTableWidget` pre porovnanie, `QThread` pre recompute worker.
- **PyInstaller kompatibilita** dobre overené.

## Dôsledky
- API mierne odlišné od PyQt6 (napr. signals/slots — nie je to 1:1 port).
- Distribúcia musí rešpektovať LGPL — ak vydáme binárku verejne, treba poskytnúť spôsob ako vymeniť PySide6 za novšiu verziu (jednoducho — PyInstaller onedir už toto umožňuje).
