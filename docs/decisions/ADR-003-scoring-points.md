# ADR-003: Bodový systém bez hornej hranice

## Status
Schválené · 2026-04-22

## Kontext
Potrebovali sme vybrať metódu výpočtu indexu. Zvažované:

- **Bodový systém (súčet bodov)** — každé pravidlo pripočíta body, finálny index je suma.
- **Vážený priemer normalizovaných sk贵ores** — každý parameter 0–100 × váha, výsledok je vážený priemer v rozsahu 0–100.
- **Utility funkcia s ideálnymi hodnotami** — každý parameter má „ideálnu” hodnotu, skóre klesá s odchýlkou.

## Rozhodnutie
**Bodový systém (súčet bodov), bez hornej hranice indexu.**

Každé pravidlo má vlastný `max_points`, ktoré sa môže škálovať násobičom (0.0 – 1.0) pri `band_*` pravidlách. Výsledný index je prostý súčet bodov — typicky 0–~120.

## Dôvody
- **Transparentnosť pre užívateľa.** Keď pozerám na číslo 86, viem „tento byt nazbieral 86 bodov z rôznych pravidiel”. Ľahšie pochopiteľné ako „vážený priemer 72 %”.
- **Lepšie modelovanie 'niektoré parametre chýbajú'.** Ak nehnuteľnosť nemá vyplnené všetky polia, dostane nižší index (niektoré pravidlá vrátia 0). To je cielené — vyplnené nehnuteľnosti sa zoradia vyššie, čo motivuje kompletné vypĺňanie.
- **Aditívna kalibrácia.** Ak chcem pridať nový parameter, pridám pravidlo s max_points=X a index sa natiahne o tú konštantu. Pri váženom priemere by som musel reskalibrovať všetky váhy.
- **Kompatibilné s ukázkou príkladu indexu 97** od používateľa v zadaní.

## Dôsledky
- Finálny index nie je percento. Nie všetky nehnuteľnosti sú porovnateľné medzi rôznymi konfiguráciami (po zmene bodovania sa čísla presunú).
- Max celkového bodu sa implicitne mení s pridávaním/odoberaním parametrov. UI v `scoring_methodology.md` zobrazuje orientačný celkový max (~116).
- Alternatíva normalizácie (index / max × 100) sa môže pridať neskôr ako zobrazovací prepočet bez zmeny DB.
