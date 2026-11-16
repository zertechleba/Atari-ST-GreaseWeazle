# Changelog

🇨🇿 [Česky](CHANGELOG.md) · 🇬🇧 **English**

The version number is in the program (`VERSION` in `st_disketa.py`), at the bottom of the page and in the manual's
file name. The first number changes with a major change, the second with every new feature or fix.

## 1.4 – 16 Nov 2026

First public release.

- Version number and licence are shown at the bottom of the page.
- Added the stand-alone `st_prohlizec.html` for viewing images without Python.
- Sources split into `src/`, built with a single `python build.py`.
- PDF manual in Czech and English, README, this changelog.
- The "Název pro uložení" (name for saving) field is wider.

## 1.3 – 16 Nov 2026

- **Fix:** when a disk could not be read, the previous disk's contents stayed on screen and the error was only
  visible below the page. Now a tab "Nečitelná disketa" (unreadable disk) opens with the reason, the `gw` output
  and a retry button.
- Status messages moved to the top, errors are highlighted.
- If the first track cannot be read, one more attempt is made with more retries.
- Previous disks are marked as removed as soon as a new read starts.
- GFA BASIC listing: syntax colouring, line numbers, larger type, separated procedures and a jump list.

## 1.2 – 16 Nov 2026

- GFA BASIC 3.x programs (`.GFA`) are listed on the page and can be saved as `.LST`.
  This is a port of gfalist; the output matches original listings made by GFA BASIC.
- Because of that the program is licensed under the GNU GPL v2 from this version on.

## 1.1 – 16 Nov 2026

- Settings on the page: path to `gw`, serial port, drive.
- Settings are stored in `.st_disketa.json` in the home folder.
- "Otestovat spojení" (test connection) button, which runs `gw info`.
- The page suggests the serial ports found on the computer.

## 1.0 – 16 Nov 2026

- Reads a floppy straight from the drive through Greaseweazle: directory first, a file when clicked, a full image on request.
- Detects the disk format from the boot sector.
- Saves a file, all files as a ZIP, `.MSA` and `.ST` images.
- Views existing `.MSA` and `.ST` images: directory, text, hex, Degas, NEOchrome and Doodle pictures,
  deleted files, sector browsing.
