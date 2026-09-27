# Stovo website

The public website for [Stovo](https://stovo.ch), a shopping list and pantry app for iPhone
and iPad: home page, privacy policy and support. It contains no app source code — the app
lives in a separate private repository.

| Page | URL |
| --- | --- |
| Home | https://stovo.ch/ |
| Privacy Policy | https://stovo.ch/privacy/ — used as the App Store privacy policy URL |
| Support | https://stovo.ch/support/ — used as the App Store support URL |

Plain HTML and one stylesheet (`assets/style.css`): no framework, no build step, no
JavaScript, cookies, analytics or external fonts. Light and dark mode follow the system.

## Structure

| Path | What it is |
| --- | --- |
| `index.html`, `privacy/`, `support/`, `404.html` | The pages |
| `assets/` | Stylesheet, app icon, favicons, screenshots |
| `CNAME` | `stovo.ch` (see *Custom domain*) |
| `scripts/check_links.py` | Link and content check, run before every deployment |
| `.github/workflows/pages.yml` | Checks and publishes the site |

Pages link to each other relatively; only `404.html` uses root-relative links, because
GitHub Pages serves it at any missing path.

## Testing locally

```sh
python3 scripts/check_links.py     # links, canonical URLs, no placeholders
python3 -m http.server 8000        # then open http://localhost:8000/
```

## Deployment

Every push to `main` (except README-only changes) runs the *Pages* workflow: it checks the
links, copies the served files into an artifact and deploys it with GitHub's official
Pages actions. It can also be run by hand under Actions → Pages → Run workflow.
Repository Settings → Pages → Build and deployment → Source is **GitHub Actions**.

## Custom domain

The site is served at `stovo.ch`, set under Settings → Pages → Custom domain. With an
Actions deployment GitHub takes the domain from that setting; the `CNAME` file only
records it. DNS for `stovo.ch` points the apex at GitHub Pages' A and AAAA addresses and
`www` at `chrisincyber.github.io` — see GitHub's
[custom domain documentation](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
for the current addresses. Enforce HTTPS is switched on in the same settings once the
certificate has been issued.

## Updating the App Store link

`index.html` shows a "Coming soon" placeholder. Replace it with the App Store link once the
listing is live.
