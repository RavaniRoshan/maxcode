# Canonical site: decision and verification

Date: 2026-10-31

## Decision

Canonical source: [`site/`](../site/) in `RavaniRoshan/maxcode`.

- Live URL: <https://ravaniroshan.github.io/maxcode/>
- Deploy workflow: [`../.github/workflows/pages.yml`](../.github/workflows/pages.yml)
- Design source of truth: [`../site/DESIGN.md`](../site/DESIGN.md)
- Archived alternative: `RavaniRoshan/maxcodesite`, now with `ARCHIVED.md` and
  its deploy workflow moved to `.github/workflows-disabled/`.

Both sources deployed successfully. The static `site/` folder was chosen because
it is the cleaner and already-compliant source:

- exact DESIGN.md tokens in light and dark;
- only blink, bob, glow pulse, and cursor blink animations;
- no GSAP, `motion`, or shader runtime;
- no npm build, `@google/genai`, `express`, `dotenv`, or other template leftovers;
- no client-side bundle that could carry an API key;
- claims already match `docs/BENCH.md` and the repository README.

`reicon-react` is not needed: the canonical site has no package manifest and its
marks are local SVGs/images.

## DESIGN.md compliance

- `site/DESIGN.md` is copied from the archived source, with the URL and OG image
  path updated from `/maxcodesite/` to `/maxcode/`.
- `site/AGENTS.md` replaces the old BoardUI token rules with a short pointer to
  `DESIGN.md`.
- Home title, description, and `og:title` match DESIGN.md section 10 exactly.
  `og:image` uses the canonical deployment path.
- No model-brand claim remains in the canonical site.
- The only animations are `blink`, `bob`, `pulse`, and the cursor blink. All
  stop under `prefers-reduced-motion`.

## Claims audit

| Site statement | Evidence |
|---|---|
| Verifier on 3/3, verifier off 3/3, N=3 | `docs/bench/2026-10-31/verifier-on/results.csv`, `verifier-off/results.csv` |
| Absolute gain 0 percentage points | `docs/BENCH.md` first paragraph and `report.txt` |
| Verifier-on hit the 300-second worker timeout | `docs/bench/2026-10-31/verifier-on/task-*/run.jsonl` |
| Requests excluded after 4 pre-existing failures | `docs/BENCH.md` failure section |
| alpha status | repository README `v0.1.0-alpha.1` |

No site page publishes a pass rate or cost without linking the committed log.

## Contrast

Token pairs use the exact DESIGN.md values. WCAG 2.1 contrast:

| Pair | Ratio |
|---|---:|
| dark text / bg | 18.34 |
| dark text-2 / bg | 9.38 |
| dark muted / bg | 6.82 |
| dark text-2 / surface-2 | 8.11 |
| dark muted / surface-2 | 5.89 |
| dark red / bg | 7.12 |
| light text / bg | 17.63 |
| light text-2 / bg | 8.27 |
| light muted / bg | 5.60 |
| light text-2 / surface-2 | 7.68 |
| light muted / surface-2 | 5.21 |
| light red / bg | 5.98 |
| terminal path / dark ground | 14.56 |
| terminal step / dark ground | 7.68 |

The terminal stays on its dark ground in both themes, because DESIGN.md's
terminal palette (silver paths, slate steps, white pass) only clears contrast on
dark. All body-text pairs are at least 4.5:1.

## Lighthouse accessibility

Run with Lighthouse 12 against the local static server, light and forced-dark
copies:

| Page | Light | Dark |
|---|---:|---:|
| `index.html` | 1.00 | 1.00 |
| `docs.html` | 1.00 | 1.00 |
| `benchmark.html` | 1.00 | 1.00 |

Command shape:

```bash
python3 -m http.server 8765 --directory site
CHROME_PATH=/snap/bin/chromium npx -y lighthouse@12 \
  http://127.0.0.1:8765/index.html \
  --only-categories=accessibility --output=json --output-path=/tmp/lh.json \
  --chrome-flags="--headless --no-sandbox --disable-gpu"
```

Dark mode was the same page with `data-theme="dark"` on `<html>`.

## External hosts

Resource requests in the canonical site are limited to Google Fonts:

- `fonts.googleapis.com`
- `fonts.gstatic.com`

Everything else external is a link destination, not a fetched resource:
GitHub repository/log links and the `text.pollinations.ai` / localhost examples
shown as configuration text. There are no external scripts, images, or fonts
beyond Google Fonts.

## API-key exposure

The canonical site has no build step, no environment variables, no provider SDK,
and no `fetch`/XHR call. A key cannot enter a client bundle because there is no
bundle. The grep checks in `site/README.md` return no API-key patterns.
