#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
st_disketa.py - prohlizec disket Atari ST primo z mechaniky pres Greaseweazle.

Spusteni:
    python st_disketa.py
    python st_disketa.py --gw "C:\\cesta\\ke\\gw.exe" --device COM5 --drive A

Cestu ke gw, port a mechaniku lze nastavit i primo na strance (Nastaveni);
ulozi se do souboru .st_disketa.json v domovske slozce uzivatele.

Program spusti maly webovy server jen pro tento pocitac (127.0.0.1) a otevre
stranku v prohlizeci. Stranka si pres nej nechava cist jen ty stopy diskety,
ktere prave potrebuje: nejdrive adresar, potom vybrany soubor, cely disk az
na pozadani. Samotne cteni dela program "gw" z Greaseweazle Tools.

Vypis souboru GFA BASIC (.GFA) na strance je prevod programu gfalist / SKY,
Copyright (C) 1992-2001 Peter Backes a dalsi (https://github.com/mmuman/gfalist),
ktery je pod licenci GNU GPL verze 2. Pokud tento soubor sirite dal, plati
pro nej jako celek stejna licence (GPL v2), bez jakekoli zaruky.

Potrebuje jen Python 3.8+ a nainstalovane Greaseweazle Tools (gw / gw.exe).
Funguje na Windows i na Linuxu (na Linuxu musi mit uzivatel pravo k seriovemu
portu, obvykle clenstvi ve skupine "dialout").
"""
import argparse
import base64
import glob
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "1.6"

# format -> (pocet stran, sektoru na stopu); vsechny maji 80 cylindru
FORMATS = {
    "atarist.360": (1, 9), "atarist.400": (1, 10), "atarist.440": (1, 11),
    "atarist.720": (2, 9), "atarist.800": (2, 10), "atarist.880": (2, 11),
}
CYLS = 80
TRACK_LINE = re.compile(r"^T(\d+)\.(\d+):\s*(.*)$")
SECTORS = re.compile(r"\((\d+)/(\d+) sectors\)")

CFG = {"gw": None, "gw_text": "", "device": "", "drive": "", "port": 0}
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".st_disketa.json")
DEVICE_RE = re.compile(r"^[A-Za-z0-9_./\\:-]{1,80}$")
DRIVES = ("", "A", "B", "0", "1", "2")


def load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            c = json.load(f)
        return c if isinstance(c, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"gw": CFG["gw_text"], "device": CFG["device"], "drive": CFG["drive"]}, f, indent=1)
        return True
    except OSError:
        return False


def clean_path(text):
    return os.path.expandvars(os.path.expanduser(str(text).strip().strip('"').strip("'").strip()))


def check_gw_path(text):
    """Cesta zadana na strance: soubor gw / gw.exe, nebo slozka, kde lezi. Vraci chybu, nebo None."""
    path = clean_path(text)
    if not path:
        return None
    if os.path.isdir(path):
        if any(os.path.isfile(os.path.join(path, n)) for n in ("gw.exe", "gw")):
            return None
        return "Ve složce %s není gw.exe ani gw." % path
    if not os.path.isfile(path):
        return "Soubor %s neexistuje." % path
    if os.path.basename(path).lower() not in ("gw", "gw.exe"):
        return "Zadejte cestu k souboru gw.exe (nebo gw), případně ke složce, kde leží."
    return None


def list_ports():
    """Seriove porty v systemu (jen jako napoveda pro stranku)."""
    ports = []
    try:
        if os.name == "nt":
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM") as k:
                i = 0
                while True:
                    try:
                        ports.append(str(winreg.EnumValue(k, i)[1]))
                    except OSError:
                        break
                    i += 1
        else:
            ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/cu.usbmodem*")
    except Exception:
        pass
    return sorted(set(ports))


def info():
    gw = CFG["gw"]
    return {"ok": True, "version": VERSION, "gw": bool(gw),
            "gw_cmd": (gw[0] if len(gw) == 1 else "modul greaseweazle v Pythonu") if gw else "",
            "gw_text": CFG["gw_text"], "device": CFG["device"], "drive": CFG["drive"],
            "ports": list_ports(), "config_file": CONFIG_FILE, "formats": sorted(FORMATS)}


def gw_flags():
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if os.name == "nt" else {}


def test_gw():
    if not CFG["gw"]:
        return {"ok": False, "log": "Program gw nebyl nalezen."}
    cmd = list(CFG["gw"]) + ["info"]
    if CFG["device"]:
        cmd.append("--device=" + CFG["device"])
    with DRIVE_LOCK:
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30, **gw_flags())
        except subprocess.TimeoutExpired:
            return {"ok": False, "log": "gw info neodpověděl do 30 sekund."}
        except OSError as e:
            return {"ok": False, "log": "Program gw se nepodařilo spustit: %s" % e}
    log = p.stdout.decode("utf-8", "replace").strip()
    ok = p.returncode == 0 and "firmware" in log.lower() and "not found" not in log.lower()
    return {"ok": ok, "log": log or "(gw nic nevypsal)"}
DRIVE_LOCK = threading.Lock()


def find_gw(explicit):
    """Vrati prikaz (seznam) pro spusteni gw, nebo None."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = []
    if explicit:
        candidates.append(clean_path(explicit))
    if os.environ.get("GW"):
        candidates.append(os.environ["GW"])
    for name in ("gw.exe", "gw"):
        candidates.append(os.path.join(here, name))
    for c in candidates:
        if os.path.isdir(c):
            for name in ("gw.exe", "gw"):
                if os.path.isfile(os.path.join(c, name)):
                    return [os.path.join(c, name)]
        elif os.path.isfile(c):
            return [c]
    found = shutil.which("gw")
    if found:
        return [found]
    if importlib.util.find_spec("greaseweazle") is not None:
        return [sys.executable, "-c",
                "import sys; from greaseweazle.cli import main; sys.argv[0]='gw'; main()"]
    return None


def ranges(nums):
    """[0,1,2,5] -> '0-2,5'"""
    nums = sorted(set(nums))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if i == j else "%d-%d" % (nums[i], nums[j]))
        i = j + 1
    return ",".join(out)


def explain(log):
    """Prelozi nejcastejsi chyby gw do cestiny."""
    low = log.lower()
    if "no index" in low:
        return "V mechanice není disketa, nebo se netočí."
    if "track 0" in low or "track0" in low:
        return "Mechanika nenašla stopu 0. Zkontrolujte kabel a volbu mechaniky (--drive)."
    if "permission denied" in low or "access is denied" in low:
        return "K portu Greaseweazle není přístup. Na Linuxu přidejte uživatele do skupiny dialout; na Windows zavřete jiný program, který port používá."
    if "no greaseweazle" in low or "could not auto-probe" in low or "serialexception" in low or "could not open port" in low:
        return "Greaseweazle nebyl nalezen. Je připojený? Port lze zadat volbou --device."
    return "Čtení selhalo."


def tail(log, n=6):
    lines = [l for l in log.strip().splitlines() if l.strip()]
    return " | ".join(lines[-n:])


def read_tracks(fmt, cyls, heads, retries):
    sides, spt = FORMATS[fmt]
    tlen = spt * 512
    spec = "c=%s:h=%s" % (ranges(cyls), ranges(heads))
    with DRIVE_LOCK, tempfile.TemporaryDirectory(prefix="stdisketa_") as tmp:
        out = os.path.join(tmp, "read.st")
        cmd = list(CFG["gw"]) + ["read", "--format=" + fmt, "--tracks=" + spec, "--retries=%d" % retries]
        if CFG["device"]:
            cmd.append("--device=" + CFG["device"])
        if CFG["drive"]:
            cmd.append("--drive=" + CFG["drive"])
        cmd.append(out)
        flags = gw_flags()
        print("gw read %s %s" % (fmt, spec), flush=True)
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               timeout=1200, **flags)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Čtení trvalo příliš dlouho a bylo ukončeno."}
        except OSError as e:
            return {"ok": False, "error": "Program gw se nepodařilo spustit: %s" % e}
        log = p.stdout.decode("utf-8", "replace")
        data = b""
        if os.path.isfile(out):
            with open(out, "rb") as f:
                data = f.read()
    status = {}
    for line in log.splitlines():
        m = TRACK_LINE.match(line.strip())
        if not m:
            continue
        c, h, rest = int(m.group(1)), int(m.group(2)), m.group(3)
        if rest.startswith("Giving up") or "WARNING" in rest:
            continue
        s = SECTORS.search(rest)
        status[(c, h)] = (int(s.group(1)), int(s.group(2))) if s else (0, spt)
    tracks = []
    for c in sorted(set(cyls)):
        for h in sorted(set(heads)):
            off = (c * sides + h) * tlen
            if (c, h) not in status or len(data) < off + tlen:
                return {"ok": False, "error": explain(log), "detail": tail(log), "log": log}
            good, total = status[(c, h)]
            tracks.append({"c": c, "h": h, "good": good, "total": total,
                           "data": base64.b64encode(data[off:off + tlen]).decode("ascii")})
    return {"ok": True, "tracks": tracks, "log": log}


class Handler(BaseHTTPRequestHandler):
    server_version = "st_disketa/" + VERSION

    def log_message(self, fmt, *args):
        pass

    def _local_only(self):
        allowed = ("127.0.0.1:%d" % CFG["port"], "localhost:%d" % CFG["port"])
        if self.headers.get("Host", "") not in allowed:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin in tuple("http://" + a for a in allowed)

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json")

    def do_GET(self):
        if not self._local_only():
            return self._json(403, {"ok": False, "error": "forbidden"})
        if self.path in ("/", "/index.html"):
            return self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        if self.path == "/api/info":
            return self._json(200, info())
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        if not self._local_only():
            return self._json(403, {"ok": False, "error": "forbidden"})
        if self.path not in ("/api/read", "/api/config", "/api/test"):
            return self._json(404, {"ok": False, "error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(min(n, 65536)).decode("utf-8") or "{}")
        except Exception as e:
            return self._json(400, {"ok": False, "error": "Chybný požadavek: %s" % e})
        if self.path == "/api/test":
            return self._json(200, test_gw())
        if self.path == "/api/config":
            gw_text = str(req.get("gw", "")).strip()
            device = str(req.get("device", "")).strip()
            drive = str(req.get("drive", "")).strip().upper()
            err = check_gw_path(gw_text)
            if not err and device and not DEVICE_RE.match(device):
                err = "Port %s nevypadá jako sériový port (například COM5 nebo /dev/ttyACM0)." % device
            if not err and drive not in DRIVES:
                err = "Neznámá mechanika %s." % drive
            if err:
                return self._json(200, {"ok": False, "error": err})
            CFG["gw_text"], CFG["device"], CFG["drive"] = gw_text, device, drive
            CFG["gw"] = find_gw(gw_text)
            out = info()
            out["saved"] = save_config()
            return self._json(200, out)
        try:
            fmt = req["format"]
            cyls = [int(x) for x in req["cyls"]]
            heads = [int(x) for x in req["heads"]]
            retries = max(0, min(10, int(req.get("retries", 3))))
            if fmt not in FORMATS or not cyls or not heads:
                raise ValueError("bad request")
            if any(c < 0 or c >= CYLS for c in cyls) or any(h < 0 or h >= FORMATS[fmt][0] for h in heads):
                raise ValueError("track out of range")
        except Exception as e:
            return self._json(400, {"ok": False, "error": "Chybný požadavek: %s" % e})
        if not CFG["gw"]:
            return self._json(200, {"ok": False, "error": "Program gw (Greaseweazle) nebyl nalezen. Použijte volbu --gw."})
        self._json(200, read_tracks(fmt, cyls, heads, retries))


def main():
    ap = argparse.ArgumentParser(description="Prohlizec disket Atari ST pres Greaseweazle.")
    ap.add_argument("--gw", help="cesta ke gw / gw.exe (nebo ke slozce, kde lezi)")
    ap.add_argument("--device", help="seriovy port Greaseweazle, napr. COM5 nebo /dev/ttyACM0")
    ap.add_argument("--drive", help="mechanika predana gw (A, B, 0, 1, ...)")
    ap.add_argument("--port", type=int, default=8737, help="port mistniho serveru (vychozi 8737)")
    ap.add_argument("--no-browser", action="store_true", help="neotvirat prohlizec")
    args = ap.parse_args()

    saved = load_config()
    CFG["gw_text"] = args.gw or str(saved.get("gw") or "")
    CFG["device"] = args.device or str(saved.get("device") or "")
    CFG["drive"] = (args.drive or str(saved.get("drive") or "")).upper()
    CFG["gw"] = find_gw(CFG["gw_text"])
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError:
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    CFG["port"] = srv.server_address[1]
    url = "http://127.0.0.1:%d/" % CFG["port"]
    print("st_disketa %s" % VERSION)
    print("gw: %s" % (" ".join(CFG["gw"][:1]) if CFG["gw"] else "NENALEZEN - cestu zadejte na strance v Nastaveni"))
    print("Stranka: %s   (ukonceni: Ctrl+C)" % url, flush=True)
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nKonec.")


PAGE = r'''@@PAGE@@'''

if __name__ == "__main__":
    main()
