"""Check GG ID: every screen in gg-id/screens at 1440 and 390 px, 3 layouts x 2 themes, the GG ID card,
the e-mail card gg-id/email-card.html and the showcase gg-id.html.

Fails on horizontal scroll, elements sticking out of the screen, missing Montserrat, console errors, dashes in text;
for the card also on text outside the card padding, wrong proportions, more than one accent, proportional digits;
for the e-mail card on low contrast in light, dark (Apple Mail) and inverted (Gmail on iPhone) modes.
Layout everywhere (screens and every component of the showcase at 1440, 1024 and 390, both themes): every element inside
its component card, no cut content, no overlapping siblings, avatars with white centred initials, one-line button labels.
gg-id-service.js: account menu (mouse, keyboard, Esc, click outside), «Сессия истекла» (401, focus trap, Esc, backdrop).
QA 08.10: screens in the split layout at 360, 375, 768, 1024 px and at 200 % zoom; short windows down to 400 px tall and the 320 px phone
(the card on the panel never overlaps the logo or the text, is never clipped, never narrower than 240 px, long data stays inside);
a visible keyboard focus ring on every stop of every screen; no endless motion with «reduce motion»; readable placeholders;
the panel in the system dark theme equals data-theme="dark".
Passkey wording (rules of 09.10.2026 and 10.10.2026, src/check_gg_id_passkey.py, also runnable alone): the sensor of Apple is always the pair «Face ID / Touch ID»,
Windows Hello, «отпечаток» and «палец» only when this browser has a confirmed key of the device; 7 devices x 8 memory states x 3 screens, the rules of the shared
localStorage memory, the real WebAuthn of Chromium (virtual authenticators), a browser without storage or WebAuthn.
The scene of the sign-in screen (rule of 10.10.2026, src/check_gg_id_stage.py, also runnable alone): on login, password, forgot, error and noaccess in the four windows of
the contract (1440 x 900, 1280 x 720, 1920 x 1080, 390 x 844) the title stands on max(28 px, (window height - 560 px) / 2) and does not move between the screens, the card,
the panel and the footer stand on the numbers of the sign-in page of the hub; the footer links the instruction; the tabs of the showcase change the screen in place.
Screenshots: shots/gg-id/. Run: uv run --with playwright python src/check_gg_id.py
With --preview it also refreshes the card pictures in gg-id/preview/ (README and PR).
"""
import html
import os
import re
import shutil
import sys
from playwright.sync_api import sync_playwright

import check_gg_id_passkey   # src/ is on sys.path when this file is run as a script
import check_gg_id_stage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENS = os.path.join(ROOT, 'gg-id', 'screens')
OUT = os.path.join(ROOT, 'shots', 'gg-id')
os.makedirs(OUT, exist_ok=True)

PROBE = '''async () => {
  await document.fonts.ready;
  const de = document.documentElement, W = de.clientWidth;
  const out = [];
  document.querySelectorAll('.gid-main *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0) return;
    if (r.right > W + 1 || r.left < -1) {
      let p = el.parentElement, clipped = false;
      while (p && p !== document.body) { const o = getComputedStyle(p).overflowX; if (o !== 'visible') { clipped = true; break; } p = p.parentElement; }
      if (!clipped) out.push((el.className && el.className.baseVal === undefined ? el.className : el.tagName) + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
    }
  });
  const card = document.querySelector('.gid-card').getBoundingClientRect();
  return {
    scrollW: de.scrollWidth, clientW: W, height: de.scrollHeight, viewH: innerHeight,
    font: document.fonts.check('700 16px Montserrat') && document.fonts.check('500 16px Montserrat'),
    usedFont: getComputedStyle(document.querySelector('.gid-h') || document.body).fontFamily,
    dashes: (document.body.innerText.match(/[\\u2014\\u2013]/g) || []).length,
    wide: out.slice(0, 8), cardW: Math.round(card.width),
    aside: getComputedStyle(document.querySelector('.gid-aside')).display
  };
}'''

# GG ID card: everything inside the padding, one accent (the status dot), monospaced digits, Montserrat
CARD_PROBE = '''async (sel) => {
  await document.fonts.ready;
  const ACCENT = '92, 195, 236', LIGHT_ACCENT = '0, 156, 220';
  const name = e => (e.className && e.className.baseVal === undefined && e.className) || e.tagName;
  const res = [];
  document.querySelectorAll(sel).forEach(c => {
    const r = c.getBoundingClientRect(), cs = getComputedStyle(c);
    const pl = parseFloat(cs.paddingLeft), pr = parseFloat(cs.paddingRight), pt = parseFloat(cs.paddingTop), pb = parseFloat(cs.paddingBottom);
    const outside = [], accents = [];
    c.querySelectorAll('*').forEach(e => {
      const q = e.getBoundingClientRect();
      if (!q.width || !q.height || e.matches('.gid-idcard-holo')) return;   // перелив на всю карту: украшение, не содержимое
      if (q.left < r.left + pl - 1 || q.right > r.right - pr + 1 || q.top < r.top + pt - 1 || q.bottom > r.bottom - pb + 1)
        outside.push(name(e) + ' @' + Math.round(q.left - r.left) + ',' + Math.round(q.top - r.top) + ' ' + Math.round(q.width) + 'x' + Math.round(q.height));
    });
    [c, ...c.querySelectorAll('*')].forEach(e => {
      if (!e.getClientRects().length) return;
      [null, '::before', '::after'].forEach(ps => {
        const s = getComputedStyle(e, ps);
        if (ps && s.content === 'none') return;
        if ([s.color, s.backgroundColor, s.borderTopColor].some(v => v.includes(ACCENT) || v.includes(LIGHT_ACCENT))) accents.push(name(e) + (ps || ''));
      });
    });
    const num = c.querySelector('[data-gid-field="id"]');
    let tnum = null;
    if (num) {
      const pr2 = document.createElement('span');
      pr2.className = num.className; pr2.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap';
      num.parentNode.appendChild(pr2);
      pr2.textContent = '1111111111'; const w1 = pr2.getBoundingClientRect().width;
      pr2.textContent = '0000000000'; const w0 = pr2.getBoundingClientRect().width;
      pr2.remove();
      tnum = Math.abs(w1 - w0) < 0.5;
    }
    const nm = c.querySelector('[data-gid-field="name"]');
    res.push({w: r.width, h: r.height, ratio: r.width / r.height, parentW: c.parentElement.getBoundingClientRect().width,
      parentPad: parseFloat(getComputedStyle(c.parentElement).paddingLeft) + parseFloat(getComputedStyle(c.parentElement).paddingRight),
      outside: outside.slice(0, 6), accents, tnum, font: nm ? getComputedStyle(nm).fontFamily : getComputedStyle(c).fontFamily});
  });
  return {cards: res, fontOk: document.fonts.check('700 16px Montserrat') && document.fonts.check('600 16px Montserrat'),
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
    dashes: (document.body.innerText.match(/[\\u2014\\u2013]/g) || []).length};
}'''

RATIO = 85.6 / 54
LONG = {'name': 'Александра Образцова-Константинопольская',
        'positions': ['Ментор', 'Руководитель направления «Магистратура в Европе»', 'Ведущая роликов YouTube-канала'],
        'email': 'aleksandra.obraztsova-konstantinopolskaya@global-generations.com', 'id': 'GG 9031-55C0E7', 'since': '2025-09',
        'status': 'active', 'passkey': True}
EMPTY = {'name': 'Лёв', 'positions': [], 'email': 'lev.demo@global-generations.com', 'id': 'GG 1', 'since': '2026-10',
         'status': 'disabled', 'passkey': False}

# e-mail card: the hub fills the placeholders (escaped), Gmail on iPhone inverts colours but not images
EMAIL = os.path.join(ROOT, 'gg-id', 'email-card.html')
EMAIL_PNG = os.path.join(ROOT, 'gg-id', 'email', 'gg-logo-navy-2x.png')
EMAIL_PNG_URL = 'https://id.global-generations-edu.com/assets/gg-id/email/gg-logo-navy-2x.png'
EMAIL_LINKS = {'link': 'https://id.global-generations-edu.com/set-password.html#token=demo&invite=1',
               'guide_url': 'https://id.global-generations-edu.com/instructions/'}
EMAIL_DEMO = {'name': 'Иван Образцов', 'positions': 'Ментор · Продажи', 'email': 'ivan.obraztsov@global-generations.com',
              'id': 'GG 0042-7F3A', **EMAIL_LINKS}
EMAIL_LONG = {'name': 'Александра Образцова-Константинопольская',
              'positions': 'Ментор · Руководитель направления «Магистратура в Европе» · Ведущая роликов YouTube-канала',
              'email': 'aleksandra.obraztsova-konstantinopolskaya@global-generations.com', 'id': 'GG 9031-55C0E7', **EMAIL_LINKS}
INVERT = '''() => {   // like Gmail on iPhone in dark mode: lightness of every colour flipped, images untouched
  const parse = v => { const m = v.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(',').map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const flip = c => { let r = c.r / 255, g = c.g / 255, b = c.b / 255; const mx = Math.max(r, g, b), mn = Math.min(r, g, b); let h = 0, s = 0, l = (mx + mn) / 2;
    if (mx !== mn) { const d = mx - mn; s = l > .5 ? d / (2 - mx - mn) : d / (mx + mn);
      h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h /= 6; }
    l = 1 - l;
    const q = l < .5 ? l * (1 + s) : l + s - l * s, p = 2 * l - q;
    const hue = t => { t = (t + 1) % 1; return t < 1 / 6 ? p + (q - p) * 6 * t : t < 1 / 2 ? q : t < 2 / 3 ? p + (q - p) * (2 / 3 - t) * 6 : p; };
    const to = x => Math.round(x * 255);
    return s === 0 ? `rgba(${to(l)}, ${to(l)}, ${to(l)}, ${c.a})` : `rgba(${to(hue(h + 1 / 3))}, ${to(hue(h))}, ${to(hue(h - 1 / 3))}, ${c.a})`; };
  const plan = [];
  document.querySelectorAll('body, body *').forEach(e => {
    if (e.tagName === 'IMG') return;
    const s = getComputedStyle(e);
    ['color', 'background-color', 'border-top-color', 'border-left-color'].forEach(prop => { const c = parse(s.getPropertyValue(prop)); if (c && c.a > 0) plan.push([e, prop, flip(c)]); });
  });
  plan.forEach(([e, prop, v]) => e.style.setProperty(prop, v, 'important'));
}'''
CONTRAST = '''() => {
  const parse = v => { const m = v.match(/rgba?\\(([^)]+)\\)/); const p = m[1].split(',').map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = c => { const f = x => { x /= 255; return x <= .03928 ? x / 12.92 : Math.pow((x + .055) / 1.055, 2.4); }; return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const bgOf = e => { for (let p = e; p; p = p.parentElement) { const c = parse(getComputedStyle(p).backgroundColor); if (c.a > 0) return c; } return {r: 255, g: 255, b: 255, a: 1}; };
  const low = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walk.nextNode(); n; n = walk.nextNode()) {
    const t = n.nodeValue.trim(); if (!t) continue;
    const e = n.parentElement; if (!e.getClientRects().length || getComputedStyle(e).display === 'none') continue;
    const cr = ratio(parse(getComputedStyle(e).color), bgOf(e));
    if (cr < 4.5) low.push(t.slice(0, 24) + ' ' + cr.toFixed(2));
  }
  const img = document.querySelector('img'), card = document.querySelector('.gidm-card');
  const plate = {r: 19, g: 68, b: 93, a: 1};   // the navy logo in the PNG (transparent around it): against the light card
  const cb = card.getBoundingClientRect();
  return {low, img: img.complete && img.naturalWidth > 0, plate: ratio(plate, bgOf(card)), bodyLum: lum(bgOf(document.body)),
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth, cardW: cb.width,
    actions: [...document.querySelectorAll('a')].some(a => a.textContent.trim() === 'Задать пароль') && [...document.querySelectorAll('a')].some(a => a.textContent.trim() === 'Инструкция: как войти'),
    left: (document.body.innerText.match(/\\{\\{|\\}\\}/g) || []).length,
    dashes: (document.body.innerText.match(/[\\u2014\\u2013]/g) || []).length};
}'''


def email_page(values):
    src = open(EMAIL, encoding='utf-8').read()
    return re.sub(r'\{\{([a-z_]+)\}\}', lambda m: html.escape(values[m.group(1)], quote=True), src)


# Layout of every component: each element inside its component card (unless an ancestor clips or scrolls it on purpose),
# no content cut by overflow:hidden, no overlapping in-flow siblings, avatars with white centred initials, one-line buttons.
LAYOUT = r'''async (sel) => {
  await document.fonts.ready;
  const name = e => {
    const c = e.className && e.className.baseVal === undefined ? String(e.className).trim().split(/\s+/).slice(0, 2).join('.') : '';
    return e.tagName.toLowerCase() + (c ? '.' + c : '');
  };
  const txt = e => '"' + (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 22) + '"';
  const clips = e => { const s = getComputedStyle(e); return s.overflowX !== 'visible' || s.overflowY !== 'visible'; };
  const scrolls = e => { const s = getComputedStyle(e); return /auto|scroll/.test(s.overflowX + s.overflowY); };
  // намеренная обрезка: рамки витрины, бегущие строки и пятна фона (корень .gid), аватар, полоса прогресса
  // .gid-chip прячет имя и стрелку на скрытой второй строке, когда остаются только инициалы
  const CROPS = '.sc-viewport,.sc-phone,.sc-thumb-frame,.sc-mini,.sc-url,.gid,.gid-aside,.gid-mq,.gid-mq-row,.gid-avatar,.sc-browser,.gid-progress,.gid-chip';
  const moving = e => e.getAnimations && e.getAnimations().some(a => a.playState === 'running' && a.effect && a.effect.getComputedTiming().iterations === 1);
  const out = {outside: [], cut: [], overlap: [], avatars: [], wrapped: [], contrast: [], small: []};
  const seen = new Set();
  const add = (k, v) => { if (!seen.has(k + v)) { seen.add(k + v); out[k].push(v); } };
  const boxes = [...document.querySelectorAll(sel)].filter(b => b.getClientRects().length);
  boxes.forEach(box => {
    const B = box.getBoundingClientRect();
    if (!B.width || !B.height) return;
    const boxScrolls = scrolls(box);   // лента вкладок и т.п.: содержимое листается, это не вылезание
    [box, ...box.querySelectorAll('*')].forEach(e => {
      if (e.closest('svg') && e.tagName.toLowerCase() !== 'svg') return;
      const shut = e.parentElement && e.parentElement.closest('details:not([open])');   // свёрнутый «Резервный вход»: виден только summary
      if (shut && !e.closest('summary')) return;
      const st = getComputedStyle(e);
      if (st.visibility === 'hidden' || !e.getClientRects().length) return;
      // content cut by overflow:hidden (not a scroll box, not an ellipsis, not an intentional crop)
      const sx = st.overflowX;
      if ((sx === 'hidden' || sx === 'clip') && e.scrollWidth > e.clientWidth + 1 && st.textOverflow !== 'ellipsis' && !e.matches(CROPS))
        add('cut', name(e) + ' ' + txt(e) + ' ' + (e.scrollWidth - e.clientWidth) + 'px');
      if (e === box || boxScrolls || moving(e)) return;   // разовая анимация (встряска поля, появление) в процессе
      const r = e.getBoundingClientRect();
      if (!r.width || !r.height) return;
      let p = e.parentElement, skip = false;
      while (p && p !== box) { if (clips(p) || scrolls(p)) { skip = true; break; } p = p.parentElement; }
      if (skip) return;
      const inline = st.display === 'inline';
      const d = Math.max(B.left - r.left, r.right - B.right, inline ? 0 : B.top - r.top, inline ? 0 : r.bottom - B.bottom);
      if (d > 0.75) add('outside', name(box) + ' > ' + name(e) + ' ' + txt(e) + ' ' + Math.round(d) + 'px');
    });
    [box, ...box.querySelectorAll('*')].forEach(parent => {
      const tag = parent.tagName.toLowerCase();
      if (tag === 'svg' || parent.closest('svg') || parent.closest('[aria-hidden="true"]')) return;
      const kids = [...parent.children].filter(k => {
        const t = k.tagName.toLowerCase();
        if (t === 'template' || t === 'script' || t === 'style') return false;
        if (parent.matches('details:not([open])') && t !== 'summary') return false;
        const s = getComputedStyle(k);
        if (/absolute|fixed/.test(s.position) || /none|inline|contents/.test(s.display) && s.display !== 'inline-block' && s.display !== 'inline-flex' && s.display !== 'inline-grid' || s.visibility === 'hidden') return false;
        const r = k.getBoundingClientRect(); return r.width > 0 && r.height > 0;
      });
      for (let i = 0; i < kids.length; i++) for (let j = i + 1; j < kids.length; j++) {
        const a = kids[i].getBoundingClientRect(), b = kids[j].getBoundingClientRect();
        const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (ox > 1 && oy > 1) add('overlap', name(parent) + ': ' + name(kids[i]) + ' x ' + name(kids[j]) + ' ' + Math.round(ox) + 'x' + Math.round(oy));
      }
    });
  });
  document.querySelectorAll('.gid-avatar').forEach(a => {
    if (!a.getClientRects().length) return;
    const s = getComputedStyle(a), r = a.getBoundingClientRect();
    if (!r.width) return;
    const t = [...a.childNodes].find(n => n.nodeType === 3 && n.nodeValue.trim());
    let dx = 0, dy = 0;
    if (t) { const rg = document.createRange(); rg.selectNodeContents(t); const q = rg.getBoundingClientRect();
      dx = (q.left + q.right) / 2 - (r.left + r.right) / 2; dy = (q.top + q.bottom) / 2 - (r.top + r.bottom) / 2; }
    if (!/grid/.test(s.display) || s.color !== 'rgb(255, 255, 255)' || Math.abs(dx) > 1.5 || Math.abs(dy) > 2 || parseFloat(s.fontSize) < 10.5)
      add('avatars', name(a.parentElement) + ' > avatar ' + txt(a) + ': display ' + s.display + ', color ' + s.color + ', font ' + s.fontSize + ', off ' + dx.toFixed(1) + ',' + dy.toFixed(1));
  });
  // кнопки: подпись контрастная (от 4,5 к фону под кнопкой, полупрозрачные слои и градиенты учтены), высота от 44 px
  const parseC = v => { const m = v && v.match(/rgba?\(([^)]+)\)/); if (!m) return null; const q = m[1].split(',').map(Number); return {r: q[0], g: q[1], b: q[2], a: q.length > 3 ? q[3] : 1}; };
  const lum = c => { const f = x => { x /= 255; return x <= .03928 ? x / 12.92 : Math.pow((x + .055) / 1.055, 2.4); }; return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const over = (top, base) => ({r: top.r * top.a + base.r * (1 - top.a), g: top.g * top.a + base.g * (1 - top.a), b: top.b * top.a + base.b * (1 - top.a), a: 1});
  const behind = el => {   // слои фона от элемента вниз до первого непрозрачного (у градиента берутся все непрозрачные цвета)
    const layers = [];
    for (let q = el; q; q = q.parentElement) {
      const st = getComputedStyle(q), c = parseC(st.backgroundColor);
      const g = st.backgroundImage !== 'none' ? (st.backgroundImage.match(/rgba?\([^)]+\)/g) || []).map(parseC).filter(x => x.a >= .99) : [];
      if (c && c.a > 0) { if (c.a >= .99) return {layers, bases: [c]}; layers.push(c); }
      if (g.length) return {layers, bases: g};
    }
    return {layers, bases: [{r: 255, g: 255, b: 255, a: 1}]};
  };
  document.querySelectorAll('.gid-sso, .gid-btn').forEach(b => {
    if (!b.getClientRects().length || b.disabled || b.closest('[aria-hidden="true"]')) return;
    const br = b.getBoundingClientRect();
    if (br.height < 43.5 && !b.closest('.sc-mini,.sc-viewport,.sc-phone,.sc-thumb-frame')) add('small', name(b) + ' ' + txt(b) + ' ' + Math.round(br.height) + 'px');   // превью витрины уменьшены
    const {layers, bases} = behind(b), fg = parseC(getComputedStyle(b).color);
    let worst = 99;
    bases.forEach(base => { let bg = base; for (let k = layers.length - 1; k >= 0; k--) bg = over(layers[k], bg);
      worst = Math.min(worst, ratio(fg.a < 1 ? over(fg, bg) : fg, bg)); });
    if (worst < 4.5) add('contrast', name(b) + ' ' + txt(b) + ' ' + worst.toFixed(2));
  });
  document.querySelectorAll('.gid-sso, .gid-btn').forEach(b => {
    if (!b.getClientRects().length) return;
    const tops = [];
    const w = document.createTreeWalker(b, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      if (!n.nodeValue.trim()) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      [...rg.getClientRects()].forEach(q => { if (q.width > 1) tops.push(q.top); });
    }
    if (tops.length && Math.max(...tops) - Math.min(...tops) > 0.6 * parseFloat(getComputedStyle(b).fontSize))
      add('wrapped', name(b) + ' ' + txt(b));
  });
  return out;
}'''
SCREEN_BOXES = '.gid-card, .gid-btn, .gid-account, .gid-who, .gid-msg, .gid-idcard, .gid-code, .gid-aside, .gid-hero-holder'
SHOWCASE_BOXES = ('.sc-top, .sc-hero, .sc-bar, .sc-seg, .sc-sel, .sc-tabs, .sc-browser, .sc-phone, .sc-thumb-frame, .sc-cap, '
                  '#stage .gid-card, .sc-card, .sc-demo, .sc-hdr, .gid-acct, .gid-menu, .gid-dialog, .gid-sso, .sc-idc-cell, '
                  '.sc-row-demo, .gid-idrow, .gid-idcard, .sc-where > div, .sc-mail-frame, .sc-mail-notes, .sc-rules, .sc-files, '
                  '.sc-api, .sc-foot')


def layout_issues(label, r):
    found = []
    for k, what in (('outside', 'sticks out of its card'), ('cut', 'content cut by overflow'), ('overlap', 'overlapping siblings'),
                    ('avatars', 'avatar initials not white and centred'), ('wrapped', 'button label on two lines'),
                    ('contrast', 'button label contrast below 4.5'), ('small', 'button lower than 44 px')):
        if r[k]:
            found.append(f'{label}: {what} {r[k][:4]}')
    return found


# ---- QA 08.10 ----
# экраны в сплите на других ширинах: 360 (маленький телефон), 375 (iPhone SE и mini: колонка 343 px, самая длинная подпись главной кнопки «Подключить Face ID / Touch ID»
# со стрелкой в неё не входит, поэтому в колонке до 355 px кегль 14 px), 768 (планшет), 1024 и масштаб 200 % окна 1440 x 900 (720 x 450 при 2x)
WIDTHS = [(360, 740, 2, '360'), (375, 812, 2, '375'), (768, 1024, 1, '768'), (1024, 768, 1, '1024'), (720, 450, 2, 'zoom200')]
# низкие окна (масштаб 200 % на 1920 x 1080, маленькие ноутбуки) и самый узкий телефон
SHORT = [(1280, 560), (1280, 450), (1024, 500), (960, 480), (1366, 640), (1440, 600), (1920, 400), (320, 568), (360, 640), (390, 664), (844, 390), (740, 360)]
LONG_HERO = {'name': 'Константин Александрович Преображенский',
             'positions': ['Руководитель направления «Магистратура в Европе»', 'Ведущий роликов YouTube-канала', 'Старший ментор по поступлению'],
             'id': 'GG 9031-55C0E7', 'qr': 'https://id.global-generations-edu.com/v/GG-9031-55C0E7'}
# панель сплита: карта не наезжает на подпись и текст, не обрезана панелью, не уже 240 px, её содержимое внутри полей, имя не длиннее 2 строк
PANEL = '''() => {
  const a = document.querySelector('.gid-aside'); if (!a || getComputedStyle(a).display === 'none') return [];
  const A = a.getBoundingClientRect(), out = [];
  const vis = e => e && e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
  const R = e => e.getBoundingClientRect();
  const lock = a.querySelector(':scope > .gid-lockup'), hold = a.querySelector('.gid-hero-holder'), lan = a.querySelector('.gid-hero-lan'),
        card = a.querySelector('.gid-idcard--hero'), copy = a.querySelector('.gid-aside-copy');
  const over = (p, q) => vis(p) && vis(q) && Math.min(R(p).right, R(q).right) - Math.max(R(p).left, R(q).left) > 1 && Math.min(R(p).bottom, R(q).bottom) - Math.max(R(p).top, R(q).top) > 1;
  if (over(hold, copy)) out.push('the card overlaps the panel text');
  if (over(hold, lock) || over(lan, lock)) out.push('the card overlaps the logo');
  [['logo', lock], ['strap', lan], ['holder', hold], ['card', card], ['text', copy]].forEach(([n, e]) => {
    if (!vis(e)) return; const r = R(e);
    if (r.left < A.left - .5 || r.right > A.right + .5 || r.top < A.top - .5 || r.bottom > A.bottom + .5) out.push(n + ' clipped by the panel');
  });
  const badge = getComputedStyle(a.querySelector('.gid-hero')).transform !== 'none';   // бейдж: та же карта, уменьшенная
  if (badge && vis(card) && over(card, lock)) out.push('the badge overlaps the logo');
  if (vis(card) && !badge) {
    const C = R(card), cs = getComputedStyle(card);
    if (C.width < 240) out.push('card narrower than 240 px: ' + Math.round(C.width));
    card.querySelectorAll('.gid-lockup, .gid-idcard-seal, .gid-idcard-big, .gid-idcard-name, .gid-idcard-roles, .gid-idcard-num, .gid-idcard-qr').forEach(e => {
      const q = R(e); if (!q.width) return;
      if (q.left < C.left + parseFloat(cs.paddingLeft) * .9 - 1 || q.right > C.right - parseFloat(cs.paddingRight) * .9 + 1 || q.bottom > C.bottom - parseFloat(cs.paddingBottom) * .9 + 1)
        out.push('card content outside its padding: ' + (e.className.baseVal !== undefined ? e.className.baseVal : e.className));
    });
    const nm = card.querySelector('.gid-idcard-name');
    if (nm && R(nm).height > parseFloat(getComputedStyle(nm).lineHeight) * 2.5) out.push('name on the card longer than 2 lines');
  }
  return out;
}'''
FOCUS = '''() => {
  const a = document.activeElement; if (!a || a === document.body) return null;
  if (!a.dataset.qaFocus) a.dataset.qaFocus = String(Math.random());
  const s = getComputedStyle(a);
  return {id: a.dataset.qaFocus, tag: a.tagName.toLowerCase(), cls: String(a.className && a.className.baseVal === undefined ? a.className : ''),
          text: (a.innerText || a.getAttribute('aria-label') || '').trim().slice(0, 30), input: a.matches('input'),
          outline: [s.outlineStyle, parseFloat(s.outlineWidth), s.outlineColor], border: s.borderTopColor, shadow: s.boxShadow};
}'''
ACCENT = {'light': 'rgb(0, 156, 220)', 'dark': 'rgb(92, 195, 236)'}
MOTION = '''() => document.getAnimations().filter(a => a.playState === 'running' && a.effect.getComputedTiming().iterations === Infinity)
  .map(a => { const t = a.effect.target; return (t.className && t.className.baseVal === undefined ? String(t.className).split(' ')[0] : t.tagName) + (a.effect.pseudoElement || '') + ' ' + a.animationName; })'''
PLACEHOLDER = '''() => {
  const parse = v => { const m = v.match(/rgba?\\(([^)]+)\\)/); const p = m[1].split(',').map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = c => { const f = x => { x /= 255; return x <= .03928 ? x / 12.92 : Math.pow((x + .055) / 1.055, 2.4); }; return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  const over = (t, b) => ({r: t.r * t.a + b.r * (1 - t.a), g: t.g * t.a + b.g * (1 - t.a), b: t.b * t.a + b.b * (1 - t.a), a: 1});
  const i = document.querySelector('.gid-main input[placeholder]');
  const page = parse(getComputedStyle(document.querySelector('.gid')).backgroundColor);
  const bg = over(parse(getComputedStyle(i).backgroundColor), page), fg = over(parse(getComputedStyle(i, '::placeholder').color), bg);
  const x = lum(fg), y = lum(bg); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
}'''

problems = []
counts = {'screens': 0, 'card': 0, 'email': 0, 'showcase': 0, 'layout': 0, 'service': 0, 'widths': 0, 'short': 0, 'focus': 0, 'motion': 0, 'passkey': 0, 'stage': 0}
with sync_playwright() as p:
    b = p.chromium.launch()
    _new_context = b.new_context

    def new_context(**kw):   # общий мак, десятки агентов: 30 секунд Playwright по умолчанию бывает мало
        c = _new_context(**kw)
        c.set_default_timeout(180000)
        c.set_default_navigation_timeout(180000)
        return c
    b.new_context = new_context
    for vw, vh, tag in [(1440, 900, 'desktop'), (390, 844, 'phone')]:
        for theme in ('light', 'dark'):
            ctx = b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=2 if vw < 500 else 1,
                                color_scheme=theme)
            pg = ctx.new_page()
            errs = []
            pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
            pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
            for fn in sorted(os.listdir(SCREENS)):
                key = fn[:-5]
                for layout in ('split', 'card', 'minimal'):
                    errs.clear()
                    pg.goto('file://' + os.path.join(SCREENS, fn) + f'?layout={layout}')
                    pg.wait_for_timeout(250)
                    r = pg.evaluate(PROBE)
                    counts['screens'] += 1
                    problems.extend(layout_issues(f'{tag}/{theme}/{layout}/{key}', pg.evaluate(LAYOUT, SCREEN_BOXES)))
                    label = f'{tag}/{theme}/{layout}/{key}'
                    if r['scrollW'] > r['clientW']:
                        problems.append(f'{label}: horizontal scroll {r["scrollW"]} > {r["clientW"]}')
                    if r['wide']:
                        problems.append(f'{label}: sticks out {r["wide"]}')
                    if not r['font'] or 'Montserrat' not in r['usedFont']:
                        problems.append(f'{label}: font {r["usedFont"]}')
                    if r['dashes']:
                        problems.append(f'{label}: dashes in text {r["dashes"]}')
                    if errs:
                        problems.append(f'{label}: console {errs[:3]}')
                    if layout == 'split' and tag == 'desktop' and r['aside'] != 'flex':
                        problems.append(f'{label}: split panel hidden on desktop')
                    if tag == 'phone' and layout != 'split' and r['aside'] != 'none':
                        problems.append(f'{label}: brand panel visible on phone in the {layout} layout')
                    if tag == 'phone' and layout == 'split' and r['aside'] != 'flex':
                        problems.append(f'{label}: split panel must sit compactly on top on the phone')
                    if layout == 'split':   # герой панели: карта GG ID на ленте, QR нарисован и цел, панель не вылезает
                        h = pg.evaluate('''() => { const a = document.querySelector('.gid-aside'), hc = a.querySelector('.gid-idcard--hero'),
                            q = a.querySelector('svg[data-gid-qr]'), m = GGID.qrMatrix(q.getAttribute('data-gid-qr'));
                            const ar = a.getBoundingClientRect(), hr = hc.getBoundingClientRect();
                            const badge = getComputedStyle(a.querySelector('.gid-hero')).transform !== 'none';   // телефон в низком окне: бейдж карты в строке над формой
                            return {hero: !!hc && hr.width > (badge ? 60 : 150), inside: hr.top >= ar.top - 1 && hr.bottom <= ar.bottom + 1 && hr.left >= ar.left - 1 && hr.right <= ar.right + 1,
                              qr: (q.querySelector('path').getAttribute('d') || '').length > 500 && m.size === m.version * 4 + 17 && m.get(0, 0) && m.get(6, 6) && !m.get(7, 7) && m.get(8, m.size - 8),
                              key: !!a.querySelector('.gid-idcard-seal use[href="#gid-id-icon"]')}; }''')
                        if not (h['hero'] and h['inside'] and h['qr'] and h['key']):
                            problems.append(f'{label}: hero card of the split panel {h}')
                    if r['height'] > r['viewH'] and tag == 'desktop':
                        problems.append(f'{label}: taller than the window {r["height"]} > {r["viewH"]}')
                    shot = (theme == 'light' and layout == 'split') or key in ('login', 'setpass', 'done', 'pin', 'card')
                    if shot:
                        pg.wait_for_timeout(900 if key == 'done' else 150)
                        pg.screenshot(path=os.path.join(OUT, f'{tag}-{theme}-{layout}-{key}.png'))

            # GG ID card on its screen (minimal layout = the plain column of the hub): demo, long and empty data
            for data_name, data in (('demo', None), ('long', LONG), ('empty', EMPTY)):
                errs.clear()
                pg.goto('file://' + os.path.join(SCREENS, 'card.html') + '?layout=minimal')
                pg.wait_for_timeout(250)
                if data:
                    pg.evaluate('(d) => GGID.card(document.querySelector(".gid-main .gid-idcard"), d)', data)
                r = pg.evaluate(CARD_PROBE, '.gid-main .gid-idcard')
                counts['card'] += 1
                label = f'card/{tag}/{theme}/{data_name}'
                c = r['cards'][0]
                if r['scrollW'] > r['clientW']:
                    problems.append(f'{label}: horizontal scroll {r["scrollW"]} > {r["clientW"]}')
                if c['outside']:
                    problems.append(f'{label}: outside the card padding {c["outside"]}')
                if not r['fontOk'] or 'Montserrat' not in c['font']:
                    problems.append(f'{label}: font {c["font"]}')
                if r['dashes']:
                    problems.append(f'{label}: dashes in text {r["dashes"]}')
                if errs:
                    problems.append(f'{label}: console {errs[:3]}')
                if c['tnum'] is not True:
                    problems.append(f'{label}: digits of the GG ID number are not monospaced')
                expect_accents = [] if data_name == 'empty' else ['gid-idcard-status::before']
                if c['accents'] != expect_accents:
                    problems.append(f'{label}: accent colour on {c["accents"]}, expected {expect_accents}')
                if c['h'] < c['w'] / RATIO - 1:
                    problems.append(f'{label}: card shorter than 85.6 x 54 ({c["w"]:.0f}x{c["h"]:.0f})')
                if data_name == 'demo' and tag == 'desktop' and abs(c['ratio'] - RATIO) > 0.01:
                    problems.append(f'{label}: proportions {c["ratio"]:.3f}, a real card is {RATIO:.3f}')
                if tag == 'phone' and c['w'] < c['parentW'] - c['parentPad'] - 1:
                    problems.append(f'{label}: not full width on the phone ({c["w"]:.0f} of {c["parentW"]:.0f})')
                if data_name == 'long':
                    if pg.evaluate('document.querySelectorAll(".gid-main .gid-idcard-roles li").length') != 3:
                        problems.append(f'{label}: three positions expected')
                if data_name == 'empty':
                    hid = pg.evaluate('[...document.querySelectorAll(\'.gid-main [data-gid-field="positions"],.gid-main [data-gid-field="passkey"]\')].map(e => getComputedStyle(e).display)')
                    if hid != ['none', 'none']:
                        problems.append(f'{label}: empty positions and passkey must be hidden ({hid})')
                pg.locator('.gid-main .gid-idcard').screenshot(path=os.path.join(OUT, f'card-{tag}-{theme}-{data_name}.png'))
            # GGID.card never parses markup from the data
            pg.evaluate('() => GGID.card(document.querySelector(".gid-main .gid-idcard"), {name: "<img src=x onerror=alert(1)>", positions: ["<b>x</b>"], email: "a<i>@global-generations.com", id: "<s>", since: "<u>"})')
            if pg.evaluate('document.querySelector(".gid-main .gid-idcard").querySelectorAll("img,b,i,s,u").length'):
                problems.append(f'card/{tag}/{theme}: GGID.card inserted markup from data')
            ctx.close()

    # ---- QA 08.10: ширины 360/375/768/1024 и масштаб 200 %, низкие окна, кольцо фокуса, «меньше движения», подсказки в полях ----
    for scheme in ('light', 'dark'):
        for vw, vh, dpr, tag in WIDTHS:
            ctx = b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=dpr, color_scheme=scheme)
            pg = ctx.new_page()
            errs = []
            pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
            pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
            for fn in sorted(os.listdir(SCREENS)):
                key = fn[:-5]
                errs.clear()
                pg.goto('file://' + os.path.join(SCREENS, fn) + '?layout=split')
                pg.wait_for_timeout(250)
                label = f'{tag}/{scheme}/split/{key}'
                r = pg.evaluate(PROBE)
                counts['widths'] += 1
                problems.extend(layout_issues(label, pg.evaluate(LAYOUT, SCREEN_BOXES)))
                if r['scrollW'] > r['clientW']:
                    problems.append(f'{label}: horizontal scroll {r["scrollW"]} > {r["clientW"]}')
                if r['wide']:
                    problems.append(f'{label}: sticks out {r["wide"]}')
                if not r['font'] or 'Montserrat' not in r['usedFont']:
                    problems.append(f'{label}: font {r["usedFont"]}')
                if errs:
                    problems.append(f'{label}: console {errs[:3]}')
                problems.extend(f'{label}: {x}' for x in pg.evaluate(PANEL))
            ctx.close()
        # низкие окна (масштаб 200 %, маленький ноутбук) и телефон 320 px: панель с картой, образец и длинные данные
        for vw, vh in SHORT:
            ctx = b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=2 if vw < 500 else 1, color_scheme=scheme)
            pg = ctx.new_page()
            for key, data in (('login', None), ('continue', LONG_HERO)):
                pg.goto('file://' + os.path.join(SCREENS, key + '.html') + '?layout=split')
                pg.wait_for_timeout(250)
                if data:
                    pg.evaluate('(d) => GGID.card(document.querySelector(".gid-aside .gid-idcard"), d)', data)
                    pg.wait_for_timeout(900)    # «оживание» данных на карте
                counts['short'] += 1
                problems.extend(f'short/{vw}x{vh}/{scheme}/{key}{"-long" if data else ""}: {x}' for x in pg.evaluate(PANEL))
                cta = pg.evaluate('''() => { const b = document.querySelector('.gid-card .gid-btn--primary'); return b ? b.getBoundingClientRect().bottom : 0; }''')
                if vw < 960 and vh >= 560 and cta > vh + 0.5:
                    problems.append(f'short/{vw}x{vh}/{scheme}/{key}: the main button is below the first screen ({cta:.0f} > {vh})')
                hs = pg.evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth]')
                if hs[0] > hs[1]:
                    problems.append(f'short/{vw}x{vh}/{scheme}/{key}: horizontal scroll {hs}')
            ctx.close()
        # кольцо фокуса с клавиатуры: на каждом экране Tab по всем элементам; у кнопок и ссылок сплошная линия 2 px акцентом,
        # у полей рамка акцентом и кольцо 1 px (видно и без мягкого ореола, и в режиме высокой контрастности Windows)
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, color_scheme=scheme)
        pg = ctx.new_page()
        for fn in sorted(os.listdir(SCREENS)):
            key = fn[:-5]
            pg.goto('file://' + os.path.join(SCREENS, fn) + '?layout=split')
            pg.wait_for_timeout(450)
            pg.add_style_tag(content='*,*::before,*::after{transition:none!important}')   # конечный вид фокуса, без середины перехода
            pg.mouse.click(3, 3)
            seen = set()
            for _ in range(20):
                pg.keyboard.press('Tab')
                pg.wait_for_timeout(30)
                f = pg.evaluate(FOCUS)
                if not f or f['id'] in seen:
                    break
                seen.add(f['id'])
                counts['focus'] += 1
                acc = ACCENT[scheme]
                ring = re.search(r'rgb\([^)]*\) 0px 0px 0px 1px', f['shadow'])   # сплошное кольцо 1 px поверх рамки (акцент, у поля с ошибкой красное)
                ok = bool(ring) if f['input'] else (f['outline'][0] == 'solid' and f['outline'][1] >= 2 and f['outline'][2] == acc)
                if not ok:
                    problems.append(f'focus/{scheme}/{key}: {f["tag"]}.{f["cls"].split(" ")[0]} "{f["text"]}" without a visible ring ({f["outline"]}, {f["shadow"][:60]})')
        ctx.close()
        # «меньше движения»: ни одна бесконечная анимация не идёт (пятна, покачивание карты, перелив, линия Face ID, пульс кнопки)
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, color_scheme=scheme, reduced_motion='reduce')
        pg = ctx.new_page()
        for fn in sorted(os.listdir(SCREENS)):
            for layout in ('split', 'card'):
                pg.goto('file://' + os.path.join(SCREENS, fn) + f'?layout={layout}')
                pg.wait_for_timeout(300)
                counts['motion'] += 1
                run = pg.evaluate(MOTION)
                if run:
                    problems.append(f'motion/{scheme}/{layout}/{fn[:-5]}: runs with «reduce motion»: {sorted(set(run))[:5]}')
        # подсказка в поле (placeholder) читается: от 4,5 к фону поля
        pg.goto('file://' + os.path.join(SCREENS, 'forgot.html') + '?layout=split')
        pg.wait_for_timeout(300)
        ph = pg.evaluate(PLACEHOLDER)
        if ph < 4.5:
            problems.append(f'placeholder/{scheme}: contrast {ph:.2f} < 4.5')
        ctx.close()
    # тёмная тема по системе = data-theme="dark": панель та же (страницы хаба темы не ставят)
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, color_scheme='dark')
    pg = ctx.new_page()
    bgs = []
    for q in ('?layout=split', '?layout=split&theme=dark'):
        pg.goto('file://' + os.path.join(SCREENS, 'login.html') + q)
        pg.wait_for_timeout(200)
        bgs.append(pg.evaluate('getComputedStyle(document.querySelector(".gid-aside")).backgroundImage'))
    if bgs[0] != bgs[1]:
        problems.append('dark theme by system: the split panel differs from data-theme="dark"')
    # ₽ и латиница с диакритикой рисуются Montserrat (подмножество latin-ext), а не системным шрифтом
    pg.goto('file://' + os.path.join(SCREENS, 'login.html') + '?layout=split')
    pg.evaluate('''() => { const s = document.createElement('p'); s.id = 'qaRub'; s.className = 'gid-sub'; s.textContent = '1 990 ₽ Łódź';
        document.querySelector('.gid-card').appendChild(s); return document.fonts.load('500 15px Montserrat', '₽Łó'); }''')
    pg.wait_for_timeout(300)
    cdp = ctx.new_cdp_session(pg)
    cdp.send('DOM.enable')
    cdp.send('CSS.enable')
    node = cdp.send('DOM.querySelector', {'nodeId': cdp.send('DOM.getDocument', {'depth': -1})['root']['nodeId'], 'selector': '#qaRub'})['nodeId']
    rub = cdp.send('CSS.getPlatformFontsForNode', {'nodeId': node})['fonts']
    if not rub or any('Montserrat' not in f['familyName'] or not f['isCustomFont'] for f in rub):
        problems.append(f'₽ and latin-ext letters are not drawn with the kit Montserrat: {rub}')
    ctx.close()

    # e-mail card: 600 and 375 px; light, dark (Apple Mail honours color-scheme), inverted (Gmail on iPhone)
    for vw, vh, tag in [(600, 900, 'wide'), (375, 812, 'phone')]:
        for mode in ('light', 'dark', 'gmail-ios'):
            for data_name, data in (('demo', EMAIL_DEMO), ('long', EMAIL_LONG)):
                ctx = b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=2,
                                    color_scheme='dark' if mode == 'dark' else 'light')
                pg = ctx.new_page()
                errs = []
                pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
                pg.route(EMAIL_PNG_URL, lambda route: route.fulfill(path=EMAIL_PNG, content_type='image/png'))
                pg.route(re.compile(r'^https?://(?!id\.global-generations-edu\.com/assets/gg-id/email/).*'),
                         lambda route: (errs.append(f'network: {route.request.url}'), route.abort()))
                pg.set_content(email_page(data), wait_until='load')
                if mode == 'gmail-ios':
                    pg.evaluate(INVERT)
                r = pg.evaluate(CONTRAST)
                counts['email'] += 1
                label = f'email/{tag}/{mode}/{data_name}'
                if r['scrollW'] > r['clientW']:
                    problems.append(f'{label}: horizontal scroll {r["scrollW"]} > {r["clientW"]}')
                if r['low']:
                    problems.append(f'{label}: low contrast {r["low"][:4]}')
                if not r['img']:
                    problems.append(f'{label}: lockup image did not load')
                if mode != 'gmail-ios' and r['plate'] < 3:     # the navy logo reads on the light card (Gmail on iPhone inverts the card, not the image)
                    problems.append(f'{label}: the navy logo has low contrast on the card ({r["plate"]:.2f})')
                if mode == 'dark' and r['bodyLum'] < 0.5:      # color-scheme light: Apple Mail keeps the letter light
                    problems.append(f'{label}: the letter went dark although it says color-scheme light (luminance {r["bodyLum"]:.2f})')
                if not r['actions']:
                    problems.append(f'{label}: no «Задать пароль» button or «Инструкция: как войти» link in the letter')
                if r['left']:
                    problems.append(f'{label}: placeholders left in text')
                if r['dashes']:
                    problems.append(f'{label}: dashes {r["dashes"]}')
                if r['cardW'] > 440.5:
                    problems.append(f'{label}: card wider than 440 px ({r["cardW"]})')
                if errs:
                    problems.append(f'{label}: console {errs[:3]}')
                if data_name == 'demo':
                    pg.screenshot(path=os.path.join(OUT, f'email-{tag}-{mode}.png'), full_page=True)
                    pg.locator('.gidm-card').screenshot(path=os.path.join(OUT, f'email-{tag}-{mode}-card.png'))
                ctx.close()

    # showcase layout: every component card at 1440, 1024 (the narrowest three-column view) and 390, both themes
    for vw, tag in ((1440, 'desktop'), (1024, 'narrow'), (390, 'phone')):
        for scheme in ('light', 'dark'):
            ctx = b.new_context(viewport={'width': vw, 'height': 900}, device_scale_factor=1, color_scheme=scheme)
            pg = ctx.new_page()
            errs = []
            pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
            pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
            for h in ('s=login&l=split&t=light&d=desktop', 's=card&l=card&t=dark&d=phone', 's=password&l=minimal&t=dark&d=all'):
                pg.goto('file://' + os.path.join(ROOT, 'gg-id.html') + '#' + h)
                pg.reload()
                pg.wait_for_timeout(600)
                counts['layout'] += 1
                problems.extend(layout_issues(f'layout/{tag}/{scheme}/{h}', pg.evaluate(LAYOUT, SHOWCASE_BOXES)))
                sw = pg.evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth]')
                if sw[0] > sw[1]:
                    problems.append(f'layout/{tag}/{scheme}/{h}: horizontal scroll {sw}')
            if vw != 1440 or scheme == 'light':
                pg.locator('.sc-comp').screenshot(path=os.path.join(OUT, f'components-{vw}-{scheme}.png'))
            if errs:
                problems.append(f'layout/{tag}/{scheme}: console {errs[:3]}')
            ctx.close()

    # gg-id-service.js on the showcase served from a test origin: menu, keyboard, click outside, 401, focus trap, Esc, backdrop
    ORIGIN = 'https://gg-id.test'

    def serve(route):
        path = route.request.url[len(ORIGIN):].split('?')[0].split('#')[0]
        if path.startswith('/api/'):
            status = 200 if path.startswith('/api/ok') else 401
            return route.fulfill(status=status, content_type='application/json', body='{}')
        local = os.path.join(ROOT, path.lstrip('/'))
        if os.path.isfile(local):
            return route.fulfill(path=local)
        return route.fulfill(status=404, body='')

    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page()
    errs = []
    pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type == 'error' and '401' not in m.text else None)
    pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
    pg.route(ORIGIN + '/**', serve)
    pg.goto(ORIGIN + '/gg-id.html#s=login&l=split&t=light&d=desktop')
    pg.wait_for_timeout(600)
    T = []                                                   # (name, ok)

    def state():
        return pg.evaluate('''() => { const c = document.querySelector('[aria-controls="scAcctMenu"]'), m = document.getElementById('scAcctMenu'),
            a = document.activeElement, items = [...m.querySelectorAll('[role="menuitem"]')];
            return {open: !m.hidden, expanded: c.getAttribute('aria-expanded'), focus: a === c ? 'chip' : items.indexOf(a)}; }''')

    def expect(name, want):
        got = state()
        T.append((name, all(got[k] == v for k, v in want.items()), got))

    expect('menu starts open in the showcase', {'open': True, 'expanded': 'true'})
    pg.click('[aria-controls="scAcctMenu"]')
    expect('click on the chip closes, focus stays on the chip', {'open': False, 'expanded': 'false', 'focus': 'chip'})
    pg.click('[aria-controls="scAcctMenu"]')
    expect('click opens, focus stays on the chip (mouse)', {'open': True, 'expanded': 'true', 'focus': 'chip'})
    pg.keyboard.press('ArrowDown')
    expect('ArrowDown moves to the first item', {'focus': 0})
    pg.keyboard.press('ArrowDown')
    expect('ArrowDown moves to the next item', {'focus': 1})
    pg.keyboard.press('End')
    expect('End moves to the last item', {'focus': 2})
    pg.keyboard.press('ArrowDown')
    expect('ArrowDown wraps to the first item', {'focus': 0})
    pg.keyboard.press('ArrowUp')
    expect('ArrowUp wraps to the last item', {'focus': 2})
    pg.keyboard.press('Home')
    expect('Home moves to the first item', {'focus': 0})
    pg.keyboard.press('Escape')
    expect('Esc closes and returns focus to the chip', {'open': False, 'focus': 'chip'})
    pg.keyboard.press('ArrowDown')
    expect('ArrowDown on the closed chip opens on the first item', {'open': True, 'focus': 0})
    pg.keyboard.press('Tab')
    expect('Tab closes the menu', {'open': False})
    pg.focus('[aria-controls="scAcctMenu"]')
    pg.keyboard.press('Enter')
    expect('Enter on the chip opens with focus on the first item', {'open': True, 'focus': 0})
    pg.mouse.click(5, 5)
    expect('click outside closes', {'open': False})
    pg.click('[aria-controls="scAcctMenu"]')
    pg.evaluate('document.activeElement.blur()')
    pg.keyboard.press('Escape')
    expect('Esc closes even when focus fell to body (Safari, Firefox)', {'open': False})
    # the standard pattern: menu inside .gid-acct, hidden at start, absolute under the chip
    pg.evaluate('''() => { const d = document.createElement('div');
      d.innerHTML = '<div class="gid-acct gid-kit" data-theme="light" id="tAcct" style="position:fixed;top:200px;right:40px">'
        + '<button class="gid-chip" type="button"><span class="gid-avatar gid-avatar--xs">ИО</span><span class="gid-chip-name">Иван</span></button>'
        + '<div class="gid-menu" hidden><a class="gid-menu-item" href="#a">А</a><button class="gid-menu-item" type="button">Б</button></div></div>';
      document.body.appendChild(d.firstChild); GGIDService.init(document.getElementById('tAcct')); }''')
    pg.click('#tAcct .gid-chip')
    acct = pg.evaluate('''() => { const a = document.getElementById('tAcct'), c = a.querySelector('.gid-chip'), m = a.querySelector('.gid-menu');
      const cr = c.getBoundingClientRect(), mr = m.getBoundingClientRect();
      return {open: !m.hidden, roles: m.getAttribute('role') + ',' + [...m.querySelectorAll('.gid-menu-item')].map(i => i.getAttribute('role')).join(','),
              below: mr.top >= cr.bottom, right: Math.abs(mr.right - cr.right) < 1.5, other: !document.getElementById('scAcctMenu').hidden}; }''')
    T.append(('.gid-acct: menu under the chip at the right edge, roles set, one menu open at a time',
              acct['open'] and acct['below'] and acct['right'] and acct['roles'] == 'menu,menuitem,menuitem' and not acct['other'], acct))
    pg.click('#tAcct .gid-menu-item >> nth=1')
    T.append(('choosing an item closes the menu', pg.evaluate('document.querySelector("#tAcct .gid-menu").hidden'), None))

    def dlg():
        return pg.evaluate('''() => { const d = document.getElementById('gid-expired'), a = document.activeElement;
            return {open: !d.hidden, inside: d.contains(a), focus: a ? (a.id || a.className || a.tagName) : '',
                    href: d.querySelector('.gid-sso').getAttribute('href')}; }''')

    pg.focus('#openDlg')
    pg.evaluate("fetch('/api/public/ping').then(() => 1)")
    pg.wait_for_timeout(150)
    T.append(('401 from a path in data-gid-401-ignore does not open the window', not dlg()['open'], dlg()))
    pg.evaluate("fetch('/api/ok').then(() => 1)")
    pg.wait_for_timeout(150)
    T.append(('200 does not open the window', not dlg()['open'], dlg()))
    pg.evaluate("fetch('/api/data').then(() => 1)")
    pg.wait_for_timeout(200)
    d = dlg()
    T.append(('401 from the own origin opens the window with focus on the sign-in button', d['open'] and d['inside'] and 'gid-sso' in d['focus'], d))
    T.append(('data-gid-return adds next=<this page> to the sign-in link', 'client_id=demo&next=%2Fgg-id.html' in d['href'], d['href']))
    pg.keyboard.press('Tab')
    T.append(('Tab stays inside the window', dlg()['inside'], dlg()))
    pg.keyboard.press('Shift+Tab')
    T.append(('Shift+Tab stays inside the window', dlg()['inside'], dlg()))
    pg.evaluate("document.getElementById('openDlg').focus()")
    T.append(('focus cannot go under the window', dlg()['inside'], dlg()))
    pg.keyboard.press('Escape')
    d = dlg()
    T.append(('Esc closes and returns focus where it was', not d['open'] and d['focus'] == 'openDlg', d))
    pg.click('#openDlg')
    pg.wait_for_timeout(100)
    T.append(('the showcase button opens the window', dlg()['open'], dlg()))
    pg.click('#gid-expired .gid-h')
    T.append(('click inside the window keeps it open', dlg()['open'], dlg()))
    pg.mouse.click(8, 450)
    T.append(('click on the backdrop closes', not dlg()['open'], dlg()))
    pg.evaluate("document.dispatchEvent(new CustomEvent('gid:session-expired'))")
    T.append(('event gid:session-expired opens the window', dlg()['open'], dlg()))
    pg.evaluate('GGIDService.closeSessionExpired()')
    T.append(('GGIDService.closeSessionExpired() closes', not dlg()['open'], dlg()))
    for name_, ok, got in T:
        counts['service'] += 1
        if not ok:
            problems.append(f'gg-id-service.js: {name_} ({got})')
    if errs:
        problems.append(f'gg-id-service.js: console {errs[:3]}')
    ctx.close()

    # showcase: page width, all modes render, console clean
    for vw, vh, tag in [(1440, 900, 'desktop'), (390, 844, 'phone')]:
        ctx = b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=2 if vw < 500 else 1)
        pg = ctx.new_page()
        errs = []
        pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
        for h in ('s=login&l=split&t=light&d=desktop', 's=setpass&l=card&t=dark&d=phone', 's=login&l=minimal&t=light&d=all',
                  's=error&l=split&t=dark&d=desktop', 's=card&l=split&t=light&d=desktop', 's=card&l=minimal&t=dark&d=phone'):
            pg.goto('file://' + os.path.join(ROOT, 'gg-id.html') + '#' + h)
            pg.reload()
            pg.wait_for_timeout(700)
            r = pg.evaluate('''() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
              gids: document.querySelectorAll('#stage .gid').length, thumbs: document.querySelectorAll('.sc-thumb').length,
              tabs: document.querySelectorAll('.sc-tab').length, rows: document.querySelectorAll('.sc-api tbody tr').length,
              idcard: document.querySelectorAll('#stage .gid-main .gid-idcard').length,
              dashes: (document.body.innerText.match(/[\\u2014\\u2013]/g) || []).length})''')
            counts['showcase'] += 1
            label = f'showcase/{tag}/{h}'
            if r['sw'] > r['cw']:
                problems.append(f'{label}: horizontal scroll {r["sw"]} > {r["cw"]}')
            if r['gids'] < 1 or r['tabs'] < 18 or r['rows'] < 18:
                problems.append(f'{label}: not rendered {r}')
            if h.startswith('s=card') and r['idcard'] != 1:
                problems.append(f'{label}: the card screen did not open ({r["idcard"]} cards on stage)')
            if r['dashes']:
                problems.append(f'{label}: dashes {r["dashes"]}')
            pg.screenshot(path=os.path.join(OUT, f'showcase-{tag}-{h.split("&")[0][2:]}-{h.split("&")[3][2:]}.png'),
                          full_page=(h.endswith('d=all')))
        # section «Карточка GG ID»: cards and rows inside their padding, the e-mail preview loaded and fitted
        r = pg.evaluate(CARD_PROBE, '#idcard .gid-idcard')
        counts['showcase'] += 1
        for i, c in enumerate(r['cards']):
            if c['outside']:
                problems.append(f'showcase/{tag}/idcard {i}: outside the card padding {c["outside"]}')
            if c['accents'] != ['gid-idcard-status::before']:
                problems.append(f'showcase/{tag}/idcard {i}: accent colour on {c["accents"]}')
        rows = pg.evaluate('''() => [...document.querySelectorAll('#idcard .gid-idrow')].map(row => { const r = row.getBoundingClientRect();
            return [...row.querySelectorAll('*')].filter(e => { const q = e.getBoundingClientRect(); return q.width && (q.right > r.right + 1 || q.left < r.left - 1); }).length; })''')
        if len(rows) != 2 or any(rows):
            problems.append(f'showcase/{tag}: compact rows {rows}')
        mail = pg.evaluate('''() => { const f = document.getElementById('mailFrame'), d = f.contentDocument;
            return {card: !!(d && d.querySelector('.gidm-card')), fit: d ? f.getBoundingClientRect().height - d.body.offsetHeight : -1}; }''')
        if not mail['card'] or abs(mail['fit']) > 2:
            problems.append(f'showcase/{tag}: e-mail preview {mail}')
        if r['cards'] and len(r['cards']) != 3:
            problems.append(f'showcase/{tag}: 3 cards expected in the section, got {len(r["cards"])}')
        pg.locator('#idcard').screenshot(path=os.path.join(OUT, f'showcase-{tag}-idcard-section.png'))
        for i in (0, 1):
            pg.locator('#idcard .sc-idc').nth(i).screenshot(path=os.path.join(OUT, f'showcase-{tag}-idcard-row{i + 1}.png'))
        # the link in the section opens the card screen in the stage
        pg.goto('file://' + os.path.join(ROOT, 'gg-id.html') + '#s=login&l=split&t=light&d=desktop')
        pg.reload()
        pg.wait_for_timeout(400)
        pg.click('#toCard')
        pg.wait_for_timeout(300)
        if pg.evaluate('document.querySelectorAll("#stage .gid-main .gid-idcard").length') != 1:
            problems.append(f'showcase/{tag}: the link in «Карточка GG ID» did not open the card screen')
        pg.goto('file://' + os.path.join(ROOT, 'gg-id.html') + '#s=login&l=split&t=light&d=desktop')
        pg.reload()
        pg.wait_for_timeout(400)
        pg.click('.sc-tab[data-key="password"]')
        pg.click('#stage .gid-btn--primary[type=submit]')
        pg.wait_for_timeout(200)
        if 's=enroll' not in pg.url:
            problems.append(f'showcase/{tag}: password submit did not lead to enroll ({pg.url})')
        pg.screenshot(path=os.path.join(OUT, f'showcase-{tag}-full.png'), full_page=True)
        if errs:
            problems.append(f'showcase/{tag}: console {errs[:5]}')
        ctx.close()

    # how the kit words a sign-in with a passkey: no method of the device without a confirmed key of this browser (src/check_gg_id_passkey.py)
    check_gg_id_passkey.run(b, problems, counts)
    # the scene of the sign-in screen: one geometry in every view and every service (src/check_gg_id_stage.py)
    check_gg_id_stage.run(b, problems, counts)
    b.close()

summary = (f'{counts["screens"]} screen renders, {counts["widths"]} renders at 360/375/768/1024 px and 200 %,{counts["short"]} short windows, '
           f'{counts["focus"]} focus stops, {counts["motion"]} reduced-motion renders, '
           f'{counts["layout"]} showcase layout states, {counts["service"]} gg-id-service.js tests, '
           f'{counts["card"]} card renders, {counts["email"]} e-mail renders, '
           f'{counts["showcase"]} showcase states, {counts["passkey"]} passkey wording checks, {counts["stage"]} stage checks')
if problems:
    print('GG ID CHECK FAILED', '|', summary)
    for x in problems:
        print(' -', x)
    sys.exit(1)
print('ok:', summary, '| shots in', OUT)

if '--preview' in sys.argv:   # pictures for gg-id/README.md and the PR, only after a green run
    PREVIEW = os.path.join(ROOT, 'gg-id', 'preview')
    os.makedirs(PREVIEW, exist_ok=True)
    for src_name, dst_name in [('showcase-desktop-idcard-row1.png', 'card-light-dark.png'),
                               ('showcase-desktop-idcard-row2.png', 'card-long-and-row.png'),
                               ('card-phone-light-demo.png', 'card-phone.png'),
                               ('email-wide-light-card.png', 'email-light.png'),
                               ('email-wide-gmail-ios-card.png', 'email-gmail-ios-dark.png')]:
        shutil.copyfile(os.path.join(OUT, src_name), os.path.join(PREVIEW, dst_name))
    print('preview pictures in', PREVIEW)
