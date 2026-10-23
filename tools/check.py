"""Measurable audit of the ACCMS build: SEO/GEO/CSP/a11y checks + a CSP-enforced render."""
import json
import re
import sys
import threading
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from functools import partial

SITE = Path(sys.argv[1])
SHOTS = Path(sys.argv[2])
SHOTS.mkdir(parents=True, exist_ok=True)
CSP = json.loads((SITE / "vercel.json").read_text())["headers"][0]["headers"][0]["value"]

results = []


def check(name, ok, detail=""):
    results.append((ok, name, detail))


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.ids, self.h1, self.imgs_noalt, self.inline_style, self.inline_script = [], [], 0, 0, 0, 0
        self.ld, self._in_ld, self._in_script_inline = [], False, False
        self.opened, self.closed = 0, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "img" and "alt" not in a:
            self.imgs_noalt += 1
        if "style" in a:
            self.inline_style += 1
        if any(k.startswith("on") for k in a):
            self.inline_script += 1
        if tag == "style":
            self.inline_style += 1
        if tag == "script":
            if a.get("type") == "application/ld+json":
                self._in_ld = True
            elif "src" not in a:
                self.inline_script += 1
        if tag == "div":
            self.opened += 1

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_ld = False
        if tag == "div":
            self.closed += 1

    def handle_data(self, data):
        if self._in_ld and data.strip():
            self.ld.append(data)


pages = {"nl": SITE / "index.html", "fr": SITE / "fr/index.html", "en": SITE / "en/index.html"}
for lang, path in pages.items():
    html = path.read_text(encoding="utf-8")
    p = P(); p.feed(html)
    meta = {a.get("name") or a.get("property"): a.get("content") for t, a in p.tags if t == "meta"}
    links = [(a.get("rel"), a.get("hreflang"), a.get("href")) for t, a in p.tags if t == "link"]
    title = re.search(r"<title>(.*?)</title>", html).group(1)
    pre = f"[{lang}] "
    check(pre + "title 30–60 tekens", 30 <= len(title) <= 60, f"{len(title)}")
    d = meta.get("description") or ""
    check(pre + "meta description 120–160 tekens", 120 <= len(d) <= 160, f"{len(d)}")
    check(pre + "exact 1 h1", p.h1 == 1, str(p.h1))
    check(pre + "canonical", any(r == "canonical" for r, _, _ in links))
    hl = {h for r, h, _ in links if r == "alternate" and h}
    check(pre + "hreflang nl-BE/fr-BE/en/x-default", hl == {"nl-BE", "fr-BE", "en", "x-default"}, ",".join(sorted(hl)))
    for k in ["og:title", "og:description", "og:image", "og:type", "og:url", "og:site_name", "og:locale", "twitter:card"]:
        check(pre + k, bool(meta.get(k)))
    try:
        data = json.loads(p.ld[0]); types = {n["@type"] for n in data["@graph"]}
        check(pre + "JSON-LD geldig (ProfessionalService, WebSite, WebPage, FAQPage)", {"ProfessionalService", "WebSite", "WebPage", "FAQPage"} <= types)
        faq_n = len(next(n for n in data["@graph"] if n["@type"] == "FAQPage")["mainEntity"])
        check(pre + "FAQ-schema = zichtbare FAQ", faq_n == html.count("<details>"), f"{faq_n}/{html.count('<details>')}")
    except Exception as e:  # noqa: BLE001
        check(pre + "JSON-LD geldig", False, str(e))
    check(pre + "geen inline style/script (strikte CSP)", p.inline_style == 0 and p.inline_script == 0, f"style={p.inline_style} script={p.inline_script}")
    check(pre + "div-balans", p.opened == p.closed, f"{p.opened}/{p.closed}")
    dup = {i for i in p.ids if p.ids.count(i) > 1}
    check(pre + "geen dubbele id's", not dup, ",".join(dup))
    check(pre + "alle img met alt", p.imgs_noalt == 0)
    check(pre + "favicon.ico + apple-touch-icon + manifest", all(any(r == x for r, _, _ in links) for x in ["icon", "apple-touch-icon", "manifest"]))
    check(pre + "wettelijke identificatie (naam, adres, KBO, btw, e-mail)", all(x in html for x in ["SMSAK", "Bosheide 9", "1035.506.672", "BE 1035.506.672", "info@accms.agency"]))
    check(pre + "geen IcecoldAI-sporen", not re.search(r"icecold", html, re.I))
    check(pre + "link naar privacyverklaring", 'href="privacy"' in html)
    check(pre + "geen placeholders [ ]", not re.search(r"\[(X|AANTAL|E-MAIL|PRIJS|PRICE|PRIX)\]", html))
    check(pre + "entiteit-definitie in eerste alinea (GEO)", "ACCMS (Adult Content Creator Management Services)" in html)
    check(pre + "self-hosted woff2, geen Google Fonts", "fonts.googleapis" not in html)

for f in ["privacy.html", "fr/privacy.html", "en/privacy.html"]:
    check(f"{f} noindex", "noindex" in (SITE / f).read_text())
for f in ["robots.txt", "sitemap.xml", "llms.txt", "favicon.ico", "site.webmanifest", "404.html", "assets/og-image.png"]:
    check(f"bestand {f}", (SITE / f).exists())
robots = (SITE / "robots.txt").read_text()
check("robots: AI-crawlers toegelaten", all(b in robots for b in ["GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended"]))
check("sitemap: 3 url's met hreflang", (SITE / "sitemap.xml").read_text().count("<loc>") == 3)
check("404 noindex", "noindex" in (SITE / "404.html").read_text())

# --- render with the real CSP header ---
class H(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Content-Security-Policy", CSP)
        super().end_headers()

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 8765), partial(H, directory=str(SITE)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for lang, path in [("nl", "/"), ("fr", "/fr/"), ("en", "/en/")]:
        for scheme in ["dark", "light"]:
            for w, h, tag in [(1440, 900, "desktop"), (390, 844, "mobile")]:
                ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                pg = ctx.new_page()
                errs = []
                pg.on("console", lambda m: errs.append(m.text) if m.type in ("error", "warning") else None)
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto("http://127.0.0.1:8765" + path, wait_until="networkidle")
                pg.wait_for_timeout(1300)
                # scroll door de pagina zodat alle reveals afgaan
                pg.evaluate("""async () => { for (let y = 0; y < document.body.scrollHeight; y += 400) { window.scrollTo({ top: y, behavior: 'instant' }); await new Promise(r => setTimeout(r, 80)); } window.scrollTo({ top: 0, behavior: 'instant' }); }""")
                pg.wait_for_timeout(1800)
                hidden = pg.evaluate("[...document.querySelectorAll('[data-reveal]')].filter(e => getComputedStyle(e).opacity !== '1').length")
                check(f"[{lang}/{scheme}/{tag}] alle reveals zichtbaar na scrollen", hidden == 0, str(hidden))
                over = pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                fonts = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family).join(',')")
                csp = [e for e in errs if "Content Security Policy" in e or "Refused" in e]
                check(f"[{lang}/{scheme}/{tag}] geen horizontale scroll", over <= 0, str(over))
                check(f"[{lang}/{scheme}/{tag}] geen CSP-blokkades of JS-fouten", not errs, " | ".join(errs)[:200])
                if tag == "desktop":
                    check(f"[{lang}/{scheme}] 3 webfonts geladen", all(x in fonts for x in ["Bricolage", "Instrument", "Manrope"]), fonts)
                if lang == "nl":
                    pg.screenshot(path=str(SHOTS / f"{lang}-{scheme}-{tag}.png"), full_page=(tag == "desktop"))
                if lang == "nl" and scheme == "dark" and tag == "desktop":
                    pg.fill("#calc-subs", "500")
                    pg.dispatch_event("#calc-subs", "input")
                    pg.wait_for_timeout(700)
                    check("[nl] hero-canvas tekent deeltjes", pg.evaluate("(() => { const c = document.querySelector('.hero-canvas'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return n; })()") > 200)
                    check("[nl] calculator rekent (500 × €18 × 0,8 = € 7.200)", pg.inner_text("#calc-monthly").replace(" ", " ") == "€ 7.200", pg.inner_text("#calc-monthly"))
                    pg.click("#theme-toggle")
                    pg.wait_for_timeout(1000)
                    check("[nl] toggle zet data-theme=light", pg.evaluate("document.documentElement.dataset.theme") == "light")
                    pg.reload(wait_until="networkidle")
                    check("[nl] thema blijft bewaard na herladen", pg.evaluate("document.documentElement.dataset.theme") == "light")
                ctx.close()
    # prefers-reduced-motion: niets mag verborgen zijn of bewegen
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    pg = ctx.new_page()
    pg.goto("http://127.0.0.1:8765/", wait_until="networkidle")
    pg.wait_for_timeout(800)
    check("[reduced-motion] geen verborgen inhoud", pg.evaluate("[...document.querySelectorAll('[data-reveal]')].every(e => getComputedStyle(e).opacity === '1')"))
    check("[reduced-motion] geen lopende animaties", pg.evaluate("document.getAnimations().filter(a => a.playState === 'running').length") == 0,
          str(pg.evaluate("document.getAnimations().filter(a => a.playState === 'running').map(a => a.animationName || a.constructor.name).join(',')")))
    check("[reduced-motion] canvas verborgen", pg.evaluate("getComputedStyle(document.querySelector('.hero-canvas')).display") == "none")
    ctx.close()
    b.close()

# zonder JavaScript: de verborgen beginstand mag enkel onder .motion (door JS gezet) bestaan
css_txt = (SITE / "css/site.css").read_text()
hide_rules = re.findall(r"([^{}]*\[data-reveal\][^{}]*)\{[^}]*opacity:\s*0", css_txt)
check("[zonder JS] reveal-verberging alleen via .motion", bool(hide_rules) and all(".motion" in r for r in hide_rules), " | ".join(r.strip() for r in hide_rules))
kf = re.findall(r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})+)\s*\}", css_txt)
bad = [n for n, body in kf if re.search(r"(?<![\w-])(top|left|right|bottom|width|height|margin[\w-]*|padding[\w-]*)\s*:", body)]
check(f"motion: {len(kf)} keyframes, alleen transform/opacity/rotate/scale/background-position", len(kf) >= 8 and not bad, ",".join(bad))
srv.shutdown()

passed = sum(1 for r in results if r[0])
for ok, name, detail in results:
    if not ok:
        print("FAIL", name, detail)
print(f"\n{passed}/{len(results)} checks geslaagd")
