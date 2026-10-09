"""10 variants of the service lockup «global-logo.svg | Название сервиса» (Лёв 28.09: «10 вариков сделай»).

Fixed by his earlier edits: only global-logo.svg in one color, service name after a thin vertical line
(«через полосочку аккуратно»), Montserrat, blue palette, no emoji / em-dash / violet.
"""
import os, re, pathlib
SRC = pathlib.Path(__file__).resolve().parent
OUT = SRC.parent / "lockups.html"
fonts = (SRC / "fonts.css").read_text()
paths = re.findall(r'<path d="([^"]+)"', (SRC / "global-logo.svg").read_text())
assert len(paths) == 20
LOGO_SYMBOL = '<symbol id="gg-logo" viewBox="0 0 777 196">' + "".join(f'<path d="{d}"/>' for d in paths) + "</symbol>"

VARIANTS = [
    ("v1", "Классика", "Линия 1 px средней высоты, название жирным серо-синим. То, что сейчас на странице айдентики."),
    ("v2", "Во всю высоту", "Линия на всю высоту логотипа, название полужирным navy. Строже и собраннее."),
    ("v3", "Тонко и легко", "Короткая линия по высоте букв, название обычным весом. Самый спокойный вариант."),
    ("v4", "Голубая линия", "Линия голубым акцентом #009CDC, название navy. Акцент ровно в одном месте."),
    ("v5", "Капс", "Название капсом с разрядкой, как подпись. Коротко и технично."),
    ("v6", "С адресом", "Под названием серый адрес сервиса. Удобно на экранах входа и в письмах."),
    ("v7", "Плотная линия", "Линия 2 px со скруглением, название жирным navy. Заметнее всего."),
    ("v8", "Голубое название", "Название цветом ссылок #0077a8, линия приглушённая. Сервис читается первым."),
    ("v9", "Воздух", "Больше расстояние, название крупнее и легче. Для экранов входа и обложек."),
    ("v10", "В тон логотипу", "Название капсом с широкой разрядкой, эхом надписи GLOBAL GENERATION."),
]
SERVICES = [("АКБ", "akb.global-generations-edu.com"), ("Пульс", "pulse.global-generations-edu.com"),
            ("Кабинет ментора", "cabinet.global-generations-edu.com"), ("Студенческий портал", "students.global-generations-edu.com")]


def lockup(v, name, dom, size="md"):
    return (f'<span class="lk {v} {size}"><svg class="gl" viewBox="0 0 777 196" fill="currentColor" aria-hidden="true"><use href="#gg-logo"/></svg>'
            f'<span class="sep"></span><span class="tx"><span class="nm">{name}</span><span class="dm">{dom}</span></span></span>')


def panel(v):
    light = "".join(f'<div class="row">{lockup(v, n, d)}</div>' for n, d in SERVICES)
    dark = "".join(f'<div class="row">{lockup(v, n, d)}</div>' for n, d in SERVICES)
    return (f'<div class="pair"><div class="box light">{light}</div><div class="box dark">{dark}</div></div>'
            f'<p class="label">В шапке сервиса</p><div class="appbar">{lockup(v, "АКБ", SERVICES[0][1], "sm")}'
            '<span class="tabs"><i class="on">Клиенты</i><i>Порталы</i><i>Выплаты</i><i>Пульс</i></span><span class="ava">ЛА</span></div>'
            f'<p class="label">Мелко: подвал письма, счёт, PDF</p><div class="tiny">{lockup(v, "Студенческий портал", SERVICES[3][1], "xs")}'
            '<span class="tinytext">Global Generation · Москва · Нью-Йорк</span></div>')


css = r"""
:root{--navy:#13445d;--ink:#0f172a;--ink2:#334155;--muted:#64748b;--line:#e2e8f0;--bg:#eef3f9;--sky:#009CDC;--sky-ink:#0077a8}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#e7eff8,#eef3f9);color:var(--ink);font-family:Montserrat,system-ui,sans-serif;font-size:14px;min-height:100vh}
.wrap{max-width:1180px;margin:0 auto;padding:30px 20px 80px}
h1{font-size:28px;font-weight:800;margin:0 0 6px;letter-spacing:-.02em}.sub{color:var(--muted);margin:0 0 18px;font-weight:500;max-width:860px;line-height:1.5}
.vt{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px;position:sticky;top:0;background:#eaf1f8;padding:10px 0;z-index:9}
.vt button{font:600 13px Montserrat,sans-serif;border:1px solid var(--line);background:#fff;color:var(--ink2);padding:8px 13px;border-radius:10px;cursor:pointer}
.vt button.on{background:var(--navy);color:#fff;border-color:var(--navy)}
.panel{display:none}.panel.on{display:block}
.desc{margin:0 0 14px;color:var(--ink2);font-weight:500}
.label{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#94a3b8;margin:22px 0 8px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.box{border-radius:14px;padding:26px 28px;display:flex;flex-direction:column;gap:22px}
.box.light{background:#fff;border:1px solid var(--line)}
.box.dark{background:linear-gradient(150deg,#1a5a7a,#0d2f42)}
.appbar{display:flex;align-items:center;gap:18px;height:64px;padding:0 20px;border-radius:14px;background:rgba(255,255,255,.55);border:1px solid var(--line)}
.appbar .tabs{display:flex;gap:2px;padding:4px;border-radius:12px;background:rgba(19,68,93,.07);margin-left:8px}
.appbar .tabs i{font-style:normal;font-weight:600;font-size:13px;color:#475569;padding:8px 12px;border-radius:9px}
.appbar .tabs i.on{background:#fff;color:var(--navy);box-shadow:0 1px 2px rgba(15,23,42,.1),0 0 0 1px rgba(15,23,42,.06)}
.appbar .ava{margin-left:auto;width:36px;height:36px;border-radius:50%;background:#dbe7f3;color:var(--navy);display:grid;place-items:center;font-weight:700;font-size:12px}
.tiny{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 20px;border-radius:12px;background:#fff;border:1px solid var(--line)}
.tinytext{font-size:11px;color:var(--muted)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden}
.card h3{margin:0;padding:14px 18px 0;font-size:14px;font-weight:800}.card h3 span{color:var(--muted);font-weight:600}
.card .l{padding:18px 18px 16px}.card .d{padding:18px;background:linear-gradient(150deg,#1a5a7a,#0d2f42)}
/* ---- base lockup ---- */
.lk{display:inline-flex;align-items:center;gap:14px;color:var(--navy);white-space:nowrap}
.lk .gl{display:block;height:40px;width:auto;flex:0 0 auto}
.lk .sep{display:block;width:1px;height:26px;background:rgba(19,68,93,.28);flex:0 0 auto}
.lk .tx{display:flex;flex-direction:column;justify-content:center}
.lk .nm{font-weight:700;font-size:18px;color:var(--ink2);line-height:1.15}
.lk .dm{display:none;font-size:11.5px;color:var(--muted);font-weight:500;margin-top:3px}
.dark .lk,.d .lk{color:#fff}.dark .lk .sep,.d .lk .sep{background:rgba(255,255,255,.35)}.dark .lk .nm,.d .lk .nm{color:#fff}.dark .lk .dm,.d .lk .dm{color:#9fc0d3}
.lk.sm .gl{height:28px}.lk.sm .sep{height:20px}.lk.sm .nm{font-size:15px}.lk.sm{gap:11px}
.lk.xs .gl{height:18px}.lk.xs .sep{height:13px}.lk.xs .nm{font-size:11px}.lk.xs{gap:8px}.lk.xs .dm{display:none!important}
/* ---- variants ---- */
.lk.v2 .sep{height:40px;background:rgba(19,68,93,.2)}.lk.v2 .nm{font-weight:600;color:var(--navy)}
.lk.v2.sm .sep{height:28px}.lk.v2.xs .sep{height:18px}
.lk.v3 .sep{height:18px}.lk.v3 .nm{font-weight:500;color:#475569}.lk.v3.sm .sep{height:14px}.lk.v3.xs .sep{height:10px}
.lk.v4 .sep{width:1.5px;background:var(--sky)}.lk.v4 .nm{color:var(--navy)}
.dark .lk.v4 .sep,.d .lk.v4 .sep{background:#5cc3ec}
.lk.v5 .sep{height:22px;background:rgba(19,68,93,.3)}.lk.v5 .nm{font-size:12.5px;text-transform:uppercase;letter-spacing:.14em;color:var(--navy)}
.lk.v5.sm .nm{font-size:11px}.lk.v5.xs .nm{font-size:9px}
.lk.v6 .sep{height:40px;background:rgba(19,68,93,.22)}.lk.v6 .nm{font-size:17px;color:var(--navy)}.lk.v6 .dm{display:block}
.lk.v6.sm .sep{height:28px}.lk.v6.sm .dm{display:none}
.lk.v7 .sep{width:2px;border-radius:2px;height:28px;background:rgba(19,68,93,.35)}.lk.v7 .nm{color:var(--navy)}
.dark .lk.v7 .sep,.d .lk.v7 .sep{background:rgba(255,255,255,.5)}
.lk.v8 .sep{background:rgba(19,68,93,.22)}.lk.v8 .nm{color:var(--sky-ink)}
.dark .lk.v8 .nm,.d .lk.v8 .nm{color:#7fd3f5}
.lk.v9{gap:22px}.lk.v9 .sep{height:30px;background:rgba(19,68,93,.18)}.lk.v9 .nm{font-weight:500;font-size:21px;color:var(--navy)}
.lk.v9.sm{gap:14px}.lk.v9.sm .nm{font-size:16px}.lk.v9.xs{gap:9px}
.lk.v10 .sep{height:30px;background:rgba(19,68,93,.3)}.lk.v10 .nm{font-weight:600;font-size:14px;text-transform:uppercase;letter-spacing:.2em;color:var(--navy)}
.lk.v10.sm .nm{font-size:12px}.lk.v10.xs .nm{font-size:9.5px;letter-spacing:.14em}
/* dark backgrounds win over every variant's light colors */
.dark .lk[class] .nm,.d .lk[class] .nm{color:#fff}
.dark .lk[class] .sep,.d .lk[class] .sep{background:rgba(255,255,255,.35)}
.dark .lk[class] .dm,.d .lk[class] .dm{color:#9fc0d3}
.dark .lk.v4[class] .sep,.d .lk.v4[class] .sep{background:#5cc3ec}
.dark .lk.v7[class] .sep,.d .lk.v7[class] .sep{background:rgba(255,255,255,.5)}
.dark .lk.v8[class] .nm,.d .lk.v8[class] .nm{color:#7fd3f5}
.dark .lk.v3[class] .nm,.d .lk.v3[class] .nm{color:#dbe7f0}
/* context sizes (header, tiny footer) win over each variant's base size */
.lk.sm[class] .nm{font-size:15px}.lk.xs[class] .nm{font-size:11px}
.lk.sm[class] .sep{height:20px}.lk.xs[class] .sep{height:13px}
.lk.v2.sm[class] .sep,.lk.v6.sm[class] .sep{height:28px}.lk.v2.xs[class] .sep,.lk.v6.xs[class] .sep{height:18px}
.lk.v3.sm[class] .sep{height:14px}.lk.v3.xs[class] .sep{height:10px}
.lk.v5.sm[class] .nm{font-size:11px}.lk.v5.xs[class] .nm{font-size:9px}
.lk.v10.sm[class] .nm{font-size:12px}.lk.v10.xs[class] .nm{font-size:9.5px}
.lk.v9.sm[class] .nm{font-size:16px}
@media (max-width:760px){.pair,.grid{grid-template-columns:1fr}h1{font-size:22px}.lk .gl{height:30px}.lk .nm{font-size:15px}.lk .sep{height:22px}
  .appbar .tabs{display:none}.tiny{flex-direction:column;align-items:flex-start}.box{padding:20px}.lk{white-space:normal}}
"""

tabs = '<button data-p="all" class="on">Все 10</button>' + "".join(f'<button data-p="{k}">{i + 1}. {t}</button>' for i, (k, t, _) in enumerate(VARIANTS))
overview = '<section class="panel on" id="p-all"><div class="grid">' + "".join(
    f'<div class="card"><h3>{i + 1}. {t} <span>· {d.split(".")[0]}</span></h3><div class="l">{lockup(k, "АКБ", SERVICES[0][1])}</div>'
    f'<div class="d">{lockup(k, "Студенческий портал", SERVICES[3][1])}</div></div>'
    for i, (k, t, d) in enumerate(VARIANTS)) + "</div></section>"
panels = "".join(f'<section class="panel" id="p-{k}"><p class="desc"><b>{i + 1}. {t}.</b> {d}</p>{panel(k)}</section>'
                 for i, (k, t, d) in enumerate(VARIANTS))
html = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Лого сервиса: 10 вариантов</title><style>{fonts}{css}</style></head><body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{LOGO_SYMBOL}</defs></svg>
<div class="wrap"><h1>Логотип + название сервиса: 10 вариантов</h1>
<p class="sub">Везде один логотип global-logo.svg одним цветом, название сервиса через тонкую линию, Montserrat. Разное: высота и цвет линии, вес и размер названия, капс, адрес под названием, расстояния. Выбери номер, можно «как 4, но капсом как 10».</p>
<div class="vt" id="vt">{tabs}</div>{overview}{panels}</div>
<script>document.getElementById('vt').addEventListener('click',function(e){{var b=e.target.closest('button');if(!b)return;
document.querySelectorAll('.vt button').forEach(function(x){{x.classList.toggle('on',x===b)}});
document.querySelectorAll('.panel').forEach(function(p){{p.classList.toggle('on',p.id==='p-'+b.dataset.p)}});window.scrollTo({{top:0}});}});</script>
</body></html>"""
assert "—" not in html and "googleapis" not in html
OUT.write_text(html)
print(OUT, len(html) // 1024, "KB")
