"""Render the PNG images of the GG ID e-mails (mail clients draw no SVG and block data: URIs, so a letter needs a PNG at a public
https address; the hub copies the kit to /assets/gg-id/):

  gg-id/email/gg-logo-navy-2x.png   the navy logo on a transparent background, 302 x 76 (2x of 151 x 38). The light card of the
                                    letter (gg-id/email-card.html, «Итог», like the invite letter of Infra-AWS #93) shows it at
                                    111 x 28 next to the text «ID», the letter head at 151 x 38. Address in the letter:
                                    https://id.global-generations-edu.com/assets/gg-id/email/gg-logo-navy-2x.png
  gg-id/email/gg-id-lockup-2x.png   the former navy card: white «logo | ID» on a navy plate (the plate survives the colour inversion
                                    of Gmail on iPhone). Kept for letters that still use it, re-rendered only with --lockup.

The logo comes from the kit sprite (gid-logo), the caption from the kit CSS (.gid-lockup).

Run: uv run --with playwright python src/rasterize_gg_id_email.py [--lockup]
"""
import os
import re
import sys
import tempfile
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, 'gg-id')
LOGO_OUT = os.path.join(KIT, 'email', 'gg-logo-navy-2x.png')
LOCKUP_OUT = os.path.join(KIT, 'email', 'gg-id-lockup-2x.png')
NAVY = '#13445d'

sprite = open(os.path.join(KIT, 'sprite.svg'), encoding='utf-8').read()
logo = re.search(r'<symbol id="gid-logo"[^>]*>.*?</symbol>', sprite, flags=re.S).group(0)

page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="file://{os.path.join(KIT, 'gg-id.css')}">
<style>
  html,body{{margin:0;background:transparent}}
  .plate{{display:inline-flex;padding:6px 8px;border-radius:8px;background:{NAVY}}}
  .plate .gid-lockup{{margin:0;--g-logo:#ffffff;--g-divider:rgba(255,255,255,.35)}}
  .navy{{display:block;width:151px;height:38px;color:{NAVY};fill:currentColor}}
</style></head>
<body><div class="gid-kit" data-theme="dark">
<svg width="0" height="0" style="position:absolute" aria-hidden="true">{logo}</svg>
<div class="plate" id="plate"><div class="gid-lockup"><svg class="gid-logo" viewBox="0 0 777 196"><use href="#gid-logo"/></svg><span class="gid-lockup-name">ID</span></div></div>
<svg class="navy" id="navy" viewBox="0 0 777 196" preserveAspectRatio="xMidYMid meet"><use href="#gid-logo"/></svg>
</div></body></html>"""

os.makedirs(os.path.dirname(LOGO_OUT), exist_ok=True)
with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    src = os.path.join(tmp, 'email-images.html')   # a file:// page may load the kit CSS and fonts from file://
    open(src, 'w', encoding='utf-8').write(page)
    b = p.chromium.launch()
    pg = b.new_page(device_scale_factor=2, viewport={'width': 400, 'height': 160})
    pg.goto('file://' + src)
    pg.evaluate('document.fonts.ready')
    assert pg.evaluate("document.fonts.check('600 16px Montserrat')"), 'Montserrat did not load'
    pg.locator('#navy').screenshot(path=LOGO_OUT, omit_background=True)
    print('ok', os.path.relpath(LOGO_OUT, ROOT), '151x38 css px (PNG is 2x)')
    if '--lockup' in sys.argv:
        box = pg.locator('#plate').bounding_box()
        pg.locator('#plate').screenshot(path=LOCKUP_OUT, omit_background=True)
        print('ok', os.path.relpath(LOCKUP_OUT, ROOT), f'{box["width"]:.0f}x{box["height"]:.0f} css px (PNG is 2x)')
    b.close()
