/* GG ID: поведение экранов входа (версия 2026-10-08.2, gg-id/VERSION). Без зависимостей и без сетевых вызовов:
   запросы к /api/auth/* делает страница хаба, кит только оживляет разметку.
   Подключение: тег script с src="gg-id.js" в конце body, всё размечается data-атрибутами (см. README.md). */
(function () {
  'use strict';

  // Вход по ключу (passkey) называем так, как его зовёт устройство человека: Face ID, Touch ID, Windows Hello.
  function passkeyKind(ua, platform, touch) {
    ua = ua || navigator.userAgent || '';
    platform = platform || (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || '';
    touch = touch == null ? (navigator.maxTouchPoints || 0) : touch;
    if (/iPhone|iPad/.test(ua) || (/Mac/.test(platform) && touch > 1)) return 'faceid';
    if (/Mac/.test(platform) || /Macintosh/.test(ua)) return 'touchid';
    if (/Android/.test(ua)) return 'finger';
    if (/Win/.test(platform) || /Windows/.test(ua)) return 'hello';
    return 'key';
  }
  // Целые фразы, а не одно слово: по-русски «войти с Face ID», но «войти по отпечатку».
  var PASSKEY_TEXT = {
    faceid:  { login: 'Войти с Face ID', enroll: 'Подключить Face ID', wait: 'Подтвердите Face ID' },
    touchid: { login: 'Войти с Touch ID', enroll: 'Подключить Touch ID', wait: 'Приложите палец к Touch ID' },
    hello:   { login: 'Войти с Windows Hello', enroll: 'Подключить Windows Hello', wait: 'Подтвердите Windows Hello' },
    finger:  { login: 'Войти по отпечатку', enroll: 'Подключить вход по отпечатку', wait: 'Приложите палец к сканеру' },
    key:     { login: 'Войти по ключу доступа', enroll: 'Создать ключ доступа', wait: 'Подтвердите ключ доступа' }
  };
  function passkeyText(phrase, kind) {
    var t = PASSKEY_TEXT[kind || passkeyKind()] || PASSKEY_TEXT.key;
    return t[phrase] || t.login;
  }
  // Значок к фразе: лицо для Face ID и Windows Hello, отпечаток для Touch ID и Android, ключ для остальных.
  var PASSKEY_ICON = { faceid: 'scan-face', hello: 'scan-face', touchid: 'fingerprint', finger: 'fingerprint', key: 'key-round' };

  function shake(el) {
    if (!el) return;
    el.classList.remove('is-shake');
    void el.offsetWidth;
    el.classList.add('is-shake');
    setTimeout(function () { el.classList.remove('is-shake'); }, 450);
  }

  // Кнопка «занята»: блокируем повторное нажатие (второй запрос Face ID или вторая сессия), показываем спиннер.
  function busy(btn, on, label) {
    if (!btn) return;
    if (on) {
      if (!btn.hasAttribute('data-gid-idle')) btn.setAttribute('data-gid-idle', btn.innerHTML);
      btn.disabled = true;
      btn.classList.add('is-busy');
      btn.setAttribute('aria-busy', 'true');
      if (label) btn.innerHTML = '<span class="gid-spin" aria-hidden="true"></span><span>' + label + '</span>';
    } else {
      btn.disabled = false;
      btn.classList.remove('is-busy');
      btn.removeAttribute('aria-busy');
      if (btn.hasAttribute('data-gid-idle')) { btn.innerHTML = btn.getAttribute('data-gid-idle'); btn.removeAttribute('data-gid-idle'); }
    }
  }

  // Ошибка под полями: текст в .gid-msg, поля подсвечиваются и коротко трясутся.
  function error(root, text, inputs) {
    var box = root.querySelector('[data-gid-error]');
    if (box) {
      box.hidden = !text;
      var t = box.querySelector('[data-gid-error-text]') || box;
      t.textContent = text || '';
    }
    (inputs || []).forEach(function (i) {
      i.classList.toggle('is-error', !!text);
      i.setAttribute('aria-invalid', text ? 'true' : 'false');
      if (text) shake(i);
    });
  }

  // Правила нового пароля (как на сервере: 12-256 символов, буквы и цифры, заглавные и строчные).
  function passwordChecks(v) {
    return {
      len: v.length >= 12 && v.length <= 256,
      mix: /\p{L}/u.test(v) && /\d/.test(v),
      'case': /\p{Lu}/u.test(v) && /\p{Ll}/u.test(v)
    };
  }
  function passwordLevel(v) {
    if (!v) return 0;
    var c = passwordChecks(v), n = (c.len ? 1 : 0) + (c.mix ? 1 : 0) + (c['case'] ? 1 : 0);
    if (n === 3 && v.length >= 14) return 4;   // как в set-password.html хаба
    return Math.max(1, n);
  }

  function fmt(s) { return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }

  function init(root, opts) {
    root = root || document;
    opts = opts || {};

    // Подписи входа по ключу: data-gid-passkey="login|enroll|wait". В витрине (opts.demo) остаётся Face ID из разметки.
    if (!opts.demo) {
      var kind = passkeyKind();
      root.querySelectorAll('[data-gid-passkey]').forEach(function (el) { el.textContent = passkeyText(el.getAttribute('data-gid-passkey'), kind); });
      root.querySelectorAll('[data-gid-passkey-icon] use').forEach(function (u) { u.setAttribute('href', '#gi-' + PASSKEY_ICON[kind]); });
    }

    // QR-код карты GG ID: <svg data-gid-qr="адрес">.
    root.querySelectorAll('svg[data-gid-qr]').forEach(qrDraw);

    // Глаз в поле пароля.
    root.querySelectorAll('[data-gid-eye]').forEach(function (b) {
      if (b._gid) return; b._gid = 1;
      b.addEventListener('click', function () {
        var input = b.parentNode.querySelector('input');
        var show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        b.setAttribute('aria-pressed', show ? 'true' : 'false');
        b.setAttribute('aria-label', show ? 'Скрыть пароль' : 'Показать пароль');
        input.focus({ preventScroll: true });
      });
    });

    // Только рабочая почта: подсказка сразу, а не после отказа сервера.
    root.querySelectorAll('input[data-gid-domain]').forEach(function (input) {
      if (input._gid) return; input._gid = 1;
      var dom = input.getAttribute('data-gid-domain').toLowerCase();
      var hint = input.closest('.gid-field') && input.closest('.gid-field').querySelector('[data-gid-domain-hint]');
      function check() {
        var v = input.value.trim().toLowerCase(), at = v.lastIndexOf('@');
        var bad = at > 0 && v.slice(at + 1).length > 2 && v.slice(at + 1) !== dom;
        input.classList.toggle('is-error', bad);
        input.setAttribute('aria-invalid', bad ? 'true' : 'false');
        if (hint) { hint.hidden = !bad; }
        return !bad;
      }
      input.addEventListener('blur', check);
      input.addEventListener('input', function () { if (input.classList.contains('is-error')) check(); });
    });

    // Новый пароль: шкала и галочки правил вживую.
    root.querySelectorAll('input[data-gid-newpass]').forEach(function (input) {
      if (input._gid) return; input._gid = 1;
      var scope = input.closest('form') || root;
      var meter = scope.querySelector('[data-gid-meter]'), rules = scope.querySelector('[data-gid-rules]');
      var repeat = scope.querySelector('input[data-gid-repeat]');
      function upd() {
        var v = input.value, c = passwordChecks(v);
        if (meter) meter.setAttribute('data-level', String(passwordLevel(v)));
        if (rules) rules.querySelectorAll('[data-rule]').forEach(function (li) { li.classList.toggle('is-ok', !!c[li.getAttribute('data-rule')]); });
        if (repeat && repeat.value) {
          var bad = repeat.value !== v;
          repeat.classList.toggle('is-error', bad);
          repeat.setAttribute('aria-invalid', bad ? 'true' : 'false');
        }
      }
      input.addEventListener('input', upd);
      if (repeat) repeat.addEventListener('input', upd);
      upd();
    });

    // Код доступа: ввод по ячейкам, вставка целиком, стирание назад. Готовый код = событие gid:code на контейнере.
    root.querySelectorAll('[data-gid-code]').forEach(function (box) {
      if (box._gid) return; box._gid = 1;
      var cells = [].slice.call(box.querySelectorAll('input'));
      box.style.setProperty('--gid-code-n', cells.length);
      function sync() {
        cells.forEach(function (c) { c.classList.toggle('is-filled', !!c.value); });
        var code = cells.map(function (c) { return c.value; }).join('');
        if (code.length === cells.length) box.dispatchEvent(new CustomEvent('gid:code', { bubbles: true, detail: { code: code } }));
      }
      function fill(from, digits) {
        for (var i = 0; i < digits.length && from + i < cells.length; i++) cells[from + i].value = digits[i];
        var next = Math.min(from + digits.length, cells.length - 1);
        cells[next].focus();
        box.classList.remove('is-error');
        sync();
      }
      cells.forEach(function (c, i) {
        c.addEventListener('input', function () {
          var d = c.value.replace(/\D/g, '');
          c.value = '';
          if (d) fill(i, d.split('')); else sync();
        });
        c.addEventListener('keydown', function (e) {
          if (e.key === 'Backspace' && !c.value && i > 0) { cells[i - 1].value = ''; cells[i - 1].focus(); sync(); e.preventDefault(); }
          if (e.key === 'ArrowLeft' && i > 0) cells[i - 1].focus();
          if (e.key === 'ArrowRight' && i < cells.length - 1) cells[i + 1].focus();
        });
        c.addEventListener('paste', function (e) {
          var d = ((e.clipboardData || window.clipboardData).getData('text') || '').replace(/\D/g, '');
          if (!d) return;
          e.preventDefault();
          fill(i, d.split(''));
        });
        c.addEventListener('focus', function () { c.select(); });
      });
      sync();
    });

    // Обратный отсчёт: «отправить ещё раз через 0:42», «попробуем снова через 0:15».
    // По нулю: data-gid-countdown-done="enable:#id" включает кнопку, "reload" перезагружает страницу, плюс событие gid:countdown.
    // opts.demo (витрина): действие не выполняется, отсчёт идёт по кругу.
    root.querySelectorAll('[data-gid-countdown]').forEach(function (el) {
      if (el._gid) clearInterval(el._gid);
      var start = parseInt(el.getAttribute('data-gid-countdown'), 10) || 0, left = start;
      el.textContent = fmt(left);
      el._gid = setInterval(function () {
        if (!el.isConnected) { clearInterval(el._gid); return; }
        left -= 1;
        el.textContent = fmt(Math.max(0, left));
        if (left > 0) return;
        if (opts.demo) { left = start + 1; return; }
        clearInterval(el._gid);
        var act = el.getAttribute('data-gid-countdown-done') || '';
        if (act === 'reload') location.reload();
        else if (act.indexOf('enable:') === 0) { var t = document.querySelector(act.slice(7)); if (t) t.disabled = false; }
        el.dispatchEvent(new CustomEvent('gid:countdown', { bubbles: true }));
      }, 1000);
    });
  }

  // QR-код карты GG ID (байтовый режим, уровень M, версии 1-10), без зависимостей и без сети.
  // <svg data-gid-qr="https://..."><path/></svg> рисуется сам при GGID.init; GGID.card(el, {qr}) меняет адрес.
  var QR = (function () {
    var LEVEL = { L: [1, 0], M: [0, 1], Q: [3, 2], H: [2, 3] };
    var ECW = [[-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18], [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26],
               [-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24], [-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28]];
    var NB = [[-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4], [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5],
              [-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8], [-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8]];
    function raw(v) { var r = (16 * v + 128) * v + 64; if (v >= 2) { var n = Math.floor(v / 7) + 2; r -= (25 * n - 10) * n - 55; if (v >= 7) r -= 36; } return r; }
    function dataCW(v, li) { return Math.floor(raw(v) / 8) - ECW[li][v] * NB[li][v]; }
    function mul(x, y) { var z = 0; for (var i = 7; i >= 0; i--) { z = (z << 1) ^ ((z >>> 7) * 0x11D); z ^= ((y >>> i) & 1) * x; } return z; }
    function rsDiv(deg) {
      var r = []; for (var k = 0; k < deg; k++) r.push(0); r[deg - 1] = 1; var root = 1;
      for (var i = 0; i < deg; i++) { for (var j = 0; j < r.length; j++) { r[j] = mul(r[j], root); if (j + 1 < r.length) r[j] ^= r[j + 1]; } root = mul(root, 2); }
      return r;
    }
    function rsRem(data, div) {
      var r = div.map(function () { return 0; });
      data.forEach(function (b) { var f = b ^ r.shift(); r.push(0); div.forEach(function (c, i) { r[i] ^= mul(c, f); }); });
      return r;
    }
    function penalty(M, n) {
      var r = 0;
      function add(len, h) { if (h[0] === 0) len += n; h.pop(); h.unshift(len); }
      function cnt(h) {
        var k = h[1], core = k > 0 && h[2] === k && h[3] === k * 3 && h[4] === k && h[5] === k;
        return (core && h[0] >= k * 4 && h[6] >= k ? 1 : 0) + (core && h[6] >= k * 4 && h[0] >= k ? 1 : 0);
      }
      function term(c, len, h) { if (c) { add(len, h); len = 0; } len += n; add(len, h); return cnt(h); }
      for (var pass = 0; pass < 2; pass++) for (var a = 0; a < n; a++) {
        var c = false, run = 0, h = [0, 0, 0, 0, 0, 0, 0];
        for (var b = 0; b < n; b++) {
          var m = pass ? M[b][a] : M[a][b];
          if (m === c) { run++; if (run === 5) r += 3; else if (run > 5) r++; } else { add(run, h); if (!c) r += cnt(h) * 40; c = m; run = 1; }
        }
        r += term(c, run, h) * 40;
      }
      for (var y = 0; y < n - 1; y++) for (var x = 0; x < n - 1; x++) {
        var q = M[y][x]; if (q === M[y][x + 1] && q === M[y + 1][x] && q === M[y + 1][x + 1]) r += 3;
      }
      var dark = 0; M.forEach(function (row) { row.forEach(function (v) { if (v) dark++; }); });
      var total = n * n; r += (Math.ceil(Math.abs(dark * 20 - total * 10) / total) - 1) * 10;
      return r;
    }
    function encode(text) {
      var fb = LEVEL.M[0], li = LEVEL.M[1];
      var bytes = Array.from(new TextEncoder().encode(text));
      var v = 1, cap = 0;
      for (; v <= 10; v++) { cap = dataCW(v, li) * 8; if (4 + (v < 10 ? 8 : 16) + bytes.length * 8 <= cap) break; }
      if (v > 10) throw new Error('QR: строка слишком длинная');
      var bits = [];
      function put(val, len) { for (var i = len - 1; i >= 0; i--) bits.push((val >>> i) & 1); }
      put(4, 4); put(bytes.length, v < 10 ? 8 : 16); bytes.forEach(function (b) { put(b, 8); });
      put(0, Math.min(4, cap - bits.length)); put(0, (8 - bits.length % 8) % 8);
      for (var pad = 0xEC; bits.length < cap; pad ^= 0xEC ^ 0x11) put(pad, 8);
      var data = [];
      for (var i = 0; i < bits.length; i += 8) { var by = 0; for (var j = 0; j < 8; j++) by = (by << 1) | bits[i + j]; data.push(by); }
      var nb = NB[li][v], ecl = ECW[li][v], rawCW = Math.floor(raw(v) / 8), nShort = nb - rawCW % nb, shortLen = Math.floor(rawCW / nb);
      var div = rsDiv(ecl), blocks = [];
      for (var bi = 0, k = 0; bi < nb; bi++) {
        var dat = data.slice(k, k + shortLen - ecl + (bi < nShort ? 0 : 1)); k += dat.length;
        var ecc = rsRem(dat, div); if (bi < nShort) dat.push(0); blocks.push(dat.concat(ecc));
      }
      var cw = [];
      for (var ci = 0; ci < blocks[0].length; ci++) blocks.forEach(function (bl, jj) { if (ci !== shortLen - ecl || jj >= nShort) cw.push(bl[ci]); });
      var n = v * 4 + 17, M = [], F = [];
      for (var row = 0; row < n; row++) { M.push([]); F.push([]); for (var col = 0; col < n; col++) { M[row].push(false); F[row].push(false); } }
      function set(x, y, d) { M[y][x] = d; F[y][x] = true; }
      for (var t = 0; t < n; t++) { set(6, t, t % 2 === 0); set(t, 6, t % 2 === 0); }
      function finder(cx, cy) {
        for (var dy = -4; dy <= 4; dy++) for (var dx = -4; dx <= 4; dx++) {
          var x = cx + dx, y = cy + dy;
          if (x >= 0 && x < n && y >= 0 && y < n) { var dd = Math.max(Math.abs(dx), Math.abs(dy)); set(x, y, dd !== 2 && dd !== 4); }
        }
      }
      finder(3, 3); finder(n - 4, 3); finder(3, n - 4);
      var ap = [];
      if (v > 1) { var na = Math.floor(v / 7) + 2, step = Math.ceil((v * 4 + 4) / (na * 2 - 2)) * 2; ap.push(6); for (var pp = n - 7; ap.length < na; pp -= step) ap.splice(1, 0, pp); }
      for (var ai = 0; ai < ap.length; ai++) for (var aj = 0; aj < ap.length; aj++) {
        if ((ai === 0 && aj === 0) || (ai === 0 && aj === ap.length - 1) || (ai === ap.length - 1 && aj === 0)) continue;
        for (var ey = -2; ey <= 2; ey++) for (var ex = -2; ex <= 2; ex++) set(ap[ai] + ex, ap[aj] + ey, Math.max(Math.abs(ex), Math.abs(ey)) !== 1);
      }
      function format(mask) {
        var d = fb << 3 | mask, rem = d;
        for (var fi = 0; fi < 10; fi++) rem = (rem << 1) ^ ((rem >>> 9) * 0x537);
        var b = (d << 10 | rem) ^ 0x5412;
        function g(q) { return ((b >>> q) & 1) !== 0; }
        for (var a1 = 0; a1 <= 5; a1++) set(8, a1, g(a1));
        set(8, 7, g(6)); set(8, 8, g(7)); set(7, 8, g(8));
        for (var a2 = 9; a2 < 15; a2++) set(14 - a2, 8, g(a2));
        for (var a3 = 0; a3 < 8; a3++) set(n - 1 - a3, 8, g(a3));
        for (var a4 = 8; a4 < 15; a4++) set(8, n - 15 + a4, g(a4));
        set(8, n - 8, true);
      }
      format(0);
      if (v >= 7) {
        var vr = v; for (var vi = 0; vi < 12; vi++) vr = (vr << 1) ^ ((vr >>> 11) * 0x1F25);
        var vb = v << 12 | vr;
        for (var vk = 0; vk < 18; vk++) { var vc = ((vb >>> vk) & 1) !== 0, va = n - 11 + vk % 3, vbb = Math.floor(vk / 3); set(va, vbb, vc); set(vbb, va, vc); }
      }
      var bit = 0;
      for (var right = n - 1; right >= 1; right -= 2) {
        if (right === 6) right = 5;
        for (var vert = 0; vert < n; vert++) for (var jx = 0; jx < 2; jx++) {
          var x2 = right - jx, up = ((right + 1) & 2) === 0, y2 = up ? n - 1 - vert : vert;
          if (!F[y2][x2] && bit < cw.length * 8) { M[y2][x2] = ((cw[bit >>> 3] >>> (7 - (bit & 7))) & 1) !== 0; bit++; }
        }
      }
      var MASK = [function (x, y) { return (x + y) % 2 === 0; }, function (x, y) { return y % 2 === 0; }, function (x) { return x % 3 === 0; },
        function (x, y) { return (x + y) % 3 === 0; }, function (x, y) { return (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0; },
        function (x, y) { return x * y % 2 + x * y % 3 === 0; }, function (x, y) { return (x * y % 2 + x * y % 3) % 2 === 0; },
        function (x, y) { return ((x + y) % 2 + x * y % 3) % 2 === 0; }];
      function apply(m) { for (var yy = 0; yy < n; yy++) for (var xx = 0; xx < n; xx++) if (!F[yy][xx] && MASK[m](xx, yy)) M[yy][xx] = !M[yy][xx]; }
      var best = 0, bestP = Infinity;
      for (var mm = 0; mm < 8; mm++) { apply(mm); format(mm); var pen = penalty(M, n); if (pen < bestP) { bestP = pen; best = mm; } apply(mm); }
      apply(best); format(best);
      return { size: n, version: v, mask: best, get: function (x, y) { return M[y][x]; } };
    }
    return { encode: encode };
  })();
  function qrDraw(svg) {
    var text = svg && svg.getAttribute('data-gid-qr');
    if (!text) return;
    var q = QR.encode(text), n = q.size, b = 4, d = '';
    for (var y = 0; y < n; y++) {
      var x = 0;
      while (x < n) {
        if (q.get(x, y)) { var e = x; while (e < n && q.get(e, y)) e++; d += 'M' + (x + b) + ' ' + (y + b) + 'h' + (e - x) + 'v1h' + (x - e) + 'z'; x = e; }
        else x++;
      }
    }
    var size = n + 2 * b, path = svg.querySelector('path');
    if (!path) { path = document.createElementNS('http://www.w3.org/2000/svg', 'path'); path.setAttribute('fill', '#13445d'); svg.appendChild(path); }
    svg.setAttribute('viewBox', '0 0 ' + size + ' ' + size);
    svg.setAttribute('shape-rendering', 'crispEdges');
    path.setAttribute('d', d);
  }

  // Карточка GG ID (.gid-idcard) и компактная строка (.gid-idrow): заполнить поля [data-gid-field] данными хаба.
  // Только textContent, поэтому имя или должность с разметкой остаются текстом. Контракт данных: README.md, «Карточка GG ID».
  var MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
  // «2024-03» или «2024-03-18» = «марта 2024» (после «В команде с»); любая другая строка остаётся как есть.
  function cardSince(v) {
    var m = /^(\d{4})-(\d{2})/.exec(String(v == null ? '' : v));
    return m && +m[2] >= 1 && +m[2] <= 12 ? MONTHS[+m[2] - 1] + ' ' + m[1] : String(v == null ? '' : v);
  }
  // Инициалы: первые буквы двух первых слов имени («Иван Образцов» = «ИО», «Лёв» = «Л»).
  function cardInitials(name) {
    return String(name || '').trim().split(/\s+/).slice(0, 2)
      .map(function (w) { return Array.from(w)[0] || ''; }).join('').toUpperCase();
  }
  function card(root, d) {
    if (!root) return;
    d = d || {};
    function each(field, fn) {
      var own = root.matches && root.matches('[data-gid-field="' + field + '"]') ? [root] : [];
      own.concat([].slice.call(root.querySelectorAll('[data-gid-field="' + field + '"]'))).forEach(fn);
    }
    each('name', function (el) { el.textContent = d.name || ''; });
    each('initials', function (el) { el.textContent = d.initials || cardInitials(d.name); });
    each('positions', function (el) {
      el.textContent = '';
      [].concat(d.positions || []).filter(Boolean).slice(0, 3).forEach(function (p) {
        var li = document.createElement('li'); li.textContent = String(p); el.appendChild(li);
      });
      el.hidden = !el.children.length;
    });
    each('email', function (el) {   // перенос строки перед @ (и после точек в длинном имени): домен в <span> не рвётся на дефисе
      var v = String(d.email || ''), at = v.lastIndexOf('@');
      el.textContent = '';
      if (at > 0) {
        var dom = document.createElement('span'), name = v.slice(0, at), from = 0;
        dom.textContent = v.slice(at);
        for (var i = 0; i < name.length; i++) {
          if ('._-'.indexOf(name.charAt(i)) !== -1) { el.appendChild(document.createTextNode(name.slice(from, i + 1))); el.appendChild(document.createElement('wbr')); from = i + 1; }
        }
        el.appendChild(document.createTextNode(name.slice(from)));
        el.appendChild(document.createElement('wbr'));
        el.appendChild(dom);
      } else el.textContent = v;
    });
    each('id', function (el) { el.textContent = d.id || ''; });
    each('since', function (el) { el.textContent = cardSince(d.since); });
    each('status', function (el) {
      var on = (d.status || 'active') === 'active';
      el.setAttribute('data-status', on ? 'active' : 'disabled');
      el.textContent = on ? 'Активен' : 'Отключён';
    });
    each('passkey', function (el) { el.hidden = !d.passkey; });
    each('qr', function (el) { if (d.qr) { el.setAttribute('data-gid-qr', d.qr); qrDraw(el); } });
    if (root.hasAttribute && root.hasAttribute('aria-label') && d.name) root.setAttribute('aria-label', 'Global Generation ID: ' + d.name);
  }

  window.GGID = {
    init: init, busy: busy, shake: shake, error: error,
    passkeyKind: passkeyKind, passkeyText: passkeyText, passwordChecks: passwordChecks, passwordLevel: passwordLevel,
    card: card, cardSince: cardSince, cardInitials: cardInitials,
    qrDraw: qrDraw, qrMatrix: function (text) { return QR.encode(text); },
    version: '2026-10-08.2'   // версия кита = gg-id/VERSION (та же у GGIDService.version)
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { if (!window.GGID_MANUAL) init(document); });
  else if (!window.GGID_MANUAL) init(document);
})();
