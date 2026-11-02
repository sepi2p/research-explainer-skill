# Launch video (rx.py promo)

A short, fast promo (15-25 s) for the work or the video: social posts, a README, a talk opener. It is motion graphics,
not an explainer: kinetic type, real footage, cuts on the beat, music and sound effects.

## How it works
- `promo/index.html` is a page whose every frame is a pure function of time: it defines `window.renderFrame(t)`.
  The runtime (`promo/runtime.js`, injected automatically) gives `P.at` (eased progress), `P.live` (scene visibility),
  `P.typed` (typewriter), `P.shake`, `P.seq` (image sequence into a canvas), and preloads `window.promoAssets`.
  Inter and Vazirmatn are loaded from the skill's fonts; Persian text works with `class="fa"` (dir rtl).
- `rx.py promo promo` captures 1920x1080 CSS pixels at `width`x`height` (default 1280x720), mixes audio, writes
  `promo/promo.mp4` and `promo/promo.jpg` (poster, baked in as frame 0 so thumbnails show it).
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
Cuts land on beats: find the track's beats (`ffmpeg ... astats`, or by ear), set `music.start` so the drop lands on the reveal,
and list the beat times in the page (`B = [...]`).

## Readability
Fast in, then hold: a line stays settled about 0.3 s per word. Pace comes from motion and cuts, never from text leaving early.
Stagger transitions (old out, then new in) or dip through the background; avoid muddy crossfades of two busy layouts.

## Sound
- `promo.json` `sfx`: `{"t": seconds, "file": name or path, "gain_db": -10}`. Bundled CC0 names (assets/sfx): impact_heavy,
  impact, glitch, error, click, key, bong, switch, drop, pop. Keep effects under the music (-8 to -18 dB); typing ticks quiet.
- Music: the user's track. Ask which one; it must be one they may use (their own, CC0 / public domain, or licensed).
  The mix is limited and normalised to -14 LUFS.

## Accuracy
Same rules as the explainer: numbers, outputs and screenshots come from claims.json, assets/ or real runs (copy them into
data.js, don't retype). Status and caveats may be shortened but not dropped when a claim is shown.
