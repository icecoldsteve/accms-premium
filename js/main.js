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
      toggle.addEventListener('click', function () {
        var next = current() === 'light' ? 'dark' : 'light';
        root.setAttribute('data-theme', next);
        try { localStorage.setItem('accms-theme', next); } catch (e) { /* niet bewaard, wel gewisseld */ }
        sync();
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
      var update = function () {
        var v = inputs.map(function (el) { return Number(el.value) || 0; });
        ids.forEach(function (id, i) {
          var out = document.getElementById('out-' + id);
          if (!out) return;
          out.textContent = id === 'subs' ? String(v[i]) : id === 'fee' ? v[i] + '%' : money.format(v[i]);
        });
        var net = v[0] * (v[1] + v[2]) * (1 - v[3] / 100);
        monthly.textContent = money.format(net);
        yearly.textContent = money.format(net * 12);
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
