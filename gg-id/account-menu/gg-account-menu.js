/* GG account menu: the account chip and its dropdown, the same in every Global Generation staff service. Kit version 2026-10-10.2 (gg-id/VERSION).
   Source of truth: Global-Generation/Infra-Brand-Identity, gg-id/account-menu/ (options, rules, snippets: gg-id/account-menu/README.md).
   The copy in a service is not edited by hand: a change of the look or behaviour is a PR to the kit and a new copy.

   No dependencies and no requests of its own except the GG ID hub: one GET for the services list (lazily, on the first open) and, on a page
   of the hub itself only, the hub sign-out. Everything a person or the hub can send (name, e-mail, titles, addresses) goes into the page through
   textContent and setAttribute only: nothing is built from HTML strings and nothing is evaluated. Addresses are checked (https, or the page's
   own origin, or http on localhost).

   Look: the same classes as the kit chip and menu (.gid-chip, .gid-menu, .gid-menu-item ...), so it is the AKB menu pixel for pixel;
   gg-account-menu.css carries those blocks verbatim (generated from gg-id.css by src/build_account_menu.py).

   The addresses of the hub are the kit defaults (HUB below): "Мои сервисы" = the cabinet, "Профиль GG ID" = its Face ID / Touch ID panel, the
   services list = GET /api/auth/service-links, the Apple Wallet badge = the pass of the GG ID card. A service passes only what is its own:

   <div id="account"></div>
   <script src="/static/gg-id/gg-account-menu.js"></script>
   <script>
     GGAccountMenu.mount('#account', {
       name: 'Иван Образцов', email: 'ivan@example.com',
       logoutUrl: '/logout',                                         // or onLogout: function () { ... } (the service's own logout, it ends the hub session too)
       items: [{ id: 'settings', label: 'Настройки', icon: 'settings', href: '/settings' }]
       // hubOrigin: settings.GG_AUTH_ORIGIN       only when the hub is not the production one (staging) or has moved
       // servicesUrl, servicesApi, profileUrl, walletUrl: single addresses, when one of them differs
     });
   </script>

   Or without a script of your own: <div data-gg-account-menu data-name="..." data-email="..." data-logout-url="..."></div>
   (items: data-gam-items='[{"label":"Настройки","icon":"settings","href":"/settings"}]'; JSON of the whole config: data-gg-account-menu='{...}').
   window.GG_ACCOUNT_MENU_MANUAL = true before this file turns the automatic mounting off (React and other late markup: call mount yourself). */
(function (win) {
  'use strict';
  var doc = win.document;
  var VERSION = '2026-10-10.2';
  var NS = 'http://www.w3.org/2000/svg';

  /* ---------- the GG ID hub: the canonical addresses, the kit defaults. hubOrigin moves all of them to another origin (staging, a moved hub),
     servicesUrl, servicesApi, profileUrl and walletUrl change one address ---------- */
  var HUB = {
    origin: 'https://id.global-generations-edu.com',
    services: '/cabinet/',                     // "Мои сервисы": the cabinet of the hub, the whole list of the person
    profile: '/cabinet/#face',                 // "Профиль GG ID": the cabinet panel with Face ID / Touch ID (passkey) and the password
    servicesApi: '/api/auth/service-links',    // GET with the hub cookie: {services: [{key, title, url, icon}]}; CORS only for the origins of the registered clients
    wallet: '/api/auth/wallet/apple.pkpass',   // GET with the hub cookie: the signed GG ID card as an Apple Wallet pass (an attachment)
    logout: '/api/auth/logout',                // POST, from a page of the hub itself only (another Origin gets 403 bad_origin)
    login: '/login.html'                       // where a page of the hub goes after its sign-out
  };

  /* ---------- icons: lucide, drawn inline as shapes (no sprite, no request). Unknown name: a plain circle ---------- */
  var ICONS = {
    'chevron-down': [['path', 'm6 9 6 6 6-6']],
    'chevron-right': [['path', 'm9 18 6-6-6-6']],
    'layout-grid': [['rect', 3, 3, 7, 7, 1], ['rect', 14, 3, 7, 7, 1], ['rect', 14, 14, 7, 7, 1], ['rect', 3, 14, 7, 7, 1]],
    'user': [['path', 'M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2'], ['circle', 12, 7, 4]],
    'log-out': [['path', 'm16 17 5-5-5-5'], ['path', 'M21 12H9'], ['path', 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4']],
    'check': [['path', 'M20 6 9 17l-5-5']],
    'external-link': [['path', 'M15 3h6v6'], ['path', 'M10 14 21 3'], ['path', 'M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6']],
    'settings': [['path', 'M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915'], ['circle', 12, 12, 3]],
    'eye': [['path', 'M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0'], ['circle', 12, 12, 3]],
    'clock': [['circle', 12, 12, 10], ['path', 'M12 6v6l4 2']],
    'pencil': [['path', 'M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z'], ['path', 'm15 5 4 4']],
    'user-cog': [['path', 'M10 15H6a4 4 0 0 0-4 4v2'], ['path', 'm14.305 16.53.923-.382'], ['path', 'm15.228 13.852-.923-.383'], ['path', 'm16.852 12.228-.383-.923'], ['path', 'm16.852 17.772-.383.924'], ['path', 'm19.148 12.228.383-.923'], ['path', 'm19.53 18.696-.382-.924'], ['path', 'm20.772 13.852.924-.383'], ['path', 'm20.772 16.148.924.383'], ['circle', 18, 15, 3], ['circle', 9, 7, 4]],
    'key-round': [['path', 'M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z'], ['dot', 16.5, 7.5, 0.5]],
    'scan-face': [['path', 'M3 7V5a2 2 0 0 1 2-2h2'], ['path', 'M17 3h2a2 2 0 0 1 2 2v2'], ['path', 'M21 17v2a2 2 0 0 1-2 2h-2'], ['path', 'M7 21H5a2 2 0 0 1-2-2v-2'], ['path', 'M8 14s1.5 2 4 2 4-2 4-2'], ['path', 'M9 9h.01'], ['path', 'M15 9h.01']],
    'shield-check': [['path', 'M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z'], ['path', 'm9 12 2 2 4-4']],
    'circle-help': [['circle', 12, 12, 10], ['path', 'M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3'], ['path', 'M12 17h.01']],
    'book-open': [['path', 'M12 5v16'], ['path', 'M20.001 19A2 2 0 0022 17V5a2 2 0 00-1.999-2L16 3.002A5 5 0 0012 5a5 5 0 00-4-2H4a2 2 0 00-2 2v12a2 2 0 001.999 2H8a5 5 0 014 2 5 5 0 014-2z']],
    'bell': [['path', 'M10.268 21a2 2 0 0 0 3.464 0'], ['path', 'M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326']],
    'mail': [['path', 'm22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7'], ['rect', 2, 4, 20, 16, 2]],
    'file-text': [['path', 'M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z'], ['path', 'M14 2v5a1 1 0 0 0 1 1h5'], ['path', 'M10 9H8'], ['path', 'M16 13H8'], ['path', 'M16 17H8']],
    'calendar': [['path', 'M8 2v3'], ['path', 'M16 2v3'], ['rect', 3, 3, 18, 18, 2], ['path', 'M3 9h18']],
    'languages': [['path', 'm5 8 6 6'], ['path', 'm4 14 6-6 2-3'], ['path', 'M2 5h12'], ['path', 'M7 2h1'], ['path', 'm22 22-5-10-5 10'], ['path', 'M14 18h6']],
    'users': [['path', 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'], ['path', 'M16 3.128a4 4 0 0 1 0 7.744'], ['path', 'M22 21v-2a4 4 0 0 0-3-3.87'], ['circle', 9, 7, 4]],
    'graduation-cap': [['path', 'M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z'], ['path', 'M22 10v6'], ['path', 'M6 12.5V16a6 3 0 0 0 12 0v-3.5']],
    'activity': [['path', 'M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2']],
    'message-square': [['path', 'M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z']],
    'video': [['path', 'm16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5'], ['rect', 2, 6, 14, 12, 2]],
    'scale': [['path', 'M12 3v18'], ['path', 'm19 8 3 8a5 5 0 0 1-6 0zV7'], ['path', 'M3 7h1a17 17 0 0 0 8-2 17 17 0 0 0 8 2h1'], ['path', 'm5 8 3 8a5 5 0 0 1-6 0zV7'], ['path', 'M7 21h10']],
    'megaphone': [['path', 'M11 6a13 13 0 0 0 8.4-2.8A1 1 0 0 1 21 4v12a1 1 0 0 1-1.6.8A13 13 0 0 0 11 14H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z'], ['path', 'M6 14a12 12 0 0 0 2.4 7.2 2 2 0 0 0 3.2-2.4A8 8 0 0 1 10 14'], ['path', 'M8 6v8']],
    'globe': [['circle', 12, 12, 10], ['path', 'M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20'], ['path', 'M2 12h20']],
    'server': [['rect', 2, 2, 20, 8, 2], ['rect', 2, 14, 20, 8, 2], ['line', 6, 6, 6.01, 6], ['line', 6, 18, 6.01, 18]],
    'wallet': [['path', 'M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1'], ['path', 'M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4']],
    'circle': [['circle', 12, 12, 10]]
  };
  var DEFAULT_SERVICE_ICON = 'layout-grid';

  var LABELS = {
    account: 'Аккаунт',
    services: 'Мои сервисы',
    profile: 'Профиль GG ID',
    profileTitle: 'Профиль, Face ID / Touch ID (passkey) и пароль',
    logout: 'Выйти',
    loading: 'Загружаем сервисы…',
    failed: 'Не удалось загрузить',
    allServices: 'Все сервисы',
    current: 'Вы здесь'
  };
  /* The Apple Wallet badge is English whatever the language of the page (decision of the owner 10.10): these are not labels a service can change */
  var WALLET = { line1: 'Add to', line2: 'Apple Wallet', name: 'Add to Apple Wallet', title: 'Add your Global Generation ID card to Apple Wallet' };

  /* ---------- small helpers ---------- */
  function arr(list) { return Array.prototype.slice.call(list || []); }
  function visible(n) { return !!(n && n.getClientRects().length); }
  function str(v) { return v == null ? '' : String(v); }
  function h(tag, cls, text) {
    var n = doc.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function shape(kind, a) {
    var n = doc.createElementNS(NS, kind === 'dot' ? 'circle' : kind);
    if (kind === 'path') n.setAttribute('d', a[0]);
    else if (kind === 'circle' || kind === 'dot') {
      n.setAttribute('cx', a[0]); n.setAttribute('cy', a[1]); n.setAttribute('r', a[2]);
      if (kind === 'dot') n.setAttribute('fill', 'currentColor');
    } else if (kind === 'rect') {
      n.setAttribute('x', a[0]); n.setAttribute('y', a[1]); n.setAttribute('width', a[2]); n.setAttribute('height', a[3]); n.setAttribute('rx', a[4]);
    } else if (kind === 'line') {
      n.setAttribute('x1', a[0]); n.setAttribute('y1', a[1]); n.setAttribute('x2', a[2]); n.setAttribute('y2', a[3]);
    } else if (kind === 'polyline') n.setAttribute('points', a[0]);
    return n;
  }
  function icon(name, cls, paths) {
    var s = doc.createElementNS(NS, 'svg');
    s.setAttribute('viewBox', '0 0 24 24');
    s.setAttribute('class', cls || 'gid-ic');
    s.setAttribute('aria-hidden', 'true');
    s.setAttribute('focusable', 'false');
    if (paths && paths.length) {                      // iconPaths: the service's own drawing, only path data, 24 x 24 grid
      paths.forEach(function (d) { s.appendChild(shape('path', [str(d)])); });
      return s;
    }
    (ICONS[name] || ICONS.circle).forEach(function (sh) { s.appendChild(shape(sh[0], sh.slice(1))); });
    return s;
  }
  function initials(name, email) {
    var v = str(name).trim().split(/\s+/).filter(Boolean).slice(0, 2).map(function (w) { return Array.from(w)[0] || ''; }).join('').toUpperCase();
    if (v) return v;
    var e = Array.from(str(email).trim())[0];
    return e ? e.toUpperCase() : 'U';
  }
  function isLocalHost(host) { return host === 'localhost' || host === '127.0.0.1' || host === '[::1]'; }
  /* An address the menu may put into href: https anywhere, the page's own origin, http only on localhost. Everything else ('' = not usable). */
  function safeUrl(u) {
    if (typeof u !== 'string' || !u.trim()) return '';
    try {
      var p = new URL(u.trim(), win.location.href);
      if (p.protocol === 'https:') return p.href;
      if (p.protocol === 'http:' && (isLocalHost(p.hostname) || p.origin === win.location.origin)) return p.href;
    } catch (e) { /* not an address */ }
    return '';
  }
  function origin(u) { try { return new URL(u).origin; } catch (e) { return ''; } }
  /* The devices that take an Apple Wallet pass straight from a page: iPhone, iPad, iPod (any browser: on iOS they are all WebKit) and Safari on a Mac.
     The same rule as the cabinet of the hub (Infra-Services-Portal, cabinet/wallet.js). An iPad in the "desktop site" mode calls itself a Mac, its touch screen gives it away. */
  function appleWalletDevice(nav) {
    nav = nav || {};
    var ua = str(nav.userAgent), touch = Number(nav.maxTouchPoints || 0);
    if (/iPhone|iPad|iPod/.test(ua)) return true;
    if (!/Macintosh|Mac OS X/.test(ua)) return false;
    if (touch > 1) return true;
    return /Safari\//.test(ua) && !/Chrome|Chromium|CriOS|Edg|OPR|Opera|Firefox|FxiOS|Vivaldi|Brave|DuckDuckGo/.test(ua);
  }
  /* e-mail into a node: a line break may come before the @ and after dots in a long name, the domain never breaks (as the kit card does) */
  function emailInto(node, email) {
    var v = str(email), at = v.lastIndexOf('@');
    node.textContent = '';
    if (at > 0) {
      var dom = h('span', 'gid-nowrap', v.slice(at)), name = v.slice(0, at), from = 0;
      for (var i = 0; i < name.length; i++) {
        if ('._-'.indexOf(name.charAt(i)) !== -1) {
          node.appendChild(doc.createTextNode(name.slice(from, i + 1)));
          node.appendChild(doc.createElement('wbr'));
          from = i + 1;
        }
      }
      node.appendChild(doc.createTextNode(name.slice(from)));
      node.appendChild(doc.createElement('wbr'));
      node.appendChild(dom);
    } else node.textContent = v;
  }
  function fire(el, name, detail) {
    try { el.dispatchEvent(new win.CustomEvent(name, { bubbles: true, detail: detail || {} })); } catch (e) { /* old browser: no event */ }
  }
  function oops(e) { if (win.console && win.console.error) win.console.error(e); }
  function warn(m) { if (win.console && win.console.warn) win.console.warn(m); }

  /* ---------- the services list: one GET to the hub, cached for the page ---------- */
  var cache = {};     // address -> promise of the normalised list (a failure is cached too: the page falls back to the link)

  function normalizeServices(data) {
    var list = Array.isArray(data) ? data : (data && Array.isArray(data.services) ? data.services : null);
    if (!list) return null;
    var out = [], seen = Object.create(null);
    list.slice(0, 200).forEach(function (s) {
      if (!s || typeof s !== 'object') return;
      var url = safeUrl(s.url), title = str(s.title).replace(/\s+/g, ' ').trim().slice(0, 120), key = str(s.key).slice(0, 64);
      if (!url || !title) return;
      var id = key || url;
      if (seen[id]) return;
      seen[id] = 1;
      out.push({ key: key, title: title, url: url, icon: Object.prototype.hasOwnProperty.call(ICONS, s.icon) ? s.icon : DEFAULT_SERVICE_ICON });
    });
    return out;
  }
  function fetchServices(api, timeout) {
    if (cache[api]) return cache[api];
    var p;
    if (!win.fetch || !win.Promise) p = Promise.reject(new Error('no fetch'));
    else {
      var ctl = typeof win.AbortController === 'function' ? new win.AbortController() : null;
      var timer = setTimeout(function () { if (ctl) ctl.abort(); }, timeout || 6000);
      p = win.fetch(api, { credentials: 'include', cache: 'no-store', headers: { Accept: 'application/json' }, signal: ctl ? ctl.signal : undefined })
        .then(function (res) { if (!res.ok) throw new Error('http ' + res.status); return res.json(); })
        .then(function (data) { var list = normalizeServices(data); if (!list || !list.length) throw new Error('empty'); return list; })
        .then(function (list) { clearTimeout(timer); return list; }, function (e) { clearTimeout(timer); throw e; });
    }
    cache[api] = p;
    return p;
  }

  /* The service the page is in: by key when the service says so, else the entry whose address is the longest prefix of this page. */
  function currentIndex(list, key) {
    var i, best = -1, bestLen = -1, here = win.location;
    if (key) { for (i = 0; i < list.length; i++) if (list[i].key === key) return i; return -1; }
    for (i = 0; i < list.length; i++) {
      var p;
      try { p = new URL(list[i].url); } catch (e) { continue; }
      if (p.origin !== here.origin) continue;
      var path = p.pathname.replace(/\/+$/, '');
      if ((here.pathname === path || here.pathname.indexOf(path + '/') === 0 || path === '') && path.length > bestLen) { best = i; bestLen = path.length; }
    }
    return best;
  }

  /* ---------- the menus on the page ---------- */
  var uid = 0;
  var menus = [];         // mounted instances
  var wired = false;
  var DOWN = win.PointerEvent ? 'pointerdown' : 'mousedown';

  function openOne() {
    for (var i = 0; i < menus.length; i++) if (menus[i].open) return menus[i];
    return null;
  }
  function wireDocument() {
    if (wired) return;
    wired = true;
    // a tap or click outside the open menu closes it; pointerdown (not click) because iOS Safari sends no click for taps on plain page areas
    doc.addEventListener(DOWN, function (e) {
      var m = openOne();
      if (m && !m.root.contains(e.target)) m.hide();
    }, true);
    doc.addEventListener('focusin', function (e) {
      var m = openOne();
      if (m && !m.root.contains(e.target)) m.hide();
    });
    // keys are read on the document: after a mouse click Safari and Firefox on Mac leave the focus on the body, Esc must still close
    doc.addEventListener('keydown', function (e) {
      var m = openOne();
      if (!m || e.defaultPrevented) return;
      var list = m.focusables(), i = list.indexOf(doc.activeElement), key = e.key;
      if (key === 'Escape') { e.preventDefault(); m.hide({ focusChip: true }); }
      else if (key === 'Tab') m.hide();                       // the focus goes on along the page, the menu closes
      else if (key === 'ArrowDown') { e.preventDefault(); if (list.length) list[i < 0 ? 0 : (i + 1) % list.length].focus(); }
      else if (key === 'ArrowUp') { e.preventDefault(); if (list.length) list[i <= 0 ? list.length - 1 : i - 1].focus(); }
      else if (key === 'Home') { e.preventDefault(); if (list.length) list[0].focus(); }
      else if (key === 'End') { e.preventDefault(); if (list.length) list[list.length - 1].focus(); }
      else if (key === 'ArrowRight' || key === 'ArrowLeft') m.sideKey(e, key);
    });
  }

  function Instance(root, opts) {
    this.root = root;
    this.baseClass = root.className || '';
    this.baseTheme = root.getAttribute('data-theme');
    this.cfg = {};
    this.open = false;
    this.dead = false;
    this.id = ++uid;
    this.sections = [];
    this.onResize = this.fit.bind(this);
    this.update(opts || {});
    menus.push(this);
    wireDocument();
  }

  Instance.prototype.emit = function (name, detail) { fire(this.root, name, detail); };

  /* options -> everything the render needs */
  Instance.prototype.resolve = function () {
    var c = this.cfg, o;
    if (c.hubOrigin === false) o = '';                                          // false: no hub addresses at all (a page that has nothing to do with the hub)
    else {
      // another hub (staging): an absolute http(s) address; a relative one would silently mean "this very service". Not said, empty (an unset setting)
      // or not usable: the production hub (a warning in the console when something was said and cannot be used)
      o = (typeof c.hubOrigin === 'string' && /^https?:\/\//i.test(c.hubOrigin.trim())) ? origin(safeUrl(c.hubOrigin)) : '';
      if (!o) {
        if (c.hubOrigin && !this.warnedHub) {                                   // once per menu, not on every update
          this.warnedHub = true;
          warn('GGAccountMenu: hubOrigin ' + JSON.stringify(str(c.hubOrigin).slice(0, 80)) + ' is not an absolute address, the production hub is used');
        }
        o = HUB.origin;
      }
    }
    this.L = {};
    for (var k in LABELS) this.L[k] = (c.labels && typeof c.labels[k] === 'string') ? c.labels[k] : LABELS[k];
    this.hub = o;
    this.onHub = !!o && o === win.location.origin;                              // this page is a page of the hub itself (cabinet, admin): its own sign-out
    this.urls = {
      services: safeUrl(c.servicesUrl) || (o ? o + HUB.services : ''),
      profile: safeUrl(c.profileUrl) || (o ? o + HUB.profile : ''),
      api: c.servicesApi === false || c.servicesApi === '' ? '' : (safeUrl(c.servicesApi) || (o ? o + HUB.servicesApi : '')),
      wallet: c.walletUrl === false || c.walletUrl === '' ? '' : (safeUrl(c.walletUrl) || (o ? o + HUB.wallet : ''))
    };
  };

  /* The Apple Wallet badge: wanted when there is an address of the pass and the device takes it ('auto', the default, as in the cabinet),
     always (wallet: true, the demo, a page that knows better) or never (wallet: false). */
  Instance.prototype.walletOn = function () {
    var w = this.cfg.wallet;
    if (!this.urls.wallet || w === false || w === 'false' || w === 'never') return false;
    if (w === true || w === 'true' || w === 'always') return true;
    return appleWalletDevice(win.navigator);
  };

  /* The badge, the last row of the header block (under the name and the e-mail). Black with a thin grey outline, as Apple draws it, English text.
     walletImage = the official artwork of Apple (their SVG file, unmodified) in place of the drawn one; the same row, the same link. */
  Instance.prototype.walletBadge = function () {
    var self = this, art = safeUrl(this.cfg.walletImage), a = h('a', 'gam-wallet' + (art ? ' gam-wallet--art' : ''));
    a.setAttribute('href', this.urls.wallet);
    a.setAttribute('role', 'menuitem');
    a.setAttribute('lang', 'en');
    a.setAttribute('aria-label', WALLET.name);
    a.setAttribute('title', WALLET.title);
    a.setAttribute('data-gam-id', 'wallet');
    a.setAttribute('data-gam-secondary', '1');                // not the first stop when the menu opens by keyboard: that is "Мои сервисы"
    if (art) {
      var pic = doc.createElement('img');
      pic.setAttribute('src', art);
      pic.setAttribute('alt', '');
      pic.setAttribute('height', '36');
      pic.setAttribute('draggable', 'false');
      a.appendChild(pic);
    } else {
      a.appendChild(icon('wallet', 'gid-ic'));
      var tx = h('span', 'gam-wallet-tx');
      tx.appendChild(h('small', null, WALLET.line1));
      tx.appendChild(doc.createTextNode(' '));
      tx.appendChild(h('b', null, WALLET.line2));
      a.appendChild(tx);
    }
    a.addEventListener('click', function () { self.emit('gam:select', { id: 'wallet', label: WALLET.name }); });
    return a;
  };

  /* an item row without behaviour: icon, label (a bare text node as in the AKB markup), meta on the right */
  Instance.prototype.row = function (def, asLink) {
    var href = asLink === false ? '' : safeUrl(def.href), node;
    if (def.static) {
      node = h('div', 'gid-menu-item gid-menu-item--static');
    } else {
      node = h(href ? 'a' : 'button', 'gid-menu-item');
      node.setAttribute('role', 'menuitem');
      if (href) {
        node.setAttribute('href', href);
        if (def.target === '_blank') { node.setAttribute('target', '_blank'); node.setAttribute('rel', 'noopener noreferrer'); }
      } else node.setAttribute('type', 'button');
    }
    if (def.id != null) node.setAttribute('data-gam-id', str(def.id));
    if (def.title) node.setAttribute('title', str(def.title));
    if (def.icon || def.iconPaths) node.appendChild(icon(def.icon, 'gid-ic', def.iconPaths));
    node.appendChild(doc.createTextNode(str(def.label)));
    if (def.meta != null && def.meta !== '') node.appendChild(h('span', 'gid-menu-meta', str(def.meta)));
    return node;
  };

  /* an item with a click: the service's onClick, the gam:select event, the menu closes (links navigate by themselves) */
  Instance.prototype.item = function (def) {
    var self = this, node = this.row(def);
    if (def.static) return node;
    node.addEventListener('click', function (ev) {
      if (typeof def.onClick === 'function') { try { def.onClick(ev, self.handle); } catch (e) { oops(e); } }
      self.emit('gam:select', { id: def.id == null ? null : def.id, label: str(def.label) });
    });
    return node;
  };

  /* ---------- expandable sections: the services switcher and any item of the service with a panel ---------- */
  Instance.prototype.section = function (menu, def, opt) {
    var self = this, pid = 'gam' + this.id + '-s' + (this.sections.length + 1);
    var btn = this.row({ label: def.label, icon: def.icon, iconPaths: def.iconPaths, meta: def.meta, title: def.title, id: def.id }, false);
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-controls', pid);
    btn.setAttribute('data-gam-keep', '1');                 // a click here opens the panel, it does not close the menu
    btn.appendChild(icon('chevron-right', 'gid-ic gam-chev'));
    var panel = h('div', 'gid-menu-sub gam-sub'); panel.id = pid; panel.setAttribute('role', 'group'); panel.setAttribute('aria-label', str(def.label)); panel.hidden = true;
    var sec = { btn: btn, panel: panel, link: opt.link || null, expanded: false, status: opt.status || 'idle', rows: opt.rows || [],
                load: opt.load, render: opt.render, retry: !!opt.retry, hideOnFail: !!opt.hideOnFail };
    if (sec.link) { sec.link.hidden = true; }
    btn.addEventListener('click', function () { self.toggleSection(sec); });
    menu.appendChild(btn);
    if (sec.link) menu.appendChild(sec.link);
    menu.appendChild(panel);
    this.sections.push(sec);
    this.paint(sec);
    return sec;
  };

  Instance.prototype.paint = function (sec) {
    var L = this.L, failed = sec.status === 'failed', active = doc.activeElement;
    var had = !!active && (active === sec.btn || sec.panel.contains(active));
    if (failed && (sec.link || sec.hideOnFail)) {
      sec.expanded = false;
      sec.btn.hidden = true;
      if (sec.link) sec.link.hidden = false;
    } else {
      sec.btn.hidden = false;
      if (sec.link) sec.link.hidden = true;
    }
    var show = sec.expanded && !sec.btn.hidden;
    sec.panel.hidden = !show;
    sec.btn.setAttribute('aria-expanded', show ? 'true' : 'false');
    while (sec.panel.firstChild) sec.panel.removeChild(sec.panel.firstChild);
    if (show) {
      var note;
      if (sec.status === 'ready') sec.render(sec.panel, sec.rows);
      else if (sec.status === 'failed') { note = h('div', 'gam-note', L.failed); sec.panel.appendChild(note); }
      else { note = h('div', 'gam-note', L.loading); note.setAttribute('role', 'status'); sec.panel.appendChild(note); }
    }
    if (had && failed && sec.link && !sec.link.hidden) sec.link.focus();
    if (this.open) this.fit();
  };

  Instance.prototype.toggleSection = function (sec, on) {
    sec.expanded = on == null ? !sec.expanded : !!on;
    if (sec.expanded) {
      if (sec.status === 'failed' && sec.retry) sec.status = 'idle';
      this.ensure(sec);
    }
    this.paint(sec);
  };

  Instance.prototype.ensure = function (sec) {
    var self = this;
    if (sec.status !== 'idle' || !sec.load) return;
    sec.status = 'loading';
    Promise.resolve().then(sec.load).then(function (rows) {
      if (self.dead) return;
      sec.rows = rows || [];
      sec.status = sec.rows.length ? 'ready' : 'failed';
      self.paint(sec);
      if (sec.announce) self.emit('gam:services', { status: sec.status === 'ready' ? 'ready' : 'failed', count: sec.rows.length });
    }, function () {
      if (self.dead) return;
      sec.status = 'failed';
      self.paint(sec);
      if (sec.announce) self.emit('gam:services', { status: 'failed', count: 0 });
    });
  };

  Instance.prototype.addServices = function (menu) {
    var self = this, c = this.cfg, L = this.L, home = this.urls.services, api = this.urls.api;
    if (c.services === false) return;
    var fixed = Array.isArray(c.services) ? normalizeServices(c.services) : null;
    if (!fixed && !api && !home) return;                     // nowhere to go and nothing to list
    var link = home ? this.item({ id: 'services', label: L.services, icon: 'layout-grid', href: home }) : null;
    var target = c.servicesTarget === '_blank' ? '_blank' : '';
    var sec = this.section(menu, { id: 'services', label: L.services, icon: 'layout-grid' }, {
      link: link, hideOnFail: true,
      status: fixed ? (fixed.length ? 'ready' : 'failed') : (api ? 'idle' : 'failed'),
      rows: fixed || [],
      load: api ? function () { return fetchServices(api, c.servicesTimeout); } : null,
      render: function (panel, list) {
        var here = currentIndex(list, c.currentKey);
        list.forEach(function (s, i) {
          var a = h('a', 'gid-menu-item gam-svc');
          a.setAttribute('role', 'menuitem');
          a.setAttribute('href', s.url);
          a.setAttribute('title', s.title);
          a.setAttribute('data-gam-key', s.key);
          if (target) { a.setAttribute('target', target); a.setAttribute('rel', 'noopener noreferrer'); }
          var tile = h('span', 'gam-tile'); tile.setAttribute('aria-hidden', 'true'); tile.appendChild(icon(s.icon));
          a.appendChild(tile);
          a.appendChild(h('span', 'gam-name', s.title));
          if (i === here) { a.setAttribute('aria-current', 'true'); a.appendChild(h('span', 'gid-menu-meta', L.current)); }
          a.addEventListener('click', function () { self.emit('gam:select', { id: 'service', key: s.key, label: s.title }); });
          panel.appendChild(a);
        });
        if (home) {
          var all = h('a', 'gid-menu-item gam-all');
          all.setAttribute('role', 'menuitem');
          all.setAttribute('href', home);
          all.appendChild(icon('external-link'));
          all.appendChild(doc.createTextNode(L.allServices));
          panel.appendChild(all);
        }
      }
    });
    sec.announce = true;
    this.services = sec;
  };

  Instance.prototype.addPanelItem = function (menu, def) {
    var self = this, p = def.panel || {};
    var fixed = Array.isArray(p.items) ? p.items : null;
    this.section(menu, def, {
      status: fixed ? 'ready' : 'idle', rows: fixed || [], retry: true,
      load: typeof p.load === 'function' ? p.load : null,
      render: function (panel, list) {
        list.forEach(function (r) { if (r) panel.appendChild(self.item(r)); });
      }
    });
  };

  Instance.prototype.addEntry = function (menu, def) {
    if (!def) return;
    if (def.type === 'separator') {
      var s = h('div', 'gid-menu-sep'); s.setAttribute('role', 'separator'); menu.appendChild(s);
    } else if (def.panel) this.addPanelItem(menu, def);
    else menu.appendChild(this.item(def));
  };

  Instance.prototype.logoutEntry = function () {
    var self = this, c = this.cfg, def = { id: 'logout', label: this.L.logout, icon: 'log-out' };
    if (typeof c.onLogout === 'function') def.onClick = c.onLogout;
    else if (c.logoutUrl) {
      if (str(c.logoutMethod).toUpperCase() === 'POST') def.onClick = function () { postForm(c.logoutUrl, c.logoutFields); };
      else def.href = c.logoutUrl;
    } else if (this.onHub) def.onClick = function () { hubSignOut(self.hub, c.logoutNext); };    // a page of the hub itself: the sign-out of the hub
    return def;
  };

  /* The sign-out of a page of the hub itself (cabinet, admin, board): POST /api/auth/logout with its own cookie, then the sign-in page (logoutNext, else the hub's).
     A service never comes here: the hub refuses another Origin (403 bad_origin); a service signs out through its own sign-out, which ends the session of the hub. */
  function hubSignOut(hub, next) {
    var to = safeUrl(next) || (hub + HUB.login);
    function go() { win.location.replace(to); }
    if (!win.fetch) { go(); return; }
    try { win.fetch(hub + HUB.logout, { method: 'POST', credentials: 'same-origin', headers: { Accept: 'application/json' } }).then(go, go); } catch (e) { go(); }
  }

  /* POST logout without a script of the service: a real form submit, the cookie goes along, the service answers with its own redirect */
  function postForm(url, fields) {
    var u = safeUrl(url);
    if (!u) return;
    var f = h('form'); f.method = 'post'; f.action = u; f.style.display = 'none';
    Object.keys(fields || {}).forEach(function (k) { var i = h('input'); i.type = 'hidden'; i.name = k; i.value = str(fields[k]); f.appendChild(i); });
    doc.body.appendChild(f);
    f.submit();
  }

  /* ---------- render ---------- */
  Instance.prototype.update = function (opts) {
    var wasOpen = this.open;
    for (var k in (opts || {})) this.cfg[k] = opts[k];
    this.resolve();
    this.render();
    if (wasOpen) this.show();
  };

  Instance.prototype.render = function () {
    var self = this, c = this.cfg, L = this.L, root = this.root;
    this.open = false;
    this.sections = [];
    this.services = null;
    root.textContent = '';
    var theme = c.theme === 'dark' || c.theme === 'auto' ? c.theme : 'light';
    root.className = (this.baseClass + ' gid-kit gam' + (c.placement === 'start' ? ' gam--start' : '') + (c.variant === 'avatar' ? ' gam--avatar' : '')).trim();
    if (theme === 'auto') root.removeAttribute('data-theme'); else root.setAttribute('data-theme', theme);
    root.setAttribute('data-gam', VERSION);

    var name = str(c.name).replace(/\s+/g, ' ').trim(), email = str(c.email).trim();
    var ini = initials(name, email), first = name ? name.split(' ')[0] : L.account;
    var pre = 'gam' + this.id;

    var chip = h('button', 'gid-chip');
    chip.type = 'button';
    chip.id = pre + '-chip';
    chip.setAttribute('aria-haspopup', 'menu');
    chip.setAttribute('aria-expanded', 'false');
    chip.setAttribute('aria-controls', pre + '-menu');
    // The name of the button is its content, not an aria-label: the visible words (the first name) stay part of it (WCAG 2.5.3, Label in Name),
    // and it is the same in the narrow chip where only the initials are drawn: a line that only screen readers read says "Аккаунт: имя".
    var av = h('span', 'gid-avatar gid-avatar--xs', ini); av.setAttribute('aria-hidden', 'true');
    chip.appendChild(av);
    var shown = h('span', 'gid-chip-name', first); shown.setAttribute('aria-hidden', 'true');
    chip.appendChild(shown);
    chip.appendChild(icon('chevron-down'));
    chip.appendChild(h('span', 'gam-sr', L.account + (name ? ': ' + name : '')));

    var menu = h('div', 'gid-menu');
    menu.id = pre + '-menu';
    menu.setAttribute('role', 'menu');
    menu.setAttribute('aria-label', L.account);
    menu.hidden = true;
    var head = h('div', 'gid-menu-head'); head.setAttribute('role', 'presentation');
    var av2 = h('span', 'gid-avatar', ini); av2.setAttribute('aria-hidden', 'true');
    var tx = h('div', 'gid-menu-head-tx');
    tx.appendChild(h('b', null, name || L.account));
    var second = h('span');
    if (email) emailInto(second, email); else second.textContent = str(c.subtitle);
    if (email || c.subtitle) tx.appendChild(second);
    head.appendChild(av2); head.appendChild(tx);
    if (this.walletOn()) { head.className += ' gam-head--wallet'; head.appendChild(this.walletBadge()); }
    menu.appendChild(head);

    this.root.appendChild(chip);
    this.root.appendChild(menu);
    this.chip = chip;
    this.menu = menu;

    this.addServices(menu);
    if (c.profile !== false && this.urls.profile) menu.appendChild(this.item({ id: 'profile', label: L.profile, icon: 'user', href: this.urls.profile, title: L.profileTitle }));
    (Array.isArray(c.items) ? c.items : []).forEach(function (def) { self.addEntry(menu, def); });
    var sep = h('div', 'gid-menu-sep'); sep.setAttribute('role', 'separator'); menu.appendChild(sep);
    menu.appendChild(this.item(this.logoutEntry()));

    chip.addEventListener('click', function (e) {
      chip.focus();   // Safari and Firefox on Mac give no focus to a button on a mouse click: without it Esc and arrows would go to the body
      if (self.open) self.hide(); else self.show({ focusFirst: e.detail === 0 });   // Enter and Space (detail 0): the focus goes to the first item
    });
    chip.addEventListener('keydown', function (e) {
      if (!self.open && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
        e.preventDefault();
        self.show(e.key === 'ArrowDown' ? { focusFirst: true } : { focusLast: true });
      }
    });
    menu.addEventListener('click', function (e) {
      var it = e.target.closest && e.target.closest('[role="menuitem"]');
      if (it && menu.contains(it) && !it.hasAttribute('data-gam-keep')) self.hide();
    });
  };

  /* ---------- open, close, keys, placement ---------- */
  Instance.prototype.focusables = function () {
    if (!this.menu) return [];
    return arr(this.menu.querySelectorAll('[role="menuitem"]')).filter(function (n) { return !n.disabled && visible(n); });
  };

  Instance.prototype.show = function (o) {
    o = o || {};
    if (this.dead) return;
    if (!this.open) {
      menus.forEach(function (m) { if (m !== this && m.open) m.hide(); }, this);       // one menu open at a time
      this.open = true;
      this.menu.hidden = false;
      this.chip.setAttribute('aria-expanded', 'true');
      win.addEventListener('resize', this.onResize);
      this.fit();
      if (this.services) this.ensure(this.services);                                   // the services list: first open, one request
      this.emit('gam:open');
    }
    if (o.focusFirst || o.focusLast) {
      var list = this.focusables(), t;
      if (o.focusLast) t = list[list.length - 1];
      else t = list.filter(function (n) { return !n.hasAttribute('data-gam-secondary'); })[0] || list[0];     // the Wallet badge is reached by the arrow up, not the first stop
      if (t) t.focus();
    }
  };

  Instance.prototype.hide = function (o) {
    if (!this.open) return;
    this.open = false;
    this.menu.hidden = true;
    this.chip.setAttribute('aria-expanded', 'false');
    win.removeEventListener('resize', this.onResize);
    this.menu.style.right = this.menu.style.left = this.menu.style.maxHeight = this.menu.style.overflowY = '';
    var self = this;
    this.sections.forEach(function (sec) { if (sec.expanded) self.toggleSection(sec, false); });    // every open again with the panels folded
    this.emit('gam:close');
    if (o && o.focusChip) this.chip.focus();
  };

  /* keeps the card inside the screen: shifted sideways when the chip is not at the edge, scrolls inside when the screen is low */
  Instance.prototype.fit = function () {
    if (!this.open) return;
    var m = this.menu, start = this.root.classList.contains('gam--start'), pad = 8;
    m.style.right = m.style.left = m.style.maxHeight = m.style.overflowY = '';
    var wrap = this.root.getBoundingClientRect(), w = m.offsetWidth, vw = doc.documentElement.clientWidth, vh = win.innerHeight;
    var left = start ? wrap.left : wrap.right - w, dx = 0;
    if (left < pad) dx = pad - left; else if (left + w > vw - pad) dx = vw - pad - (left + w);
    if (dx) { if (start) m.style.left = dx + 'px'; else m.style.right = (-dx) + 'px'; }
    var room = vh - (wrap.bottom + 8) - pad;
    if (m.offsetHeight > room && room >= 160) { m.style.maxHeight = room + 'px'; m.style.overflowY = 'auto'; }
  };

  /* ArrowRight on a folded section opens it, ArrowLeft inside an open panel folds it and goes back to the item */
  Instance.prototype.sideKey = function (e, key) {
    var active = doc.activeElement, i, sec;
    for (i = 0; i < this.sections.length; i++) {
      sec = this.sections[i];
      if (key === 'ArrowRight' && active === sec.btn && !sec.expanded) { e.preventDefault(); this.toggleSection(sec, true); return; }
      if (key === 'ArrowLeft' && sec.expanded && (active === sec.btn || sec.panel.contains(active))) {
        e.preventDefault(); this.toggleSection(sec, false); sec.btn.focus(); return;
      }
    }
  };

  Instance.prototype.destroy = function () {
    if (this.dead) return;
    if (this.open) this.hide();
    this.dead = true;
    win.removeEventListener('resize', this.onResize);
    var i = menus.indexOf(this);
    if (i >= 0) menus.splice(i, 1);
    this.root.textContent = '';
    this.root.className = this.baseClass;
    if (this.baseTheme == null) this.root.removeAttribute('data-theme'); else this.root.setAttribute('data-theme', this.baseTheme);
    this.root.removeAttribute('data-gam');
    this.root.__ggAccountMenu = null;
  };

  /* ---------- public API ---------- */
  function resolveEl(el) {
    if (typeof el === 'string') el = doc.querySelector(el);
    if (!el || el.nodeType !== 1) throw new TypeError('GGAccountMenu.mount: the element is not found');
    return el;
  }

  function mount(el, opts) {
    el = resolveEl(el);
    if (el.__ggAccountMenu) { el.__ggAccountMenu.update(opts || {}); return el.__ggAccountMenu.handle; }
    var inst = new Instance(el, opts);
    inst.handle = {
      el: el,
      open: function () { inst.show(); },
      close: function () { inst.hide(); },
      toggle: function () { if (inst.open) inst.hide(); else inst.show(); },
      isOpen: function () { return inst.open; },
      update: function (more) { inst.update(more || {}); },
      destroy: function () { inst.destroy(); },
      refreshServices: function () {
        if (inst.urls.api) delete cache[inst.urls.api];
        inst.update({});
      }
    };
    el.__ggAccountMenu = inst;
    return inst.handle;
  }

  function configFrom(node) {
    var cfg = {}, raw = node.getAttribute('data-gg-account-menu'), items = node.getAttribute('data-gam-items');
    if (raw && raw.charAt(0) === '{') { try { cfg = JSON.parse(raw) || {}; } catch (e) { oops(e); } }
    var map = { name: 'data-name', email: 'data-email', subtitle: 'data-subtitle', hubOrigin: 'data-hub-origin', servicesUrl: 'data-services-url',
                profileUrl: 'data-profile-url', servicesApi: 'data-services-api', services: 'data-services', profile: 'data-profile',
                walletUrl: 'data-wallet-url', wallet: 'data-wallet', walletImage: 'data-wallet-image',
                logoutUrl: 'data-logout-url', logoutMethod: 'data-logout-method', logoutNext: 'data-logout-next',
                theme: 'data-gam-theme', placement: 'data-gam-placement', variant: 'data-gam-variant', currentKey: 'data-current-key' };
    Object.keys(map).forEach(function (k) { if (node.hasAttribute(map[k])) cfg[k] = node.getAttribute(map[k]); });
    ['services', 'servicesApi', 'profile', 'hubOrigin', 'walletUrl', 'wallet'].forEach(function (k) {       // an attribute cannot hold the boolean false (or true)
      if (cfg[k] === 'false') cfg[k] = false;
      else if (k === 'wallet' && cfg[k] === 'true') cfg[k] = true;
    });
    if (items) { try { cfg.items = JSON.parse(items); } catch (e) { oops(e); } }
    return cfg;
  }

  function init(root) {
    root = root || doc;
    var nodes = arr(root.querySelectorAll ? root.querySelectorAll('[data-gg-account-menu]') : []);
    if (root.matches && root.matches('[data-gg-account-menu]')) nodes.unshift(root);
    nodes.forEach(function (n) {
      try { mount(n, configFrom(n)); } catch (e) { oops(e); }
    });
  }

  win.GGAccountMenu = {
    version: VERSION,                                      // = gg-id/VERSION
    mount: mount,                                          // mount(el | selector, options) -> { open, close, toggle, isOpen, update, destroy, refreshServices }
    init: init,                                            // mount every [data-gg-account-menu] inside root (document by default)
    initials: initials,
    icons: Object.keys(ICONS),
    hub: (function () { var o = {}; for (var k in HUB) o[k] = HUB[k]; return o; })(),   // the canonical hub addresses the defaults are made of (a copy: read only)
    walletDevice: appleWalletDevice,                       // walletDevice(navigator): does this device take an Apple Wallet pass from a page (the 'auto' rule)
    reset: function () { cache = {}; }                     // forget the cached services answer (tests, a login in another tab)
  };

  function auto() { if (!win.GG_ACCOUNT_MENU_MANUAL) init(doc); }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', auto); else auto();
})(window);
