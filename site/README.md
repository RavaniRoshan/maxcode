# Canonical maxcode site

- Live URL: <https://ravaniroshan.github.io/maxcode/>
- Deploy source: this folder, via [`../.github/workflows/pages.yml`](../.github/workflows/pages.yml)
- Design source of truth: [`DESIGN.md`](DESIGN.md)
- Archived alternative: <https://ravaniroshan.github.io/maxcodesite/> (source: `RavaniRoshan/maxcodesite`)

## Decision

Both sources deployed successfully. This static folder is canonical because it
is already the cleaner, design-compliant source:

- it uses the DESIGN.md tokens directly and has no GSAP, `motion`, or shader
  dependency;
- its only animations are blink, bob, glow pulse, and cursor blink;
- it has no npm build, no server, no `@google/genai`, `express`, `dotenv`, or
  other template leftovers;
- its claims already match `docs/BENCH.md` and the repository README;
- it has no client-side bundling path that could carry an API key.

The `maxcodesite` repository is archived. Its Pages workflow is disabled and its
AGENTS/DESIGN instructions are kept for historical reference only.

## Verification

```bash
# External resource hosts: only fonts.googleapis.com / fonts.gstatic.com
grep -RInE "https?://" --include='*.html' --include='*.css' --include='*.js' --include='*.svg' .

# Forbidden template/dependency traces in shipped assets
grep -RInE "maxm1|powered by|@google/genai|express|dotenv|gsap|shader|motion/|sk-[A-Za-z0-9]|GEMINI_API_KEY|OPENAI_API_KEY" \
  --include='*.html' --include='*.css' --include='*.js' --include='*.svg' .

# Contrast: DESIGN.md token pairs pass WCAG AA for body text in both themes.
# Lighthouse accessibility: see the run recorded in ../docs/SITE.md.
```

The site is static. `python3 -m http.server` is enough to preview it.
