# Engine guide: the paper-diorama page

The video is an HTML page whose every frame is a pure function of time: `renderFrame(t)` builds one SVG string, and a
headless browser captures it frame by frame. Each scene is one file in `scenes/`. A scene writer writes **one scene
file only**; this guide is everything they need. The demo (averaging noisy readings, 4 scenes, ~45 s) is the worked
example: read `scenes/s1_reading.js` first.

## Files

| File | What it holds |
|---|---|
| `engine/core.js` | maths, springs, text (`E.text`, `E.html`, `E.num`, Persian helpers), SVG helpers, the hand-drawn shape helper `E.R`, timeline (`E.B`, `E.cue`), data (`E.D`), palette `E.C`, language (`E.LANG`, `E.RTL`, `E.L`) |
| `components/base.js` | Slip and Plot (graph paper: real data), Torn, Sticky, Stamp, TermCard, Chip, Bubble, FrameBorder, Check, Cross, Ladder, Ribbon, **Reveal** (the naming template), Legend, Caption |
| `components/chars.js` | the puppet **Pip** (`E.comp.Pip`); poses and expressions are listed at the top |
| `components/set.js` | the world: `E.comp.Bench` (the baker's bench), fixed positions `E.POS`, props (scale, window, clock, rail, ticket, board, draught), the demo chart `E.chartPlot`, **frame shots** (`E.frameShot`, `E.frameInside`, `E.frameGlow`) |
| `main.js` | frame composer: camera, the rung-climb transition, ladder HUD, ribbon, chapter labels, captions, grain. **Its top block is the video's configuration** (scene order, chapter labels, rungs, cracks) |
| `scenes/s1_reading.js` | **the reference scene**: read it fully before writing yours, and copy its patterns |
| `../narration.json` | the script: scenes → beats `{id, en, fa?, pause?}`; one idea per beat |
| `timeline.js` (+ `../timeline.json`) | every beat's start, end and spoken text (from `work/timeline.py`) |
| `data.js` | `window.DATA`, every number graph paper may show (from `work/make_data.py`; keys below) |

Do **not** edit the shared files (core, base, chars, set, main, index.html, data.js, timeline.js) while several people
or agents write scenes in parallel. If you need a helper, define it inside your scene file under
`E.props.<sceneid>_<name>`. If a shared component has a bug or lacks something, work around it locally and report it.

## The scene contract

```js
(() => {
  const { C } = E, P = E.POS;
  // times come from the narration, never typed: E.B('W1').start, E.cue('W2', 'quarter', -0.2), ...
  E.scenes.s1_reading = t => ({
    cam: { x, y, z },      // world point at the screen centre, zoom (z = 1: one world px = one screen px)
    world: '...',          // SVG in world coordinates (drawn under the camera); usually E.comp.Bench(t, cam, {...})
    screen: '...',         // SVG in screen coordinates 854 x 480 (over the camera; readable text and data)
    frame: { k, chip },    // only in frame shots: the saffron frame border (k = visibility 0..1)
    hud: { ladder: 1 },    // optional: ladder visibility; caption: 0 hides the caption; ribbon: 0 hides the ribbon
  });
})();
```

- Register the file in `index.html` and its id in `main.js` (`ORDER`, `CHAPTER`, `RUNG_OF`).
- A scene is active from `E.sceneStart(id)` (= its first beat's start − 1.0 s) to `E.sceneEnd(id)`. During the first
  and last 0.45 s, `main.js` slides the old and new scenes vertically (the "rung climb"), so the first and last frames
  must already look complete. The chapter label is drawn by main.js.
- `t` is the global video time. Use beat times: `E.B(id).start/.end/.dur`, `E.cue(id, 'substring', offset)` (when the
  narration reaches that substring: the real spoken time when the voice was word-aligned, else estimated by character
  position, ±0.3 s), `E.cueEnd`. A cue can be `{en: 'two kilos', fa: '...'}`; an English substring also works in a
  translated render (it maps by its position in the English source, ±0.5 s).
- Viewers see 854 × 480. **Visual change at least every 2–3 s**, and something always moves: the set has dust in the
  light shaft, a ticking clock and line boil; the puppet breathes and blinks; add your own (springs, camera moves with
  `E.etrack`).

## Coordinates and camera (the demo's world)

- World coordinates are fixed in `E.POS` (set.js): bench top y 330; the scale at (760, 330) with its ticket slot
  `E.SLOT()`; Pip at (575, 342); the ticket rail x 830–1090 at y 196 (`E.railXY(i)` = hanging point of ticket i);
  the window centred (1250, 160); the clock (960, 74); the chart board (1480, 205), 192 × 108 (16:9, the frame-shot
  target `E.POS.frame`); the two-paper legend (330, 214).
- `cam.z` guide: 0.74 is a wide shot of the bench; 1.2–1.3 the scale with Pip and the rail; 1.6 a close-up;
  `E.FRAME_Z()` (= 854 / 192 ≈ 4.45) means the board fills the screen.
- Text drawn in world coordinates shrinks with the zoom. **Readable text and data must end up at least the minimum
  size on screen** (world size × z). When the camera is wide, put text and data in `screen` instead.
- Camera motion: `E.etrack(t, [[t0, v0], [t1, v1, dur], ...])` for eased moves, `E.track` for springs. Keep moves
  0.6–1.6 s long (slow push-ins may be longer), with no hard cuts.
- **Frame shots**: `E.frameShot(t, fromCam, tIn, tOut, toCam, dIn, dOut)` returns `{cam, k}`: the camera zooms
  through the frame until its edges are the screen edges; draw the frame's content full size with
  `E.frameInside(t, k, innerSvg)` and return `frame: { k }`. Inside a frame there is only what the frame holds: the
  HUD hides itself. `E.frameGlow(t, k)` outlines the frame while zooming. The board draws the same chart scaled down
  (`E.props.board` takes 854 × 480 content), so the zoom cross-fades without a jump.

## Visual rules (the style)

- **Two-paper contract:**
  - Graph-paper `E.comp.Slip` and `E.comp.Plot` are ONLY for real data. A Slip takes a data **key**
    (`key: 'readings.sigma'`) and an optional `fmt(value)` that returns HTML; a Plot takes keys for its x values,
    traces, guide curves and levels. Never pass literal data text.
  - Torn paper (`E.comp.Torn`) is for metaphors, schematic drawings and anything invented (no measured numbers).
  - Sticky notes are the viewer's idea in plain words (≤ 6 words), used by the reveal.
- **Palette:** use `E.C` tokens only. Meanings in the demo: saffron = the puppet, the frame, the current rung;
  teal = independent readings; steel = the shared (correlated) part; pistachio = success / the true value;
  **pomegranate = wrong or error only** (never decoration); brick = stamps and names; schematic grey = theory and
  illustrations. Pick meanings for your video and keep them.
- **Text and language** (`E.LANG` comes from the timeline: `work/timeline.py --lang`):
  - `E.text(x, y, s, {size, weight, anchor})` and wrapped `E.html(x, y, w, h, html, {size})` default to the render
    language: Inter, left-to-right for English; Vazirmatn, right-to-left for Persian (`'fa'`).
  - Mixed text: `E.lat('RMSE')` isolates a Latin term inside Persian HTML, `E.rtlSpan(...)` Persian inside English,
    `E.mono(...)` for code and ids (JetBrains Mono, no ligatures). Pass `dir: 'ltr'` for an English label in a
    Persian render.
  - Numbers: `E.num(v, dec)` (Persian digits in a Persian render), `E.fa`, `E.faNum` (always Persian digits).
  - Component labels (the slip stamp, the naming stamp, the legend) come from `E.L`, per language (core.js `E.LABELS`).
  - The demo's own on-screen words are English; a Persian video writes its scene strings in Persian.
- **Minimum on-screen sizes:**
  - body text: 18 px (Persian) / 16 px (English);
  - slips and chart values: 15 px (tick labels 14 px);
  - footers, citations and HUD labels: 11–12 px.
  - A slip shows **at most 12 words**. For longer real text, show an excerpt ending in "…".
  - A wrapped html box hides its overflow, so **check that no text is cut**. Height needed ≈ lines × size × 1.45 +
    padding; a slip also needs 16 px for its footer and 4 px for its stamp.
  - In a text-only render the caption bar covers y ≈ 420–470: keep important content above it.
- **Naming reveal:** `E.comp.Reveal(t, {t0, tStamp, sticky: {x, y, text, w, h}, card: {title, sub, cite, year},
  cardXY, flyTo, tFly, stampLabel})`.
  - `tStamp` must be the cue of the **name word** (`E.cue('A3', 'standard')`); the sticky appears about 2.5 s before.
  - The card flies to its rung (about `[836, rungY]`; with 4 rungs, rung i is at y = 356 − 60·i) if `flyTo` is given.
  - `year` is optional; with a year, also register a ribbon pin at `tStamp`:
    `E.PINS.push({ year, label, t0: tStamp })` (the ribbon only appears when pins exist).
  - Chips (`E.comp.Chip`) are quick names or settings with no stamp. ≤ 7 full reveals per video.
- **The puppet:** `E.comp.Pip(t, {x, y, s, poseKeys: [[t, 'rest'], ...], exprKeys: [[t, 'happy'], ...], look: [dx, dy], talk: [[t0, t1]], hop, prop})`.
  - Poses: rest, pointL, pointR, pointUp, think, cheer, shrug, hold, write, wave.
  - Expressions: neutral, happy, focused, puzzled, surprised.
  - Animated on twos (12 fps). No walking and no hand contact: objects move on their own (tickets fly from the slot).
  - Draw Pip through `E.comp.Bench(t, cam, { puppet: svg })` so the bench front hides the lower body.
- **The set:** `E.comp.Bench(t, cam, {scale: {value, avg, avgK, bag, bagY, trueMark, lean, slotGlow}, window: {open,
  wind}, draught, board, boardShared, extraWall, puppet, extraL2})`. Parallax layers: wall 0.3, shelf 0.6, bench 1.0,
  foreground 1.3.
- **Hand-drawn shapes:** `E.R(type, args, opts, id, t)`, where type is one of rectangle, circle, ellipse, line,
  linearPath, polygon, path, arc, curve (rough.js: circle takes a diameter).
  - Draw in fixed local coordinates and move the result with `E.g(E.tf(x, y, s, rot), inner)`, so the cache hits and
    the boil stays stable.
  - **Data is never boiled:** use plain `E.rect`, `E.path`, `E.line`, `E.text` for charts, tables, dials and numbers.

## Data keys (window.DATA, from data.js)

`data/readings.py` (numpy, seed 0, no network) writes `data/readings.json`; `work/make_data.py` turns every
`data/*.json` into `DATA.<file stem>`.

| Key | Contents |
|---|---|
| `readings.true` | 2.0: the bag's true weight (kg) |
| `readings.sigma` | 0.25: noise standard deviation of one reading (kg) |
| `readings.rho` | 0.5: correlation between two readings of a session in the shared-wobble case |
| `readings.ns` | [1, 4, 16, 64]: readings averaged |
| `readings.sessions`, `readings.seed` | 20000 sessions per n; seed 0 |
| `readings.independent` | measured RMSE of the average, independent noise: [0.249, 0.1256, 0.0624, 0.0313] |
| `readings.theory` | σ/√n: [0.25, 0.125, 0.0625, 0.0312] |
| `readings.shared` | measured RMSE with correlation 0.5: [0.2513, 0.1977, 0.1827, 0.1776] |
| `readings.shared_theory` | σ·√(ρ + (1 − ρ)/n): [0.25, 0.1976, 0.1822, 0.1782] |
| `readings.shared_floor` | σ·√ρ = 0.1768: the error averaging cannot remove |
| `readings.session.readings` | one example session: 64 readings (kg, 2 decimals): 2.28, 1.68, 1.75, 1.87, 2.12, … |
| `readings.session.running_mean` | the running average of that session (64 values) |
| `readings.session.mean64` | 2.05: the average of its 64 readings |

## How to check your work (required)

```bash
cd <project>/video
./stills_scene.sh <your scene stem> "t1,t2,t3,..." ../work/stills/<your scene stem>   # stills (854x480) + sheet.png
PAGE=.preview/<your scene stem>.html node debug.mjs t1 t2 ...                      # JS errors with stack traces
./stills.sh "t1,t2,..." ../work/stills/all                                         # the whole page (seams too)
```

`stills_scene.sh` builds a private preview page that loads the shared engine and only your scene file, so other
scene files that are half-written cannot break your preview (other scenes show as "missing scene"), and writes the
contact sheet `sheet.png`. Then **look at the sheet** (and at single stills when you need detail). Take stills at
every beat's start, middle and end, at every reveal, and at both scene edges.

Score your scene 1–10 on each criterion:
1. clarity of the idea in every frame;
2. readability at 480p (nothing cut, overlapping or too small);
3. motion: something meaningful changes every 2–3 s;
4. composition and balance (nothing under the ladder labels or the caption bar);
5. accuracy: real data only on graph paper, numbers match DATA and the narration;
6. text direction and digits correct for the render language;
7. consistency with `s1_reading.js`'s look.

Fix the three worst and repeat until every score is 8 or more. A still renders in well under a second.
