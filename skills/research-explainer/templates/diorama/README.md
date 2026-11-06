# Paper-diorama template

A hand-drawn cut-paper explainer, rendered frame by frame from an HTML/SVG page: rough.js ink lines that "boil" 8
times a second, a puppet animated on twos, parallax paper layers, dust in a light shaft, a camera that glides and zooms
(never cuts), crisp **graph-paper slips that carry only real computed data**, torn paper for illustrations, sticky
notes that get **stamped with their real name** and fly onto a ladder of chapters. The look, the fixed style decisions
and the lessons are in [references/style-diorama.md](../../references/style-diorama.md).

This folder renders as is: a **45-second demo** on averaging noisy measurements, set at a baker's bench.

| Scene | Time | What happens |
|---|---|---|
| `s1_reading` · One reading | 0–10 s | A bag of flour (truly 2 kg) drops onto a wobbly kitchen scale. Pip, the puppet, points at the dial; the needle never settles on 2. The scale prints five real readings (2.28, 1.68, 1.75, 1.87, 2.12) onto graph-paper tickets that fly to a rail; the noise setting σ = 0.25 kg appears on graph paper. |
| `s2_average` · Average | 10–26 s | The scale prints readings 6…64 into a basket; a graph-paper counter shows n and the real running average (2.05 kg at 64) while a saffron pointer settles on the dial. **Frame shot**: the camera zooms through the chart board on the wall until it is the screen; the measured error appears on the spoken numbers (0.249, 0.126, 0.062, 0.031) with the σ/√n curve. Pull-back and **reveal**: the sticky "more readings, smaller error" is stamped NAMED on "standard error" and its card flies to the ladder. |
| `s3_shared` · Shared wobble | 26–38 s | The window swings open; a draught pushes the needle and every hanging ticket the same way. Torn paper: each wobble = its own part + a shared push (correlation 0.5 on graph paper). A graph-paper chart slides in: with the shared part the error stalls (0.198, 0.183, 0.178) at the floor σ·√0.5 = 0.177; the "Average" rung cracks. |
| `s4_takeaway` · Takeaway | 38–45 s | The window shuts; two torn notes: "own wobble: averages away", "shared push: stays". The camera settles on Pip and the two-paper legend; the locked top rung pulses (the next question). |

Every number on graph paper comes from `data/readings.py` (numpy, seed 0, 20,000 sessions per n, no network). The
demo is text-only: the narration is timed by reading speed and shown as captions; add a voice with the steps below.

```
narration.json   the script: scenes -> beats {id, en, fa?, pause?, tone?}; one idea per beat
timeline.json    beat times (from work/timeline.py; also video/timeline.js)
data/            readings.py (the experiment) -> readings.json
video/           the page: index.html, main.js (the video's configuration at the top), engine/core.js,
                 components/{base,chars,set}.js, scenes/s1..s4, data.js + timeline.js (generated),
                 lib/rough.js (roughjs 4.6.6, MIT), fonts/ (JetBrains Mono, Caveat; OFL),
                 render_seg.mjs, render_par.sh (parallel render), stills.sh, stills_scene.sh, debug.mjs, ENGINE.md
work/            make_data.py, timeline.py, srt.py, sheet.py, audio.py (voice + music bed + synthesized SFX),
                 assemble.py (-14 LUFS), render_part.sh (draft of one part), voice_piper.py (free voice),
                 narrate.py + oa.py (paid OpenAI translation and voice), proc_voice.py, wordtimes.py, pauses.py
```

## Quick check

Needs node and the skill's Playwright (`promo/node_modules`; `RX_SKILL` points to the skill if it is not at
`~/.claude/skills/research-explainer`), ffmpeg, and Python 3 with Pillow for contact sheets.

```bash
cp -r templates/diorama ~/dio && cd ~/dio/video
./stills.sh "3,17,24.2,34,42.6" ../work/stills      # five stills + sheet.png, a few seconds
./render_par.sh index.html ../build/demo_480.mp4 $(python3 -c "import json;print(json.load(open('../timeline.json'))['total'])") 8 --width 854 --height 480
```

The full 480p render takes about 20 s with 10 browsers; use `--width 1920 --height 1080` for the final export.

## Make your own

1. **Story.** One idea per beat, 1–2 short sentences; a real failing case first, then the fix built in plain words,
   proved with real numbers, then named (style-diorama.md §4). Write `narration.json` (`en`; add `fa` or another
   language per beat for a translated render).
2. **Real data.** Write `data/<name>.py` (seeded, offline when possible) that saves `data/<name>.json`, then
   `python3 work/make_data.py` → `video/data.js`. Scenes read it with `E.D('<name>.<key>')`; graph paper refuses
   anything else.
3. **Timing.** `python3 work/timeline.py` (text-only: reading time, captions on). With a voice it uses the clips'
   lengths instead (below). `pause` in a beat adds seconds after it for the picture.
4. **World and cast.** Replace `components/set.js` (your set, `E.POS`, props, the frame-shot target) and
   `components/chars.js` (your puppet, ≤ 3 animated characters); keep `base.js`, `core.js`, `main.js`.
5. **Scenes.** One file per scene in `video/scenes/`, registered in `index.html` and in the configuration block at the
   top of `main.js` (scene order, chapter labels, ladder rungs, cracks). The contract, the components and the checks
   are in [video/ENGINE.md](video/ENGINE.md); `s1_reading.js` is the reference scene. Check each scene with
   `./stills_scene.sh <scene> "t1,t2,..."` and look at the sheet.
6. **Sound (optional).** Edit the SFX table in `work/audio.py`, then `python3 work/audio.py` (numpy) →
   `work/audio/mix.wav`. A music bed is your own licensed track at `work/music/bed.wav` (or .mp3/.flac/.m4a).
7. **Render and deliver.** Drafts at 480p first (`work/render_part.sh NAME "s2_average" T0 T1` for one part,
   `render_par.sh` for all), then `python3 work/assemble.py silent.mp4 out.mp4` if there is sound;
   `python3 work/srt.py` writes `work/subs_<lang>.srt`.

## Adding a voice

The page needs no audio: a text-only render is complete. To narrate it:

- **Free, offline (Piper):** `python3 work/voice_piper.py [--lang en] [--voice en_GB-alan-medium]` → `voice/en/`
  (a ⏸ in the text becomes a pause), then `python3 work/proc_voice.py` (trim, −18 LUFS) → `voice/en_proc/`.
- **Your own recordings:** one file per beat, `voice/<lang>/<beat id>.wav`, then `python3 work/proc_voice.py --lang <lang>`.
- **OpenAI (paid):** `python3 work/narrate.py voice --lang <lang>` (every take is transcribed back and checked), then
  `TEMPO=1.06 python3 work/proc_voice.py --lang <lang> --stray`; optional word timing for exact cues:
  `python3 work/wordtimes.py --lang <lang>` and real pauses at ⏸ marks: `python3 work/pauses.py --lang <lang>`.

Then `python3 work/timeline.py --lang <lang>` picks up the clip lengths (and word times) automatically and turns the
captions off (`--captions` keeps them as burned subtitles), re-render, `python3 work/audio.py`, and
`python3 work/assemble.py`. Scene cues follow the new timing by themselves.

## Persian and other right-to-left languages

The engine is bilingual: with `python3 work/timeline.py --lang fa` (beats need a `fa` text), text defaults to
Vazirmatn right-to-left, numbers use Persian digits (`E.num`), component labels switch (`E.L`), and the captions are
Persian. `work/narrate.py translate --to fa` drafts the translation; the skill's Persian number speller
(`scripts/explainer/fa_numbers.py`) is used for voicing and alignment. Scene cues written against the English script
still work (they map by position); the demo's own on-screen words are English, so a Persian video writes its scene
strings in Persian. See ENGINE.md, "Text and language".

## Licences and what is not included

rough.js is MIT (`video/lib/LICENSE_roughjs.txt`); JetBrains Mono and Caveat are OFL (`video/fonts/`); Inter and
Vazirmatn come from the skill's `assets/fonts` (OFL), injected by `render_seg.mjs`. Not included: voice clips, music,
rendered videos and Python environments (re-create them with the scripts above).
