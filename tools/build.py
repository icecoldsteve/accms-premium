# -*- coding: utf-8 -*-
"""Generate the ACCMS static site (deploy) and an artifact preview from content.py."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from content import T, PLATFORMS_REACH, PLATFORMS_REVENUE  # noqa: E402

SITE = Path(sys.argv[1])
PREVIEW = Path(sys.argv[2])
DOMAIN = "https://www.accms.agency"
EMAIL = "info@accms.agency"
COMPANY = dict(name="SMSAK", owner="Steve Van der Mieren", street="Bosheide 9", postal="8660", city="De Panne",
               kbo="1035.506.672", vat="BE 1035.506.672")
LEGAL = {
    "nl": f"ACCMS is een handelsnaam van {COMPANY['name']} ({COMPANY['owner']}) · {COMPANY['street']}, {COMPANY['postal']} {COMPANY['city']} · KBO {COMPANY['kbo']} · btw {COMPANY['vat']}",
    "fr": f"ACCMS est une dénomination commerciale de {COMPANY['name']} ({COMPANY['owner']}) · {COMPANY['street']}, {COMPANY['postal']} {COMPANY['city']} · BCE {COMPANY['kbo']} · TVA {COMPANY['vat']}",
    "en": f"ACCMS is a trading name of {COMPANY['name']} ({COMPANY['owner']}) · {COMPANY['street']}, {COMPANY['postal']} {COMPANY['city']}, Belgium · Company no. {COMPANY['kbo']} · VAT {COMPANY['vat']}",
}
PRIVACY_LABEL = {"nl": "Privacyverklaring", "fr": "Politique de confidentialité", "en": "Privacy policy"}
LANGS = ["nl", "fr", "en"]
HREFLANG = {"nl": "nl-BE", "fr": "fr-BE", "en": "en"}
LANG_NAME = {"nl": "NL", "fr": "FR", "en": "EN"}

SUN = '<svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>'
MOON = '<svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.6A8.5 8.5 0 0 1 9.4 3.5a8.5 8.5 0 1 0 11.1 11.1Z"/></svg>'


def money(lang, n):
    """Match Intl.NumberFormat output so the page reads the same before and after JS runs."""
    if lang == "en":
        return f"€{n:,}"
    grouped = f"{n:,}".replace(",", "." if lang == "nl" else " ")
    return f"€ {grouped}" if lang == "nl" else f"{grouped} €"


def url_for(lang):
    return DOMAIN + T[lang]["path"]


def schema(lang):
    t = T[lang]
    org_id = DOMAIN + "/#organization"
    offers = []
    for p in t["plans"]:
        name, price, unit = p["schema"]
        spec = {"@type": "UnitPriceSpecification", "priceCurrency": "EUR", "valueAddedTaxIncluded": False}
        if p["price"].lower().startswith(("vanaf", "dès", "from")):
            spec["minPrice"] = price
        else:
            spec["price"] = price
        if unit:
            spec["unitCode"] = unit
        offers.append({"@type": "Offer", "name": name, "description": " · ".join(p["items"]),
                       "priceSpecification": spec, "availability": "https://schema.org/InStock",
                       "url": url_for(lang) + "#pricing"})
    graph = [
        {"@type": "ProfessionalService", "@id": org_id, "name": "ACCMS", "legalName": COMPANY["name"],
         "vatID": COMPANY["vat"].replace(" ", ""), "taxID": COMPANY["kbo"],
         "founder": {"@type": "Person", "name": COMPANY["owner"]},
         "address": {"@type": "PostalAddress", "streetAddress": COMPANY["street"], "postalCode": COMPANY["postal"],
                     "addressLocality": COMPANY["city"], "addressCountry": "BE"},
         "alternateName": "Adult Content Creator Management Services",
         "url": DOMAIN + "/", "logo": DOMAIN + "/assets/icon-512.png", "image": DOMAIN + "/assets/og-image.png",
         "description": t["lead"], "email": EMAIL, "priceRange": "€199–€599",
         "areaServed": {"@type": "Country", "name": "Belgium"},
         "knowsLanguage": ["nl", "fr", "en"],
         "knowsAbout": ["Instagram", "TikTok", "OnlyFans", "Fansly", "MYM", "creator monetization", "link-in-bio websites"],
         "hasOfferCatalog": {"@type": "OfferCatalog", "name": t["price_label"], "itemListElement": offers}},
        {"@type": "WebSite", "@id": DOMAIN + "/#website", "url": DOMAIN + "/", "name": "ACCMS",
         "inLanguage": ["nl-BE", "fr-BE", "en"], "publisher": {"@id": org_id}},
        {"@type": "WebPage", "@id": url_for(lang) + "#webpage", "url": url_for(lang), "name": t["title"],
         "description": t["desc"], "inLanguage": t["html_lang"], "isPartOf": {"@id": DOMAIN + "/#website"},
         "about": {"@id": org_id}, "dateModified": "2026-10-23"},
        {"@type": "FAQPage", "@id": url_for(lang) + "#faq", "inLanguage": t["html_lang"],
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t["faq"]]},
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)


def head(lang, prefix):
    t = T[lang]
    alts = "\n".join(f'<link rel="alternate" hreflang="{HREFLANG[l]}" href="{url_for(l)}">' for l in LANGS)
    alts += f'\n<link rel="alternate" hreflang="x-default" href="{DOMAIN}/">'
    og_alt = "\n".join(f'<meta property="og:locale:alternate" content="{T[l]["og_locale"]}">' for l in LANGS if l != lang)
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{t["title"]}</title>
<meta name="description" content="{t["desc"]}">
<link rel="canonical" href="{url_for(lang)}">
{alts}
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#111111" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta property="og:type" content="website">
<meta property="og:site_name" content="ACCMS">
<meta property="og:title" content="{t["title"]}">
<meta property="og:description" content="{t["desc"]}">
<meta property="og:url" content="{url_for(lang)}">
<meta property="og:image" content="{DOMAIN}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="ACCMS">
<meta property="og:locale" content="{t["og_locale"]}">
{og_alt}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t["title"]}">
<meta name="twitter:description" content="{t["desc"]}">
<meta name="twitter:image" content="{DOMAIN}/assets/og-image.png">
<link rel="icon" href="{prefix}favicon.ico" sizes="any">
<link rel="icon" href="{prefix}assets/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{prefix}assets/apple-touch-icon.png">
<link rel="manifest" href="{prefix}site.webmanifest">
<link rel="preload" href="{prefix}fonts/bricolage-grotesque.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{prefix}fonts/manrope.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{prefix}css/site.css">
<script src="{prefix}js/theme.js"></script>
<script src="{prefix}js/main.js" defer></script>
<script src="{prefix}js/motion.js" defer></script>
<script type="application/ld+json">
{schema(lang)}
</script>"""


def lang_href(from_lang, to_lang, preview):
    up = "" if from_lang == "nl" else "../"
    if to_lang == "nl":
        target = up if up else "./"
        return (up + "index.html") if preview else (target)
    return (up + f"{to_lang}/" + ("index.html" if preview else ""))


# Platform icons: Font Awesome Free 6.7.2 Brands (CC BY 4.0, https://fontawesome.com/license/free).
# Trademarks belong to their owners. Only reach platforms have a supplied icon; revenue platforms stay text.
ICON_FILES = {"Instagram": "instagram.svg", "TikTok": "tiktok.svg", "X": "x.svg", "YouTube Shorts": "youtube.svg"}
ICONS = {}
for _name, _file in ICON_FILES.items():
    _svg = (SITE / "assets" / "platforms" / _file).read_text(encoding="utf-8")
    ICONS[_name] = (re.search(r'viewBox="([^"]+)"', _svg).group(1), re.search(r' d="([^"]+)"', _svg).group(1))


def icon(name):
    if name not in ICONS:
        return ""
    vb, d = ICONS[name]
    return f'<svg class="pf-icon" viewBox="{vb}" aria-hidden="true" focusable="false"><path fill="currentColor" d="{d}"/></svg>'


def privacy_href(lang, preview):
    return "privacy" + (".html" if preview else "")


def body(lang, prefix, preview):
    t = T[lang]
    nav = "".join(f'<a href="{h}">{label}</a>' for h, label in t["nav"])
    langs = "".join(
        f'<a href="{lang_href(lang, l, preview)}" hreflang="{HREFLANG[l]}" lang="{HREFLANG[l]}"'
        + (' aria-current="page"' if l == lang else "") + f'>{LANG_NAME[l]}</a>' for l in LANGS)
    h1 = "".join(f'<span class="line"><span style-d="{i}">{part}</span></span>' for i, part in enumerate(t["h1"]))
    micro = "".join(f"<span>{m}</span>" for m in t["micro"])

    def nodes(items, start):
        return "".join(f'<li class="node n{i}"><span>{icon(p)}{p}</span></li>' for i, p in enumerate(items))

    usp = "".join(f"<li>{u}</li>" for u in t["usp"])
    services = "".join(f'<div class="col" data-reveal><h3>{a}</h3><p>{b}</p></div>' for a, b in t["services"])
    funnel = "".join(f'<div data-reveal><span class="step">{s}</span><h3>{h}</h3><p>{p}</p></div>' for s, h, p in t["funnel"])
    cards = ""
    for name, kind, badge, bullets, kword, kval, core in t["road"]:
        lis = "".join(f"<li>{b}</li>" for b in bullets)
        cards += (f'<article data-reveal class="card{" core" if core else ""}"><div class="card-top"><h3>{name}</h3>'
                  f'<span class="badge {kind}">{badge}</span></div><ul>{lis}</ul>'
                  f'<p class="kpi"><strong>{kword}</strong> · {kval}</p></article>')
    timeline = "".join(f'<li><span class="when">{w}</span><p>{x}</p></li>' for w, x in t["timeline"])
    fields = ""
    for fid, label, mn, mx, st, val in t["calc_fields"]:
        shown = str(val) if fid == "subs" else (f"{val}%" if fid == "fee" else money(lang, val))
        fields += (f'<div class="field"><label for="calc-{fid}"><span>{label}</span>'
                   f'<output id="out-{fid}" for="calc-{fid}">{shown}</output></label>'
                   f'<input id="calc-{fid}" type="range" min="{mn}" max="{mx}" step="{st}" value="{val}"></div>')
    steps = "".join(f"<li data-reveal><h3>{a}</h3><p>{b}</p></li>" for a, b in t["process"])
    plans = ""
    for p in t["plans"]:
        lis = "".join(f"<li>{i}</li>" for i in p["items"])
        flag = f'<span class="badge hi flag">{t["featured"]}</span>' if p["featured"] else ""
        note = f'<p class="note">{p["note"]}</p>' if p["note"] else ""
        btn = "btn-primary" if p["featured"] else "btn-ghost"
        plans += (f'<article data-reveal class="plan{" featured" if p["featured"] else ""}">{flag}<h3>{p["name"]}</h3>'
                  f'<p class="price">{p["price"]}<small>{p["unit"]}</small></p>{note}<ul>{lis}</ul>'
                  f'<a class="btn {btn}" href="#contact">{p["cta"]}</a></article>')
    trust = "".join(f"<div data-reveal><h3>{a}</h3><p>{b}</p></div>" for a, b in t["trust"])
    faq = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in t["faq"])
    mailto = f"mailto:{EMAIL}?subject=ACCMS%20intake"

    return f"""<div class="progress" aria-hidden="true"></div>
<a class="skip" href="#main">{t["skip"]}</a>
<header class="site-header">
<div class="wrap header-row">
<a class="brand" href="{lang_href(lang, lang, preview)}" aria-label="ACCMS">
<img class="logo-dark" src="{prefix}assets/accms-logo-dark.svg" alt="{t["logo_alt"]}" width="176" height="44">
<img class="logo-light" src="{prefix}assets/accms-logo-light.svg" alt="{t["logo_alt"]}" width="176" height="44">
</a>
<nav class="main-nav" aria-label="Menu">{nav}</nav>
<div class="header-tools">
<nav class="lang" aria-label="{t["lang_label"]}">{langs}</nav>
<button class="theme-toggle" id="theme-toggle" type="button" aria-label="{t["theme_label"]}" aria-pressed="false">{SUN}{MOON}</button>
<a class="btn btn-primary header-cta" href="#contact">{t["header_cta"]}</a>
</div>
</div>
</header>

<main id="main">
<section class="hero">
<canvas class="hero-canvas" aria-hidden="true"></canvas>
<div class="wrap hero-grid">
<div class="hero-copy">
<p class="label fade-in">{t["eyebrow"]}</p>
<h1>{h1}</h1>
<p class="lead fade-in">{t["lead"]}</p>
<p class="promise fade-in">{t["promise"]}</p>
<div class="hero-ctas fade-in"><a class="btn btn-primary" href="#contact">{t["cta1"]}</a><a class="btn btn-ghost" href="#roadmap">{t["cta2"]}</a></div>
<p class="micro fade-in">{micro}</p>
</div>
<figure class="hero-visual" role="img" aria-label="{t["orbit_label"]}">
<div class="orbit">
<div class="comet" aria-hidden="true"></div>
<ul class="ring" aria-hidden="true">{nodes(PLATFORMS_REVENUE, -45)}</ul>
<ul class="ring inner" aria-hidden="true">{nodes(PLATFORMS_REACH, 0)}</ul>
<div class="orbit-core"><span class="pulse" aria-hidden="true"></span><span class="pulse p2" aria-hidden="true"></span><img src="{prefix}assets/icon.svg" alt="" width="120" height="120"></div>
</div>
<figcaption class="orbit-legend" aria-hidden="true"><span class="reach">{t["legend_reach"]}</span><span>{t["legend_rev"]}</span></figcaption>
</figure>
</div>
</section>

<div class="usp"><div class="track"><ul>{usp}</ul><ul aria-hidden="true">{usp}</ul></div></div>

<section class="section" id="services" aria-labelledby="h-services">
<div class="wrap">
<div class="section-head" data-reveal><p class="label">{t["services_label"]}</p><h2 id="h-services">{t["services_h2"]}</h2></div>
<div class="cols-4">{services}</div>
</div>
</section>

<section class="section band" aria-labelledby="h-funnel">
<div class="wrap">
<div class="section-head" data-reveal><p class="label">{t["funnel_label"]}</p><h2 id="h-funnel">{t["funnel_h2"]}</h2></div>
<div class="funnel">{funnel}</div>
</div>
</section>

<section class="section" id="roadmap" aria-labelledby="h-roadmap">
<div class="wrap">
<div class="section-head" data-reveal><p class="label">{t["road_label"]}</p><h2 id="h-roadmap">{t["road_h2"]}</h2><p>{t["road_intro"]}</p></div>
<div class="cards">{cards}</div>
</div>
</section>

<section class="section band" aria-labelledby="h-timeline">
<div class="wrap">
<div class="section-head" data-reveal><p class="label">{t["time_label"]}</p><h2 id="h-timeline">{t["time_h2"]}</h2></div>
<ol class="timeline" data-reveal>{timeline}</ol>
</div>
</section>

<section class="section" id="forecast" aria-labelledby="h-forecast">
<div class="wrap">
<div class="section-head" data-reveal><p class="label">{t["calc_label"]}</p><h2 id="h-forecast">{t["calc_h2"]}</h2><p>{t["calc_intro"]}</p></div>
<div class="calc" data-reveal>
<div class="calc-inputs">{fields}</div>
<div class="calc-result" aria-live="polite">
<span class="label">{t["calc_month"]}</span>
<span class="big" id="calc-monthly">{money(lang, 4320)}</span>
<span class="label">{t["calc_year"]}</span>
<span class="mid" id="calc-yearly">{money(lang, 51840)}</span>
<small>{t["calc_note"]}</small>
</div>
</div>
<div class="cta-strip" data-reveal><p>{t["strip_text"]}</p><a class="btn btn-primary" href="#contact">{t["strip_cta"]}</a></div>
</div>
</section>

<section class="section band" id="process" aria-labelledby="h-process">
<div class="wrap">
<div class="section-head" data-reveal><p class="label">{t["proc_label"]}</p><h2 id="h-process">{t["proc_h2"]}</h2></div>
<ol class="steps">{steps}</ol>
</div>
</section>

<section class="section" id="pricing" aria-labelledby="h-pricing">
<div class="wrap">
<div class="section-head" data-reveal><p class="label">{t["price_label"]}</p><h2 id="h-pricing">{t["price_h2"]}</h2></div>
<div class="plans">{plans}</div>
</div>
</section>

<section class="section band" aria-labelledby="h-trust">
<div class="wrap">
<div class="section-head" data-reveal><p class="label">{t["trust_label"]}</p><h2 id="h-trust">{t["trust_h2"]}</h2></div>
<div class="trust">{trust}</div>
</div>
</section>

<section class="section" id="faq" aria-labelledby="h-faq">
<div class="wrap faq">
<div class="section-head" data-reveal><p class="label">{t["faq_label"]}</p><h2 id="h-faq">{t["faq_h2"]}</h2></div>
<div class="faq-list" data-reveal>{faq}</div>
</div>
</section>

<section class="section contact" id="contact" aria-labelledby="h-contact">
<div class="wrap contact-row">
<div><h2 id="h-contact">{t["contact_h2"]}</h2><p>{t["contact_p"]}</p></div>
<div class="mail"><a id="mail-address" href="{mailto}">{EMAIL}</a><button class="copy-btn" id="copy-mail" type="button" data-done="{t["copy_done"]}">{t["copy_label"]}</button></div>
</div>
</section>
</main>

<footer class="site-footer">
<div class="wrap footer-row">
<img class="logo-dark" src="{prefix}assets/accms-logo-dark.svg" alt="ACCMS" width="224" height="56" loading="lazy">
<img class="logo-light" src="{prefix}assets/accms-logo-light.svg" alt="ACCMS" width="224" height="56" loading="lazy">
<div class="footer-meta"><span>© 2026 ACCMS · Adult Content Creator Management Services</span><span>{LEGAL[lang]}</span><span>{t["foot_tag"]} {t["foot_updated"]} · <a href="{privacy_href(lang, preview)}">{PRIVACY_LABEL[lang]}</a></span></div>
<nav class="lang" aria-label="{t["lang_label"]}">{langs}</nav>
</div>
</footer>"""


def fix_delays(html):
    # h1 line delays are applied with classes instead of inline styles (strict CSP: no style attributes)
    for i in range(4):
        html = html.replace(f'<span style-d="{i}">', f'<span class="d{i}">')
    return html


def node_classes(html):
    return html


def page(lang, preview):
    t = T[lang]
    prefix = "" if lang == "nl" else "../"
    b = fix_delays(body(lang, prefix, preview))
    if preview and lang == "nl":
        # Artifact page: the host wraps it in its own skeleton
        return (f'<title>ACCMS</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
                f'<link rel="stylesheet" href="css/site.css">\n<script src="js/theme.js"></script>\n'
                f'<script src="js/main.js" defer></script>\n<script src="js/motion.js" defer></script>\n'
                f'<div class="page" data-locale-host="{t["locale"]}">\n{b}\n</div>\n')
    return (f'<!doctype html>\n<html lang="{t["html_lang"]}" data-locale="{t["locale"]}">\n<head>\n{head(lang, prefix)}\n</head>\n'
            f'<body>\n{b}\n</body>\n</html>\n')


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


for lang in LANGS:
    rel = "index.html" if lang == "nl" else f"{lang}/index.html"
    write(SITE / rel, page(lang, preview=False))
    write(PREVIEW / rel, page(lang, preview=True))

# 404
PRIV = {
    "nl": dict(title="Privacyverklaring · ACCMS", h1="Privacy<em>verklaring</em>", back="Terug naar de homepage", updated="Laatst bijgewerkt: 23 oktober 2026", sections=[
        ("Wie is verantwoordelijk?", f"{LEGAL['nl']}. Vragen over je gegevens stuur je naar {EMAIL}."),
        ("Welke gegevens verwerken we?", "Alleen wat je ons zelf mailt: je naam, je e-mailadres, de inhoud van je bericht en, als je klant wordt, de profielgegevens en cijfers die je deelt voor je audit. Deze website heeft geen formulier, geen analytics en geen tracking- of advertentiecookies."),
        ("Lokale opslag", "Kies je licht of donker thema, dan bewaart je browser die keuze lokaal (localStorage). Dat is strikt functioneel, wordt niet naar ons verstuurd en vraagt geen toestemming."),
        ("Waarom en op welke basis?", "Om je vraag te beantwoorden en een offerte of overeenkomst voor te bereiden en uit te voeren (artikel 6.1.b AVG), en om onze facturatie en boekhouding te voeren (wettelijke verplichting, artikel 6.1.c AVG). Serverlogs van de hosting gebruiken we alleen voor beveiliging (gerechtvaardigd belang, artikel 6.1.f AVG)."),
        ("Hoe lang bewaren we ze?", "Correspondentie zonder opdracht tot 2 jaar na het laatste contact. Gegevens die nodig zijn voor facturatie zo lang als de Belgische boekhoudwetgeving vereist."),
        ("Met wie delen we ze?", "Met niemand voor marketing. Technische verwerkers: Vercel Inc. (hosting van deze website) en Amazon Web Services (ontvangst en verzending van e-mail). We verkopen je gegevens nooit en tonen geen klantnamen zonder jouw schriftelijke toestemming."),
        ("Jouw rechten", f"Je kunt je gegevens inzien, laten verbeteren of wissen, de verwerking laten beperken, bezwaar maken en je gegevens laten overdragen. Mail naar {EMAIL}; we antwoorden binnen 30 dagen. Je kunt ook klacht indienen bij de Gegevensbeschermingsautoriteit (www.gegevensbeschermingsautoriteit.be)."),
    ]),
    "fr": dict(title="Politique de confidentialité · ACCMS", h1="Politique de <em>confidentialité</em>", back="Retour à l'accueil", updated="Dernière mise à jour : 23 octobre 2026", sections=[
        ("Qui est responsable ?", f"{LEGAL['fr']}. Pour toute question sur tes données : {EMAIL}."),
        ("Quelles données traitons-nous ?", "Uniquement ce que tu nous envoies par e-mail : ton nom, ton adresse e-mail, le contenu de ton message et, si tu deviens cliente ou client, les données de profil et chiffres que tu partages pour ton audit. Ce site n'a pas de formulaire, pas d'analytics et pas de cookies de suivi ou de publicité."),
        ("Stockage local", "Si tu choisis le thème clair ou sombre, ton navigateur garde ce choix localement (localStorage). C'est strictement fonctionnel, ce n'est pas envoyé chez nous et ne demande pas de consentement."),
        ("Pourquoi et sur quelle base ?", "Pour répondre à ta demande et préparer ou exécuter une offre ou un contrat (article 6.1.b RGPD), et pour notre facturation et comptabilité (obligation légale, article 6.1.c RGPD). Les journaux du serveur servent uniquement à la sécurité (intérêt légitime, article 6.1.f RGPD)."),
        ("Combien de temps ?", "La correspondance sans mission jusqu'à 2 ans après le dernier contact. Les données nécessaires à la facturation aussi longtemps que l'exige la législation comptable belge."),
        ("Avec qui les partageons-nous ?", "Avec personne à des fins de marketing. Sous-traitants techniques : Vercel Inc. (hébergement du site) et Amazon Web Services (réception et envoi d'e-mails). Nous ne vendons jamais tes données et ne citons aucun nom de client sans ton accord écrit."),
        ("Tes droits", f"Tu peux consulter, rectifier ou effacer tes données, en limiter le traitement, t'y opposer et en demander la portabilité. Écris à {EMAIL} ; nous répondons sous 30 jours. Tu peux aussi porter plainte auprès de l'Autorité de protection des données (www.autoriteprotectiondonnees.be)."),
    ]),
    "en": dict(title="Privacy policy · ACCMS", h1="Privacy <em>policy</em>", back="Back to the homepage", updated="Last updated: 23 October 2026", sections=[
        ("Who is responsible?", f"{LEGAL['en']}. Questions about your data: {EMAIL}."),
        ("What data do we process?", "Only what you email us: your name, your email address, the content of your message and, if you become a client, the profile data and figures you share for your audit. This website has no form, no analytics and no tracking or advertising cookies."),
        ("Local storage", "If you pick the light or dark theme, your browser stores that choice locally (localStorage). It is strictly functional, never sent to us and needs no consent."),
        ("Why and on what basis?", "To answer your request and to prepare and perform a quote or contract (Article 6(1)(b) GDPR), and to keep our invoicing and accounts (legal obligation, Article 6(1)(c) GDPR). Hosting server logs are used for security only (legitimate interest, Article 6(1)(f) GDPR)."),
        ("How long do we keep it?", "Correspondence without an assignment for up to 2 years after the last contact. Data needed for invoicing for as long as Belgian accounting law requires."),
        ("Who do we share it with?", "Nobody, for marketing. Technical processors: Vercel Inc. (website hosting) and Amazon Web Services (receiving and sending email). We never sell your data and never name clients without your written consent."),
        ("Your rights", f"You can access, correct or erase your data, restrict or object to processing, and ask for portability. Email {EMAIL}; we reply within 30 days. You can also complain to the Belgian Data Protection Authority (www.dataprotectionauthority.be)."),
    ]),
}


def privacy_page(lang, preview):
    p = PRIV[lang]
    t = T[lang]
    prefix = "" if lang == "nl" else "../"
    home = "index.html" if preview else "./"
    secs = "".join(f"<section><h2>{h}</h2><p>{x}</p></section>" for h, x in p["sections"])
    return f"""<!doctype html>
<html lang="{t["html_lang"]}" data-locale="{t["locale"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{p["title"]}</title>
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{url_for(lang)}privacy">
<link rel="icon" href="{prefix}favicon.ico" sizes="any">
<link rel="stylesheet" href="{prefix}css/site.css">
<script src="{prefix}js/theme.js"></script>
</head>
<body>
<header class="site-header"><div class="wrap header-row">
<a class="brand" href="{home}" aria-label="ACCMS">
<img class="logo-dark" src="{prefix}assets/accms-logo-dark.svg" alt="{t["logo_alt"]}" width="176" height="44">
<img class="logo-light" src="{prefix}assets/accms-logo-light.svg" alt="{t["logo_alt"]}" width="176" height="44">
</a>
<a class="btn btn-ghost header-cta" href="{home}">{p["back"]}</a>
</div></header>
<main class="section legal"><div class="wrap">
<div class="section-head"><p class="label">ACCMS</p><h1>{p["h1"]}</h1><p>{p["updated"]}</p></div>
<div class="legal-body">{secs}</div>
</div></main>
</body>
</html>
"""


for lang in LANGS:
    sub = "" if lang == "nl" else f"{lang}/"
    write(SITE / f"{sub}privacy.html", privacy_page(lang, preview=False))
    write(PREVIEW / f"{sub}privacy.html", privacy_page(lang, preview=True))

write(SITE / "404.html", f"""<!doctype html>
<html lang="nl-BE" data-locale="nl-BE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Pagina niet gevonden · ACCMS</title>
<meta name="robots" content="noindex, follow">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="stylesheet" href="/css/site.css">
<script src="/js/theme.js"></script>
</head>
<body>
<main class="section"><div class="wrap section-head">
<p class="label">404</p>
<h1>Deze pagina bestaat <em>niet (meer)</em>.</h1>
<p class="muted">Page introuvable · Page not found</p>
<div class="hero-ctas"><a class="btn btn-primary" href="/">Naar de homepage</a><a class="btn btn-ghost" href="/fr/">Version française</a><a class="btn btn-ghost" href="/en/">English version</a></div>
</div></main>
</body>
</html>
""")

# robots.txt — AI-crawlers expliciet toegelaten (GEO)
write(SITE / "robots.txt", f"""User-agent: *
Allow: /
Disallow: /404.html

User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
""")

alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{HREFLANG[l]}" href="{url_for(l)}"/>' for l in LANGS)
alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{DOMAIN}/"/>'
urls = "".join(f"""
  <url>
    <loc>{url_for(l)}</loc>
    <lastmod>2026-10-23</lastmod>{alts}
  </url>""" for l in LANGS)
write(SITE / "sitemap.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">{urls}
</urlset>
""")

# llms.txt — samenvatting voor AI-zoekmachines (GEO)
nl = T["nl"]
faq_md = "\n".join(f"- **{q}** {a}" for q, a in T["en"]["faq"])
write(SITE / "llms.txt", f"""# ACCMS

> ACCMS (Adult Content Creator Management Services) is a Belgian service that helps adult (18+) content creators in Belgium grow on Instagram, TikTok, X, OnlyFans, Fansly, MYM and F2F. Creators keep their own accounts, passwords and revenue; ACCMS delivers strategy, a 90-day roadmap, a revenue forecast and technical support. No revenue share of 50%: fixed prices.

## Pages
- [Nederlands]({DOMAIN}/): main site in Dutch
- [Français]({DOMAIN}/fr/): site in French
- [English]({DOMAIN}/en/): site in English

## Services and prices (excl. VAT)
- Audit + roadmap: from €199, one-off. Analysis of all profiles, 90-day roadmap per platform, revenue forecast in three scenarios, one-hour review call.
- Growth management: from €599 per month, optional 10% of net growth above the starting level, 3-month minimum. Weekly content planning, pricing and PPV strategy, customs menu, monthly KPI report.
- Tech package: €399 first year, €199 per year from year 2. Hand-coded link-in-bio website on the creator's own domain, hosting, email capture, click tracking.

## Process
1. Email request, personal reply within 48 hours
2. Free 20-minute intake
3. Audit and 90-day roadmap with revenue forecast
4. First changes live within one week
5. Weekly updates and monthly KPI review

## FAQ
{faq_md}

## Contact
- Email: {EMAIL}
- Languages: Dutch, French, English
- Only works with creators aged 18 or older
""")

write(SITE / "site.webmanifest", json.dumps({
    "name": "ACCMS", "short_name": "ACCMS", "start_url": "/", "display": "standalone",
    "background_color": "#111111", "theme_color": "#111111",
    "icons": [{"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2))

write(SITE / "vercel.json", json.dumps({
    "cleanUrls": True,
    "headers": [{"source": "/(.*)", "headers": [
        {"key": "Content-Security-Policy", "value": "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests"},
        {"key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload"},
        {"key": "X-Content-Type-Options", "value": "nosniff"},
        {"key": "X-Frame-Options", "value": "DENY"},
        {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
        {"key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=(), interest-cohort=()"},
        {"key": "Cross-Origin-Opener-Policy", "value": "same-origin"}]},
        {"source": "/fonts/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]}]}, indent=2))
print("built")
