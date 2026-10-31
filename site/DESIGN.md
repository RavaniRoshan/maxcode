# maxcode site: DESIGN.md

Spec for https://ravaniroshan.github.io/maxcode/. Dark by default. Terminal-native. Pixel-crisp. Silver and white.

## 1. Principles

1. **Terminal-native.** The site looks like a place a developer already works. Monospace, hard edges, 1px borders.
2. **Pixel-crisp.** Max is built on a pixel grid. Spacing and shapes follow the same grid. No soft blobs, no gradients on surfaces.
3. **Glow means verified.** The white glow and the white tick appear only when something passed a check. Never use them as decoration.
4. **Show, don't claim.** Every number on the site comes from a published log. No logo walls, no invented stats.

## 2. Color tokens

The page is a deep ink-navy. Silver and white carry the brand, so Max reads as a bright object on a dark stage.

### Dark (default)

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#070B14` | Page background (ink navy) |
| `--surface` | `#0E1422` | Cards, code blocks |
| `--surface-2` | `#141C2E` | Hover, nested surfaces |
| `--border` | `#1E2A40` | 1px borders, dividers |
| `--text` | `#F5F7FA` | Headings and body |
| `--text-2` | `#A9B4C4` | Secondary text |
| `--muted` | `#8D99AB` | Captions, placeholders (passes AA on `--bg`) |
| `--silver` | `#D9DEE5` | Brand. Max's body. Borders on hover, icons |
| `--silver-hi` | `#FFFFFF` | Highlights, the tick, primary button fill |
| `--silver-mid` | `#AEB6C2` | Shade, pressed states |
| `--silver-lo` | `#8D99AB` | Feet, hard shadows |
| `--aura` | `#BEE6FF` | Glow only. Used at low opacity |
| `--red` | `#F87171` | Failed state only |
| `--blue` | `#7DD3FC` | Info, sweat drop |
| `--slate` | `#94A3B8` | Working state |
| `--ink` | `#0A0F1E` | Max's eyes. Text on white buttons |

### Light

| Token | Hex |
|---|---|
| `--bg` | `#F4F6F9` |
| `--surface` | `#FFFFFF` |
| `--surface-2` | `#EAEEF4` |
| `--border` | `#D5DCE6` |
| `--text` | `#0A0F1E` |
| `--text-2` | `#3D4A60` |
| `--muted` | `#56637A` |
| `--red` | `#B91C1C` |

Silver is low contrast on light backgrounds. In light mode, Max always sits on a dark tile (`#070B14`, 8px padding, 6px radius). Links in light mode use `--text` with an underline.

### CSS

```css
:root {
  --bg: #070B14;  --surface: #0E1422;  --surface-2: #141C2E;  --border: #1E2A40;
  --text: #F5F7FA;  --text-2: #A9B4C4;  --muted: #8D99AB;
  --silver: #D9DEE5;  --silver-hi: #FFFFFF;  --silver-mid: #AEB6C2;  --silver-lo: #8D99AB;
  --aura: #BEE6FF;
  --red: #F87171;  --blue: #7DD3FC;  --slate: #94A3B8;  --ink: #0A0F1E;
  color-scheme: dark;
}
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) {
    --bg: #F4F6F9;  --surface: #FFFFFF;  --surface-2: #EAEEF4;  --border: #D5DCE6;
    --text: #0A0F1E;  --text-2: #3D4A60;  --muted: #56637A;
    --red: #B91C1C;
    color-scheme: light;
  }
}
:root[data-theme="light"] { /* same values as the light table */ }
```

### Color rules

- **Proportion.** About 65% `--bg`, 30% surfaces and text, 5% silver and white accents.
- **Semantics.** White glow and tick = verified. Red = failed. Slate = in progress. Gray = unverified.
- **One bright thing per view.** White is the strongest color on the page. Use it on one element per screen: the primary button or Max.
- **No hue accent.** The site has no brand color besides silver and white. The aura blue appears only inside glows.
- **Never** put `--muted` or `--text-2` text on `--surface-2` below 14px.

## 3. Typography

| Role | Font | Fallback |
|---|---|---|
| Display and code | JetBrains Mono (OFL) | ui-monospace, SFMono-Regular, Menlo, Consolas, monospace |
| Body | Inter (OFL) | system-ui, -apple-system, Segoe UI, sans-serif |

Both fonts load from Google Fonts with `display=swap`. The page must stay readable on the fallback stack.

| Style | Size / line height | Weight | Font |
|---|---|---|---|
| H1 | 56 / 60 (36 / 40 on mobile) | 700 | Mono |
| H2 | 32 / 38 | 700 | Mono |
| H3 | 20 / 28 | 600 | Mono |
| Body | 17 / 28 | 400 | Inter |
| Small | 14 / 20 | 400 | Inter |
| Code | 14 / 22 | 400 | Mono |

Rules: left-align everything. Max line length 68 characters. Use sentence case. No all-caps except the 12px label style (mono, 600, +0.08em tracking).

## 4. Layout and spacing

- **Grid.** Base unit 8px. Spacing scale: 4, 8, 16, 24, 32, 48, 64, 96.
- **Width.** Content max 1120px. Prose max 680px. Side padding 24px (16px on mobile).
- **Section rhythm.** 96px between sections on desktop, 64px on mobile.
- **Radius.** Cards 6px. Buttons 4px. Chips 2px. Max is never rounded.
- **Borders.** 1px `--border`. No drop shadows on cards.
- **Hard shadow.** The primary button uses `box-shadow: 4px 4px 0 var(--silver-lo)`. On press, remove the shadow and move 4px down-right.

## 5. Mascot: Max

Files: `max.svg` (idle, animated), `max-sheet.svg` (all poses), `max-favicon.svg` (face only).

Body: `#D9DEE5`, top row `#FFFFFF`, right and bottom edge `#AEB6C2`, feet `#8D99AB`. Eyes and mouth: `#0A0F1E`. Tick: `#FFFFFF`. Glow: `#BEE6FF`.

### Poses

| Pose | Where it appears |
|---|---|
| idle | Hero, 404 page, footer |
| working | "Work" step in the loop section |
| pass | "Done" step, benchmark pass rows, success states |
| fail | "Rolled back" step, error pages |

### Rules

1. One Max per viewport. Never crowd the page with copies.
2. Minimum size 32px. Below that, use the favicon face.
3. Keep the proportions. Never stretch, rotate, or add outlines.
4. Never recolor the body. Silver and white only.
5. Never add arms, a hat, or a second color. The silhouette stays: block, two feet, tick.
6. The tick and the glow appear only in idle and pass poses. They are the verified mark.
7. The glow is a soft radial gradient behind Max. Never add a hard-edged frame, box, or outline around it.
8. Render the body with `shape-rendering="crispEdges"`. For PNG exports use `image-rendering: pixelated`.

### Placement

```html
<link rel="icon" href="max-favicon.svg" type="image/svg+xml">

<img src="max.svg" alt="Max, the maxcode mascot" width="168" height="189">
```

Embed with `<img>`. The blink, bob, and glow pulse run inside the SVG. They stop under `prefers-reduced-motion`.

## 6. Pages

The site has four pages: Home, Docs, Benchmark, GitHub (external link).

### Home

| # | Section | Content |
|---|---|---|
| 1 | Nav | Wordmark `maxcode` + blinking white block cursor. Links: Docs, Benchmark, GitHub. Theme toggle. |
| 2 | Hero | H1, one sentence, install command with copy button, secondary link to the benchmark. Max (idle) on the right. |
| 3 | The loop | Four cards in a row: Plan, Work, Verify, Done. Each card shows one Max pose and one sentence. |
| 4 | Terminal demo | One static transcript in a code block, labeled "example run". Plan, steps, check output, result. |
| 5 | Why a gate | Three cards: checks run outside the model, every step has a checkpoint, cost per finished task. |
| 6 | Benchmark teaser | Table of pass rate with the verifier on and off. Link to the logs. |
| 7 | Open source | Apache-2.0, bring your own key, any OpenAI-compatible provider. |
| 8 | Footer | License, attribution line, GitHub link, Max (idle, 48px). |

Hero copy (original, replace freely):

- H1: `Done means the checks passed.`
- Sub: `maxcode is an open-source coding CLI. It plans the task, makes the edits, and runs your tests before it says done.`
- Install: `uvx maxcode` (confirm the command works before launch).

### Docs

Single page with a left sidebar. Sections: Install, Config, Commands, How a run works, Checkpoints and undo, Cost report, Benchmark method.

### Benchmark

Method paragraph, results table, link to raw logs and the script. Show failures. Never show a number that is not in the published logs.

## 7. Components

| Component | Spec |
|---|---|
| Primary button | `--silver-hi` fill, `--ink` text, mono 600, 48px tall, hard shadow. |
| Secondary button | 1px `--border`, `--text`, transparent fill. Hover: border `--silver`. |
| Code block | `--surface`, 1px `--border`, 6px radius, 16px padding. Copy button top-right. Prompt `$` in `--muted`. |
| Card | `--surface`, 1px `--border`, 24px padding. Hover: border becomes `--silver-lo`. |
| Status chip | Mono 12px label. `pass` = white text + white-tinted border. `fail` = red. `working` = slate. `unverified` = muted. |
| Table | Mono numbers, right-aligned. 1px row dividers. No zebra stripes. |
| Nav | 64px tall, sticky, `--bg` with 1px bottom border. |
| Cursor | A 12 x 24px `--silver-hi` block after the wordmark. Blinks at 1.1s with `steps(1)`. |

Terminal demo coloring: `$` muted, step labels slate, `pass` white, `fail` red, file paths silver.

## 8. Motion

- Max blink: every 4s. Tick bob: 1.6s, 0.4px. Glow pulse: 3s. Cursor blink: 1.1s.
- Page transitions: none. Hover transitions: 120ms, `steps` or linear. No easing curves, no parallax.
- Reduced motion: disable every animation above.

## 9. Accessibility

- Body text contrast at least 4.5:1. Verify `--muted` and `--text-2` on every surface.
- Visible focus ring: 2px `--silver-hi` outline, 2px offset.
- Max images get alt text. Decorative copies use `alt=""`.
- Copy buttons have a text label for screen readers.
- Never use color alone for pass or fail. Always add the word.
- Support keyboard navigation for the nav, the copy buttons, and the theme toggle.

## 10. Copy and claims rules

1. **Original copy only.** Write every sentence yourself. Do not reuse wording from the Sarvam Code site or press pages.
2. **No false model claims.** The archived page title claimed a model that maxcode does not have (a PRD non-goal). The canonical site makes no model claim.
3. **No numbers without logs.** Pass rates and cost figures appear only after the benchmark logs are public.
4. **Attribution.** Footer line: `Built on the Apache-2.0 Codex CLI. Not affiliated with OpenAI or Sarvam AI.` Use the name only in this line, never as branding. Never use their logos.
5. **No "clone".** Say "open-source alternative" or "open-source coding CLI".
6. **Meta tags.** Replace the current title and description.

```html
<title>maxcode | Open-source coding CLI that finishes only when checks pass</title>
<meta name="description" content="maxcode plans a coding task, edits your repo, and runs your tests before it says done. Open source. Bring your own model key.">
<meta property="og:title" content="maxcode | Done means the checks passed">
<meta property="og:image" content="/maxcode/og.png">
```

OG image: 1200 x 630, `--bg` background, Max (idle, with glow) left, the H1 right.

## 11. Asset checklist

- [ ] `max.svg`, `max-sheet.svg`, `max-favicon.svg` in the site folder
- [ ] `og.png` at 1200 x 630
- [ ] Fonts: JetBrains Mono, Inter (licenses checked)
- [ ] Light and dark both tested, Max on a dark tile in light mode
- [ ] No external image, script, or font host except Google Fonts
- [ ] No Sarvam or OpenAI asset, logo, or text
- [ ] Lighthouse accessibility score 95 or higher
- [ ] Benchmark page links to real logs

## 12. Don'ts

- Don't use gradients on surfaces. The only gradient is Max's glow.
- Don't add a color accent. The brand is silver and white.
- Don't show more than one Max at once.
- Don't add testimonials, logo walls, or fake metrics.
- Don't copy layout, palette, or text from the Sarvam site. Use it as a reference for section order only.
