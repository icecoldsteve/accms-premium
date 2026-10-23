/* ACCMS motion: alleen transform/opacity, pauzeert buiten beeld, uit bij prefers-reduced-motion.
   Premium layer + Lenis smooth scroll, magnetic, 3D tilts, cursor glow/trail, ambient orbs. */
(function () {
  var root = document.documentElement;
  var mq = function (q) { return window.matchMedia ? window.matchMedia(q).matches : false; };
  if (mq('(prefers-reduced-motion: reduce)')) return;
  var finePointer = mq('(hover: hover) and (pointer: fine)');

  document.addEventListener('DOMContentLoaded', function () {
    try { initLenis(); } catch (e) { console.warn('lenis', e); }
    try { reveals(); } catch (e) { console.warn('reveal', e); }
    try { particles(); } catch (e) { console.warn('particles', e); }
    try { injectPremium(); } catch (e) { console.warn('premium inject', e); }
    if (finePointer) {
      try { parallax(); } catch (e) { console.warn('parallax', e); }
      try { spotlight(); } catch (e) { console.warn('spotlight', e); }
      try { magnetic(); } catch (e) { console.warn('magnetic', e); }
      try { tiltCards(); } catch (e) { console.warn('tilt', e); }
      try { cursorGlow(); } catch (e) { console.warn('cursor', e); }
      try { headerScroll(); } catch (e) { console.warn('header', e); }
      try { cursorTrail(); } catch (e) { console.warn('trail', e); }
    }
  });

  // Lenis smooth scroll (from darkroomengineering/lenis)
  function initLenis() {
    if (typeof Lenis === 'undefined') return;
    var lenis = new Lenis({
      autoRaf: true,
      lerp: 0.08,
      smoothWheel: true,
      wheelMultiplier: 0.9,
      anchors: true
    });
    // Optional: expose for debugging
    window.lenis = lenis;
  }

  // Inject ambient orbs + cursor glow element
  function injectPremium() {
    var hero = document.querySelector('.hero');
    if (hero && !hero.querySelector('.ambient-orbs')) {
      var orbs = document.createElement('div');
      orbs.className = 'ambient-orbs';
      orbs.innerHTML = '<div class="orb"></div><div class="orb"></div><div class="orb"></div>';
      hero.insertBefore(orbs, hero.firstChild);
    }
    if (finePointer && !document.querySelector('.cursor-glow')) {
      var glow = document.createElement('div');
      glow.className = 'cursor-glow';
      document.body.appendChild(glow);
      document.body.classList.add('has-cursor');
    }
  }

  // Scroll-reveals
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

  // Hero particles (original)
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
        var t = 1 - Math.min(p.d / p.d0, 1);
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

  // Orbit parallax
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

  // Spotlight on cards
  function spotlight() {
    [].forEach.call(document.querySelectorAll('.card'), function (card) {
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
        card.style.setProperty('--my', (e.clientY - r.top) + 'px');
      });
    });
  }

  // Magnetic buttons
  function magnetic() {
    var strength = 0.35;
    [].forEach.call(document.querySelectorAll('.btn, .theme-toggle'), function (el) {
      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var x = e.clientX - (r.left + r.width / 2);
        var y = e.clientY - (r.top + r.height / 2);
        el.style.transform = 'translate(' + (x * strength) + 'px, ' + (y * strength) + 'px)';
      });
      el.addEventListener('pointerleave', function () {
        el.style.transform = '';
      });
    });
  }

  // 3D tilt on cards and plans
  function tiltCards() {
    var maxTilt = 8;
    [].forEach.call(document.querySelectorAll('.card, .plan'), function (el) {
      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width;
        var py = (e.clientY - r.top) / r.height;
        var tiltX = (py - 0.5) * -maxTilt;
        var tiltY = (px - 0.5) * maxTilt;
        el.style.transform = 'perspective(900px) rotateX(' + tiltX + 'deg) rotateY(' + tiltY + 'deg) translateY(-4px) scale(1.015)';
      });
      el.addEventListener('pointerleave', function () {
        el.style.transform = '';
      });
    });
  }

  // Soft cursor glow
  function cursorGlow() {
    var glow = document.querySelector('.cursor-glow');
    if (!glow) return;
    var x = 0, y = 0, tx = 0, ty = 0;
    document.addEventListener('pointermove', function (e) {
      tx = e.clientX;
      ty = e.clientY;
    });
    function loop() {
      x += (tx - x) * 0.15;
      y += (ty - y) * 0.15;
      glow.style.left = x + 'px';
      glow.style.top = y + 'px';
      requestAnimationFrame(loop);
    }
    loop();
  }

  // Lightweight cursor trail (canvas dots)
  function cursorTrail() {
    var canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:6;mix-blend-mode:screen;';
    document.body.appendChild(canvas);
    var ctx = canvas.getContext('2d');
    var dots = [];
    var maxDots = 18;
    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);
    document.addEventListener('pointermove', function (e) {
      dots.push({ x: e.clientX, y: e.clientY, life: 1, size: 3 + Math.random() * 3 });
      if (dots.length > maxDots) dots.shift();
    });
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (var i = dots.length - 1; i >= 0; i--) {
        var d = dots[i];
        d.life -= 0.04;
        if (d.life <= 0) { dots.splice(i, 1); continue; }
        ctx.globalAlpha = d.life * 0.55;
        ctx.fillStyle = '#E5A93C';
        ctx.beginPath();
        ctx.arc(d.x, d.y, d.size * d.life, 0, Math.PI * 2);
        ctx.fill();
      }
      requestAnimationFrame(draw);
    }
    draw();
  }

  // Header elevation on scroll
  function headerScroll() {
    var header = document.querySelector('.site-header');
    if (!header) return;
    var onScroll = function () {
      if (window.scrollY > 40) header.classList.add('scrolled');
      else header.classList.remove('scrolled');
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }
})();
