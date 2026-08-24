# desktopdigitalomanai

The **DigitalOman.ai** scroll film — a single-page, scroll-scrubbed product film.
Open `index.html`, or serve this repo with GitHub Pages.

## Enabling Pages

Settings → Pages → Build and deployment → **Deploy from a branch** → `main` / `/ (root)`.
Nothing to build; the site is static and every path is relative, so it works on a
project page (`sivavimel.github.io/desktopdigitalomanai/`) as well as a custom domain.

## What is here

```
index.html                 the whole film — markup, styles and the timeline engine
fonts/fonts-inline.css     Inter + JetBrains Mono, latin subset, embedded as data URIs
images/                    the mark, and the two photographic plates
light/                     screens captured from the running app, light theme
audit.py                   layout regression test (see below)
.nojekyll                  skip the Jekyll build step
```

14 files, ~1.2 MB. No dependencies, no build step, no server config.

## How it works

There is no video and no CSS animation. The page is one continuous timeline that
the reader scrubs with the scroll wheel:

```
T = section index + that section's progress      // one global clock
draw(T)  →  every stage sets its own inline styles
```

Each `<section>` is a spacer that supplies scroll distance; each `.stage` is
`position: fixed` and cross-dissolves with its neighbours, so sections hand over
the way a cut does. `draw()` is a pure function of scroll position, so the film
runs forwards, backwards, and at any speed it is flung.

Headlines arrive a word at a time while the line re-centres around them. Word
widths are measured once, and each word's presence drives both its reveal and the
width it claims, so the line breathes apart and the word materialises into it.
Long lines wrap into rows that each re-centre on their own, which is how a phone
gets the identical move rather than a shrunken one.

## Checking a change

```bash
python3 -m http.server 8899
python3 audit.py
```

Walks the whole reel at 15 viewports — 320 px to 2560 px, portrait and landscape —
firing the height-only resize a phone produces when its address bar slides, and
asserts that no two words of a line overlap and that no anchored text leaves the
frame. Exits non-zero on failure.

Three invariants it protects, each of which broke once:

1. **Never measure a hidden element.** A span inside a `display:none` stage
   measures as zero width, and zero widths put every word of a line on the same
   point. Lines re-measure lazily at draw time, when the stage is on screen by
   definition.
2. **A phone's address bar fires resize constantly.** Height does not affect text
   metrics, so a height-only change only redraws; width changes and rotations
   re-measure.
3. **Measure text, not its box.** Most headings are full-width absolutely
   positioned centring boxes, so their own rect is the frame.
