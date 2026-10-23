# -*- coding: utf-8 -*-
"""ACCMS business cards: A4 imposition (2x5, butt-cut, crop marks) in dark and light, plus previews."""
import io
import sys
from pathlib import Path

import segno
from playwright.sync_api import sync_playwright

SITE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
FONTS = SITE / "fonts"

W, H = 85, 55            # card mm
COLS, ROWS = 2, 5
PW, PH = 210, 297        # A4 mm
GX = (PW - COLS * W) / 2  # 20 mm
GY = (PH - ROWS * H) / 2  # 11 mm
BLEED = 2                 # mm of background beyond the outer grid edge (dark only)

THEMES = {
    "dark": dict(bg="#111111", fg="#F4EFE6", muted="#B5AD9F", gold="#E5A93C", gold_ink="#E5A93C",
                 hair="rgba(229,169,60,.55)", hair2="rgba(229,169,60,.28)", glow=True, qr_bg="#F4EFE6"),
    "light": dict(bg="#FFFFFF", fg="#111111", muted="#555555", gold="#E5A93C", gold_ink="#946414",
                  hair="rgba(148,100,20,.55)", hair2="rgba(148,100,20,.28)", glow=False, qr_bg="transparent"),
}


def qr_svg():
    q = segno.make("https://www.accms.agency", error="m")
    buf = io.BytesIO()
    q.save(buf, kind="svg", dark="#111111", light=None, border=0, xmldecl=False, svgns=True, omitsize=True)
    return buf.getvalue().decode()


QR = qr_svg()


def css(t):
    glow = (f"radial-gradient(circle at 82% 30%, rgba(229,169,60,.22), rgba(229,169,60,0) 55%)" if t["glow"] else "none")
    return f"""
@font-face{{font-family:B;src:url('{(FONTS/'bricolage-grotesque.woff2').as_uri()}') format('woff2');font-weight:200 800}}
@font-face{{font-family:I;src:url('{(FONTS/'instrument-serif-italic.woff2').as_uri()}') format('woff2');font-style:italic}}
@font-face{{font-family:M;src:url('{(FONTS/'manrope.woff2').as_uri()}') format('woff2');font-weight:200 800}}
@page{{size:A4;margin:0}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{-webkit-print-color-adjust:exact;print-color-adjust:exact;background:#fff}}
.sheet{{position:relative;width:{PW}mm;height:{PH}mm;overflow:hidden;page-break-after:always;background:#fff}}
.bleed{{position:absolute;left:{GX-BLEED}mm;top:{GY-BLEED}mm;width:{COLS*W+2*BLEED}mm;height:{ROWS*H+2*BLEED}mm;background:{t['bg']}}}
.slot{{position:absolute;width:{W}mm;height:{H}mm}}
.mark{{position:absolute;background:#000}}
.card{{position:relative;width:{W}mm;height:{H}mm;overflow:hidden;background:{t['bg']};color:{t['fg']};font-family:M,sans-serif}}
.card .glow{{position:absolute;inset:0;background:{glow}}}
.arc{{position:absolute;border-radius:50%;border:.22mm solid {t['hair']}}}
.arc.a2{{border-style:dashed;border-color:{t['hair2']}}}
.front .a1{{width:50mm;height:50mm;left:45mm;top:2.5mm}}
.front .a2{{width:32mm;height:32mm;left:54mm;top:11.5mm}}
.front .dot{{position:absolute;width:1.6mm;height:1.6mm;border-radius:50%;background:{t['gold']}}}
.front .d1{{left:53.1mm;top:7.5mm}} .front .d2{{left:77.2mm;top:40.6mm}}
.icon{{position:absolute;display:grid;place-items:center;border-radius:50%;border:.35mm solid {t['gold']};
  font-family:B;font-weight:750;color:{t['gold']};background:{t['bg']}}}
.front .core{{left:62.5mm;top:20mm;width:15mm;height:15mm;font-size:18pt}}
.word{{position:absolute;left:7mm;top:13mm;font-family:B;font-weight:760;font-size:24pt;letter-spacing:.06em;line-height:1;color:{t['fg']}}}
.full{{position:absolute;left:7.3mm;top:23.6mm;width:46mm;font-family:B;font-weight:600;font-size:5.6pt;letter-spacing:.2em;text-transform:uppercase;line-height:1.55;color:{t['muted']}}}
.rule{{position:absolute;left:7.3mm;top:33.6mm;width:10mm;height:.3mm;background:{t['gold']}}}
.tag{{position:absolute;left:7mm;bottom:7mm;font-family:I;font-style:italic;font-size:11.5pt;line-height:1.05;color:{t['gold_ink']}}}
.age{{position:absolute;right:6mm;bottom:6.2mm;font-family:B;font-weight:650;font-size:6pt;letter-spacing:.14em;color:{t['muted']}}}
.back .a1{{width:70mm;height:70mm;left:-38mm;top:-8mm}}
.back .head{{position:absolute;left:7mm;top:6.5mm;display:flex;align-items:center;gap:2.2mm}}
.back .head .icon{{position:relative;width:6.2mm;height:6.2mm;font-size:8pt;border-width:.28mm}}
.back .head span{{font-family:B;font-weight:760;font-size:9pt;letter-spacing:.1em}}
.rows{{position:absolute;left:7mm;top:19mm;display:grid;gap:2.7mm}}
.row{{display:grid;gap:.4mm}}
.row .k{{font-family:B;font-weight:650;font-size:5.4pt;letter-spacing:.2em;text-transform:uppercase;color:{t['gold_ink']}}}
.row .v{{font-family:B;font-weight:600;font-size:9.2pt;letter-spacing:.01em;color:{t['fg']}}}
.qrbox{{position:absolute;right:6.5mm;top:13mm;width:21mm;height:21mm;border-radius:2mm;background:{t['qr_bg']};padding:1.8mm}}
.qrbox svg{{width:100%;height:100%;display:block}}
.qrcap{{position:absolute;right:6.5mm;top:35.6mm;width:21mm;text-align:center;font-family:B;font-weight:650;font-size:5pt;letter-spacing:.18em;text-transform:uppercase;color:{t['muted']}}}
.plat{{position:absolute;left:7mm;right:7mm;bottom:5.6mm;border-top:.2mm solid {t['hair2']};padding-top:1.6mm;
  font-family:B;font-weight:600;font-size:5pt;letter-spacing:.16em;text-transform:uppercase;color:{t['muted']};display:flex;justify-content:space-between}}
"""


def front():
    return """<div class="card front"><div class="glow"></div><div class="arc a1"></div><div class="arc a2"></div>
<i class="dot d1"></i><i class="dot d2"></i><div class="icon core">A</div>
<div class="word">ACCMS</div><div class="full">Adult Content Creator Management Services</div><div class="rule"></div>
<div class="tag">Van volgers naar<br>betalende fans.</div><div class="age">18+</div></div>"""


def back():
    return f"""<div class="card back"><div class="glow"></div>
<div class="head"><div class="icon">A</div><span>ACCMS</span></div>
<div class="rows">
<div class="row"><span class="k">Website</span><span class="v">www.accms.agency</span></div>
<div class="row"><span class="k">WhatsApp</span><span class="v">+32 467 01 04 68</span></div>
<div class="row"><span class="k">E-mail</span><span class="v">info@accms.agency</span></div>
</div>
<div class="qrbox">{QR}</div><div class="qrcap">Scan · site</div>
<div class="plat"><span>Instagram</span><span>TikTok</span><span>OnlyFans</span><span>Fansly</span><span>MYM</span></div></div>"""


def marks():
    out, L, GAP, TH = [], 4.5, 2.6 + BLEED, .2  # mark length, gap from grid, line thickness
    xs = [GX + i * W for i in range(COLS + 1)]
    ys = [GY + j * H for j in range(ROWS + 1)]
    for x in xs:  # vertical marks above and below the grid
        out.append(f'<i class="mark" style="left:{x-TH/2}mm;top:{GY-GAP-L}mm;width:{TH}mm;height:{L}mm"></i>')
        out.append(f'<i class="mark" style="left:{x-TH/2}mm;top:{GY+ROWS*H+GAP}mm;width:{TH}mm;height:{L}mm"></i>')
    for y in ys:  # horizontal marks left and right of the grid
        out.append(f'<i class="mark" style="top:{y-TH/2}mm;left:{GX-GAP-L-6}mm;height:{TH}mm;width:{L+6}mm"></i>')
        out.append(f'<i class="mark" style="top:{y-TH/2}mm;left:{GX+COLS*W+GAP}mm;height:{TH}mm;width:{L+6}mm"></i>')
    return "".join(out)


def sheet(theme, side):
    card = front() if side == "front" else back()
    bleed = '<div class="bleed"></div>' if theme == "dark" else ""
    slots = "".join(f'<div class="slot" style="left:{GX+c*W}mm;top:{GY+r*H}mm">{card}</div>' for r in range(ROWS) for c in range(COLS))
    return f'<section class="sheet">{bleed}{slots}{marks()}</section>'


with sync_playwright() as p:
    b = p.chromium.launch()
    for theme, t in THEMES.items():
        html = f"<!doctype html><html><head><meta charset='utf-8'><style>{css(t)}</style></head><body>{sheet(theme, 'front')}{sheet(theme, 'back')}</body></html>"
        f = OUT / f"_sheet_{theme}.html"
        f.write_text(html, encoding="utf-8")
        pg = b.new_page()
        pg.goto(f.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        pg.pdf(path=str(OUT / f"ACCMS_visitekaartjes_A4_{theme}.pdf"), format="A4", print_background=True,
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}, prefer_css_page_size=True)
        # previews: one card, front and back, at 12 px/mm
        for side, fn in [("front", front), ("back", back)]:
            pv = OUT / f"_card_{theme}_{side}.html"
            pv.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{css(t)} body{{background:{t['bg']}}}</style></head><body>{fn()}</body></html>", encoding="utf-8")
            pg2 = b.new_page(viewport={"width": 322, "height": 208}, device_scale_factor=4)
            pg2.goto(pv.as_uri())
            pg2.evaluate("document.fonts.ready")
            pg2.wait_for_timeout(300)
            pg2.locator(".card").screenshot(path=str(OUT / f"preview_{theme}_{side}.png"))
    b.close()
print("ok")
