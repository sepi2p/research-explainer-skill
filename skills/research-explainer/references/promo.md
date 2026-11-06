# Launch video (rx.py promo)

A short, fast promo (15-25 s) for the work or the video: social posts, a README, a talk opener. It is motion graphics,
not an explainer: kinetic type, real footage, cuts on the beat, music and sound effects.

## How it works
- `promo/index.html` is a page whose every frame is a pure function of time: it defines `window.renderFrame(t)`.
  No timers, CSS transitions, requestAnimationFrame or state kept between frames (the renderer re-seeds `Math.random` per
  frame; use `P.rng(seed)` for noise). The runtime (`promo/runtime.js`, injected automatically) gives:
  - motion: `P.sp(t, start, 'snappy'|'base'|'heavy'|'playful')` (springs), `P.track(t, [[time, value], ...])` (a value
    with several targets), `P.swapAlpha` (text inside a morphing box), `P.at` (eased progress), `P.live` (scene visibility);
  - grid and shape: `P.beat(n)`, `P.bar(n)` (beat times), `P.format` ('landscape' | 'vertical' | 'square');
  - content: `P.typed` (typewriter), `P.shake`, `P.seq` (image sequence into a canvas); `window.promoAssets` is preloaded.
  Inter and Vazirmatn are loaded from the skill's fonts; Persian text works with `class="fa"` (dir rtl).
- `rx.py promo promo` captures 1920x1080 CSS pixels at `width`x`height` (default 1280x720), mixes audio, writes
  `promo/promo.mp4` and `promo/promo.jpg` (poster, baked in as frame 0 so thumbnails show it), and review sheets in
  `promo/work/sheets*/` (add `"check_at": [times of fast moves]` for strips). `--format vertical|square` renders the same
  timeline on a 1080x1920 / 1080x1080 page (outputs `promo_vertical.mp4` ...): lay the page out from `P.format`, don't
  crop. `--sub 4` or `"motion_blur": 4` blends sub-frames (motion blur, 4x the render time).
- Two languages from one page: read `?lang=` in the page (`new URLSearchParams(location.search).get('lang')`), keep the
  strings in a per-language table, mirror positions for Persian, and run `rx.py promo promo --lang en` and `--lang fa`
  (outputs `promo_en.mp4`, `promo_fa.mp4`).
- Footage from the explainer: cut 2-3 s clips from `build/<slug>_<lang>_<mode>.mp4` into frame folders
  (`ffmpeg -ss <t> -t 2.4 -i ... -vf fps=15 media/<lang>/<clip>/f%03d.jpg`) and play them with `P.seq(canvas, frames, t, start, 15)`.
- `rx.py promo promo --stills 1.5,7.2,20` writes stills to `promo/work/stills/`: look at every scene and at mid-transition
  frames before the full render.

## Shape
Hook (0-3 s, the claim in big type) -> drop/reveal (name + one line) -> 2-3 highlights, each one real thing
(footage, the claims check catching a number, Persian rendering) -> install line -> end card (repo, star, author sign-off).
Cuts land on beats. Before code, write the state list on the beat grid (bar | beat | time | on screen | sound) and show it.
The grid comes from the music: `"music": {"synth": {...}}` brings its own; for a supplied track run `rx.py beats <track>`
and set `"beats": "<track>.beats.json"` (times are shifted by `music.start` for you). Use `P.beat(n)` / `P.bar(n)` in the
page instead of typed times.

## Readability
Fast in, then hold: a line stays settled about 0.3 s per word. Pace comes from motion and cuts, never from text leaving early.
Stagger transitions (old out, then new in) or dip through the background; avoid muddy crossfades of two busy layouts.

## Sound
- `promo.json` `sfx`: `{"t": seconds, "file": name or path, "gain_db": -10}`. Bundled CC0 names (assets/sfx): impact_heavy,
  impact, glitch, error, click, key, bong, switch, drop, pop. Keep effects under the music (-8 to -18 dB); typing ticks quiet.
- Cues on the grid: `{"downbeat": 2, "file": "impact_heavy"}`, `{"beat": 9, "offset": -0.02, "file": "pop"}`,
  `{"hit": 3, ...}`, or plain `{"t": 4.2, ...}`.
- Music, two choices:
  - original, synthesized in code: `"music": {"synth": {"bpm": 120, "drop": 3, "offset": 0, "mood": "dark" | "bright", "seed": 7}}`
    (`offset`: seconds before the first downbeat; `drop` counts from there and snaps to a bar).
    Kick, clap, hats, bass, pad, a riser into the drop and an impact on it, all on one exact grid. No licence question, so
    it can ship anywhere. (`rx.py music out.wav --duration 23` makes one by hand.)
    A long ad (over ~40 s) needs an arrangement, not one loop: `"sections": "intro:4,build:4,drop:8,groove:8,break:6,build:2,lift:8"`
    (bars). Kinds: intro (pad), build (swelling kick, snare roll, riser, half a beat of silence before the next drop), drop,
    groove (lighter, room for footage), break (no drums, other chords: the quiet, tense part), lift (drop + lead melody),
    outro (added at the end). The grid gets `sections` and `drops`: put section changes on them, the biggest reveals on drops,
    explanations on grooves and breaks.
  - the user's track: it must be one they may use (their own, CC0 / public domain, or licensed); `"file"`, `"start"`.
  The mix is limited and normalised to -14 LUFS.

## Accuracy
Same rules as the explainer: numbers, outputs and screenshots come from claims.json, assets/ or real runs (copy them into
data.js, don't retype). Status and caveats may be shortened but not dropped when a claim is shown.
