document.addEventListener('DOMContentLoaded', function () {
  var root = document.documentElement;
  var locale = root.getAttribute('data-locale') || 'nl-BE';

  // Licht/donker-toggle
  try {
    var toggle = document.getElementById('theme-toggle');
    if (toggle) {
      var current = function () {
        var attr = root.getAttribute('data-theme');
        if (attr === 'light' || attr === 'dark') return attr;
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
      };
      var sync = function () { toggle.setAttribute('aria-pressed', current() === 'light' ? 'true' : 'false'); };
      sync();
      var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      toggle.addEventListener('click', function () {
        var next = current() === 'light' ? 'dark' : 'light';
        var apply = function () {
          root.setAttribute('data-theme', next);
          try { localStorage.setItem('accms-theme', next); } catch (e) { /* niet bewaard, wel gewisseld */ }
          sync();
          document.dispatchEvent(new CustomEvent('accms:theme'));
        };
        if (!document.startViewTransition || reduce) { apply(); return; }
        // Nieuw thema opent als cirkel vanuit de knop
        var r = toggle.getBoundingClientRect();
        var x = r.left + r.width / 2, y = r.top + r.height / 2;
        var end = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
        root.classList.add('vt-theme');
        var vt = document.startViewTransition(apply);
        vt.ready.then(function () {
          root.animate({ clipPath: ['circle(0px at ' + x + 'px ' + y + 'px)', 'circle(' + end + 'px at ' + x + 'px ' + y + 'px)'] },
            { duration: 700, easing: 'cubic-bezier(0, 0, 0.3, 1)', pseudoElement: '::view-transition-new(root)' });
        }).catch(function () { /* overgang overgeslagen */ });
        vt.finished.then(function () { root.classList.remove('vt-theme'); }, function () { root.classList.remove('vt-theme'); });
      });
    }
  } catch (e) { console.warn('theme toggle', e); }

  // Omzetcalculator
  try {
    var ids = ['subs', 'price', 'extra', 'fee'];
    var inputs = ids.map(function (id) { return document.getElementById('calc-' + id); });
    var monthly = document.getElementById('calc-monthly');
    var yearly = document.getElementById('calc-yearly');
    if (inputs.every(Boolean) && monthly && yearly) {
      var money = new Intl.NumberFormat(locale, { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
      var calmMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var box = monthly.closest ? monthly.closest('.calc-result') : null;
      var shown = null, raf = 0, flashT = 0;
      var paint = function (n) { monthly.textContent = money.format(n); yearly.textContent = money.format(n * 12); };
      var tween = function (to) {
        if (shown === null || calmMotion) { shown = to; paint(to); return; }
        var from = shown, t0 = 0, dur = 400;
        cancelAnimationFrame(raf);
        var tick = function (ts) {
          if (!t0) t0 = ts;
          var k = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(1 - k, 3);
          shown = from + (to - from) * e;
          paint(shown);
          if (k < 1) raf = requestAnimationFrame(tick); else shown = to;
        };
        raf = requestAnimationFrame(tick);
        if (box) { box.classList.add('flash'); clearTimeout(flashT); flashT = setTimeout(function () { box.classList.remove('flash'); }, 160); }
      };
      var update = function () {
        var v = inputs.map(function (el) { return Number(el.value) || 0; });
        ids.forEach(function (id, i) {
          var out = document.getElementById('out-' + id);
          if (!out) return;
          out.textContent = id === 'subs' ? String(v[i]) : id === 'fee' ? v[i] + '%' : money.format(v[i]);
        });
        tween(v[0] * (v[1] + v[2]) * (1 - v[3] / 100));
      };
      inputs.forEach(function (el) { el.addEventListener('input', update); });
      update();
    }
  } catch (e) { console.warn('calculator', e); }

  // E-mailadres kopiëren
  try {
    var copy = document.getElementById('copy-mail');
    var mail = document.getElementById('mail-address');
    if (copy && mail) {
      var label = copy.textContent;
      copy.addEventListener('click', function () {
        var done = function () { copy.textContent = copy.getAttribute('data-done') || label; setTimeout(function () { copy.textContent = label; }, 2000); };
        var fallback = function () {
          var r = document.createRange(); r.selectNodeContents(mail);
          var s = window.getSelection(); if (s) { s.removeAllRanges(); s.addRange(r); }
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(mail.textContent.trim()).then(done, fallback);
        } else { fallback(); }
      });
    }
  } catch (e) { console.warn('copy', e); }
});
