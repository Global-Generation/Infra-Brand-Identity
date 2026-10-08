/* GG ID: поведение экранов входа (2026-10-08). Без зависимостей и без сетевых вызовов:
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
    each('email', function (el) {   // перенос строки только перед @: домен в <span> не рвётся на дефисе
      var v = String(d.email || ''), at = v.lastIndexOf('@');
      el.textContent = '';
      if (at > 0) {
        var dom = document.createElement('span');
        dom.textContent = v.slice(at);
        el.appendChild(document.createTextNode(v.slice(0, at)));
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
    if (root.hasAttribute && root.hasAttribute('aria-label') && d.name) root.setAttribute('aria-label', 'Global Generation ID: ' + d.name);
  }

  window.GGID = {
    init: init, busy: busy, shake: shake, error: error,
    passkeyKind: passkeyKind, passkeyText: passkeyText, passwordChecks: passwordChecks, passwordLevel: passwordLevel,
    card: card, cardSince: cardSince, cardInitials: cardInitials
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { if (!window.GGID_MANUAL) init(document); });
  else if (!window.GGID_MANUAL) init(document);
})();
