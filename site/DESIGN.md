# maxcode site: design system

Canonical URL: <https://ravaniroshan.github.io/maxcode/>
Docs: <https://ravaniroshan.github.io/maxcode/docs/>
The documentation framework is [Fumadocs](https://www.fumadocs.dev/).

The visual language follows Fumadocs' neutral system: Geist + JetBrains Mono,
light/dark surfaces, 1px translucent borders, rounded cards, pill controls, and
a 1400px layout. The product keeps one distinctive object: Max, the pixel
mascot, and a dark terminal panel.

## Tokens

### Light

Tokens use Fumadocs' `--color-fd-*` namespace, with short `--fd-*` aliases.

| Token | Value | Use |
|---|---|---|
| `--color-fd-background` | `hsl(0,0%,96%)` | Page ground |
| `--color-fd-foreground` | `hsl(0,0%,3.9%)` | Headings and body |
| `--color-fd-muted-foreground` | `#5F5F5F` | Secondary text (AA override of the preset) |
| `--color-fd-card` | `hsl(0,0%,94.7%)` | Cards, panels |
| `--color-fd-card-foreground` | `hsl(0,0%,3.9%)` | Text on cards |
| `--color-fd-secondary` | `hsl(0,0%,93.1%)` | Secondary buttons, icon tiles |
| `--color-fd-border` | `hsla(0,0%,80%,50%)` | 1px borders |
| `--color-fd-primary` | `hsl(0,0%,9%)` | Primary button |
| `--color-fd-primary-foreground` | `hsl(0,0%,98%)` | Primary button text |
| `--color-fd-ring` | `hsl(0,0%,63.9%)` | Focus ring |
| `--success` | `#166534` | Pass text |
| `--danger` | `#B91C1C` | Failure text |

### Dark

| Token | Value |
|---|---|
| `--color-fd-background` | `hsl(0,0%,7.04%)` |
| `--color-fd-foreground` | `hsl(0,0%,92%)` |
| `--color-fd-muted-foreground` | `#B3B3B3` |
| `--color-fd-card` | `hsl(0,0%,9.8%)` |
| `--color-fd-card-foreground` | `hsl(0,0%,98%)` |
| `--color-fd-secondary` | `hsl(0,0%,12.9%)` |
| `--color-fd-border` | `hsla(0,0%,40%,20%)` |
| `--color-fd-primary` | `hsl(0,0%,98%)` |
| `--color-fd-primary-foreground` | `hsl(0,0%,9%)` |
| `--color-fd-ring` | `hsl(0,0%,54.9%)` |
| `--success` | `#4ADE80` |
| `--danger` | `#F87171` |

The terminal is always dark: `#0A0A0A` ground, `#EDEDED` text, silver paths,
slate labels, white pass, red fail. This keeps DESIGN's terminal palette legible
in both themes.

## Typography

| Role | Font |
|---|---|
| Display and body | Geist |
| Code, labels, numbers | JetBrains Mono |

Body 16/1.6, lead 19/1.6, H1 `clamp(38px, 5.4vw, 64px)` at 1.04, H2
`clamp(28px, 3.4vw, 40px)`, H3 18/1.35. Mono labels are 12px, 600, uppercase,
0.08em tracking. Sentence case.

## Layout

- Layout width 1400px; prose width 760px; side padding 24px (16px mobile).
- Nav 56px, sticky, translucent background with 12px blur, 1px bottom border.
- Section rhythm 72px desktop, 48px mobile.
- Radii: controls 6–10px, cards 16px, feature panels 24px.
- Cards: 1px border, card surface, 24px padding, no surface gradient.
- Buttons: pill, 42px minimum height. Primary is near-black/near-white.
- Code panels: 1px border, 6–16px radius, mono 13px.
- Only one Max per viewport. The hero uses `max.svg`; the footer uses the
  favicon face.

## Motion

Allowed animations only:

- Max blink: 4s.
- Tick bob: 1.6s, 0.4px.
- Glow pulse: 3s.
- Cursor blink: 1.1s.

Hover/focus transitions are 150ms linear or steps. No scroll animation,
parallax, GSAP, `motion`, or shaders. All animations stop under
`prefers-reduced-motion`.

## Accessibility

- Body text at least 4.5:1 in both themes.
- Focus ring: 2px `--fd-ring`, 2px offset.
- Max images get alt text; decorative copies use `alt=""`.
- Copy buttons have `aria-label`.
- Tables have captions (`.sr-only` where the visible heading already names it).
- Never use color alone for pass/fail; always include the word.
- Nav, copy buttons, and theme toggle are keyboard operable.

## Claims

- No model of its own. Do not claim a model or training capability.
- Every number must match `docs/BENCH.md` and the repository README.
- The published benchmark is N=3, 3/3 in both arms, 0-point gain. State that
  plainly.
- No pricing or billing claim. Local runs report tokens and a `$0.0000` partial
  cost because no price is configured.
- Attribution line only: `Built on the Apache-2.0 Codex CLI. Not affiliated with
  OpenAI or Sarvam AI.` Never use an upstream logo or brand asset.

## Docs

`site/docs/` is a Fumadocs app. It uses `fumadocs-core`, `fumadocs-mdx`, and
`fumadocs-ui` with the neutral theme, Geist, search, sidebar, MDX, and static
export. `site/build.sh` builds it with `BASE_PATH=/maxcode` and merges the output
into `dist/` beside the static marketing pages. `/docs` is the Fumadocs index;
the marketing nav links there with no trailing slash.

## Assets

- `max.svg`, `max-sheet.svg`, `max-favicon.svg`
- `og.png` 1200×630
- Fonts: Geist and JetBrains Mono via Google Fonts (display=swap)
- No external image, script, or font host except Google Fonts
- No Sarvam or OpenAI asset, logo, or text
