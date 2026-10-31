# maxcode documentation

Fumadocs app for <https://ravaniroshan.github.io/maxcode/docs>.

- Framework: Next.js 16 static export + Fumadocs 16
- Content: `content/docs/*.mdx`
- Navigation: `content/docs/meta.json`
- Layout: `app/docs/layout.tsx`
- Source adapter: `lib/source.ts`
- Theme: Fumadocs neutral, Geist + JetBrains Mono, with a darker muted token
  for AA contrast

## Develop

```bash
npm ci
npm run dev
# http://localhost:3001/docs
```

## Build

```bash
BASE_PATH=/maxcode NEXT_TELEMETRY_DISABLED=1 npm run build
```

The static export lands in `out/`. The repository build script
(`../build.sh`) merges it into the canonical `dist/` beside the marketing pages.

## Claims

Every number and comparison in `content/docs/` must match `docs/BENCH.md` and
the repository README. The benchmark page currently publishes N=3, 3/3 in both
verifier arms, and a 0-point gain. Do not add model, pricing, or training claims
that the repository cannot support.
