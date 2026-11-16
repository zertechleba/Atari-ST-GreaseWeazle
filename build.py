#!/usr/bin/env python3
"""Sestavi st_disketa.py a st_prohlizec.html ze zdroju ve slozce src/.

    python build.py

Cislo verze se bere z src/server_template.py (VERSION = "x.y").
"""
import base64
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def read(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def write(name, text):
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


template = read("src", "server_template.py")
version = re.search(r'^VERSION = "([^"]+)"', template, re.M).group(1)
gfa = read("src", "gfa.js").replace("/*@@GFA_TABLES@@*/", read("src", "gfa_tables.js").strip())
with open(os.path.join(HERE, "src", "logo.png"), "rb") as f:
    logo = base64.b64encode(f.read()).decode("ascii")
page = read("src", "page.html")
for mark in ("/*@@GFA_MODULE@@*/", "@@VERSION@@", "@@LOGO@@"):
    assert mark in page, mark
page = page.replace("/*@@GFA_MODULE@@*/", gfa).replace("@@VERSION@@", version).replace("@@LOGO@@", logo)
assert "'''" not in page
write("st_prohlizec.html", page)
write("st_disketa.py", template.replace("@@PAGE@@", page))
print("st_disketa.py a st_prohlizec.html, verze", version)
