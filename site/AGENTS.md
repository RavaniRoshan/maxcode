# maxcode site

`DESIGN.md` in this folder is the source of truth for tokens, type, layout, motion, copy, and accessibility.

- Keep this site static: HTML, CSS, and vanilla JS. No build step and no runtime dependency.
- The only allowed animations are blink, bob, glow pulse, and cursor blink. Respect `prefers-reduced-motion`.
- The only external resource host is Google Fonts. GitHub is a link destination, not a bundled dependency.
- Every number and comparison must match `docs/BENCH.md` and the repository README. No number without a committed log.
- Never add an API key, a provider SDK, or a client-side model call.
