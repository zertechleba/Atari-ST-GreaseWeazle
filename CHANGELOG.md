# Seznam změn

🇨🇿 **Česky** · 🇬🇧 [English](CHANGELOG.en.md)

Číslo verze je v programu (`VERSION` v `st_disketa.py`), dole na stránce a v názvu návodu.
První číslo se mění při velké změně, druhé při každé nové funkci nebo opravě.

## 1.4 – 16. 11. 2026

První zveřejněná verze.

- Číslo verze a licence jsou vidět dole na stránce.
- Přidán samostatný soubor `st_prohlizec.html` pro prohlížení obrazů bez Pythonu.
- Zdroje rozdělené do složky `src/`, sestavení jedním příkazem `python build.py`.
- Návod v PDF česky a anglicky, README, tento seznam změn.
- Pole „Název pro uložení“ je širší.

## 1.3 – 16. 11. 2026

- **Oprava:** když se disketa nepodařila načíst, zůstal zobrazený obsah té předchozí a chyba byla vidět jen dole
  pod stránkou. Teď se otevře záložka „Nečitelná disketa“ s důvodem, výpisem z `gw` a tlačítkem pro nový pokus.
- Hlášení o stavu jsou nahoře pod záhlavím, chyby zvýrazněné.
- Když první stopa nejde přečíst, zkusí se ještě jednou s více opakováními.
- Po kliknutí na načtení se předchozí diskety hned označí jako vyjmuté.
- Výpis GFA BASICu: barevné zvýraznění, čísla řádků, větší písmo, oddělené procedury a seznam „Přejít na …“.

## 1.2 – 16. 11. 2026

- Výpis programů GFA BASIC 3.x (`.GFA`) přímo na stránce, uložení jako `.LST`.
  Jde o převod programu gfalist; výstup souhlasí s originálními výpisy z GFA BASICu.
- Kvůli tomu je program od této verze pod licencí GNU GPL v2.

## 1.1 – 16. 11. 2026

- Nastavení přímo na stránce: cesta ke `gw`, sériový port, mechanika.
- Nastavení se ukládá do souboru `.st_disketa.json` v domovské složce.
- Tlačítko „Otestovat spojení“ (spustí `gw info`).
- Stránka nabízí sériové porty nalezené v počítači.

## 1.0 – 16. 11. 2026

- Čtení diskety přímo z mechaniky přes Greaseweazle: nejdřív adresář, soubor až po kliknutí, celý obraz na požádání.
- Automatické rozpoznání formátu diskety z boot sektoru.
- Uložení souboru, všech souborů jako ZIP, obrazu `.MSA` a `.ST`.
- Prohlížení hotových obrazů `.MSA` a `.ST`: adresář, text, hex, obrázky Degas, NEOchrome a Doodle,
  smazané soubory, procházení po sektorech.
