# ACCMS — Adult Content Creator Management Services

Statische site (NL/FR/EN) voor www.accms.agency. Handelsnaam van SMSAK. Gehost op Vercel, geen build-stap.

## Structuur
- `index.html`, `fr/`, `en/` — homepage per taal (gegenereerd)
- `privacy.html` per taal, `404.html`
- `css/site.css`, `js/theme.js` (thema vóór paint), `js/main.js` (toggle, calculator, kopieerknop)
- `fonts/` — self-hosted woff2 (Bricolage Grotesque, Instrument Serif italic, Manrope)
- `assets/` — logo's, iconen, og-image; `favicon.ico` in root
- `robots.txt`, `sitemap.xml`, `llms.txt`, `site.webmanifest`, `vercel.json` (CSP + security headers)

## Teksten aanpassen
Alle copy staat in `tools/content.py`. Daarna:

```bash
python3 tools/build.py . /tmp/accms-preview      # genereert de HTML opnieuw
python3 tools/check.py . /tmp/accms-shots        # 124 checks: SEO, GEO, CSP, a11y, render
python3 tools/render_assets.py .                 # alleen bij nieuw icoon/logo: favicon + og-image
```

`tools/` wordt via `.vercelignore` niet gedeployed.
