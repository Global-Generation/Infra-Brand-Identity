#!/usr/bin/env python3
"""Фавиконы сервисов GG: 10 вариантов на выбор -> favicons-variants.html.

Буквы = контуры Montserrat 800 из src/fonts.css (SVG-фавикон не грузит шрифты).
Пиктограммы варианта 10 нарисованы под сетку 64 и читаются на 16 px.

  uv run --with fonttools --with brotli python src/build_favicon_variants.py
  ... --out DIR          ещё одна копия страницы (например, на Desktop)
  ... --apply N          записать вариант N в assets/favicons/*.svg
"""
import argparse
import base64
import html
import io
import re
import shutil
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent

NAVY, SKY, LINK, INK, WHITE = "#13445d", "#009CDC", "#0077a8", "#0f172a", "#ffffff"
MAIN = "MAINC"  # цвет «чернил» у вариантов без плитки: navy на светлом, белый на тёмном
FLAT = {"root": NAVY, "mentor": NAVY, "student": SKY, "ops": LINK, "core": INK}
GRAD = {
    "root": ("#1f6a90", "#0d2f42"),
    "mentor": ("#2a7aa3", "#0d2f42"),
    "student": ("#6fd0f5", "#0086c2"),
    "ops": ("#35a6d6", "#085a80"),
    "core": ("#4b5b73", "#0f172a"),
}

# code: короткая подпись (аббревиатуры АКБ и LLM как есть, остальным две буквы)
# code3: первые три буквы, для варианта «Тикер»
SERVICES = [
    dict(key="root", name="Global Generation", note="вход, каталог, письма", contour="root", code="GG", code3="GG"),
    dict(key="akb", name="АКБ", contour="mentor", code="АКБ", code3="АКБ"),
    dict(key="pulse", name="Пульс", contour="mentor", code="ПУ", code3="ПУЛ"),
    dict(key="cabinet", name="Кабинет ментора", contour="mentor", code="КМ", code3="КАБ"),
    dict(key="portal", name="Студенческий портал", contour="student", code="СП", code3="СТУ"),
    dict(key="legal", name="Юротдел", contour="ops", code="ЮР", code3="ЮРО"),
    dict(key="accounting", name="Бухгалтерия", contour="ops", code="БХ", code3="БУХ"),
    dict(key="reporter", name="Репортер", contour="ops", code="РП", code3="РЕП"),
    dict(key="onboarding", name="Онбординг", contour="ops", code="ОН", code3="ОНБ"),
    dict(key="levauth", name="Сервисы", contour="core", code="СЕ", code3="СЕР"),
    dict(key="strategy", name="Стратегия", contour="core", code="СТ", code3="СТР"),
    dict(key="llm", name="LLM-расходы", contour="core", code="LLM", code3="LLM"),
]
BY_KEY = {s["key"]: s for s in SERVICES}
CONTOUR_NAMES = {"mentor": "менторы", "student": "студенты", "ops": "операционка", "core": "ядро"}


def fmt(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


# ---------- шрифт -> контуры ----------

class Type:
    def __init__(self, weight=800, tracking=-0.01):
        css = (ROOT / "src/fonts.css").read_text()
        self.fonts = []
        for data in dict.fromkeys(re.findall(r"base64,([^)]+)\)", css)):
            f = TTFont(io.BytesIO(base64.b64decode(data)))
            if "fvar" in f:
                f = instantiateVariableFont(f, {"wght": weight})
            self.fonts.append((f, f.getBestCmap(), f.getGlyphSet()))
        head = self.fonts[0][0]
        self.cap = head["OS/2"].sCapHeight
        self.upm = head["head"].unitsPerEm
        self.tracking = tracking

    def _glyph(self, ch):
        for f, cmap, gs in self.fonts:
            if ord(ch) in cmap:
                return f, gs, cmap[ord(ch)]
        raise KeyError(ch)

    def _layout(self, text):
        x, items, xs = 0.0, [], []
        for ch in text:
            f, gs, g = self._glyph(ch)
            items.append((gs, g, x))
            bp = BoundsPen(gs)
            gs[g].draw(TransformPen(bp, (1, 0, 0, 1, x, 0)))
            if bp.bounds:
                xs += [bp.bounds[0], bp.bounds[2]]
            x += f["hmtx"][g][0] + self.tracking * self.upm
        return items, min(xs), max(xs)

    def ratio(self, text):
        _, x0, x1 = self._layout(text)
        return (x1 - x0) / self.cap

    def path(self, text, cap, *, cx=32, left=None, cy=32, baseline=None):
        items, x0, x1 = self._layout(text)
        s = cap / self.cap
        L = cx - (x1 - x0) * s / 2 if left is None else left
        B = cy + cap / 2 if baseline is None else baseline
        out = []
        for gs, g, off in items:
            pen = SVGPathPen(gs, ntos=fmt)
            gs[g].draw(TransformPen(pen, (s, 0, 0, -s, L + (off - x0) * s, B)))
            out.append(pen.getCommands())
        return "".join(out)


# ---------- примитивы ----------

MARK_PATHS = re.findall(r'<path d="([^"]+)"', (ROOT / "assets/logo/gg-mark.svg").read_text())
LEGACY = ROOT / "src/legacy-favicons"  # фавиконы до 07.10 (градиент + lucide), для вкладки «Сейчас»


def mark(cx, cy, w, color):
    s = w / 30.4688
    tx, ty = cx - 19.2344 * s, cy - 19.0769 * s
    paths = "".join(f'<path d="{d}"/>' for d in MARK_PATHS)
    return f'<g transform="translate({fmt(tx)} {fmt(ty)}) scale({s:.4f})" fill="{color}">{paths}</g>'


def svg(inner, defs=""):
    d = f"<defs>{defs}</defs>" if defs else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{d}{inner}</svg>'


def tile(fill, rx=14):
    return f'<rect width="64" height="64" rx="{rx}" fill="{fill}"/>'


def rr(x, y, w, h, r):
    return (f"M{x + r} {y}H{x + w - r}A{r} {r} 0 0 1 {x + w} {y + r}V{y + h - r}"
            f"A{r} {r} 0 0 1 {x + w - r} {y + h}H{x + r}A{r} {r} 0 0 1 {x} {y + h - r}"
            f"V{y + r}A{r} {r} 0 0 1 {x + r} {y}Z")


def circ(cx, cy, r):
    return f"M{cx - r} {cy}A{r} {r} 0 1 0 {cx + r} {cy}A{r} {r} 0 1 0 {cx - r} {cy}Z"


def grad(contour):
    a, b = GRAD[contour]
    return (f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>')


# ---------- пиктограммы (вариант 10) ----------

def pictogram(key, m, acc=SKY):
    if key == "root":
        return mark(32, 32, 58, m), ""
    if key == "akb":
        front = "M4 58V50A14 14 0 0 1 18 36H28A14 14 0 0 1 42 50V58Z"
        defs = ('<mask id="k"><rect width="64" height="64" fill="#fff"/>'
                f'<circle cx="23" cy="23" r="14" fill="#000"/>'
                f'<path d="{front}" fill="#000" stroke="#000" stroke-width="7" stroke-linejoin="round"/></mask>')
        back = (f'<g mask="url(#k)" fill="{acc}"><circle cx="43" cy="19" r="9"/>'
                '<path d="M30 54V45A12 12 0 0 1 42 33H48A12 12 0 0 1 60 45V54Z"/></g>')
        return back + f'<g fill="{m}"><circle cx="23" cy="23" r="10.5"/><path d="{front}"/></g>', defs
    if key == "pulse":
        return (f'<path d="M5 34H15L22 16L33 48L40 34H45" fill="none" stroke="{m}" stroke-width="7" '
                f'stroke-linecap="round" stroke-linejoin="round"/><circle cx="56" cy="34" r="6" fill="{acc}"/>'), ""
    if key == "cabinet":
        return (f'<path d="M23 20V14A4 4 0 0 1 27 10H37A4 4 0 0 1 41 14V20" fill="none" stroke="{m}" stroke-width="6"/>'
                f'<path d="{rr(6, 19, 52, 37, 8)}" fill="{m}"/><path d="{rr(27, 32, 10, 9, 2)}" fill="{acc}"/>'), ""
    if key == "portal":
        return (f'<path d="M32 9L62 23L32 37L2 23Z" fill="{m}"/>'
                f'<path d="M14 31.5L32 40L50 31.5V44C50 50 42 54.5 32 54.5C22 54.5 14 50 14 44Z" fill="{m}"/>'
                f'<path d="M56 25V41" stroke="{acc}" stroke-width="3.5" stroke-linecap="round"/>'
                f'<circle cx="56" cy="45" r="4.5" fill="{acc}"/>'), ""
    if key == "legal":
        return (f'<g fill="{m}"><path d="{rr(29.5, 12, 5, 40, 1)}"/><path d="{rr(17, 51, 30, 6, 3)}"/>'
                f'<path d="{rr(8, 13, 48, 5.5, 2.75)}"/><circle cx="32" cy="10" r="4.5"/></g>'
                f'<path d="M16 18L9 37M16 18L23 37M48 18L41 37M48 18L55 37" fill="none" stroke="{m}" stroke-width="2.5" stroke-linecap="round"/>'
                f'<path d="M4 37H28A12 12 0 0 1 4 37ZM36 37H60A12 12 0 0 1 36 37Z" fill="{acc}"/>'), ""
    if key == "accounting":
        keys = "".join(rr(18 + 11 * i, 30 + 10 * j, 7, 6, 1.5) for j in range(3) for i in range(3))
        return (f'<path d="{rr(12, 4, 40, 56, 8)}{keys}" fill="{m}" fill-rule="evenodd"/>'
                f'<path d="{rr(18, 10, 28, 14, 3)}" fill="{acc}"/>'), ""
    if key == "reporter":
        return (f'<path d="{rr(6, 34, 14, 24, 3)}{rr(25, 22, 14, 36, 3)}" fill="{m}"/>'
                f'<path d="{rr(44, 8, 14, 50, 3)}" fill="{acc}"/>'), ""
    if key == "onboarding":
        return (f'<path d="{rr(11, 6, 6, 54, 3)}" fill="{m}"/>'
                f'<path d="M17 9H53L45 21L53 33H17Z" fill="{acc}"/>'), ""
    if key == "levauth":
        return (f'<path d="{circ(23, 23, 17)}{circ(23, 23, 8.5)}" fill="{m}" fill-rule="evenodd"/>'
                f'<path d="M33 33L55 55M44 44L38.5 49.5M51 51L45.5 56.5" fill="none" stroke="{m}" stroke-width="7.5" stroke-linecap="round"/>'
                f'<circle cx="23" cy="23" r="4.5" fill="{acc}"/>'), ""
    if key == "strategy":
        return (f'<path d="{circ(32, 32, 29)}{circ(32, 32, 23)}" fill="{m}" fill-rule="evenodd"/>'
                f'<path d="M45 19L36.95 36.95L27.05 27.05Z" fill="{acc}"/>'
                f'<path d="M19 45L27.05 27.05L36.95 36.95Z" fill="{m}"/>'), ""
    if key == "sat":  # лист теста и карандаш
        lines = rr(17, 16, 20, 4.5, 2.25) + rr(17, 26, 20, 4.5, 2.25) + rr(17, 36, 12, 4.5, 2.25)
        return (f'<path d="{rr(9, 6, 36, 50, 7)}{lines}" fill="{m}" fill-rule="evenodd"/>'
                f'<path d="M37 53L55 35" stroke="{acc}" stroke-width="10" stroke-linecap="round"/>'), ""
    if key == "ielts":  # реплика с тремя точками
        dots = circ(18, 26, 3.6) + circ(30, 26, 3.6) + circ(42, 26, 3.6)
        return (f'<path d="{rr(4, 8, 52, 36, 11)}{dots}" fill="{m}" fill-rule="evenodd"/>'
                f'<path d="M15 40L12 57L30 40Z" fill="{m}"/>'
                f'<circle cx="54" cy="50" r="7" fill="{acc}"/>'), ""
    if key == "apply":  # анкета на планшете
        rows = rr(20, 27, 24, 4.5, 2.25) + rr(20, 37, 24, 4.5, 2.25) + rr(20, 47, 15, 4.5, 2.25)
        return (f'<path d="{rr(11, 9, 42, 52, 8)}{rows}" fill="{m}" fill-rule="evenodd"/>'
                f'<path d="{rr(22, 3, 20, 12, 4)}" fill="{acc}"/>'), ""
    if key == "deck":  # экран презентации с графиком
        bars = rr(15, 26, 7, 10, 1.5) + rr(28, 18, 7, 18, 1.5) + rr(41, 22, 7, 14, 1.5)
        return (f'<path d="{rr(4, 6, 56, 38, 6)}{bars}" fill="{m}" fill-rule="evenodd"/>'
                f'<path d="M32 44V56M20 58H44" fill="none" stroke="{m}" stroke-width="5" stroke-linecap="round"/>'), ""
    if key == "llm":
        defs = '<mask id="c"><rect width="64" height="64" fill="#fff"/><circle cx="40" cy="38" r="22" fill="#000"/></mask>'
        return (f'<circle cx="24" cy="26" r="18" fill="{m}" mask="url(#c)"/>'
                f'<circle cx="40" cy="38" r="18" fill="{acc}"/>'
                f'<circle cx="40" cy="38" r="10" fill="none" stroke="{WHITE}" stroke-opacity=".55" stroke-width="3"/>'), defs
    raise KeyError(key)


# ---------- 10 вариантов ----------

def build_variants(T):
    codes = [s["code"] for s in SERVICES if s["key"] != "root"]
    codes3 = [s["code3"] for s in SERVICES if s["key"] != "root"]

    def caps(cap, max_w, group=codes):
        out = {}
        for n in sorted({len(c) for c in group}):
            r = max(T.ratio(c) for c in group if len(c) == n)
            out[n] = min(cap, max_w / r)
        if 3 in out and 2 in out:
            out[3] = min(out[3], out[2])
        return out

    def letters(code, color, cs, **kw):
        return f'<path fill="{color}" d="{T.path(code, cs[len(code)], **kw)}"/>'

    c1 = caps(24, 44)
    c3 = caps(22, 40)
    c4 = caps(22, 54, codes3)
    c5 = caps(34, 62)
    c6 = caps(22, 40)
    c7 = caps(20, 44)
    c9 = caps(9.5, 19)

    def v_now(s, m):
        return (LEGACY / f"{s['key']}.svg").read_text().strip()

    def v1(s, m):
        body = mark(32, 32, 44, WHITE) if s["key"] == "root" else letters(s["code"], WHITE, c1)
        return svg(tile(NAVY) + body)

    def v2(s, m):
        body = mark(32, 32, 44, WHITE) if s["key"] == "root" else letters(s["code"], WHITE, c1)
        return svg(tile("url(#g)") + body, grad(s["contour"]))

    def v3(s, m):
        bg = f'<circle cx="32" cy="32" r="32" fill="{FLAT[s["contour"]]}"/>'
        body = mark(32, 32, 42, WHITE) if s["key"] == "root" else letters(s["code"], WHITE, c3)
        return svg(bg + body)

    def v4(s, m):
        body = mark(32, 32, 48, WHITE) if s["key"] == "root" else letters(s["code3"], WHITE, c4)
        return svg(tile(FLAT[s["contour"]], 9) + body)

    def v5(s, m):
        body = mark(32, 32, 60, m) if s["key"] == "root" else letters(s["code"], m, c5)
        return svg(body)

    def v6(s, m):
        col = FLAT[s["contour"]]
        frame = f'<rect x="2.5" y="2.5" width="59" height="59" rx="12" fill="{WHITE}" stroke="{col}" stroke-width="5"/>'
        body = mark(32, 32, 40, NAVY) if s["key"] == "root" else letters(s["code"], NAVY, c6)
        return svg(frame + body)

    def v7(s, m):
        acc = f'<path d="{rr(43, 9, 12, 12, 2)}" fill="{SKY}"/>'
        if s["key"] == "root":
            body = mark(25, 42, 32, WHITE)
        else:
            body = letters(s["code"], WHITE, c7, left=9, baseline=55)
        return svg(tile(NAVY, 8) + acc + body)

    def v8(s, m):
        clip = '<clipPath id="t"><rect width="64" height="64" rx="14"/></clipPath>'
        if s["key"] == "root":
            body = mark(40, 34, 84, WHITE)
        else:
            body = f'<path fill="{WHITE}" d="{T.path(s["code"], 44, left=7, baseline=60)}"/>'
        return svg(tile(FLAT[s["contour"]]) + f'<g clip-path="url(#t)">{body}</g>', clip)

    def v9(s, m):
        if s["key"] == "root":
            return svg(tile(NAVY) + mark(32, 32, 46, WHITE))
        badge = f'<circle cx="46" cy="46" r="15.5" fill="{SKY}" stroke="{NAVY}" stroke-width="4"/>'
        return svg(tile(NAVY) + mark(26, 26, 38, WHITE) + badge + letters(s["code"], WHITE, c9, cx=46, cy=46))

    def v10(s, m):
        body, defs = pictogram(s["key"], m)
        return svg(body, defs)

    return [
        dict(n=0, slug="now", title="Сейчас", fn=v_now, adaptive=False,
             idea="Градиентная плитка и тонкая иконка lucide. На 16 px линии иконки сливаются, все сервисы похожи на шаблон.",
             plus="", minus=""),
        dict(n=1, slug="mono", title="Монограмма", fn=v1, adaptive=False,
             idea="Плоская navy-плитка, белые буквы сервиса жирным Montserrat. Строго и корпоративно, как пространства в Notion и Linear.",
             plus="читается на 16 px, одна семья с логотипом", minus="все плитки одного цвета, различаешь только буквами"),
        dict(n=2, slug="grad", title="Градиент + буквы", fn=v2, adaptive=False,
             idea="Градиенты контуров оставляем, иконку меняем на буквы. Быстрый ответ на вопрос, что бесит: иконка или плитка.",
             plus="минимальная правка, контуры различимы по цвету", minus="градиент на 16 px всё равно сереет"),
        dict(n=3, slug="circles", title="Круги", fn=v3, adaptive=False,
             idea="Круг цвета контура и буквы. Менторы navy, студенты голубой, операционка синий, ядро почти чёрный. Как аватарки в мессенджере.",
             plus="группы различаются цветом с первого взгляда", minus="круг выглядит мельче квадрата в той же клетке"),
        dict(n=4, slug="ticker", title="Тикер", fn=v4, adaptive=False,
             idea="Три буквы во всю ширину, как биржевой тикер или код аэропорта: АКБ, БУХ, СТР. Плоский цвет контура, углы жёстче.",
             plus="самый информативный, слово узнаётся целиком", minus="на 16 px буквы мелкие, нужен Retina"),
        dict(n=5, slug="bare", title="Без плитки", fn=v5, adaptive=True,
             idea="Только буквы, без фона. В светлой теме navy, в тёмной белые: SVG переключается сам.",
             plus="самый лёгкий и крупный, ничего лишнего", minus="без плитки теряется ощущение «приложения»"),
        dict(n=6, slug="outline", title="Обводка", fn=v6, adaptive=False,
             idea="Белая плитка с рамкой цвета контура, буквы navy. Спокойно на светлой панели, ярко на тёмной.",
             plus="светлый, аккуратный, контур виден по рамке", minus="на светлой панели белый фон почти сливается"),
        dict(n=7, slug="swiss", title="Швейцарский", fn=v7, adaptive=False,
             idea="Буквы прижаты в левый нижний угол, голубой квадрат справа сверху. Сетка и акцент как в швейцарской графике.",
             plus="фирменный голубой на каждой вкладке, выглядит дизайнерски", minus="буквы меньше, чем в монограмме"),
        dict(n=8, slug="crop", title="Крупный срез", fn=v8, adaptive=False,
             idea="Огромные буквы, обрезанные краем плитки: видна первая буква и кусок второй. Цвет контура.",
             plus="самый смелый, лучше всего запоминается", minus="СЕ и СТ отличаются только краем второй буквы"),
        dict(n=9, slug="badge", title="Знак GG + метка", fn=v9, adaptive=False,
             idea="На каждой вкладке знак GG, сервис = голубая метка с буквами в углу, как бейдж уведомления.",
             plus="бренд первым, все вкладки сразу «наши»", minus="на 16 px метку не прочесть, вкладки различаются плохо"),
        dict(n=10, slug="pict", title="Свои пиктограммы", fn=v10, adaptive=True,
             idea="Если смысловые значки всё же нужны: свои, толстые, залитые, navy и голубой акцент, без плитки. Не lucide, нарисованы под 16 px.",
             plus="смысл виден без букв", minus="значки всё равно надо учить, рисуем на каждый новый сервис"),
    ]


# ---------- вариант 9 с иконками: светлые палитры без navy/голубого ----------

GRAPHITE, HAIR = "#18181B", "#E4E4E7"
INV = "INVC"  # цвет иконки на метке у варианта без плитки: белый на светлом, графит на тёмном
CONTOUR_COL = {"mentor": "#F76B15", "student": "#2F9E62", "ops": "#3E63DD", "core": "#27272A"}
SERVICE_COL = {
    "akb": "#F76B15", "pulse": "#E5484D", "cabinet": "#64748B", "portal": "#06A5C9",
    "legal": "#A0703C", "accounting": "#2F9E62", "reporter": "#3E63DD", "onboarding": "#D49B00",
    "levauth": "#27272A", "strategy": "#0F9488", "llm": "#6BA80F",
}


def rgba(hex_color, a):
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def v9_icons(p):
    """Знак GG слева сверху, круглая метка с иконкой справа снизу, без пересечения."""
    def fn(s, m):
        ink = GRAPHITE if m == NAVY else m
        inv = {NAVY: WHITE, WHITE: GRAPHITE, MAIN: INV}[m]
        mark_col = ink if p["mark"] == "ink" else p["mark"]
        parts = []
        if p.get("tile"):
            stroke = f' stroke="{p["border"]}" stroke-width="1.5"' if p.get("border") else ""
            parts.append(f'<rect x=".75" y=".75" width="62.5" height="62.5" rx="13.5" fill="{p["tile"]}"{stroke}/>')
        if s["key"] == "root":
            parts.append(mark(32, 32, 40, mark_col))
            return svg("".join(parts))
        bc = p["badge"](s)
        badge, icon = (ink, inv) if bc == "ink" else (bc, WHITE)
        acc = icon if icon == INV else rgba(icon, 0.62)
        body, defs = pictogram(s["key"], icon, acc)
        k, c = 21 / 64, 45.5
        parts.append(mark(19, 20, 30, mark_col))
        parts.append(f'<circle cx="{c}" cy="{c}" r="17" fill="{badge}"/>')
        parts.append(f'<g transform="translate({c - 32 * k:.2f} {c - 32 * k:.2f}) scale({k:.4f})">{body}</g>')
        return svg("".join(parts), defs)
    return fn


def build_v9_icons(variants):
    white = dict(tile=WHITE, border=HAIR, mark=GRAPHITE)
    same = "все метки одного цвета, сервис различаешь по иконке"
    return [
        dict(variants[9], n=0, label="9", slug="v9", title="Исходный 9"),
        dict(n=1, slug="mono", title="Чёрно-белый", fn=v9_icons(dict(white, badge=lambda s: GRAPHITE)), adaptive=False,
             idea="Белая плитка, графитовый знак GG, чёрная метка с белой иконкой. Чисто и строго, как у Apple и Vercel.",
             plus="самый чистый, ничего лишнего", minus=same),
        dict(n=2, slug="orange", title="Оранжевый", fn=v9_icons(dict(white, badge=lambda s: "#F76B15")), adaptive=False,
             idea="Белая плитка, графитовый знак, оранжевая метка. Один тёплый акцент на всех сервисах.",
             plus="живой акцент, вкладки GG видно сразу", minus=same),
        dict(n=3, slug="green", title="Зелёный", fn=v9_icons(dict(white, badge=lambda s: "#2F9E62")), adaptive=False,
             idea="Белая плитка, графитовый знак, зелёная метка. Спокойный свежий акцент.",
             plus="спокойно, не спорит с интерфейсом", minus=same),
        dict(n=4, slug="coral", title="Коралл", fn=v9_icons(dict(white, badge=lambda s: "#FF6B5B")), adaptive=False,
             idea="Белая плитка, графитовый знак, коралловая метка. Мягче красного, светлее оранжевого.",
             plus="самый лёгкий из цветных", minus="рядом с алертами похож на цвет ошибки"),
        dict(n=5, slug="contour", title="По контурам", fn=v9_icons(dict(white, badge=lambda s: CONTOUR_COL[s["contour"]])), adaptive=False,
             idea="Цвет метки = контур: менторы оранжевый, студенты зелёный, операционка синий, ядро графит.",
             plus="группы сервисов читаются по цвету", minus="четыре цвета, чуть пестрее"),
        dict(n=6, slug="each", title="Каждому свой", fn=v9_icons(dict(white, badge=lambda s: SERVICE_COL[s["key"]])), adaptive=False,
             idea="У каждого сервиса свой цвет метки, как у приложений Google. Плитка и знак общие.",
             plus="на 16 px различаешь по цвету, даже если иконку не видно", minus="самый пёстрый"),
        dict(n=7, slug="bare", title="Без плитки", fn=v9_icons(dict(mark="ink", badge=lambda s: "ink")), adaptive=True, ink=GRAPHITE,
             idea="Только знак и метка, без фона: графит на светлом, белые на тёмном, иконка на метке наоборот.",
             plus="самый лёгкий", minus="без плитки меньше похоже на приложение"),
    ]


# ---------- клиентские GG = версии фавикона сайта, внутренние = тёмная плитка ----------
# SAT и IELTS теперь Aura (отдельный бренд), сюда не входят. Маяк остаётся с Джи-джи.

CLIENT_SERVICES = [
    dict(key="site", name="Сайт GG", note="global-generations.com", contour="student", client=True),
    dict(key="portal", name="Студенческий портал", note="кабинет студента", contour="student", client=True),
    dict(key="apply", name="Анкета", note="apply.*, после оплаты", contour="student", client=True),
    dict(key="deck", name="Презентация клиенту", note="/d/, после консультации", contour="student", client=True),
]
INTERNAL_SERVICES = [s for s in SERVICES if s["key"] != "portal"]
ALL_BY_KEY = {**BY_KEY, **{s["key"]: s for s in CLIENT_SERVICES}}
SITE_SVG = (ROOT / "assets/logo/gg-mark.svg").read_text().strip()  # = фавикон global-generations.com
SITE_LIGHT, SITE_NAVY, MK_NAVY = "#3D6488", "#1F3053", "#12284C"
DARK_TILE, DARK_LINE = GRAPHITE, "#3F3F46"
DARK_TYPE = {"mentor": "#F76B15", "ops": "#3E63DD", "core": WHITE, "student": "#2F9E62"}


def site_tile():
    defs = (f'<radialGradient id="sg" cx="32" cy="32" r="32" gradientUnits="userSpaceOnUse">'
            f'<stop stop-color="{SITE_LIGHT}"/><stop offset="1" stop-color="{SITE_NAVY}"/></radialGradient>')
    return '<rect width="64" height="64" rx="14.8" fill="url(#sg)"/>', defs


def badge(key, cx, cy, r, fill, icon, k, ring=None):
    body, defs = pictogram(key, icon, rgba(icon, 0.55))
    ring_attr = f' stroke="{ring}" stroke-width="3.5"' if ring else ""
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{ring_attr}/>'
            f'<g transform="translate({cx - 32 * k:.2f} {cy - 32 * k:.2f}) scale({k:.4f})">{body}</g>'), defs


def internal_dark(s, m):
    """Внутренние: графитовая плитка, белый знак GG, метка цвета типа (ядро белое, иконка графит)."""
    t = (f'<rect x=".75" y=".75" width="62.5" height="62.5" rx="13.5" fill="{DARK_TILE}" '
         f'stroke="{DARK_LINE}" stroke-width="1.5"/>')
    if s["key"] == "root":
        return svg(t + mark(32, 32, 40, WHITE))
    c = DARK_TYPE[s["contour"]]
    b, defs = badge(s["key"], 45.5, 45.5, 17, c, GRAPHITE if c == WHITE else WHITE, 21 / 64)
    return svg(t + mark(19, 20, 30, WHITE) + b, defs)


def client_version(kind, everyone=False):
    """everyone=True: внутренние тоже как клиентские (выбор Лёва 07.10: «знак меньше + метка» для всех)."""
    def fn(s, m):
        if s["key"] == "root":
            return SITE_SVG if everyone else internal_dark(s, m)
        if not s.get("client") and not everyone:
            return internal_dark(s, m)
        if s["key"] == "site" or kind == "same":
            return SITE_SVG
        t, defs = site_tile()
        if kind == "small":
            b, bd = badge(s["key"], 45.5, 45.5, 17, WHITE, MK_NAVY, 21 / 64)
            return svg(t + mark(19, 20, 30, WHITE) + b, defs + bd)
        b, bd = badge(s["key"], 49, 49, 13.5, WHITE, MK_NAVY, 17 / 64, ring=SITE_NAVY)  # "over"
        return svg(t + mark(31.6, 31.3, 50, WHITE) + b, defs + bd)
    return fn


def build_client():
    return [
        dict(n=1, slug="small", title="Знак меньше + метка", fn=client_version("small"), adaptive=False,
             idea="Клиентские = фавикон сайта: тот же navy-градиент и белый знак, знак чуть меньше слева сверху, в углу белая метка с иконкой продукта. Та же сетка, что у внутренних.",
             plus="продукт читается, родство с сайтом очевидно", minus="знак мельче, чем на сайте"),
        dict(n=2, slug="over", title="Знак как на сайте + метка", fn=client_version("over"), adaptive=False,
             idea="Фавикон сайта без изменений, белая метка с иконкой продукта лежит на правом нижнем углу.",
             plus="максимально как на сайте", minus="метка закрывает край знака"),
        dict(n=3, slug="same", title="Один фавикон сайта", fn=client_version("same"), adaptive=False,
             idea="Все клиентские страницы просто с фавиконом сайта, без меток.",
             plus="полный бренд, ноль новых картинок", minus="вкладки клиентских продуктов не различаются"),
    ]


def client_cards(v):
    tabs = [("site", "Global Generation"), ("portal", "Мой кабинет · GG"), ("apply", "Анкета · GG"),
            ("accounting", "Бухгалтерия"), ("deck", "Презентация · GG"), ("onboarding", "Онбординг"), ("gigi", "Маяк · Джи-джи")]
    return (f'<div class="card"><h3>Во вкладках Chrome <span>клиентские и внутренние вперемешку, 16 px</span></h3>'
            f'{chrome(v, False, ["root", "akb", "legal"], tabs)}{chrome(v, True, ["root", "akb", "legal"], tabs)}</div>'
            f'<div class="card"><h3>Клиентские <span>версии фавикона global-generations.com; Маяк с Джи-джи</span></h3>{grid(v, CLIENT_SERVICES)}</div>'
            f'<div class="card"><h3>Внутренние <span>тёмная плитка: менторы оранжевый, операционка синий, ядро белый</span></h3>{grid(v, INTERNAL_SERVICES)}</div>'
            f'<div class="card"><h3>Размеры <span>Портал, Анкета, АКБ: 16, 20, 24, 32, 48, 64</span></h3>{sizes(v, ("portal", "apply", "akb"))}</div>')


def render(v, s, dark=False):
    return v["fn"](s, WHITE if dark else NAVY)


def export(v, s):
    """Самостоятельный SVG-файл; у вариантов без плитки цвет переключается по теме."""
    out = v["fn"](s, MAIN)
    if MAIN in out or INV in out:
        ink = v.get("ink", NAVY)
        out = (out.replace(f'fill="{MAIN}"', 'class="f"').replace(f'stroke="{MAIN}"', 'class="s"')
               .replace(f'fill="{INV}"', 'class="i"').replace(f'stroke="{INV}"', 'class="j"'))
        style = (f"<style>.f{{fill:{ink}}}.s{{stroke:{ink}}}.i{{fill:#fff}}.j{{stroke:#fff}}"
                 f"@media (prefers-color-scheme:dark){{.f{{fill:#fff}}.s{{stroke:#fff}}.i{{fill:{ink}}}.j{{stroke:{ink}}}}}</style>")
        out = out.replace('viewBox="0 0 64 64">', 'viewBox="0 0 64 64">' + style, 1)
    return out


# ---------- страница ----------

_uid = [0]


def inline(svg_text, size):
    """Инлайн-SVG: id уникальные на всю страницу (иначе градиенты/маски разных иконок путаются)."""
    _uid[0] += 1
    sfx = f"-{_uid[0]}"
    ids = re.findall(r'id="([^"]+)"', svg_text)
    for i in ids:
        svg_text = svg_text.replace(f'id="{i}"', f'id="{i}{sfx}"').replace(f"url(#{i})", f"url(#{i}{sfx})")
    return svg_text.replace("<svg ", f'<svg width="{size}" height="{size}" aria-hidden="true" ', 1)


X_ICON = ('<svg class="x" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
          'stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>')
PINNED = ["root", "pulse", "legal"]
OPEN_TABS = [("akb", "АКБ - Маяк"), ("gigi", "Маяк · Джи-джи"), ("accounting", "Бухгалтерия"),
             ("strategy", "Стратегия"), ("llm", "LLM-расходы"), ("onboarding", "Онбординг")]


def chrome(v, dark, pinned=PINNED, open_tabs=OPEN_TABS):
    def fav(key):
        if key == "gigi":
            return '<span class="fav gigi"></span>'
        return f'<span class="fav">{inline(render(v, ALL_BY_KEY[key], dark), 16)}</span>'

    tabs = [f'<div class="t pin" title="{ALL_BY_KEY[k]["name"]}">{fav(k)}</div>' for k in pinned]
    for i, (k, title) in enumerate(open_tabs):
        on = " on" if i == 0 else ""
        tabs.append(f'<div class="t{on}">{fav(k)}<span class="tt">{html.escape(title)}</span>{X_ICON}</div>')
    theme = "d" if dark else "l"
    label = "Тёмная тема" if dark else "Светлая тема"
    return (f'<div class="chrome {theme}" aria-label="{label}"><div class="strip">{"".join(tabs)}</div>'
            f'<div class="bar"><span class="dot"></span><span class="dot"></span><div class="omni"></div></div></div>')


def grid(v, services=SERVICES):
    cards = []
    for s in services:
        sub = s.get("note") or CONTOUR_NAMES[s["contour"]]
        cards.append(
            f'<div class="svc"><div class="big">{inline(render(v, s), 64)}</div>'
            f'<div class="mini"><span class="chip l">{inline(render(v, s), 16)}</span>'
            f'<span class="chip d">{inline(render(v, s, True), 16)}</span>'
            f'<span class="chip l c32">{inline(render(v, s), 32)}</span></div>'
            f'<div class="nm">{html.escape(s["name"])}</div><div class="ct">{html.escape(sub)}</div></div>')
    return '<div class="svcgrid">' + "".join(cards) + "</div>"


def sizes(v, keys=("akb", "legal", "levauth")):
    rows = []
    for dark in (False, True):
        cells = []
        for key in keys:
            s = ALL_BY_KEY[key]
            icons = "".join(f'<span class="sz"><span class="art">{inline(render(v, s, dark), px)}</span><small>{px}</small></span>'
                            for px in (16, 20, 24, 32, 48, 64))
            cells.append(f'<div class="szrow">{icons}</div>')
        rows.append(f'<div class="szpanel {"d" if dark else "l"}">{"".join(cells)}</div>')
    return '<div class="szwrap">' + "".join(rows) + "</div>"


LOCK = ('<svg width="56" height="56" viewBox="0 0 56 56" aria-hidden="true"><rect width="56" height="56" rx="14" fill="#e6f5fc"/>'
        '<g transform="translate(16 16)" fill="none" stroke="#2a7aa3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></g></svg>')


def login(v):
    s = BY_KEY["onboarding"]
    icon = LOCK if v["n"] == 0 else inline(render(v, s), 56)
    lockup = '<div class="lk"><svg class="gl" viewBox="0 0 777 196" aria-label="Global Generation" role="img"><use href="#gglogo"/></svg><span class="svcname">Онбординг</span></div>'
    rest = ('<div class="lh">Вход для команды</div><div class="ls">Введите PIN-код, чтобы открыть раздел</div>'
            '<div class="pins"><i></i><i></i><i></i><i></i></div>')
    first = "Сейчас: замок в бледной плашке" if v["n"] == 0 else "Значок сервиса из этого варианта"
    return ('<div class="logins">'
            f'<div class="login">{lockup}<div class="ic">{icon}</div>{rest}<div class="cap">{first}</div></div>'
            f'<div class="login">{lockup}{rest}<div class="cap">Без значка: сервис уже подписан у логотипа</div></div>'
            '</div>')


def final_fav(s, m):
    """Итог = ровно файлы из assets/favicons (то, что ушло в PR сервисов)."""
    key = "root" if s["key"] == "site" else s["key"]
    return (ROOT / f"assets/favicons/{key}.svg").read_text().strip()


def final_cards(v):
    pinned = ["root", "legal", "onboarding"]
    tabs = [("akb", "АКБ - Маяк"), ("portal", "Мой кабинет · GG"), ("accounting", "Бухгалтерия"), ("apply", "Анкета · GG"),
            ("strategy", "Стратегия"), ("deck", "Презентация · GG"), ("gigi", "Маяк · Джи-джи")]
    rest = ('<div class="lh">Вход для команды</div><div class="ls">Введите PIN-код, чтобы открыть раздел</div>'
            '<div class="pins"><i></i><i></i><i></i><i></i></div>')

    def lockup(name):
        return (f'<div class="lk"><svg class="gl" viewBox="0 0 777 196" aria-label="Global Generation" role="img">'
                f'<use href="#gglogo"/></svg><span class="svcname">{name}</span></div>')
    logins = ('<div class="logins">'
              f'<div class="login">{lockup("Онбординг")}{rest}</div>'
              f'<div class="login">{lockup("Юротдел")}{rest}</div></div>')
    return (f'<div class="card"><h3>Во вкладках Chrome <span>реальный размер 16 px, закреплённые вкладки слева</span></h3>'
            f'{chrome(v, False, pinned, tabs)}{chrome(v, True, pinned, tabs)}</div>'
            f'<div class="card"><h3>Клиентские <span>сайт, портал, анкета, презентация; Маяк с Джи-джи</span></h3>{grid(v, CLIENT_SERVICES)}</div>'
            f'<div class="card"><h3>Внутренние <span>та же схема, отличается иконка</span></h3>{grid(v, INTERNAL_SERVICES)}</div>'
            f'<div class="card"><h3>Экран входа <span>никакого значка над заголовком</span></h3>{logins}</div>'
            f'<div class="card"><h3>Размеры <span>АКБ, Портал, Юротдел: 16, 20, 24, 32, 48, 64</span></h3>{sizes(v, ("akb", "portal", "legal"))}</div>')


CSS = """
:root{--navy:#13445d;--sky:#009CDC;--sky-ink:#0077a8;--fg:#0f172a;--sfg:#334155;--mfg:#64748b;--border:#e2e8f0;--soft:#f1f5f9;
  --font:'Montserrat',system-ui,-apple-system,'Segoe UI',sans-serif;--ui:system-ui,-apple-system,'Segoe UI',sans-serif}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;color:var(--fg);font-family:var(--font);font-weight:500;line-height:1.5;-webkit-font-smoothing:antialiased;
  background:linear-gradient(180deg,#e7eff8 0%,#eef3f9 100%) no-repeat,#eef3f9;background-size:100% 900px,auto}
.wrap{max-width:1120px;margin:0 auto;padding:0 24px}
@media(max-width:620px){.wrap{padding:0 16px}}
header{background:rgba(255,255,255,.78);-webkit-backdrop-filter:saturate(180%) blur(16px);backdrop-filter:saturate(180%) blur(16px);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:20}
.hd{display:flex;align-items:center;gap:14px;height:62px}
.hd .gl{height:24px;width:auto;display:block;flex:0 0 auto}
.hd .svcname{align-self:stretch;display:flex;align-items:center;margin:13px 0;padding-left:14px;border-left:1px solid rgba(19,68,93,.2);font-weight:600;font-size:15px;color:var(--navy);white-space:nowrap}
.tabs{display:flex;flex-wrap:wrap;gap:4px;padding:10px 0 12px}
@media(max-width:620px){.tabs{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:0 0 auto;display:inline-flex;align-items:center;gap:8px;height:36px;padding:0 12px 0 8px;border-radius:10px;border:0;background:transparent;
  font:600 13.5px/1 var(--font);color:#475569;cursor:pointer;white-space:nowrap}
.tab .n{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:7px;background:rgba(19,68,93,.08);color:var(--navy);font-size:11.5px;font-weight:700}
.tab:hover{color:var(--navy);background:rgba(255,255,255,.6)}
.tab[aria-selected=true]{color:#fff;background:var(--navy)}
.tab[aria-selected=true] .n{background:rgba(255,255,255,.18);color:#fff}
.tab:focus-visible{outline:2px solid var(--sky);outline-offset:2px}
.intro{padding:34px 0 8px}
.kick{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--mfg);font-weight:700}
h1{font-size:34px;line-height:1.12;letter-spacing:-.03em;margin:8px 0 10px;font-weight:700}
.intro p{margin:0;max-width:780px;color:var(--sfg);font-size:15.5px}
.intro p b{color:var(--fg)}
section[hidden]{display:none}
.vh{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px 24px;padding:26px 0 16px}
.vh h2{font-size:28px;letter-spacing:-.025em;margin:6px 0 6px;font-weight:700;line-height:1.15}
.vh p{margin:0;max-width:640px;color:var(--sfg);font-size:15px}
.pm{display:flex;flex-direction:column;gap:6px;font-size:13px;color:var(--sfg);max-width:360px}
.pm div{display:flex;gap:8px;align-items:flex-start}
.pm svg{width:16px;height:16px;flex:0 0 16px;margin-top:2px;fill:none;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}
.pm .p svg{stroke:#16a34a}.pm .m svg{stroke:#b45309}
.card{background:#fff;border:1px solid var(--border);border-radius:16px;box-shadow:0 1px 2px rgba(15,23,42,.06);padding:20px;margin-bottom:16px}
.card h3{font-size:14px;margin:0 0 14px;font-weight:700;color:var(--fg)}
.card h3 span{font-weight:500;color:var(--mfg)}
.chrome{border-radius:12px;overflow:hidden;border:1px solid rgba(15,23,42,.12)}
.chrome+.chrome{margin-top:12px}
.strip{display:flex;align-items:flex-end;padding:8px 8px 0;height:44px;overflow:hidden}
.t{position:relative;display:flex;align-items:center;gap:8px;height:34px;padding:0 9px 0 12px;flex:0 1 196px;min-width:44px;
  font:400 12.5px/1 var(--ui);border-radius:9px 9px 0 0;white-space:nowrap;overflow:hidden}
.t.pin{flex:0 0 42px;min-width:42px;padding:0;justify-content:center}
.t:not(.on)+.t:not(.on)::before{content:"";position:absolute;left:0;top:10px;bottom:10px;width:1px;background:currentColor;opacity:.22}
.fav{width:16px;height:16px;flex:0 0 16px;display:block}
.fav svg{display:block}
.fav.gigi{background:url(@GIGI@) center/contain no-repeat;border-radius:50%}
.tt{overflow:hidden;text-overflow:ellipsis;flex:1 1 auto;min-width:0}
.x{width:14px;height:14px;flex:0 0 14px;opacity:.55}
.bar{height:40px;display:flex;align-items:center;gap:10px;padding:0 12px}
.dot{width:12px;height:12px;border-radius:50%;background:currentColor;opacity:.18;flex:0 0 12px}
.omni{flex:1;height:28px;border-radius:14px}
.chrome.l .strip{background:#dfe3e8;color:#3c4043}.chrome.l .t.on{background:#fff;color:#1f1f1f}.chrome.l .bar{background:#fff;color:#3c4043}.chrome.l .omni{background:#eef1f4}
.chrome.d .strip{background:#1f2023;color:#c4c7c5}.chrome.d .t.on{background:#35363a;color:#e8eaed}.chrome.d .bar{background:#35363a;color:#e8eaed}.chrome.d .omni{background:#202124}
.svcgrid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}
@media(max-width:980px){.svcgrid{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:620px){.svcgrid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.svc{border:1px solid var(--border);border-radius:14px;padding:10px;min-width:0}
.svc .big{height:92px;border-radius:10px;background:var(--soft);display:grid;place-items:center}
.svc .big svg{display:block}
.mini{display:flex;align-items:center;gap:6px;margin-top:8px}
.chip{display:grid;place-items:center;width:28px;height:28px;border-radius:7px;flex:0 0 28px}
.chip.c32{width:42px;height:42px;flex-basis:42px}
.chip.l{background:#fff;border:1px solid var(--border)}.chip.d{background:#1f2023}
.chip svg{display:block}
.nm{font-weight:700;font-size:13px;margin-top:8px;line-height:1.25;overflow-wrap:anywhere}
.ct{font-size:11.5px;color:var(--mfg);font-weight:600}
.szpanel{border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:14px;overflow:hidden}
.szwrap{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
@media(max-width:760px){.szwrap{grid-template-columns:minmax(0,1fr)}}
.szpanel.l{background:var(--soft)}.szpanel.d{background:#1f2023;color:#9aa0a6}
.szrow{display:flex;align-items:flex-end;gap:18px;flex-wrap:wrap}
.sz{display:flex;flex-direction:column;align-items:center;gap:6px}
.sz .art svg{display:block}
.sz small{font-size:11px;font-weight:600;color:var(--mfg)}
.szpanel.d .sz small{color:#9aa0a6}
@media(max-width:620px){.szrow{gap:10px}}
.logins{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
@media(max-width:760px){.logins{grid-template-columns:minmax(0,1fr)}}
.login{background:linear-gradient(180deg,#e7eff8 0%,#eef3f9 100%);border-radius:14px;padding:28px 16px 16px;display:flex;flex-direction:column;align-items:center;text-align:center;min-width:0}
.lk{display:flex;align-items:center;gap:14px;height:34px;max-width:100%}
.lk .gl{height:30px;width:auto;display:block;flex:0 1 auto;min-width:0;fill:var(--navy)}
.lk .svcname{align-self:stretch;display:flex;align-items:center;padding-left:14px;border-left:1px solid rgba(19,68,93,.2);font-weight:600;font-size:17px;color:var(--navy);white-space:nowrap}
.login .ic{margin-top:26px;line-height:0}
.lh{font-size:22px;font-weight:700;letter-spacing:-.02em;margin-top:22px;color:var(--fg)}
.login .ic+.lh{margin-top:18px}
.ls{font-size:13.5px;color:var(--mfg);margin-top:6px}
.pins{display:flex;gap:10px;margin-top:18px}
.pins i{width:44px;height:50px;border-radius:12px;background:#fff;border:1.5px solid #cbd5e1;display:block}
.cap{margin-top:18px;font-size:11.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--mfg)}
.foot{padding:8px 0 48px;color:var(--sfg);font-size:14px;max-width:780px}
.foot b{color:var(--fg)}
@media(max-width:620px){h1{font-size:26px}.vh h2{font-size:23px}.card{padding:14px}}
"""

JS = """
(function(){
  var tabs=[].slice.call(document.querySelectorAll('.tab')),secs=[].slice.call(document.querySelectorAll('section[data-v]'));
  var fav=document.getElementById('fav');
  function show(i,focus){
    tabs.forEach(function(t,j){t.setAttribute('aria-selected',j===i?'true':'false');t.tabIndex=j===i?0:-1});
    secs.forEach(function(s,j){s.hidden=j!==i});
    fav.href='data:image/svg+xml,'+encodeURIComponent(secs[i].getAttribute('data-fav'));
    document.title='Фавиконы GG · '+tabs[i].getAttribute('data-title');
    if(focus){tabs[i].focus();tabs[i].scrollIntoView({block:'nearest',inline:'nearest'})}
    try{history.replaceState(null,'','#'+secs[i].id)}catch(e){}
  }
  tabs.forEach(function(t,i){
    t.addEventListener('click',function(){show(i)});
    t.addEventListener('keydown',function(e){
      if(e.key==='ArrowRight'){e.preventDefault();show((i+1)%tabs.length,true)}
      if(e.key==='ArrowLeft'){e.preventDefault();show((i-1+tabs.length)%tabs.length,true)}
    });
  });
  var start=Math.min(1,secs.length-1),h=location.hash.slice(1);
  secs.forEach(function(s,j){if(s.id===h)start=j});
  show(start);
})();
"""

CHECK = ('<svg viewBox="0 0 24 24" stroke="currentColor"><path d="M20 6 9 17l-5-5"/></svg>')
MINUS = ('<svg viewBox="0 0 24 24" stroke="currentColor"><path d="M12 8v5M12 16.5v.5"/><circle cx="12" cy="12" r="9.5"/></svg>')


def default_cards(v):
    return (f'<div class="card"><h3>Во вкладках Chrome <span>реальный размер 16 px, закреплённые вкладки слева</span></h3>'
            f'{chrome(v, False)}{chrome(v, True)}</div>'
            f'<div class="card"><h3>Все сервисы <span>64 px, 16 px на светлом и тёмном, 32 px</span></h3>{grid(v)}</div>'
            f'<div class="card"><h3>Экран входа <span>вместо замка в бледной плашке</span></h3>{login(v)}</div>'
            f'<div class="card"><h3>Размеры <span>АКБ, Юротдел, Сервисы: 16, 20, 24, 32, 48, 64</span></h3>{sizes(v)}</div>')


PAGES = {
    "variants": dict(
        file="favicons-variants.html", title="Фавиконы GG", kick="Вариант {n} из 10",
        description="Фавиконы внутренних сервисов Global Generation: 10 вариантов на выбор во вкладках Chrome, сеткой и в размерах.",
        h1="Фавиконы: 10 вариантов вместо иконок lucide",
        intro="Сейчас у каждого сервиса градиентная плитка и тонкая иконка, на 16 px это каша. Ниже 10 направлений: каждое во вкладках Chrome, сеткой по всем сервисам и в размерах. <b>Вкладка этой страницы тоже меняет фавикон</b> на АКБ выбранного варианта. Плюс экран входа: замок в бледной плашке убираем, на его место значок сервиса или ничего. Маяк остаётся с Джи-джи, его не трогаем.",
        foot="напиши номер или комбинацию, например «3, но буквы как в 4». После выбора соберу финальные SVG, PNG и ICO для всех сервисов в assets/favicons и раскатаю по сервисам."),
    "v9": dict(
        file="favicons-v9-icons.html", title="Фавиконы GG: вариант 9", kick="Палитра {n} из 7",
        description="Вариант 9 фавиконов GG: знак GG и метка сервиса с иконкой, 7 светлых палитр без navy и голубого.",
        h1="Вариант 9 с иконками: светлее и чище",
        intro="Знак GG на каждой вкладке, в углу круглая метка сервиса с иконкой. Navy и голубой убрал, плитка белая, знак и метка больше не налезают друг на друга. Иконки свои, толстые и залитые: тонкие lucide в метке такого размера не видны. <b>Вкладка этой страницы меняет фавикон</b> на выбранную палитру. На первой вкладке исходный 9 для сравнения.",
        foot="напиши номер палитры или комбинацию, например «1, но метка как в 6». После выбора соберу финальные SVG, PNG и ICO в assets/favicons, поменяю замок на экране входа и раскатаю по сервисам."),
    "client": dict(
        file="favicons-client-site.html", title="Фавиконы GG: клиентские и внутренние", kick="Вариант {n} из 3",
        description="Фавиконы GG: клиентские продукты как версии фавикона сайта, внутренние на тёмной плитке.",
        h1="Клиентские = версии фавикона сайта, внутренние = тёмная плитка",
        intro="Клиентские GG (сайт, Студенческий портал, анкета, презентация клиенту) делаем версиями фавикона global-generations.com: тот же navy-градиент и белый знак. SAT и IELTS теперь Aura, их тут нет. Маяк остаётся с Джи-джи. Внутренние на тёмной плитке: белый знак GG и цветная метка по типу (менторы оранжевый, операционка синий, ядро белый). Ниже 3 варианта клиентских. <b>Вкладка этой страницы меняет фавикон</b> на Студенческий портал выбранного варианта.",
        foot="напиши номер варианта для клиентских. Внутренние на тёмной плитке пересоберу в assets/favicons и обновлю уже открытые PR сервисов.",
        fav_key="portal", cards=client_cards),
    "final": dict(
        file="favicons-final.html", title="Фавиконы GG: итог", kick="Утверждено 07.10.2026",
        description="Итоговые фавиконы Global Generation: версии фавикона сайта с меткой сервиса, экран входа без значка.",
        h1="Фавиконы GG: итог",
        intro="Все фавиконы GG, клиентские и внутренние, это версии фавикона global-generations.com: navy-градиент, белый знак GG чуть меньше и белая метка с иконкой сервиса. Сайт и вход с фавиконом сайта как есть, Маяк с Джи-джи. На экранах входа значков нет. Страница рисует ровно файлы из assets/favicons, которые ушли в PR сервисов. <b>Вкладка этой страницы тоже с новым фавиконом</b> (АКБ).",
        foot="напиши «деплой», и я смержу PR и выкачу с проверкой каждого сервиса на проде.", foot_label="Дальше:",
        fav_key="akb", cards=final_cards),
}


def page(variants, meta):
    fonts = (ROOT / "src/fonts.css").read_text()
    gigi = "data:image/png;base64," + base64.b64encode((ROOT / "src/gigi-256.png").read_bytes()).decode()
    logo = (ROOT / "assets/logo/global-logo-navy.svg").read_text().strip()
    logo_inner = re.search(r"<svg[^>]*>(.*)</svg>", logo, re.S).group(1)
    symbol = f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="gglogo" viewBox="0 0 777 196">{logo_inner}</symbol></svg>'
    logo = '<svg class="gl" viewBox="0 0 777 196" fill="#13445d" aria-label="Global Generation" role="img"><use href="#gglogo"/></svg>'

    nav, secs = [], []
    for v in variants:
        n = v["n"]
        num = v.get("label") or str(n)
        nav.append(f'<button class="tab" role="tab" aria-controls="v-{v["slug"]}" data-title="{html.escape(v["title"])}">'
                   f'<span class="n">{num}</span>{html.escape(v["title"])}</button>')
        kick = "Для сравнения" if n == 0 else meta["kick"].format(n=n)
        pm = ""
        if v["plus"]:
            pm = (f'<div class="pm"><div class="p">{CHECK}<span><b>Плюс:</b> {html.escape(v["plus"])}</span></div>'
                  f'<div class="m">{MINUS}<span><b>Минус:</b> {html.escape(v["minus"])}</span></div></div>')
        fav_s = ALL_BY_KEY[meta.get("fav_key", "akb")]
        fav = html.escape(export(v, fav_s) if n else render(v, fav_s))
        secs.append(
            f'<section id="v-{v["slug"]}" data-v="{n}" data-fav="{fav}" role="tabpanel">'
            f'<div class="vh"><div><div class="kick">{kick}</div><h2>{html.escape(v["title"])}</h2>'
            f'<p>{html.escape(v["idea"])}</p></div>{pm}</div>'
            + meta.get("cards", default_cards)(v) + "</section>")

    css = CSS.replace("@GIGI@", gigi)
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{meta["title"]}</title>
<meta name="description" content="{meta["description"]}">
<link id="fav" rel="icon" href="data:,">
<style>{fonts}
{css}</style>
</head>
<body>
{symbol}
<header><div class="wrap"><div class="hd">{logo}<span class="svcname">Фавиконы сервисов</span></div></div></header>
<div class="wrap">
<div class="intro"><div class="kick">Айдентика · 07.10.2026</div><h1>{meta["h1"]}</h1>
<p>{meta["intro"]}</p></div>
<div class="tabs" role="tablist" aria-label="Варианты">{"".join(nav)}</div>
{"".join(secs)}
<p class="foot"><b>{meta.get("foot_label", "Как выбрать:")}</b> {meta["foot"]}</p>
</div>
<script>{JS}</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="дополнительная папка для копии страницы")
    ap.add_argument("--apply", type=int, help="записать вариант N в assets/favicons/*.svg")
    ap.add_argument("--apply-v9", type=int, help="записать палитру N варианта 9 с иконками в assets/favicons/*.svg")
    ap.add_argument("--apply-final", action="store_true",
                    help="стандарт 07.10: плитка сайта, знак меньше + белая метка с иконкой для всех")
    a = ap.parse_args()

    T = Type()
    sets = {"variants": build_variants(T)}
    sets["v9"] = build_v9_icons(sets["variants"])
    sets["client"] = build_client()
    sets["final"] = [dict(n=1, slug="final", title="Итог", fn=final_fav, adaptive=False,
                          idea="Плитка сайта, знак меньше, белая метка с иконкой сервиса. Одинаково для клиентских и внутренних.",
                          plus="", minus="")]

    if a.apply_final:
        v = dict(fn=client_version("small", everyone=True))
        for s in SERVICES + [c for c in CLIENT_SERVICES if c["key"] not in BY_KEY and c["key"] != "site"]:
            (ROOT / f"assets/favicons/{s['key']}.svg").write_text(export(v, s) + "\n")
        print("стандарт 07.10 записан в assets/favicons/")
        return

    for key, n in (("variants", a.apply), ("v9", a.apply_v9)):
        if n:
            v = next(x for x in sets[key] if x["n"] == n)
            for s in SERVICES:
                (ROOT / f"assets/favicons/{s['key']}.svg").write_text(export(v, s) + "\n")
            print(f"{key} {n} записан в assets/favicons/")
            return

    for key, variants in sets.items():
        meta = PAGES[key]
        dst = ROOT / meta["file"]
        dst.write_text(page(variants, meta))
        print(f"{dst} ({dst.stat().st_size // 1024} KB)")
        if a.out:
            out = Path(a.out).expanduser()
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy(dst, out / dst.name)
            print(out / dst.name)


if __name__ == "__main__":
    main()
