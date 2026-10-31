# Canonical site: decision and verification

Date: 2026-10-31

## Decision

Canonical source: [`site/`](../site/) in `RavaniRoshan/maxcode`.

- Marketing URL: <https://ravaniroshan.github.io/maxcode/>
- Documentation URL: <https://ravaniroshan.github.io/maxcode/docs>
- Deploy workflow: [`../.github/workflows/pages.yml`](../.github/workflows/pages.yml)
- Design source of truth: [`../site/DESIGN.md`](../site/DESIGN.md)
- Archived alternative: `RavaniRoshan/maxcodesite`, with `ARCHIVED.md` and its
  deploy workflow moved to `.github/workflows-disabled/`.

The canonical site is now a Fumadocs-neutral system for marketing and a real
Fumadocs app for documentation. The archived React/GSAP/shader site is no longer
deployed or linked.

## Fumadocs documentation

`site/docs/` is a Next.js 16 + Fumadocs 16 static-export app:

- `content/docs/*.mdx` — overview, quickstart, providers, commands, run loop,
  checkpoints, cost, benchmark, security, legal
- Fumadocs sidebar, search, table of contents, MDX, and static export
- neutral theme, Geist + JetBrains Mono, self-hosted font files in `_next`
- build: `BASE_PATH=/maxcode npm run build` from `site/docs`
- merge: `site/build.sh` copies the static marketing files and the Fumadocs
  export into `dist/`; `/docs` is the docs index

## Design system

The marketing pages use the same neutral primitives as Fumadocs:

- light `#F5F5F5` ground, `#0A0A0A` foreground, `#F1F1F1` cards,
  `rgba(0,0,0,.16)` borders;
- dark `#121212` ground, `#EDEDED` foreground, `#191919` cards,
  `rgba(255,255,255,.14)` borders;
- Geist for display/body, JetBrains Mono for code, labels, and numbers;
- 56px blurred sticky nav, 1400px layout, pill buttons, 16/24px rounded cards;
- one dark terminal panel that keeps DESIGN's silver/slate/white code palette.

Only blink, bob, glow pulse, and cursor blink animate. All stop under
`prefers-reduced-motion`.

## Contrast

WCAG 2.1 ratios for the shipped token pairs:

| Pair | Ratio |
|---|---:|
| light foreground / background | 18.16 |
| light muted / background | 5.86 |
| light muted / card | 5.65 |
| light success / card | 6.31 |
| light danger / card | 5.73 |
| dark foreground / background | 16.00 |
| dark muted / background | 8.93 |
| dark muted / card | 8.39 |
| dark success / card | 10.09 |
| dark danger / card | 6.36 |
| terminal path / ground | 14.64 |
| terminal step / ground | 9.44 |
| terminal pass / ground | 19.80 |
| terminal fail / ground | 7.16 |
| docs muted light | 5.86 |
| docs muted dark | 8.93 |
| code red light | 6.53 |
| code red dark | 10.38 |

All body-text pairs pass 4.5:1. The Fumadocs muted token was darkened from
`#737373` to `#5F5F5F` in light mode; Shiki's light red token was darkened to
`#A61E2E` and its dark red to `#FFB3B8`.

## Lighthouse accessibility

Lighthouse 12, local Pages-shaped build, light and forced dark:

| Page | Light | Dark |
|---|---:|---:|
| marketing `/` | 1.00 | 1.00 |
| docs index `/docs` | 1.00 | 1.00 |
| docs quickstart `/docs/quickstart` | 1.00 | 1.00 |
| benchmark `/benchmark.html` | 1.00 | 1.00 |

Command shape:

```bash
BASE_PATH=/maxcode bash site/build.sh
mkdir -p /tmp/maxcode-pages
cp -r site/dist /tmp/maxcode-pages/maxcode
python3 -m http.server 8765 --directory /tmp/maxcode-pages

CHROME_PATH=/snap/bin/chromium npx -y lighthouse@12 \
  http://127.0.0.1:8765/maxcode/ \
  --only-categories=accessibility --output=json --output-path=/tmp/lh.json \
  --chrome-flags="--headless --no-sandbox --disable-gpu"
```

## External hosts

The built site was scanned for `script`, `link`, `img`, and `iframe` resources:

- marketing pages load Google Fonts only (`fonts.googleapis.com`,
  `fonts.gstatic.com`);
- the Fumadocs app self-hosts its Geist/JetBrains Mono files under
  `/maxcode/_next/static/media`;
- GitHub links are anchor destinations, not fetched resources;
- no external images, scripts, analytics, or iframes.

## API-key exposure

The marketing pages are static and have no build step. The Fumadocs app has no
provider SDK and no API-key read. There is no client-side bundle path that
carries a key. A grep of the shipped HTML/JS for key patterns returns nothing.

## Claims

| Site statement | Evidence |
|---|---|
| 3/3 verifier on, 3/3 verifier off, N=3 | `docs/bench/2026-10-31/verifier-{on,off}/results.csv` |
| 0-point gain | `docs/BENCH.md` first paragraph, `report.txt` |
| verifier-on 300s timeout | `docs/bench/2026-10-31/verifier-on/task-*/run.jsonl` |
| requests excluded after 4 failures | `docs/BENCH.md` |
| alpha status | repository README `v0.1.0-alpha.1` |

No page claims a maxcode-owned model, training capability, or outcome-based
billing.
