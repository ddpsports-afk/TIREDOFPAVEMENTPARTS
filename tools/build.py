#!/usr/bin/env python3
"""Turn the canvas .dc.html artboards into a plain static site for Netlify."""
import html, json, os, re, shutil, sys
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f"{REPO}/source/canvas"
PHOTOS = f"{REPO}/source/photos"
OUT = f"{REPO}/site"
DOMAIN = "https://tiredofpavementparts.com"

PAGES = [
    # file, out path, url path, form name, description
    ("Main.dc.html", "index.html", "/", "offer-home",
     "Sell your motorcycle, dirt bike or ATV without listing it. Text a photo, get a straight cash offer, and we haul it away. Serving Keystone Heights, Starke, Middleburg, Palatka and Gainesville, FL."),
    ("CashToday.dc.html", "cash-today/index.html", "/cash-today/", "offer-cash-today",
     "Get cash for your motorcycle, dirt bike or ATV this week, running or not. Cash at pickup within 30 miles of Keystone Heights, Florida."),
    ("GetItGone.dc.html", "get-it-gone/index.html", "/get-it-gone/", "offer-get-it-gone",
     "Get that old motorcycle or four-wheeler out of your yard. Send one photo, get a cash offer, and we haul it away. Keystone Heights, FL area."),
    ("SkipTheHassle.dc.html", "skip-the-hassle/index.html", "/skip-the-hassle/", "offer-skip-the-hassle",
     "Skip the Marketplace hassle. One fair cash offer for your motorcycle, dirt bike or ATV and a pickup on your schedule in North Central Florida."),
    ("Faq.dc.html", "faq/index.html", "/faq/", None,
     "Straight answers about selling a motorcycle, dirt bike or ATV for cash in North Central Florida: titles, paperwork, pickup, payment and what we buy."),
]

LINKS = {
    'href="Main.dc.html"': 'href="/"',
    'href="CashToday.dc.html"': 'href="/cash-today/"',
    'href="GetItGone.dc.html"': 'href="/get-it-gone/"',
    'href="SkipTheHassle.dc.html"': 'href="/skip-the-hassle/"',
    'href="Faq.dc.html"': 'href="/faq/"',
}

IMAGES = {
    "/_blob/5a36974e92c9036e010bbdb6e9b839fe": (f"{PHOTOS}/raptor.png", "raptor.jpg"),
    "/_blob/c702a6728cb671d1c5ecc814ba9f89c2": (f"{PHOTOS}/trailer.jpg", "trailer.jpg"),
    "/_blob/8887eeff096e9b7140a97eeebbf2a8dc": (f"{PHOTOS}/wreck-gsxr.jpg", "wrecked-gsxr.jpg"),
    "/_blob/c3198855f025d1b96a79d4c687c0e33a": (f"{PHOTOS}/wreck-r6.jpg", "stripped-r6.jpg"),
    "/_blob/a6fc392263b2eb7b66370c35f030dca6": (f"{PHOTOS}/van-wide.jpg", "van-trailer.jpg"),
}

EXTRA_CSS = """
html{scroll-behavior:smooth}
img{max-width:100%;height:auto}
h1,h2,h3{text-wrap:balance}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,summary:focus-visible{outline:3px solid #FF6B1A;outline-offset:3px}
.form-ok{display:none}
@media (max-width:600px){
  form{grid-template-columns:minmax(0,1fr)!important;padding:24px!important}
  form > *{grid-column:1 / -1!important}
}
"""

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="8" fill="#141611"/><circle cx="20" cy="20" r="13" fill="none" stroke="#FF6B1A" stroke-width="6" stroke-dasharray="3.6 2.6"/><circle cx="20" cy="20" r="4.5" fill="none" stroke="#F3EFE6" stroke-width="2.5"/></svg>"""

INPUT_STYLE = "font: inherit; font-weight: 400; font-size: 16px; padding: 12px 14px; border: 1px dashed #B9B09D; border-radius: 8px; background: #FFFFFF; color: #141611; min-height: 48px; box-sizing: border-box; width: 100%"


def extract(src):
    helmet = re.search(r"<helmet>(.*?)</helmet>", src, re.S).group(1)
    body = re.search(r"</helmet>(.*?)</x-dc>", src, re.S).group(1)
    title = html.unescape(re.search(r"<title>(.*?)</title>", src, re.S).group(1))
    style = re.search(r"<style>(.*?)</style>", helmet, re.S).group(1)
    links = "\n".join(re.findall(r"<link[^>]*>", helmet))
    return title, links, style, body


def wire_forms(body, form_name, page_label):
    def repl(m):
        attrs = (f'<form name="{form_name}" method="POST" action="/thanks/" '
                 f'data-netlify="true" netlify-honeypot="bot-field" enctype="multipart/form-data" ')
        hidden = (f'\n<p hidden><label>Leave this blank <input name="bot-field"></label></p>'
                  f'\n<input type="hidden" name="form-name" value="{form_name}">'
                  f'\n<input type="hidden" name="subject" value="New bike lead from the {page_label} page">')
        return attrs + m.group(1) + ">" + hidden
    body, n = re.subn(r"<form (style=\"[^\"]*\")>", repl, body)
    assert n <= 1, n
    photo = (f'<label style="grid-column: 1 / -1; display: flex; flex-direction: column; gap: 8px; font-weight: 600; font-size: 15px">'
             f'Photo of the bike (optional)<input type="file" name="photo" accept="image/*" style="{INPUT_STYLE}"></label>\n')
    body = body.replace('<button type="submit"', photo + '<button type="submit"', 1)
    body = body.replace('<input type="tel" name="phone"', '<input type="tel" name="phone" required autocomplete="tel"')
    body = body.replace('<input type="text" name="name"', '<input type="text" name="name" autocomplete="given-name"')
    return body


def head(title, desc, path, links, style, jsonld=""):
    url = DOMAIN + path
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Tired of Pavement Parts">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{DOMAIN}/images/raptor.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#141611">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{links}
<style>{style}{EXTRA_CSS}</style>
{jsonld}</head>
<body>"""


def ld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, indent=2, ensure_ascii=False) + "\n</script>\n"


BUSINESS = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "@id": DOMAIN + "/#business",
    "name": "Tired of Pavement Parts",
    "description": "Local cash buyer of used, wrecked and non-running motorcycles, dirt bikes, ATVs, side-by-sides and UTVs. We part them out and sell the parts.",
    "url": DOMAIN + "/",
    "telephone": "+1-772-713-1669",
    "email": "ddpsports@gmail.com",
    "image": DOMAIN + "/images/trailer.jpg",
    "address": {"@type": "PostalAddress", "addressLocality": "Keystone Heights", "addressRegion": "FL", "addressCountry": "US"},
    "areaServed": [
        {"@type": "AdministrativeArea", "name": c} for c in
        ["Clay County, FL", "Bradford County, FL", "Putnam County, FL", "Alachua County, FL", "Union County, FL"]
    ],
}


def faq_ld(body):
    qa = re.findall(r"<h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p>", body, re.S)
    strip = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": strip(q),
             "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in qa
        ],
    }, len(qa)


def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(f"{OUT}/images")

    # images: resize + compress
    for blob, (src, name) in IMAGES.items():
        im = Image.open(src).convert("RGB")
        im.thumbnail((1400, 1400))
        im.save(f"{OUT}/images/{name}", "JPEG", quality=80, optimize=True, progressive=True)

    shared_links = shared_style = None
    for fname, out, path, form, desc in PAGES:
        src = open(f"{SRC}/{fname}", encoding="utf-8").read()
        title, links, style, body = extract(src)
        shared_links, shared_style = links, style
        for a, b in LINKS.items():
            body = body.replace(a, b)
        for blob, (_, name) in IMAGES.items():
            body = body.replace(blob, f"/images/{name}")
        # lazy-load images below the first screen
        body = re.sub(r"<img (?!src=\"/images/raptor)", "<img loading=\"lazy\" decoding=\"async\" ", body)
        if form:
            label = {"/": "home", "/cash-today/": "cash today", "/get-it-gone/": "get it gone",
                     "/skip-the-hassle/": "skip the hassle"}[path]
            body = wire_forms(body, form, label)
        jsonld = ""
        if path == "/":
            jsonld = ld(BUSINESS)
        if path == "/faq/":
            obj, n = faq_ld(body)
            print(f"FAQ schema: {n} questions")
            jsonld = ld(obj)
        doc = head(title, desc, path, links, style, jsonld) + body + "\n</body>\n</html>\n"
        leftovers = [s for s in ("x-dc", "helmet", ".dc.html", "_blob", "{{", "support.js") if s in doc]
        assert not leftovers, (fname, leftovers)
        os.makedirs(os.path.dirname(f"{OUT}/{out}") or OUT, exist_ok=True)
        open(f"{OUT}/{out}", "w", encoding="utf-8").write(doc)
        print("wrote", out)

    # thanks + 404 pages share the look
    simple = lambda title, h1, p, cta: head(title, title, "/thanks/" if "Thanks" in title else "/404", shared_links, shared_style) + f"""
<div style="font-family: 'Barlow', system-ui, sans-serif; background: #141611; color: #F3EFE6; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 48px 24px; box-sizing: border-box">
<div style="max-width: 640px; text-align: center">
<a href="/" style="text-decoration: none; color: #F3EFE6; display: inline-flex; align-items: center; gap: 12px"><img src="/favicon.svg" width="44" height="44" alt=""><span style="font-family: 'Barlow Condensed', sans-serif; font-weight: 800; font-size: 24px; letter-spacing: 0.04em; text-transform: uppercase">Tired of Pavement</span></a>
<h1 style="font-family: 'Barlow Condensed', sans-serif; font-weight: 800; text-transform: uppercase; font-size: clamp(48px, 8vw, 88px); line-height: 0.9; margin: 40px 0 0">{h1}</h1>
<p style="font-size: 20px; line-height: 1.6; color: #CFC9BA; margin: 24px 0 0">{p}</p>
<div style="display: flex; flex-wrap: wrap; gap: 14px; justify-content: center; margin-top: 36px">{cta}</div>
</div>
</div>
</body>
</html>
"""
    btn = 'style="background: #FF6B1A; color: #141611; text-decoration: none; font-weight: 800; font-size: 18px; padding: 18px 28px; border-radius: 8px"'
    ghost = 'style="color: #F3EFE6; text-decoration: none; font-weight: 700; font-size: 18px; padding: 18px 28px; border-radius: 8px; border: 2px solid #4A5042"'
    thanks = simple("Thanks, we got it | Tired of Pavement Parts", "Got it. <span style=\"color: #FF6B1A\">Thanks!</span>",
                    "A real person will text you back with an offer, usually the same day. Want to speed it up? Text a photo of the bike to 772-713-1669.",
                    f'<a href="sms:+17727131669" {btn}>Text a photo now</a><a href="/" {ghost}>Back to home</a>')
    thanks = thanks.replace("<head>", "<head>\n<meta name=\"robots\" content=\"noindex\">", 1)
    os.makedirs(f"{OUT}/thanks")
    open(f"{OUT}/thanks/index.html", "w").write(thanks)
    nf = simple("Page not found | Tired of Pavement Parts", "Wrong turn.",
                "That page doesn't exist, but we're still buying bikes.",
                f'<a href="/" {btn}>Go to the home page</a><a href="sms:+17727131669" {ghost}>Text 772-713-1669</a>')
    nf = nf.replace("<head>", "<head>\n<meta name=\"robots\" content=\"noindex\">", 1)
    open(f"{OUT}/404.html", "w").write(nf)

    open(f"{OUT}/favicon.svg", "w").write(FAVICON)
    open(f"{OUT}/robots.txt", "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    urls = "".join(f"  <url><loc>{DOMAIN}{p[2]}</loc><lastmod>2026-10-23</lastmod></url>\n" for p in PAGES)
    open(f"{OUT}/sitemap.xml", "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
    print("done")


if __name__ == "__main__":
    build()
