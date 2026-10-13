"""Render the PNG of the GG ID e-mails (mail clients draw no SVG and block data: URIs, so a letter needs a PNG at a public https address;
the hub copies the kit to /assets/gg-id/):

  gg-id/email/gg-id-pill-3x.png   the GG ID logo, the pill (navy capsule, white GG mark and ID), on a transparent background, 246 x 90 (3x of 82 x 30).
                                  The light card of the letter (gg-id/email-card.html, «Итог», like the invite letter of Infra-AWS #93) shows it at 82 x 30.
                                  Address in the letter: https://id.global-generations-edu.com/assets/gg-id/email/gg-id-pill-3x.png

The pill is the approved file assets/logo/gg-id-pill.svg, drawn as it is (it is never redrawn).

Two older PNGs stay in the kit as they are and are no longer generated, because letters already sent point at their addresses:
gg-id/email/gg-logo-navy-2x.png (the navy logo of Global Generation, which the former letters showed next to the text «ID») and
gg-id/email/gg-id-lockup-2x.png (white «logo | ID» on a navy plate).

Run: uv run --with playwright python src/rasterize_gg_id_email.py
"""
import os
import tempfile
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, 'gg-id')
PILL_SVG = os.path.join(ROOT, 'assets', 'logo', 'gg-id-pill.svg')
PILL_OUT = os.path.join(KIT, 'email', 'gg-id-pill-3x.png')
W, H, SCALE = 82, 30, 3          # css px of the picture in the letter (426.265 : 156 = 2.7326, 82 : 30 = 2.7333) and the pixel ratio of the file

page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{{margin:0;background:transparent}}img{{display:block;width:{W}px;height:{H}px}}</style></head>
<body><img id="pill" src="file://{PILL_SVG}" width="{W}" height="{H}" alt="GG ID"></body></html>"""

os.makedirs(os.path.dirname(PILL_OUT), exist_ok=True)
with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    src = os.path.join(tmp, 'email-pill.html')   # a file:// page may load the SVG from file://
    open(src, 'w', encoding='utf-8').write(page)
    b = p.chromium.launch()
    pg = b.new_page(device_scale_factor=SCALE, viewport={'width': 120, 'height': 60})
    pg.goto('file://' + src)
    pg.wait_for_function("document.getElementById('pill').complete && document.getElementById('pill').naturalWidth > 0")
    pg.locator('#pill').screenshot(path=PILL_OUT, omit_background=True)
    b.close()
png = open(PILL_OUT, 'rb').read()
pw, ph = int.from_bytes(png[16:20], 'big'), int.from_bytes(png[20:24], 'big')
assert (pw, ph) == (W * SCALE, H * SCALE), f'{PILL_OUT} is {pw}x{ph}, expected {W * SCALE}x{H * SCALE}'
print('ok', os.path.relpath(PILL_OUT, ROOT), f'{W}x{H} css px (PNG is {SCALE}x: {pw}x{ph})')
