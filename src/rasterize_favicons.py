#!/usr/bin/env python3
"""assets/favicons/*.svg -> png/<key>-180.png (apple-touch-icon) и ico/<key>.ico (16/32/48).

SVG рендерит headless Chromium (маски и rgba, как в браузере), ICO собирает ImageMagick.
  uv run --with playwright python src/rasterize_favicons.py
"""
import asyncio
import subprocess
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
FAV = ROOT / "assets/favicons"


async def render(page, svg, px, out):
    await page.set_viewport_size({"width": px, "height": px})
    await page.set_content(
        f'<html><body style="margin:0;background:transparent">'
        f'<img src="data:image/svg+xml;base64,{__import__("base64").b64encode(svg.encode()).decode()}" '
        f'width="{px}" height="{px}" style="display:block"></body></html>')
    await page.wait_for_timeout(30)
    await page.screenshot(path=str(out), omit_background=True)


async def main():
    (FAV / "png").mkdir(exist_ok=True)
    (FAV / "ico").mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page()
        with tempfile.TemporaryDirectory() as tmp:
            for f in sorted(FAV.glob("*.svg")):
                svg, key = f.read_text(), f.stem
                await render(page, svg, 180, FAV / "png" / f"{key}-180.png")
                parts = []
                for px in (16, 32, 48):
                    out = Path(tmp) / f"{key}-{px}.png"
                    await render(page, svg, px, out)
                    parts.append(str(out))
                subprocess.run(["magick", *parts, str(FAV / "ico" / f"{key}.ico")], check=True)
                print(key)
        await b.close()


if __name__ == "__main__":
    asyncio.run(main())
