/* GG ID: поведение компонентов в сервисах (не в хабе): меню аккаунта, окно «Сессия истекла», перехват 401.
   Источник правды: Global-Generation/Infra-Brand-Identity, gg-id/gg-id-service.js (правила и разметка: gg-id/README.md,
   раздел «Поведение в сервисе»). Без зависимостей и без сетевых вызовов. Копия в сервисе руками не правится.

   Подключение: <script src="/static/gg-id/gg-id-service.js" defer></script> (после разметки или с defer).
   Само находит и оживляет:
     .gid-acct  = button.gid-chip[aria-expanded] + меню .gid-menu (внутри .gid-acct или по aria-controls на чипе),
                  пункты меню: role="menuitem" или класс .gid-menu-item;
     окно       = .gid-scrim с id="gid-expired" или атрибутом data-gid-expired (внутри .gid-dialog и кнопка .gid-sso).
   Окно открывается: ответ 401 любого fetch на свой origin, GGIDService.sessionExpired(), событие document «gid:session-expired».
   window.GGID_SERVICE_MANUAL = true до подключения отключает автозапуск: тогда GGIDService.init() и watchFetch() вручную. */
(function () {
  'use strict';
  var doc = document, win = window;
  var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

  function arr(list) { return Array.prototype.slice.call(list || []); }
  function visible(el) { return !!(el && el.getClientRects().length); }
  function fire(el, name) { try { el.dispatchEvent(new CustomEvent(name, { bubbles: true })); } catch (e) {} }

  /* ---------- меню аккаунта ---------- */
  var menus = [];   // [{ acct, chip, menu }]

  function menuOf(acct, chip) {
    var id = chip.getAttribute('aria-controls');
    return (id && doc.getElementById(id)) || acct.querySelector('.gid-menu');
  }
  function items(m) {
    return arr(m.menu.querySelectorAll('[role="menuitem"],.gid-menu-item')).filter(function (el, i, all) {
      return all.indexOf(el) === i && !el.hasAttribute('disabled') && visible(el);
    });
  }
  function isOpen(m) { return !m.menu.hidden; }
  function setOpen(m, open, opts) {
    opts = opts || {};
    if (open) menus.forEach(function (o) { if (o !== m && isOpen(o)) setOpen(o, false); });   // открыто одно меню
    if (isOpen(m) !== open) {
      m.menu.hidden = !open;
      m.chip.setAttribute('aria-expanded', open ? 'true' : 'false');
      fire(m.acct, open ? 'gid:menu-open' : 'gid:menu-close');
    }
    if (open && opts.focusFirst) { var list = items(m); if (list[0]) list[0].focus(); }
    if (!open && opts.focusChip) m.chip.focus();
  }

  function wireMenu(acct) {
    if (acct._gidAcct) return;
    var chip = acct.querySelector('.gid-chip');
    if (!chip) return;
    var menu = menuOf(acct, chip);
    if (!menu) return;
    acct._gidAcct = 1;
    var m = { acct: acct, chip: chip, menu: menu };
    menus.push(m);
    chip.setAttribute('aria-haspopup', 'menu');
    if (menu.id) chip.setAttribute('aria-controls', menu.id);
    if (!menu.getAttribute('role')) menu.setAttribute('role', 'menu');
    arr(menu.querySelectorAll('.gid-menu-item')).forEach(function (it) { if (!it.getAttribute('role')) it.setAttribute('role', 'menuitem'); });
    chip.setAttribute('aria-expanded', isOpen(m) ? 'true' : 'false');

    chip.addEventListener('click', function (e) {
      chip.focus();   // Safari и Firefox на Mac не дают кнопке фокус по клику мышью: ставим сами, иначе Esc и стрелки уходят в body
      if (isOpen(m)) { setOpen(m, false); return; }
      setOpen(m, true, { focusFirst: e.detail === 0 });   // с клавиатуры (Enter, пробел: detail 0) фокус сразу на первый пункт
    });
    menu.addEventListener('click', function (e) {          // выбрали пункт: меню закрывается
      var it = e.target.closest && e.target.closest('[role="menuitem"],.gid-menu-item');
      if (it && menu.contains(it)) setOpen(m, false);
    });
  }

  // клик вне открытого меню и вне его чипа закрывает меню
  doc.addEventListener('click', function (e) {
    menus.forEach(function (m) {
      if (isOpen(m) && !m.menu.contains(e.target) && !m.chip.contains(e.target)) setOpen(m, false);
    });
  });

  // клавиши слушаем на документе: после клика мышью фокус может остаться на body (Safari, Firefox), Esc всё равно закрывает
  doc.addEventListener('keydown', function (e) {
    if (dialog.el && !dialog.el.hidden) return;            // окно поверх: клавиши обрабатывает окно
    var open = null;
    menus.forEach(function (m) { if (isOpen(m)) open = m; });
    if (!open) {
      var chipM = null;
      menus.forEach(function (m) { if (e.target === m.chip) chipM = m; });
      if (chipM && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
        e.preventDefault();
        setOpen(chipM, true, { focusFirst: true });
        if (e.key === 'ArrowUp') { var l = items(chipM); if (l.length) l[l.length - 1].focus(); }
      }
      return;
    }
    var list = items(open), i = list.indexOf(doc.activeElement);
    if (e.key === 'Escape') { e.preventDefault(); setOpen(open, false, { focusChip: true }); }
    else if (e.key === 'Tab') { setOpen(open, false); }    // Tab уводит фокус дальше по странице, меню закрывается
    else if (!list.length) { return; }
    else if (e.key === 'ArrowDown') { e.preventDefault(); list[i < 0 ? 0 : (i + 1) % list.length].focus(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); list[i <= 0 ? list.length - 1 : i - 1].focus(); }
    else if (e.key === 'Home') { e.preventDefault(); list[0].focus(); }
    else if (e.key === 'End') { e.preventDefault(); list[list.length - 1].focus(); }
  });

  /* ---------- окно «Сессия истекла» ---------- */
  var dialog = { el: null, before: null };

  function focusables() {
    return arr(dialog.el.querySelectorAll(FOCUSABLE)).filter(visible);
  }
  function returnUrl(a) {   // data-gid-return="next": к ссылке входа добавляется возврат на эту же страницу
    var p = a.getAttribute('data-gid-return');
    if (!p) return;
    if (!a.hasAttribute('data-gid-href')) a.setAttribute('data-gid-href', a.getAttribute('href') || '');
    var base = a.getAttribute('data-gid-href'), here = location.pathname + location.search + location.hash;
    a.setAttribute('href', base + (base.indexOf('?') < 0 ? '?' : '&') + encodeURIComponent(p) + '=' + encodeURIComponent(here));
  }
  function showExpired() {
    var el = dialog.el;
    if (!el || !el.hidden) return;
    dialog.before = doc.activeElement;
    menus.forEach(function (m) { if (isOpen(m)) setOpen(m, false); });
    arr(el.querySelectorAll('[data-gid-return]')).forEach(returnUrl);
    el.hidden = false;
    var f = focusables();
    if (f[0]) f[0].focus();
    fire(el, 'gid:expired-open');
  }
  function hideExpired() {
    var el = dialog.el;
    if (!el || el.hidden) return;
    el.hidden = true;
    if (dialog.before && dialog.before.focus && doc.contains(dialog.before)) dialog.before.focus();
    dialog.before = null;
    fire(el, 'gid:expired-close');
  }
  function wireDialog(el) {
    if (!el || el._gidDlg) return;
    el._gidDlg = 1;
    dialog.el = el;
    var box = el.querySelector('.gid-dialog');
    if (box) {
      if (!box.getAttribute('role')) box.setAttribute('role', 'dialog');
      box.setAttribute('aria-modal', 'true');
    }
    el.addEventListener('click', function (e) { if (e.target === el) hideExpired(); });   // клик по фону, не по окну
  }
  doc.addEventListener('keydown', function (e) {
    var el = dialog.el;
    if (!el || el.hidden) return;
    if (e.key === 'Escape') { e.preventDefault(); hideExpired(); return; }
    if (e.key !== 'Tab') return;
    var f = focusables();                                   // фокус-ловушка: Tab и Shift+Tab ходят только внутри окна
    if (!f.length) { e.preventDefault(); return; }
    var i = f.indexOf(doc.activeElement);
    if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && (i < 0 || i === f.length - 1)) { e.preventDefault(); f[0].focus(); }
  });
  doc.addEventListener('focusin', function (e) {            // фокус не уходит под окно (клик мышью, программный focus)
    var el = dialog.el;
    if (el && !el.hidden && !el.contains(e.target)) { var f = focusables(); if (f[0]) f[0].focus(); }
  });
  doc.addEventListener('gid:session-expired', showExpired);

  /* ---------- 401 от своих запросов: окно ---------- */
  var watching = false, ignore = [];
  function sameOrigin(url) {
    try { return new URL(url, location.href).origin === location.origin; } catch (e) { return false; }
  }
  function ignored(url) {
    try { var path = new URL(url, location.href).pathname; } catch (e) { return false; }
    return ignore.some(function (p) { return p && path.indexOf(p) === 0; });
  }
  function watchFetch(opts) {
    opts = opts || {};
    if (opts.ignore) ignore = ignore.concat(opts.ignore);
    if (watching || !win.fetch) return;
    watching = true;
    var nativeFetch = win.fetch;
    win.fetch = function (input) {
      var asked = typeof input === 'string' ? input : (input && input.url) || String(input);
      return nativeFetch.apply(this, arguments).then(function (res) {
        var url = (res && res.url) || asked;
        if (res && res.status === 401 && sameOrigin(url) && !ignored(url)) GGIDService.sessionExpired();
        return res;
      });
    };
  }

  /* ---------- запуск ---------- */
  function init(root) {
    root = root || doc;
    arr(root.querySelectorAll('.gid-acct')).forEach(wireMenu);
    if (root.matches && root.matches('.gid-acct')) wireMenu(root);
    var el = (root.querySelector && root.querySelector('#gid-expired,[data-gid-expired]')) ||
             (root.matches && root.matches('#gid-expired,[data-gid-expired]') ? root : null);
    if (el) {
      wireDialog(el);
      var ign = el.getAttribute('data-gid-401-ignore');
      if (ign) ignore = ignore.concat(ign.split(/[\s,]+/));
    }
  }

  var GGIDService = win.GGIDService = {
    init: init,                                                        // оживить разметку внутри root (повторно безопасно)
    openMenu: function (acct) { menus.forEach(function (m) { if (!acct || m.acct === acct) setOpen(m, true); }); },
    closeMenu: function (acct) { menus.forEach(function (m) { if (!acct || m.acct === acct) setOpen(m, false); }); },
    sessionExpired: function () { if (dialog.el) showExpired(); else fire(doc, 'gid:session-expired'); },
    closeSessionExpired: hideExpired,
    watchFetch: watchFetch,                                            // fetch: 401 со своего origin = окно
    version: '2026-10-09.2'                                            // = gg-id/VERSION
  };

  function auto() {
    if (win.GGID_SERVICE_MANUAL) return;
    init(doc);
    if (dialog.el) watchFetch();
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', auto); else auto();
})();
