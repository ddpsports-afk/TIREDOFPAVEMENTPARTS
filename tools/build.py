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
    ("Wrecked.dc.html", "sell-wrecked-motorcycle/index.html", "/sell-wrecked-motorcycle/", "offer-wrecked",
     "Sell a wrecked, crashed or salvage-title motorcycle, ATV or UTV for cash. We buy for parts, pay cash at pickup and haul it away. Keystone Heights and North Central Florida."),
    ("NonRunning.dc.html", "sell-non-running-motorcycle/index.html", "/sell-non-running-motorcycle/", "offer-non-running",
     "Won't start, seized or sitting for years? We buy non-running motorcycles, dirt bikes, ATVs and UTVs as-is for cash, with pickup usually within 48 hours. Keystone Heights, FL."),
    ("Faq.dc.html", "faq/index.html", "/faq/", None,
     "Straight answers about selling a motorcycle, dirt bike or ATV for cash in North Central Florida: titles, paperwork, pickup, payment and what we buy."),
]

LINKS = {
    'href="Main.dc.html"': 'href="/"',
    'href="CashToday.dc.html"': 'href="/cash-today/"',
    'href="GetItGone.dc.html"': 'href="/get-it-gone/"',
    'href="SkipTheHassle.dc.html"': 'href="/skip-the-hassle/"',
    'href="Faq.dc.html"': 'href="/faq/"',
    'href="Wrecked.dc.html"': 'href="/sell-wrecked-motorcycle/"',
    'href="NonRunning.dc.html"': 'href="/sell-non-running-motorcycle/"',
}

IMAGES = {
    "/_blob/5a36974e92c9036e010bbdb6e9b839fe": (f"{PHOTOS}/raptor.png", "raptor.jpg"),
    "/_blob/c702a6728cb671d1c5ecc814ba9f89c2": (f"{PHOTOS}/trailer.jpg", "trailer.jpg"),
    "/_blob/8887eeff096e9b7140a97eeebbf2a8dc": (f"{PHOTOS}/wreck-gsxr.jpg", "wrecked-gsxr.jpg"),
    "/_blob/c3198855f025d1b96a79d4c687c0e33a": (f"{PHOTOS}/wreck-r6.jpg", "stripped-r6.jpg"),
    "/_blob/a6fc392263b2eb7b66370c35f030dca6": (f"{PHOTOS}/van-wide.jpg", "van-trailer.jpg"),
}

WIDE_IMAGES = {"van-trailer.jpg"}
WIDE_SIZES = "(max-width: 1288px) 100vw, 1240px"
CARD_SIZES = "(max-width: 760px) 100vw, 640px"
PRIVACY_LINK = ('<div style="max-width: 1240px; margin: 20px auto 0; font-size: 14px">'
                '<a href="/privacy/" style="color: #B8B3A3">Privacy policy</a></div>\n')

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
    "@type": "AutomotiveBusiness",
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


def _sec(title, *paras):
    ps = "".join(f'<p style="font-size: 18px; line-height: 1.7; color: #2A2D25; margin: 12px 0 0">{t}</p>' for t in paras)
    return f'<h2 style="font-family: \'Barlow Condensed\', sans-serif; font-weight: 800; text-transform: uppercase; font-size: 32px; margin: 44px 0 0">{title}</h2>{ps}'


PRIVACY_BODY = ("""
<div style="font-family: 'Barlow', system-ui, sans-serif; color: #141611; background: #F3EFE6; min-height: 100vh">
<header style="background: #141611; border-bottom: 1px solid #2E3229">
<div style="max-width: 1240px; margin: 0 auto; padding: 16px 24px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px">
<a href="/" style="text-decoration: none; display: flex; align-items: center; gap: 12px; color: #F3EFE6"><img src="/favicon.svg" width="40" height="40" alt=""><span style="font-family: 'Barlow Condensed', sans-serif; font-weight: 800; font-size: 24px; letter-spacing: 0.04em; text-transform: uppercase">Tired of Pavement</span></a>
<a href="sms:+17727131669" style="background: #FF6B1A; color: #141611; text-decoration: none; font-weight: 700; font-size: 15px; padding: 12px 20px; border-radius: 6px">Text us a photo</a>
</div>
</header>
<main style="max-width: 800px; margin: 0 auto; padding: 72px 24px 96px">
<h1 style="font-family: 'Barlow Condensed', sans-serif; font-weight: 800; text-transform: uppercase; font-size: clamp(44px, 7vw, 72px); line-height: 0.95; margin: 0">Privacy policy</h1>
<p style="font-size: 16px; color: #5A5E52; margin: 16px 0 0">Last updated October 23, 2026</p>
<p style="font-size: 19px; line-height: 1.7; color: #2A2D25; margin: 28px 0 0">Tired of Pavement Parts buys used motorcycles, dirt bikes, ATVs and UTVs in the Keystone Heights, Florida area. This page explains what information we get when you contact us through this website and what we do with it. Plain and short.</p>
"""
+ _sec("What we collect",
       "When you fill out an offer form, we get what you type in: your name, mobile number, the year, make and model of your machine, its condition, your town, any notes, and a photo if you attach one.",
       "When you text or email us, we get your phone number or email address and whatever you send, including photos.",
       "Like almost every website, our host automatically receives basic technical information when you visit, such as your IP address and browser type.")
+ _sec("How we use it",
       "Only to do business with you: to look at your machine, make you an offer, schedule a pickup, and keep records of what we buy, like bills of sale and VIN checks.",
       "We only text or call you about the machine you asked us about. If you'd rather we stop, just tell us and we will.")
+ _sec("Who we share it with",
       "We don't sell your information, and we don't share it with anyone for their own marketing.",
       "A few services help run this site: Netlify hosts the website and receives form submissions and emails them to us, and Google Fonts supplies the lettering on the pages, which means your browser connects to Google to load it. We may also share information when the law requires it.")
+ _sec("Cookies and tracking",
       "This site doesn't set its own cookies or run advertising trackers. If that changes, for example if we add tools to measure how our ads perform, we'll update this page first.")
+ _sec("How long we keep it",
       "If you don't sell to us, we delete your inquiry when we no longer need it. If you do, we keep the records of the purchase as long as we need them for our business and legal records.")
+ _sec("Your choices",
       "You can ask us what information we have about you, or ask us to delete it, unless we need to keep it for a completed purchase. Text 772-713-1669 or email <a href=\"mailto:ddpsports@gmail.com\">ddpsports@gmail.com</a>.")
+ _sec("Not for kids",
       "This site is for adults selling their own machines. We don't knowingly collect information from anyone under 18.")
+ _sec("Changes",
       "If we change this policy, we'll post the new version here and update the date at the top.")
+ """
</main>
<footer style="background: #141611; color: #B8B3A3; padding: 40px 24px; font-size: 15px">
<div style="max-width: 1240px; margin: 0 auto; display: flex; flex-wrap: wrap; justify-content: space-between; gap: 16px">
<span>&copy; 2026 Tired of Pavement Parts &middot; Keystone Heights, FL</span>
<span style="display: flex; flex-wrap: wrap; gap: 24px"><a href="/" style="color: #B8B3A3">Home</a><a href="/faq/" style="color: #B8B3A3">FAQ</a></span>
</div>
</footer>
</div>""")


LLMS_TXT = f"""# Tired of Pavement Parts

> Local cash buyer of used, wrecked, salvage and non-running motorcycles, dirt bikes, ATVs, side-by-sides and UTVs, based in Keystone Heights, Florida. We buy machines as-is for their parts, pay cash at pickup and haul them away. Sellers start by texting a photo to 772-713-1669.

## Key facts

- Business: Tired of Pavement Parts, Keystone Heights, Florida, USA
- Contact: text or call 772-713-1669, email ddpsports@gmail.com
- What we buy: motorcycles, sportbikes, dirt bikes, dual-sports, ATVs, side-by-sides and UTVs from major brands (Honda, Yamaha, Kawasaki, Suzuki, KTM, Husqvarna, Harley-Davidson, Polaris, Can-Am, Arctic Cat, Triumph, Ducati, BMW, Kymco)
- Condition: running or not, wrecked, crashed, salvage title, seized, missing parts, or sitting for years
- Pickup area: within 30 miles of Keystone Heights as standard, up to 50 miles for the right machine, farther for multi-bike deals. Covers Clay, Bradford, Putnam, Alachua and Union counties (Keystone Heights, Starke, Middleburg, Green Cove Springs, Interlachen, Palatka, Melrose, Hawthorne, Gainesville, Lake Butler)
- Pickup timing: usually within 48 hours of the seller accepting the offer
- Payment: cash at pickup. No separate pickup fee; the cost is built into the offer
- Paperwork: VIN checked on every machine and a signed bill of sale for every purchase. Lost titles handled case by case. We do not buy stolen machines
- Example purchases: two wrecked Suzuki GSX-Rs for $2,100 each and a stripped Yamaha R6 for $700 (picked up in Sanford, FL)

## Pages

- [Home]({DOMAIN}/): how to sell a motorcycle or ATV without listing it, process, what we buy, pickup area, offer form
- [Sell a wrecked or salvage motorcycle]({DOMAIN}/sell-wrecked-motorcycle/): why wrecks still have value, how we price them, Florida salvage and title paperwork
- [Sell a non-running motorcycle]({DOMAIN}/sell-non-running-motorcycle/): why not to fix it first, non-runners we buy, what to send for an offer
- [FAQ]({DOMAIN}/faq/): titles, paperwork, pickup, payment and what we buy

## Optional

- [Cash this week]({DOMAIN}/cash-today/): short offer page
- [Get it out of your yard]({DOMAIN}/get-it-gone/): short offer page
- [Skip the Marketplace hassle]({DOMAIN}/skip-the-hassle/): short offer page
- [Privacy policy]({DOMAIN}/privacy/)
"""


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
    webp = {}
    for blob, (src, name) in IMAGES.items():
        im = Image.open(src).convert("RGB")
        im.thumbnail((1400, 1400))
        im.save(f"{OUT}/images/{name}", "JPEG", quality=80, optimize=True, progressive=True)
        stem = name.rsplit(".", 1)[0]
        variants = []
        for target in (700, 1400):
            w = min(target, im.width)
            if variants and w == variants[-1][1]:
                continue
            v = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS) if w != im.width else im
            v.save(f"{OUT}/images/{stem}-{w}.webp", "WEBP", quality=78, method=6)
            variants.append((f"/images/{stem}-{w}.webp", w))
        webp[name] = variants

    shared_links = shared_style = None
    for fname, out, path, form, desc in PAGES:
        src = open(f"{SRC}/{fname}", encoding="utf-8").read()
        title, links, style, body = extract(src)
        shared_links, shared_style = links, style
        for a, b in LINKS.items():
            body = body.replace(a, b)
        for blob, (_, name) in IMAGES.items():
            v = webp[name]
            sizes = WIDE_SIZES if name in WIDE_IMAGES else CARD_SIZES
            srcset = ", ".join(f"{u} {w}w" for u, w in v)
            body = body.replace(f'src="{blob}"', f'src="{v[-1][0]}" srcset="{srcset}" sizes="{sizes}"')
        # privacy link in every footer
        body = body.replace("</footer>", PRIVACY_LINK + "</footer>")
        # lazy-load images below the first screen
        body = re.sub(r"<img (?!src=\"/images/raptor)", "<img loading=\"lazy\" decoding=\"async\" ", body)
        if form:
            label = {"/": "home", "/cash-today/": "cash today", "/get-it-gone/": "get it gone",
                     "/skip-the-hassle/": "skip the hassle",
                     "/sell-wrecked-motorcycle/": "wrecked bikes", "/sell-non-running-motorcycle/": "non-running bikes"}[path]
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
                    "A real person will text you back with an offer. Want to speed it up? Text a photo of the bike to 772-713-1669.",
                    f'<a href="sms:+17727131669" {btn}>Text a photo now</a><a href="/" {ghost}>Back to home</a>')
    thanks = thanks.replace("<head>", "<head>\n<meta name=\"robots\" content=\"noindex\">", 1)
    os.makedirs(f"{OUT}/thanks")
    open(f"{OUT}/thanks/index.html", "w").write(thanks)
    nf = simple("Page not found | Tired of Pavement Parts", "Wrong turn.",
                "That page doesn't exist, but we're still buying bikes.",
                f'<a href="/" {btn}>Go to the home page</a><a href="sms:+17727131669" {ghost}>Text 772-713-1669</a>')
    nf = nf.replace("<head>", "<head>\n<meta name=\"robots\" content=\"noindex\">", 1)
    open(f"{OUT}/404.html", "w").write(nf)

    privacy = head("Privacy Policy | Tired of Pavement Parts",
                   "How Tired of Pavement Parts handles the information you send us when you ask for an offer on your motorcycle, dirt bike, ATV or UTV.",
                   "/privacy/", shared_links, shared_style) + PRIVACY_BODY + "\n</body>\n</html>\n"
    os.makedirs(f"{OUT}/privacy")
    open(f"{OUT}/privacy/index.html", "w").write(privacy)

    open(f"{OUT}/llms.txt", "w").write(LLMS_TXT)
    open(f"{OUT}/favicon.svg", "w").write(FAVICON)
    open(f"{OUT}/robots.txt", "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    urls = "".join(f"  <url><loc>{DOMAIN}{p[2]}</loc><lastmod>2026-10-23</lastmod></url>\n" for p in PAGES)
    open(f"{OUT}/sitemap.xml", "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
    print("done")


if __name__ == "__main__":
    build()
