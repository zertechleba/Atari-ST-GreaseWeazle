#!/usr/bin/env python3
"""Sestavi PDF navody z docs/src/*.html (vyzaduje: pip install playwright, playwright install chromium).

    python tools/build_manual.py
"""
import os
import re
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "src", "server_template.py"), encoding="utf-8") as f:
    VERSION = re.search(r'^VERSION = "([^"]+)"', f.read(), re.M).group(1)
JOBS = [("navod.html", "ST_disketa_navod_v%s.pdf", "ST disketa %s – návod", "strana"),
        ("manual.html", "ST_disketa_manual_v%s_EN.pdf", "ST disketa %s – manual", "page")]
FOOT = ('<div style="width:100%%;font-family:DejaVu Sans,Liberation Sans,sans-serif;font-size:7.5pt;color:#5d6a60;'
        'padding:0 17mm;display:flex;justify-content:space-between"><span>%s</span>'
        '<span>%s <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for src, out, title, word in JOBS:
        page = browser.new_page()
        page.goto("file://" + os.path.join(ROOT, "docs", "src", src))
        page.evaluate("v => document.querySelectorAll('.ver').forEach(e => e.textContent = v)", VERSION)
        page.wait_for_load_state("networkidle")
        target = os.path.join(ROOT, "docs", out % VERSION)
        page.pdf(path=target, format="A4", print_background=True, prefer_css_page_size=True,
                 display_header_footer=True, header_template="<span></span>",
                 footer_template=FOOT % (title % VERSION, word))
        print(target)
        page.close()
    browser.close()
