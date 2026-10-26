#!/usr/bin/env python3
"""Checks the site before it is published.

- Every local link and image resolves to a file in the repository.
- Pages link to each other relatively; only 404.html uses root-relative links, because
  GitHub Pages serves it at any missing path.
- Nothing is loaded from another site, and only the listed external pages are linked.
- Every page except 404.html declares its canonical https://stovo.ch URL.
- No http:// URLs, no localhost, no placeholders.

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
