"""Render the lockup of the e-mail GG ID card: gg-id/email/gg-id-lockup-2x.png (white «logo | ID» on a navy plate).

Mail clients draw no SVG and block data: URIs, so the e-mail card needs a PNG at a public https address. The hub copies
the kit to /assets/gg-id/, so the file lands at https://levauth.global-generations-edu.com/assets/gg-id/email/gg-id-lockup-2x.png
(the address written in gg-id/email-card.html).

The navy plate (#13445d, the colour of the e-mail card) is part of the PNG on purpose: in dark mode Gmail on iPhone inverts
the colours of the card but never images, so the white logo keeps its own navy plate and stays readable. On the normal
navy card the plate is invisible. The logo comes from the kit sprite (gid-logo), the caption from the kit CSS (.gid-lockup).

Run: uv run --with playwright python src/rasterize_gg_id_email.py
"""
import os
import re
import tempfile
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, 'gg-id')
OUT = os.path.join(KIT, 'email', 'gg-id-lockup-2x.png')
NAVY = '#13445d'

sprite = open(os.path.join(KIT, 'sprite.svg'), encoding='utf-8').read()
logo = re.search(r'<symbol id="gid-logo"[^>]*>.*?</symbol>', sprite, flags=re.S).group(0)

page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="file://{os.path.join(KIT, 'gg-id.css')}">
<style>
  html,body{{margin:0;background:transparent}}
  .plate{{display:inline-flex;padding:6px 8px;border-radius:8px;background:{NAVY}}}
  .plate .gid-lockup{{margin:0;--g-logo:#ffffff;--g-divider:rgba(255,255,255,.35)}}
</style></head>
<body><div class="gid-kit" data-theme="dark">
<svg width="0" height="0" style="position:absolute" aria-hidden="true">{logo}</svg>
<div class="plate" id="plate"><div class="gid-lockup"><svg class="gid-logo" viewBox="0 0 777 196"><use href="#gid-logo"/></svg><span class="gid-lockup-name">ID</span></div></div>
</div></body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    src = os.path.join(tmp, 'lockup.html')   # a file:// page may load the kit CSS and fonts from file://
    open(src, 'w', encoding='utf-8').write(page)
    b = p.chromium.launch()
    pg = b.new_page(device_scale_factor=2, viewport={'width': 400, 'height': 120})
    pg.goto('file://' + src)
    pg.evaluate('document.fonts.ready')
    assert pg.evaluate("document.fonts.check('600 16px Montserrat')"), 'Montserrat did not load'
    box = pg.locator('#plate').bounding_box()
    pg.locator('#plate').screenshot(path=OUT, omit_background=True)
    b.close()
print('ok', os.path.relpath(OUT, ROOT), f'{box["width"]:.0f}x{box["height"]:.0f} css px (PNG is 2x)')
