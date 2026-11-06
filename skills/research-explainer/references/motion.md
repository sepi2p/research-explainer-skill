# Motion rules and the critique loop

The request is a small part of a good video; most of it comes from the setup around the model: rules that ban the generic
look, a reference to copy the grammar of, a beat grid, and the habit of looking at your own frames and fixing them. These
rules apply to every explainer and every launch video. (Adapted from Lukas Margerie's video "How to Make Insane Motion
Graphics With Opus 5.5", youtube.com/watch?v=747ZnEtsRbg, and the Movez course it cites, "How to build motion design
studio with Opus 5.5", x.com/0xMovez/status/2104216919033192746.)

## House rules

**Render contract**
- Every frame is a pure function of time. Manim scenes are; keep any randomness seeded (`particles(seed=...)`,
  `np.random.default_rng(seed)`). Launch pages: `window.renderFrame(t)` with no timers, CSS transitions,
  requestAnimationFrame or state carried between frames. The renderer re-seeds `Math.random` per frame, but prefer
  `P.rng(seed)`.

**Look: banned defaults** (the giveaways of generic AI video)
- A centred title on a gradient as a shot; everything fading in; decorative corner labels and frame borders; glow on UI
  chrome; particle bursts that stand for nothing. Our status tag and source line are not decoration: one small, fixed place.
- Things arrive by moving: from where they come from, by morph, wipe, scale or a spring, not by opacity alone.
- One display face, one text face (Inter, Vazirmatn for Persian, a mono for code). One accent colour unless project.json
  "palette" says otherwise; colours keep one meaning for the whole video.

**Pace**
- The hook is in the first 2 s: the most striking real image, number or failure, not a title card.
- Something new happens every 2-4 s. In an explainer, every beat has a transformation; in a launch video, something changes
  on every beat of the grid.

**Motion with mass** (the spring helpers below are in the launch-video engine; in HyperFrames templates use GSAP eases,
and never let a value with meaning overshoot)
- Springs instead of fixed curves: they accelerate, overshoot a hair and settle. Manim:
  `rate_func=spring("snappy"), run_time=spring_time("snappy")`. Pages: `P.sp(t, start, 'snappy')`.
  Presets: snappy (buttons, leading edges), base (cards, camera), heavy (big type, logo lockups: no overshoot),
  playful (stickers, mascots: visible overshoot). Tiny overshoot on UI, none on type.
- A value that changes target several times (a cursor, a width) is a sum of springs, one per change: `P.track(t, keys)`.
- Text inside a morphing container enters after the morph starts and leaves before the next one (`P.swapAlpha`).
- Continuity: when it fits, one element morphs from state to state instead of cutting (a photo becomes pixels, pixels
  become maps; a button becomes a loader becomes a check).

**Real things only**
- Real screenshots, real outputs, real data (the accuracy rules). Never invent UI, results or screens.

**Readable on a phone** (these sizes are for 16:9 landscape; vertical shorts at 540x960 use the sizes in shorts.md)
- The key words of each shot are at least 5 % of the frame height (Manim `T(size >= 30)`; pages >= 54 CSS px on the
  1080-high landscape page). Labels a viewer must read are at least 3.5 % (`T(size >= 22)`, 38 CSS px). Smaller text is
  texture and must not carry meaning. The phone sheet (360 px wide) is the test: if it can't be read there, it is texture.

## Reference: copy the grammar, never the content
A named reference beats a described style. Ask the user for one (their earlier video, a channel they like, a launch film,
a single frame). Then:
1. `rx.py reference <video>`: one frame every 0.5 s, contact sheets, cut times, shot lengths (refs/<name>/).
2. Look at every sheet. Write `docs/style_guide.md`: palette (hex), type (family, weight, tracking), shot lengths,
   transition types, camera moves, texture/grain, how text enters and exits.
3. Write the plan (scenes.md or the launch shot list) in that style. Take its grammar; never its content, logos or characters.
4. Show both to the user before any code.
For a single frame: say what to take (palette, type, grain) and what not to take (the subject). Give the look and the
constraints, not the library; the engines are fixed here (Manim for explainers, the promo engine for launch videos).

## Beat grid (launch videos)
- Music is either the user's track, measured with `rx.py beats <track>` (bpm, beats, downbeats, hits, a drop guess), or
  original music made in code: `"music": {"synth": {"bpm": 120, "drop": 3, "mood": "dark"}}` in promo.json (no licence
  question; `rx.py music` makes one by hand). A synthesized track comes with its exact grid.
- State changes go on beats, big moments on downbeats, sound effects on hits. The page reads `P.beat(n)` and `P.bar(n)`;
  sound-effect cues can be `{"downbeat": 2, "file": "impact_heavy"}` or `{"beat": 9, "offset": -0.02, "file": "pop"}`.
- Before code, write the state list on the grid and show it: one row per beat or half-bar (bar | beat | time | what is on
  screen | sound). Start on a downbeat.
- Explainers: the voice (or reading time) sets the timing; the grid does not apply.

## Gates
plan (scenes.md / shot list on the grid) -> stills of every shot -> animatic (low quality, full length) -> critique ->
full render -> polish -> sound -> final. Fix pacing in the animatic, never in the polish.

## Critique loop (before the user sees anything)
1. Make sheets: `rx.py sheets <video> --at <times of fast moves>` (contact sheet at ~2 frames/s, a phone-size sheet at
   360 px wide, 12-frame strips around each `--at` time). `rx.py promo` makes them automatically; explainers also have the
   per-scene sheets from `rx.py qc`.
2. Open them and look as a harsh motion director, not a proud author. Score 1-10:
   hook (first 2 s) · readability at phone size · motion (springs, no sliding, no dead frames) · variety (new thing every
   2-4 s) · composition · accuracy (every number and screen real, status and caveats present) · sound sync.
3. Write the 3 biggest problems with timestamps in `docs/review_log.md` (template: templates/review_log.md). Hunt for:
   text overlapping during swaps, text too small at phone size, linear slides, corner labels and frame borders, centred
   title on gradient, blurry scaled text, a beat where nothing happens, empty frames between scenes, Persian in the wrong
   direction.
4. Fix, re-render only what changed (`--scenes id`, or the affected seconds), make new sheets, score again. Repeat until
   every score is 8 or more (at least two rounds; after five, stop and tell the user what is still below 8).
5. Fresh eyes help: if you can, give the sheets to a separate reviewer agent for scoring.
6. Report the final scores with the delivery, and what you would improve next.

## Formats (launch videos)
`rx.py promo --format vertical|square` renders the same timeline on a 1080x1920 or 1080x1080 page; the page reads
`P.format` and reflows. Reframe type and footage for each format; never crop a 16:9 render. `--sub 4` (or
`"motion_blur": 4`) blends sub-frames for motion blur on fast moves (4x render time).

## Long productions
For a new film use a high reasoning effort; for small fixes a normal one. When scenes are coded in parallel (subagents),
first write `docs/animation_guide.md` (palette, type sizes, spring presets, motion vocabulary, the banned list, one finished
scene as the example) so every scene is coded in the same style; then one critique pass over the assembled video.
