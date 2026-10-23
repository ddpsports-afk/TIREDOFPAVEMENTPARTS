# tiredofpavementparts.com

Website for Tired of Pavement Parts, a cash buyer of used, wrecked and non-running motorcycles, dirt bikes and ATVs in Keystone Heights, FL.

## What's where

| Folder | What it is |
| --- | --- |
| `site/` | The live website. Netlify publishes this folder exactly as it is. |
| `source/canvas/` | The design pages (from the Claude design canvas) the site is generated from. |
| `source/photos/` | Photos used on the site, already cropped and cleaned (no plates or other branding). |
| `tools/build.py` | Turns `source/` into `site/`: page links, SEO tags, FAQ and business schema, Netlify forms, compressed images, sitemap. |

## Pages

- `/`: home
- `/cash-today/`, `/get-it-gone/`, `/skip-the-hassle/`: Facebook ad landing pages
- `/faq/`: questions and answers, with FAQ schema for Google and AI search
- `/thanks/`: shown after a form is sent (not indexed)

## Making changes

Edit the files in `source/`, run `python3 tools/build.py` (needs Python 3 and Pillow), then commit both `source/` and `site/`. Netlify redeploys automatically on every push.

Form submissions arrive through Netlify Forms. Form detection and the email notification to ddpsports@gmail.com are set in the Netlify dashboard.
