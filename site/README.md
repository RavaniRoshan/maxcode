# Canonical maxcode site

- Live URL: <https://ravaniroshan.github.io/maxcode/>
- Documentation: <https://ravaniroshan.github.io/maxcode/docs/>
- Deploy source: this folder, via [`../.github/workflows/pages.yml`](../.github/workflows/pages.yml)
- Design source of truth: [`DESIGN.md`](DESIGN.md)
- Archived alternative: <https://ravaniroshan.github.io/maxcodesite/> (source: `RavaniRoshan/maxcodesite`)

## Structure

- Static marketing pages: `index.html`, `benchmark.html`, `style.css`, `app.js`
- Fumadocs documentation: `docs/` (Next.js static export, Fumadocs UI)
- Build and merge: [`build.sh`](build.sh) → `dist/`

## Decision

Both sources deployed successfully. This folder is canonical because it is the
cleaner, design-compliant source:

- Fumadocs neutral tokens in light and dark;
- only blink, bob, glow pulse, and cursor blink animations;
- no GSAP, `motion`, or shader runtime;
- no `@google/genai`, `express`, `dotenv`, or other template leftovers;
- no client-side bundle that could carry an API key;
- claims already match `docs/BENCH.md` and the repository README.

The `maxcodesite` repository is archived. Its Pages workflow is disabled and its
AGENTS/DESIGN instructions are kept for historical reference only.

## Build

```bash
cd site
BASE_PATH=/maxcode bash build.sh
```

The script runs `npm ci` and `npm run build` in `docs/`, then merges the
Fumadocs export into `dist/` beside the static pages. `dist/` is ignored.

Preview the exact Pages layout by serving a parent directory:

```bash
mkdir -p /tmp/maxcode-pages
cp -r dist /tmp/maxcode-pages/maxcode
python3 -m http.server 8765 --directory /tmp/maxcode-pages
# open http://127.0.0.1:8765/maxcode/ and /maxcode/docs/
```

## Verification

```bash
# Build first.
BASE_PATH=/maxcode bash build.sh

# External resource hosts in the shipped dist:
# only fonts.googleapis.com / fonts.gstatic.com (plus self references).
grep -RInE "https?://" --include='*.html' --include='*.css' --include='*.js' --include='*.svg' dist

# Forbidden template/dependency traces in shipped assets.
grep -RInE "powered by|@google/genai|express|dotenv|gsap|shader|motion/|sk-[A-Za-z0-9]|GEMINI_API_KEY|OPENAI_API_KEY" \
  --include='*.html' --include='*.css' --include='*.js' --include='*.svg' dist

# Contrast and Lighthouse results: ../docs/SITE.md
```

The Fumadocs app uses its own self-hosted Geist/JetBrains Mono files from the
build. The marketing pages load Google Fonts only. No other resource host is
allowed.
