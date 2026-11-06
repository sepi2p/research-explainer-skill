# Vertical short template (HyperFrames)

A finished 35.5 s, 540×960 vertical short (YouTube Shorts, LinkedIn), kept as a template: "Averaging noisy readings", a
demo on the skill's own example topic (`examples/averaging-noise`). HTML compositions rendered by the HyperFrames CLI
(headless Chrome); PixiJS cards and p5.js particles drawn from GSAP timelines; two GL Transitions (InvertedPageCurl,
InkBleed) between snapshot stills; a gpt-audio-1.5 voice with transcript checks; captions from the script text timed
with Parakeet word times; an original score from CC0 samples (Lemo-Opuscar sampler: VSCO 2 CE, VCSL). The recipe and
the rules are in [references/shorts.md](../../references/shorts.md); read it first.

## What the demo shows

| film time (s) | scene | on screen | voice (`work/script.py`) |
|---|---|---|---|
| 0 – 4.95 | `s1` hook | the question is on screen from frame 0 (it is the thumbnail); a meter steps through the 20 readings; a red circle round "right?" | V1 "Measure the same thing twenty times … Which one is right?" |
| 4.95 – 10.2 | `s2` PixiJS | the meter shrinks into card #20, the other 19 reading cards rain into a 4×5 grid with a counter; the cards shiver on "random noise"; a chip "noise: σ = 0.25" | V2 |
| 9.9 – 10.5 | `t1` | GL Transition InvertedPageCurl between stills of s2 and s3 | |
| 10.2 – 18.35 | `s3` p5.js | the cards burst into ink particles that settle as a dot plot on a number line; the true value 1.00; the dots run together into their average 0.95; brackets: the worst reading misses by 0.58, the average by 0.05 | V3, V4 |
| 18.1 – 18.65 | `t2` | GL Transition InkBleed between stills of s3 and s4 | |
| 18.35 – 30.95 | `s4` DOM/SVG | the error of the average for n = 1, 4, 16, 64: independent noise 0.250 → 0.125 (÷2) → 0.063 (÷4) → 0.031 (÷8) with the curve 0.25 ÷ √n; then shared noise (correlation 0.5): 0.198, 0.182, 0.178, stalled on the floor 0.177 | V5 – V7 |
| 30.95 – 35.5 | `s5` end card | "÷ √n", "Averaging cancels random noise, not shared noise." word by word, an end line (composition variable `endline`) | V8 |

Captions run from 4.85 s to 30.95 s: the hook and the end card already show their words.

**Data.** `assets/data.js` is written by `work/make_data.py`, a seeded numpy simulation (seed 0, no API calls): 20
readings of a quantity whose true value is 1.00, each with independent Gaussian noise of standard deviation 0.25
(rounded to 2 decimals, as a display shows them); and the error (RMSE) of the average of n = 1, 4, 16, 64 readings over
1,000,000 simulated trials, for independent noise and for noise with correlation 0.5 between readings, with the floor
0.25·√0.5 ≈ 0.177. Every number on screen comes from that file (the scenes read `window.DATA`), and the numbers in the
narration were copied from it. The scenes say so on screen (stamps "SIMULATED · SEED 0"). `assets/captions.js` holds the
demo voice's word times. The voice, the music and the mix are not shipped (the voice was a paid OpenAI voice);
`setup.sh` puts a silent placeholder in their place.

**Timings are hard-coded for this 35.5 s script.** A new script must be re-timed by hand: the scene starts and lengths in
`index.html` (s1–s5, t1, t2, captions, mix), the tween times inside each `compositions/*.html`, `OFF`/`END` in
`captions.html`, the word times in `s5.html`, `GAP` in `work/assemble_voice.py`, `SHOW` in `work/make_captions.py`, the
scene starts `S1`…`S5` and the accent times in `work/music.py`, and the still times for `work/stills.sh`. Take them from
`work/lines.json` and `assets/captions.js` (each tween's comment names the word it lands on).

```
index.html               the film: hosts for bg, s1–s5, the transitions t1/t2, captions, and one <audio> (assets/mix.wav)
compositions/            bg (paper, bell curve, ruler), s1 hook (meter), s2 20 readings (PixiJS), s3 average (p5.js),
                         s4 error chart (SVG + DOM), s5 end card, t1/t2 GL transitions, captions
assets/                  data.js (seeded simulation), captions.js (word times), fonts/Caveat.ttf (OFL); setup.sh adds lib/,
                         paper.jpg, placeholder t*_from|to.png and mix.wav
work/make_data.py        seeded simulation -> assets/data.js (numpy)
work/script.py           the lines (one claim per line) and per-line delivery hints
work/voice.py            gpt-audio-1.5 (marin) per line, up to TAKES takes (default 4), gpt-4o-transcribe check >= 0.95
                         (oa.py, en_numbers.py: 0.58, .58 and "zero point five eight" compare equal)
work/assemble_voice.py   tempo (SPEED, pitch kept), trim, cap pauses inside a line at 0.20 s, planned gaps
                         -> assets/voice.wav, work/lines.json
work/check_voice.py      re-transcribe every trimmed line: the cuts must not clip a word
work/make_captions.py    words from the script, times from Parakeet (difflib by position), gaps filled -> assets/captions.js
work/make_paper.py       seeded paper texture -> assets/paper.jpg
work/music.py            CC0 sampled score, accents on the on-screen hits, ducked under the voice -> assets/music.wav
work/mix.sh              voice -16 LUFS + music + limiter -> assets/mix.wav
work/stills.sh           snapshot the frames each GL transition blends -> assets/t1_from.png ... t2_to.png
setup.sh                 browser libraries (exact versions) -> assets/lib/, transitions.js, paper, placeholders
```

## Needs

- node + npm. HyperFrames CLI 0.9.19 through `npx --yes hyperframes@0.9.19` (Apache-2.0); on first use it downloads a
  headless Chrome and the Inter and JetBrains Mono fonts into `~/.cache/hyperframes`. Telemetry off:
  `export DO_NOT_TRACK=1` (or `HYPERFRAMES_NO_TELEMETRY=1`).
- ffmpeg; Python 3 with numpy, soundfile and pillow (`PYTHON=... ./setup.sh` picks the interpreter for the paper);
  scipy and soxr as well for the music.
- Voice (paid): an OpenAI key in `~/.config/openai/key` (chmod 600) or `$OPENAI_API_KEY`, read by `work/oa.py` and never
  printed. Any other voice works too: put one `work/voice/<id>.wav` (48 kHz mono) per line and skip `voice.py`
  (`check_voice.py` also calls the OpenAI transcriber; without a key, listen to every trimmed line instead).
- Word times: NVIDIA Parakeet TDT 0.6B v3 (CC-BY-4.0), installed once by `npx hyperframes models install parakeet`
  (an int8 ONNX copy, about 670 MB, runs locally).
- Music: [Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar) (MIT) with its CC0 sample packs VSCO 2 CE and VCSL:
  `git clone https://github.com/lemomo-ai/lemo-opuscar ~/lemo-opuscar && cd ~/lemo-opuscar && sh tools/fetch.sh instruments vsco2ce && sh tools/fetch.sh instruments vcsl`
  (about 670 MB). Elsewhere: `export LEMO_OPUSCAR=/path/to/lemo-opuscar`.

## Steps

```bash
cp -r <skill>/templates/short <project> && cd <project>
export DO_NOT_TRACK=1; HF="npx --yes hyperframes@0.9.19"
./setup.sh                                  # libraries, transitions.js, paper, placeholder stills and silent mix
work/stills.sh                              # real stills for the two transitions: the demo now renders as is (silent)
$HF preview                                 # look at it in the browser

# the demo's sound (paid voice), or your own short after the changes below
python3 work/make_data.py                   # -> assets/data.js (the demo's file is already there)
TAKES=2 python3 work/voice.py               # voice every line; python3 work/voice.py V3 V7 retakes two lines
python3 work/assemble_voice.py              # -> assets/voice.wav, work/lines.json
python3 work/check_voice.py                 # every line >= 0.95 after the cuts
$HF models install parakeet                 # once
$HF transcribe assets/voice.wav --engine parakeet      # -> assets/transcript.json
python3 work/make_captions.py               # -> assets/captions.js
python3 work/music.py                       # -> assets/music.wav, work/credits.txt (put the credit line in the description)
work/mix.sh                                 # -> assets/mix.wav
TIMES="9.9 10.5 18.1 18.65" work/stills.sh  # start and end of t1 and t2; again after any layout change
$HF lint && $HF check --json                # 14 px type floor at 540 wide, WCAG contrast, layout, craft, audio
$HF snapshot --at 0.05,2.6,5.45,7.6,10.6,12.5,15,17.6,19.6,23,28.8,33 --no-end --keep -o work/snap_r   # every beat; look
$HF render --quality draft -o renders/draft_540x960.mp4
ffmpeg -hide_banner -nostats -i renders/draft_540x960.mp4 -af ebur128=peak=true -f null -   # set data-volume on <audio id="mix">
$HF render --resolution portrait -o renders/final_1080x1920.mp4                           # same files at 1080x1920
```

The demo's own run: lint 0 errors, 0 warnings; `check --json` ok with no findings (before `work/mix.sh` it warns
`audio_clip_silent` about the placeholder mix, as it should); the draft measured -15.0 LUFS at `data-volume="0.79"`.

## Make your own

1. **Numbers first.** Write the script that makes them (a seeded simulation like `work/make_data.py`, or a copy of
   recorded runs) into `assets/data.js`, and stamp each panel with where its numbers come from (SIMULATED, REAL RUN).
   Never type a number into a composition or the narration that is not in that file.
2. **Lines.** One claim per line in `work/script.py`, about 85–100 words for 30–35 s, the hook a real question that is
   on screen at frame 0. Voice, assemble and check them; if the film runs long, cut a line and show it on screen
   instead (this demo turned "the error shrinks with the square root of the count" into the formula chip in s4), ask
   for a brisker delivery in `TONE`, or raise `SPEED` in `assemble_voice.py` a little (1.1 here).
3. **Scenes.** Keep the patterns and swap the content: a PixiJS scene (`s2`: `app.init`, then `draw(t)` from a GSAP
   tween), a p5.js scene (`s3`: `noLoop`, `redraw()` from the tween; particles on seeded paths), DOM/SVG with GSAP
   (`s4`, `s5`), the GL transitions (`t1`, `t2`: only the stills and the transition name change), the captions. Every
   pixel a function of scene time; seeded PRNG; async setup registers `window.__hf.buildReady[key]`; initial hidden
   states with `gsap.set` or `fromTo`, not `tl.set` at 0.
4. **Timing.** Re-time everything in the list above from `lines.json` and `captions.js`, then `stills.sh`, `lint`,
   `check`, snapshots of every beat, a draft render, and frames decoded from the MP4 before delivering.

Third-party licences (GSAP, p5.js, PixiJS, gl-transitions and the two shaders, Caveat, HyperFrames, Parakeet,
Lemo-Opuscar and the sample packs): [THIRD_PARTY.md](../../../../THIRD_PARTY.md).
