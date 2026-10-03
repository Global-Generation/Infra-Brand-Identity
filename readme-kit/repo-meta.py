#!/usr/bin/env python3
"""README specs (Infra-Brand-Identity/readme-kit/specs/*.json) -> /var/www/levauth/repo-meta.json.
The hub and the personal board render every card README-style (title, tagline, badges) from this file,
so a new repo gets the same card face as soon as its spec is committed (skill gg-readme).
Cron (root): */10 * * * * /opt/levauth-refresh/repo-meta.py >> /var/log/levauth-repo-meta.log 2>&1
Only changed specs are downloaded (blob sha cache in /var/cache/levauth-repo-meta).
"""
import base64, json, os, sys, tempfile, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOKEN = Path("/etc/levauth-refresh.token").read_text().strip()
REPO = "Global-Generation/Infra-Brand-Identity"
PREFIX = "readme-kit/specs/"
OUT = Path("/var/www/levauth/repo-meta.json")
CACHE = Path("/var/cache/levauth-repo-meta")


def gh(path):
    req = urllib.request.Request("https://api.github.com" + path, headers={
        "Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "levauth-repo-meta"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    tree = gh(f"/repos/{REPO}/git/trees/main?recursive=1")["tree"]
    specs = [t for t in tree if t["type"] == "blob" and t["path"].startswith(PREFIX) and t["path"].endswith(".json")]
    meta, fetched = {}, 0
    for t in specs:
        c = CACHE / (t["sha"] + ".json")
        if not c.exists():
            blob = gh(f"/repos/{REPO}/git/blobs/{t['sha']}")
            c.write_bytes(base64.b64decode(blob["content"]))
            fetched += 1
        try:
            spec = json.loads(c.read_text(encoding="utf-8"))
        except Exception:
            continue
        name = t["path"][len(PREFIX):-len(".json")]
        meta[name.lower()] = {"repo": name, "title": spec.get("title"), "tagline": spec.get("card_tagline") or spec.get("tagline"),  # card_tagline: строка только для карточек (README не меняется)
                              "badges": spec.get("badges", []), "brand": spec.get("brand")}
    data = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "count": len(meta), "repos": meta}
    fd, tmp = tempfile.mkstemp(dir=str(OUT.parent), prefix=".repo-meta-", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    os.chmod(tmp, 0o644)
    try:
        import pwd, grp
        os.chown(tmp, pwd.getpwnam("www-data").pw_uid, grp.getgrnam("www-data").gr_gid)
    except Exception:
        pass
    os.replace(tmp, OUT)
    print(f"{data['generated_at']} OK {len(meta)} specs ({fetched} fetched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
