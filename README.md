# Suricata Rule Index

This repository contains the source index for Suricata rule and threat intelligence feeds plus a static website for GitHub Pages.

`index.yaml` is the source of truth. The Pages workflow builds a deployable `_site` payload from `.site/`, writes active-only `index.yaml` and `index.json` files, and excludes sources marked `deprecated` or `obsolete` from the published site. The build renders all rulesets into `index.html`, so the site requires no client-side JavaScript.

## Local preview

```sh
python3 -m pip install PyYAML
python3 .site/build-site.py --output _site
python3 -m http.server 8000 --directory _site
```

Then open `http://localhost:8000/`.

## Publishing

The `Deploy GitHub Pages` workflow runs on pushes to `master` and can also be started manually from GitHub Actions. The workflow publishes the generated `_site` artifact through GitHub Pages.
