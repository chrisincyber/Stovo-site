#!/usr/bin/env python3
"""Checks the site before it is published.

- Every local link and image resolves to a file in the repository.
- Pages link to each other relatively; only 404.html uses root-relative links, because
  GitHub Pages serves it at any missing path.
- Nothing is loaded from another site, and only the listed external pages are linked.
- Every page except 404.html declares its canonical https://stovo.ch URL.
- No http:// URLs, no localhost, no placeholders.
- Languages (en at the root; de, fr, es, it, ja under <page>/<lang>/, the home page under <lang>/): the <html lang> matches
  the path, every page lists hreflang alternates for all its language versions plus x-default, and each points at an
  existing page; every #anchor link resolves to an id in its target; all language versions of a page have the same ids;
  translated privacy and terms pages link to the English page; sitemap.xml lists every page.

    python3 scripts/check_links.py
"""
import glob
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SITE = "https://stovo.ch"
ALLOWED_EXTERNAL = {
    "https://www.apple.com/legal/privacy/",
    "https://logo.dev",
    "https://www.logo.dev/legal/privacy",
    "https://world.openfoodfacts.org",
    "https://opendatacommons.org/licenses/odbl/1-0/",
    "https://supabase.com",
    "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/",
    "https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement",
}
FORBIDDEN = ["localhost", "127.0.0.1", "github.io", "[Developer name]", "[support email]", "TODO", "lorem",
             # Superseded: the publisher is Petertil TripPortier, and Stovo has no recipes or cooking.
             "Christian Petertil", "know what you can cook"]
COPYRIGHT = "© 2026 Petertil TripPortier"

errors = []
pages = sorted(p for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True) if "/_site/" not in p)
for page in pages:
    html = open(page, encoding="utf-8").read()
    name = os.path.relpath(page, ROOT)
    is_404 = name == "404.html"

    for word in FORBIDDEN:
        if word in html:
            errors.append(f"{name}: contains “{word}”")
    if "http://" in html:
        errors.append(f"{name}: contains an http:// URL")

    if not is_404 and COPYRIGHT not in html:
        errors.append(f"{name}: footer should say {COPYRIGHT}")

    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    if not is_404:
        expected = SITE + "/" + (os.path.dirname(name) + "/" if os.path.dirname(name) else "")
        if not canonical or canonical.group(1) != expected:
            errors.append(f"{name}: canonical should be {expected}")

    for attribute, ref in re.findall(r'\b(href|src)="([^"]+)"', html):
        if ref.startswith(("mailto:", "#")) or (attribute == "href" and ref.startswith(SITE + "/")):
            continue
        if ref.startswith(("http://", "https://", "//")):
            if attribute == "src":
                errors.append(f"{name}: loads {ref} from another site")
            elif ref not in ALLOWED_EXTERNAL:
                errors.append(f"{name}: unexpected external link {ref}")
            continue
        if ref.startswith("/"):
            if not is_404:
                errors.append(f"{name}: {ref} is root-relative; use a relative link")
                continue
            target = os.path.normpath(os.path.join(ROOT, ref.lstrip("/")))
        else:
            target = os.path.normpath(os.path.join(os.path.dirname(page), ref.split("#")[0]))
        if ref.split("#")[0].endswith("/") or os.path.isdir(target):
            target = os.path.join(target, "index.html")
        if not os.path.exists(target):
            errors.append(f"{name}: {ref} does not exist")

# --- Languages ---------------------------------------------------------------------------------------------------
LANGS = ["en", "de", "fr", "es", "it", "ja"]
def page_info(name):
    """(group, language) for a page path such as privacy/fr/index.html, or None."""
    parts = name.split(os.sep)
    if parts[-1] != "index.html":
        return None
    parts = parts[:-1]
    lang = "en"
    if parts and parts[-1] in LANGS[1:]:
        lang = parts.pop()
    return ("/".join(parts) or "home", lang)

def page_url(group, lang):
    return SITE + "/" + ("" if group == "home" else group + "/") + ("" if lang == "en" else lang + "/")

groups = {}
for page in pages:
    name = os.path.relpath(page, ROOT)
    info = page_info(name)
    if info:
        groups.setdefault(info[0], {})[info[1]] = page
ids = {}
for group, versions in groups.items():
    for lang, page in versions.items():
        html = open(page, encoding="utf-8").read()
        name = os.path.relpath(page, ROOT)
        ids[page] = set(re.findall(r'\bid="([^"]+)"', html))
        if not re.search(r'<html lang="%s">' % lang, html):
            errors.append(f"{name}: <html lang> should be {lang}")
        found = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html))
        expected = {l: page_url(group, l) for l in versions}
        expected["x-default"] = page_url(group, "en")
        if found != expected:
            errors.append(f"{name}: hreflang alternates should be {sorted(expected)} (found {sorted(found)})")
        if group in ("privacy", "terms") and lang not in ("en", "de"):
            english = "../" * 2 + group + "/"
            if not re.search(r'class="translation-note"[^>]*>[^<]*<a href="%s" hreflang="en"' % re.escape(english), html):
                errors.append(f"{name}: missing translation note linking to the English page")
    reference = ids[versions["en"]]
    for lang, page in versions.items():
        if ids[page] != reference:
            errors.append(f"{os.path.relpath(page, ROOT)}: ids differ from the English page: {sorted(ids[page] ^ reference)}")

# Anchor links: the id must exist in the target page.
for page in pages:
    html = open(page, encoding="utf-8").read()
    name = os.path.relpath(page, ROOT)
    for ref in re.findall(r'\bhref="([^"]*#[^"]+)"', html):
        path_part, fragment = ref.split("#", 1)
        if path_part.startswith(("http://", "https://", "mailto:")):
            continue
        if path_part == "":
            target = page
        else:
            target = os.path.normpath(os.path.join(os.path.dirname(page), path_part))
            if os.path.isdir(target) or path_part.endswith("/"):
                target = os.path.join(target, "index.html")
        if target in ids and fragment not in ids[target]:
            errors.append(f"{name}: anchor {ref} has no matching id")
        elif target not in ids and os.path.exists(target) and f'id="{fragment}"' not in open(target, encoding="utf-8").read():
            errors.append(f"{name}: anchor {ref} has no matching id")

# sitemap.xml lists every page (not 404) and nothing else.
try:
    listed = set(re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()))
    wanted = {page_url(g, l) for g, v in groups.items() for l in v}
    if listed != wanted:
        errors.append(f"sitemap.xml: differs from the pages: {sorted(listed ^ wanted)}")
except OSError as error:
    errors.append(f"sitemap.xml: {error}")

if open(os.path.join(ROOT, "CNAME")).read().strip() != "stovo.ch":
    errors.append("CNAME: must be stovo.ch")

# The file that lets stovo.ch/join/… open the app: must exist and be valid JSON with the app's id.
import json
aasa = os.path.join(ROOT, ".well-known", "apple-app-site-association")
try:
    details = json.load(open(aasa, encoding="utf-8"))["applinks"]["details"]
    if not any("JZU698Q4SL.com.stovo.Stovo" in d.get("appIDs", []) for d in details):
        errors.append(".well-known/apple-app-site-association: the app id is missing")
except Exception as error:  # missing, unreadable or not JSON
    errors.append(f".well-known/apple-app-site-association: {error}")

for message in errors:
    print(message)
print(f"{len(pages)} pages checked, {len(errors)} problems")
sys.exit(1 if errors else 0)
