"""Render favicon.ico, PNG icons and the Open Graph image for the ACCMS site."""
import sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

SITE = Path(sys.argv[1])
ASSETS = SITE / "assets"
icon_svg = (ASSETS / "icon.svg").read_text()
logo_svg = (ASSETS / "accms-logo-dark.svg").read_text()
fonts = (SITE / "fonts").resolve()

OG_HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:B;src:url('file://{fonts}/bricolage-grotesque.woff2') format('woff2');font-weight:200 800}}
@font-face{{font-family:I;src:url('file://{fonts}/instrument-serif-italic.woff2') format('woff2');font-style:italic}}
html,body{{margin:0;width:1200px;height:630px;background:#111111;overflow:hidden}}
.g{{position:absolute;right:-120px;top:-120px;width:640px;height:640px;border-radius:50%;
background:radial-gradient(circle,rgba(229,169,60,.28),rgba(229,169,60,0) 65%)}}
.r{{position:absolute;right:70px;top:95px;width:440px;height:440px;border-radius:50%;border:2px solid rgba(229,169,60,.55)}}
.r2{{position:absolute;right:140px;top:165px;width:300px;height:300px;border-radius:50%;border:2px dashed rgba(229,169,60,.35)}}
.ic{{position:absolute;right:230px;top:255px;width:120px;height:120px}}
.t{{position:absolute;left:80px;top:150px;width:620px;font-family:B;font-weight:700;font-size:76px;line-height:1;color:#F4EFE6;letter-spacing:-2px}}
.t em{{font-family:I;font-weight:400;color:#E5A93C;font-size:84px}}
.lg{{position:absolute;left:66px;top:46px;width:280px}}
.p{{position:absolute;left:80px;bottom:70px;font-family:B;font-weight:600;font-size:24px;letter-spacing:3px;color:#B5AD9F}}
</style></head><body><div class="g"></div><div class="r"></div><div class="r2"></div>
<div class="ic">{icon_svg}</div><div class="lg">{logo_svg}</div>
<div class="t">From followers to <em>paying fans.</em></div>
<div class="p">INSTAGRAM · TIKTOK · ONLYFANS · FANSLY · MYM · 18+</div></body></html>"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 512, "height": 512})
    pg.set_content(f"<html><body style='margin:0;background:transparent'><div style='width:512px;height:512px'>{icon_svg.replace('<svg ', '<svg width=\"512\" height=\"512\" ')}</div></body></html>")
    pg.screenshot(path=str(ASSETS / "icon-512.png"), omit_background=True)
    pg2 = b.new_page(viewport={"width": 1200, "height": 630})
    og_file = Path(__file__).parent / "og.html"
    og_file.write_text(OG_HTML.replace("width:280px", "width:340px"))
    pg2.goto(og_file.resolve().as_uri())
    pg2.evaluate("document.fonts.ready")
    pg2.wait_for_timeout(400)
    pg2.screenshot(path=str(ASSETS / "og-image.png"))
    b.close()

big = Image.open(ASSETS / "icon-512.png").convert("RGBA")
big.resize((192, 192), Image.LANCZOS).save(ASSETS / "icon-192.png")
# apple-touch-icon: opaque background, iOS adds its own mask
touch = Image.new("RGBA", (180, 180), (17, 17, 17, 255))
touch.alpha_composite(big.resize((180, 180), Image.LANCZOS))
touch.convert("RGB").save(ASSETS / "apple-touch-icon.png")
big.save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
print("ok", [f.name for f in ASSETS.iterdir()], (SITE / "favicon.ico").stat().st_size)
