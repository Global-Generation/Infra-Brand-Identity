#!/usr/bin/env python3
"""assets/favicons/manifest.json из списка ресурсов SITES в build_favicon_variants.py (без шрифтов).

  uv run --with fonttools --with brotli python src/build_manifest.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_favicon_variants as b  # noqa: E402

ICONS = {"akb": "people", "pulse": "pulse", "cabinet": "briefcase", "legal": "scale", "accounting": "calculator",
         "reporter": "bars", "onboarding": "flag", "levauth": "key", "strategy": "compass", "llm": "coins",
         "production": "clapperboard", "studio": "camera", "scripts": "script", "youtube": "play",
         "infracost": "cloud", "paid": "target", "publisher": "upload", "guide": "book", "crmchats": "chats",
         "team": "org-chart", "preview": "flag"}

rows = [("root", "Global Generation: сайт, вход, PIN-ворота, SSO, письма", "-", "root", "-")]
rows += [(k, n, h, f, r) for k, n, h, f, r, _ in b.SITES if k != "root"]
rows.insert(1, ("pulse", "Пульс (вкладка АКБ)", "hub.*", "internal", "GG-Product-Mentorship-AKB"))
out = []
for key, name, host, fam, repo in rows:
    if key == "site":
        continue
    bg = b.SITE_LIGHT + " > " + b.SITE_NAVY if key == "root" else (
        " > ".join(b.CLIENT_BG["blues"][key]) if fam == "client" else " > ".join(b.INTERNAL_BG["sky"]))
    out.append(dict(key=key, name=name, host=host, repo=repo, family=fam,
                    favicon=f"assets/favicons/{key}.svg",
                    png={px: f"assets/favicons/png/{key}-{px}.png" for px in (32, 180, 192, 512)},
                    ico=f"assets/favicons/ico/{key}.ico",
                    icon=("gg/" + ICONS[key]) if fam == "internal" else None, bg=bg))
out.append(dict(key="mayak", name="Маяк · Джи-джи", family="client", favicon="assets/gigi/gigi-mascot.png",
                note="свой визуал Джи-джи, не менять"))
p = b.ROOT / "assets/favicons/manifest.json"
p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
print(len(out), "entries ->", p)
