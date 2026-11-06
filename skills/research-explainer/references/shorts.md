# Vertical shorts (YouTube Shorts, LinkedIn) with HyperFrames, PixiJS, p5.js, GL Transitions and Lemo-Opuscar

A complete, runnable example: [`templates/short/`](../templates/short/) ("Averaging noisy readings", 35.5 s, 540x960, on
the skill's example topic `examples/averaging-noise`; its README lists every file and command). Start with `./setup.sh` there: it fetches the browser
libraries at exact versions (not bundled), builds `assets/lib/transitions.js`, and writes placeholder stills and a silent
mix so the page loads at once. Tools: the HyperFrames CLI (`npx --yes hyperframes@0.9.19`, telemetry off with
`DO_NOT_TRACK=1`); optional agent helpers: the HyperFrames and pixijs-skills plugins, the `algorithmic-art` (p5.js) and
`gl-transitions` skills; for the score, the Lemo-Opuscar library (github.com/lemomo-ai/lemo-opuscar, `LEMO_OPUSCAR`) with
its CC0 sample packs VSCO 2 CE and VCSL.

## Pipeline
1. **Script**: one claim per line, ~100 words for 40 s, every number from a recorded run or a seeded script (graph paper +
   a stamp that says which: REAL RUN, SIMULATED · SEED 0). Open on a real question already on screen at frame 0 (it is
   the thumbnail). Give context first (what is measured, what is made up).
2. **Voice**: `work/voice.py` (gpt-audio-1.5 marin, brisk prompt, gpt-4o-transcribe check >= 0.95, retake on misheard
   terms, e.g. an acronym read as a word). `work/assemble_voice.py` trims each line, caps pauses inside a line at 0.20 s
   (viewers drop off in pauses that are not there for impact: cap them), joins lines with planned gaps ->
   `assets/voice.wav`, `lines.json`.
   `work/check_voice.py` re-transcribes every trimmed line: the cuts must not clip a word.
3. **Word times**: `npx hyperframes transcribe assets/voice.wav --engine parakeet` (local; once:
   `npx hyperframes models install parakeet`). Parakeet skips words now and then: `work/make_captions.py` takes the
   words from the script, times from Parakeet (difflib by position), fills gaps.
4. **Composition**: design at **540x960** (draft = native size; final export of the same files: `render --resolution
   portrait`, DPR 2, canvases use `devicePixelRatio`). Safe band for text: y 84-665; captions at y ~600; below 665 only
   decoration (the app draws its UI there). Hide captions where the screen already shows the words (hook, end card).
5. **Canvas libraries** (PixiJS cards, p5.js particles): drive drawing from a GSAP tween in the scene timeline
   (`tl.fromTo(st,{t:0},{t:DUR,duration:DUR,ease:"none",onUpdate:()=>draw(st.t)},0)`); every pixel a function of t,
   seeded PRNG; async setup (Pixi `app.init`, p5 setup, fonts) registers `window.__hf.buildReady[key]`.
6. **GL Transitions**: snapshot the two scene frames (`npx hyperframes snapshot --at a,b --no-end --keep`) with the
   captions host and the transition hosts set `data-hidden` (`work/stills.sh` does this and restores `index.html`);
   draw the GLSL (from `gl-transitions.json`, all params at their defaults) on a WebGL canvas between the two stills
   (`templates/short/compositions/t1.html`). `setup.sh` copies only the transitions the compositions name
   (`window.GLT["Name"]`) into `transitions.js`, with author and licence. Placeholder PNGs are needed for the first
   snapshot (a hidden host still runs its setup; `setup.sh` writes them). Re-snapshot after any layout change.
7. **Music**: `work/music.py` with Lemo's `core/audio/sampler.py` (VSCO 2 CE + VCSL, CC0; `credits()` for the lines):
   a bed on one tempo grid + accents at the exact on-screen hits (each card = one rising note), bed ducked under the
   voice, light room. Measured, not heard: say so. Loudness (`work/mix.sh`): voice loudnorm -16 LUFS, music ~12 dB
   under, premix through `alimiter` (TP -1.9); the HyperFrames render came out ~3 dB louder than the WAV: measure the MP4
   (`ebur128`) and set `data-volume` (0.79 gave -15.0 LUFS).
8. **Checks**: `npx hyperframes lint`, `check --json` (sizes at 540 wide: key words 23-30 px and more, data labels at
   least 14 px, the check's floor; WCAG contrast: brick #9C4130 and
   teal #1D6B62 for small text on paper), snapshots of every beat, then frames decoded from the rendered MP4.
9. **Render**: draft at native size (`render --quality draft`), final from the same files with `render --resolution
   portrait` (1080x1920). The example's timings are hard-coded for its 35.5 s script; a new script means re-timing
   `index.html`, the compositions, the captions window and the music accents (list in the template README).


## Story shorts in watercolor

For a short that tells a story with characters (painted set, animated painted puppets, one narrator, made-up data
labelled as a dramatization), read [style-watercolor.md](style-watercolor.md) and start from `templates/watercolor-story/`.
