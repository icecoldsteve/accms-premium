/* ACCMS motion: alleen transform/opacity, pauzeert buiten beeld, uit bij prefers-reduced-motion. */
(function () {
  var root = document.documentElement;
  var mq = function (q) { return window.matchMedia ? window.matchMedia(q).matches : false; };
  if (mq('(prefers-reduced-motion: reduce)')) return;
  var finePointer = mq('(hover: hover) and (pointer: fine)');

  document.addEventListener('DOMContentLoaded', function () {
    try { reveals(); } catch (e) { console.warn('reveal', e); }
    try { particles(); } catch (e) { console.warn('particles', e); }
    if (finePointer) {
      try { parallax(); } catch (e) { console.warn('parallax', e); }
      try { spotlight(); } catch (e) { console.warn('spotlight', e); }
    }
  });

  // Scroll-reveals: wat bij het laden al in beeld staat, wordt nooit verborgen.
  function reveals() {
    if (!('IntersectionObserver' in window)) return;
    var els = [].slice.call(document.querySelectorAll('[data-reveal]'));
    if (!els.length) return;
    var vh = window.innerHeight || 800;
    root.classList.add('motion');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
    els.forEach(function (el) {
      if (el.getBoundingClientRect().top < vh * 0.9) { el.classList.add('in'); return; }
      var sibs = el.parentElement ? [].slice.call(el.parentElement.children).filter(function (c) { return c.hasAttribute('data-reveal'); }) : [];
      var i = sibs.indexOf(el);
      if (i > 0) el.style.setProperty('--stagger', Math.min(i, 6) * 80 + 'ms');
      io.observe(el);
    });
  }

  // Hero: volgers (grijze stipjes) stromen in een spiraal naar het A-icoon en worden goud.
  function particles() {
    var hero = document.querySelector('.hero');
    var cv = document.querySelector('.hero-canvas');
    var core = document.querySelector('.orbit-core');
    if (!hero || !cv || !core || !cv.getContext) return;
    var ctx = cv.getContext('2d');
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var W = 0, H = 0, cx = 0, cy = 0, R = 0, parts = [], raf = 0, onScreen = true, frame = 0;
    var col = { gold: '#E5A93C', dim: '#B5AD9F' };

    function readColors() {
      var cs = getComputedStyle(root);
      col.gold = cs.getPropertyValue('--accent').trim() || col.gold;
      col.dim = cs.getPropertyValue('--muted').trim() || col.dim;
    }
    function size() {
      var r = hero.getBoundingClientRect();
      W = r.width; H = r.height;
      cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var c = core.getBoundingClientRect();
      cx = c.left - r.left + c.width / 2; cy = c.top - r.top + c.height / 2;
      R = Math.hypot(Math.max(cx, W - cx), Math.max(cy, H - cy));
    }
    function spawn(p, fresh) {
      var a = Math.random() * Math.PI * 2;
      var d = R * (fresh ? 0.25 + Math.random() * 0.8 : 0.85 + Math.random() * 0.3);
      p.a = a; p.d = d; p.d0 = Math.max(d, R * 0.6);
      p.v = 0.25 + Math.random() * 0.45;
      p.w = (Math.random() < 0.5 ? -1 : 1) * (0.0016 + Math.random() * 0.0026);
      p.r = 0.6 + Math.random() * 1.5;
      return p;
    }
    function init() {
      size(); readColors();
      var n = W < 700 ? 38 : 90;
      parts = [];
      for (var i = 0; i < n; i++) parts.push(spawn({}, true));
    }
    function step() {
      frame++;
      if (frame % 45 === 0) readColors();
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        var t = 1 - Math.min(p.d / p.d0, 1);          // 0 = ver weg, 1 = bij de kern
        p.d -= p.v * (1 + t * 2.4);
        p.a += p.w * (1 + t * 3);
        if (p.d < 26) { spawn(p, false); continue; }
        var x = cx + Math.cos(p.a) * p.d, y = cy + Math.sin(p.a) * p.d;
        var fade = Math.min(1, (R - p.d) / 80) * Math.min(1, (p.d - 26) / 50);
        ctx.globalAlpha = (0.18 + t * 0.75) * fade;
        ctx.fillStyle = t > 0.45 ? col.gold : col.dim;
        ctx.beginPath();
        ctx.arc(x, y, p.r * (0.8 + t * 0.9), 0, 6.2832);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(step);
    }
    function play() { if (!raf && onScreen && !document.hidden) raf = requestAnimationFrame(step); }
    function pause() { if (raf) { cancelAnimationFrame(raf); raf = 0; } }

    init();
    play();
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (e) { onScreen = e[0].isIntersecting; onScreen ? play() : pause(); }).observe(hero);
    }
    document.addEventListener('visibilitychange', function () { document.hidden ? pause() : play(); });
    var t;
    window.addEventListener('resize', function () { clearTimeout(t); t = setTimeout(init, 150); });
    document.addEventListener('accms:theme', readColors);
  }

  // Orbit beweegt licht mee met de muis.
  function parallax() {
    var hero = document.querySelector('.hero'), orbit = document.querySelector('.orbit');
    if (!hero || !orbit) return;
    hero.addEventListener('pointermove', function (e) {
      var r = hero.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
      orbit.style.setProperty('--px', (x * 18).toFixed(1) + 'px');
      orbit.style.setProperty('--py', (y * 14).toFixed(1) + 'px');
    });
    hero.addEventListener('pointerleave', function () { orbit.style.setProperty('--px', '0px'); orbit.style.setProperty('--py', '0px'); });
  }

  // Spotlight op de roadmap-kaarten.
  function spotlight() {
    [].forEach.call(document.querySelectorAll('.card'), function (card) {
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
        card.style.setProperty('--my', (e.clientY - r.top) + 'px');
      });
    });
  }
})();
