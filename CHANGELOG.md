# What changed

Newest first. Agents: read this after an update to learn new commands; every feature lands here and in SKILL.md in the
same commit.

## 0.6.0 (2026-11-07)

- Diorama template, sound: `work/probe_motion.mjs` (with `work/probe_hooks.js`) steps through the whole video at 15
  samples a second without drawing and writes `work/audio/motion_events.json`: paper components appearing (slips,
  torn paper, stickies, stamps, term cards, chips, bubbles, marks, plots and their timed points and lines), ribbon pins,
  camera moves and the rung climb into each scene. Things already on screen when a shot arrives get no event. Playwright
  comes from the skill, as in `render_seg.mjs`; 4 browser pages by default, about 5 s for the demo.
- `work/audio.py` turns those events into quiet automatic sounds where the hand-placed SFX table has none (within
  0.22 s of a hand cue: left to it; at most 10 a second; quick runs become soft rising ticks; camera moves of at least
  0.4 s get a whoosh). No events file: nothing changes. New library sounds `wood()` and `bonk()`.
- `work/assemble.py`: after the two-pass loudnorm, a 4x-oversampled limiter at −2 dBFS, so the encoded file stays at or
  under −1 dBTP at −14 LUFS; it prints loudness and true peak. An optional third argument picks another soundtrack.
- `work/srt.py`: cues longer than 42 characters go onto two lines (broken at the space nearest the middle); an empty
  `DIGITS` list of (spoken phrase, digits) pairs, applied to subtitles only, for a project to fill in.

- Diorama template, original music (`references/music-diorama.md`, the brief): `work/measure_voice.py` measures the
  narrator (f0 p5/median/p95, LTAS octave shares and centroid, pauses per minute, words per minute) and derives the
  no-sustain zone, the voice body band and the speech spans → `work/music/voice_profile.json`. `work/make_cuemap.py`
  builds `work/music/cuemap.json` (sections per scene and function, hits, dropouts) from the timeline and the SFX cues,
  with a CONFIG block for asides, dry lines, holds, calls to action, outro, teaser and recap. `work/music.py` composes
  a warm chamber score with the Lemo-Opuscar sampler (CC0 samples): one free-running grid per chapter, written 2-bar
  contoured figures instead of a random walk, composed phrases in pauses of 1.5 s or more, register rules from the
  voice profile, chord plans checked for cross-relations, motifs M1-M3, the brief's lint and checks, per-chapter
  parallel render with 1 s crossfades, section levels set to the energy plan; deterministic (SEED). Writes
  `work/music/score.wav` (exact length, unducked), stems, `credits.txt` and `score_meta.json`.
- `work/audio.py` uses `work/music/score.wav` when it exists (in stereo, normalised to its reference bed, then the
  same ducking as a bed); `bed.*` stays the fallback. With a voice and music it prints voice minus music under
  speech (median, p5, and at 1-4 kHz).

## 0.5.0 (2026-11-06)

- Watercolor story shorts (`references/style-watercolor.md`, `templates/watercolor-story/`): a vertical short that tells a
  small made-up story with characters, then explains (demo: a bakery scale that never shows the same weight twice, and
  why averaging works). gpt-image-2 paints the empty set (from an engine frame, so it lines up) and a paper wash; the
  engine animates rough.js puppets (blinks, mime tracks, reactions, a close-up, a camera keyframe table) painted live by
  an SVG watercolor filter; one narrator voice; captions from the first word. Looks in one line: watercolor, paper
  cut-out, hand-drawn ink. `work/explore_styles.py` repaints a frame in five styles to choose a look.
- The guide records the craft beat by beat, the pitfalls met while building such a short (with fixes) and the review loop.
- Intake asks for the look (3b1b dark, paper diorama, watercolor story); README preview `docs/style_watercolor.jpg`.
- The diorama and vertical-short templates now ship neutral demos on the skill's example topic (averaging noisy
  measurements) with seeded data; every number on screen says where it comes from.

## 0.4.0 (2026-11-06)
Lessons from Lukas Margerie's video "How to Make Insane Motion Graphics With Opus 5.5" and the Movez course it cites,
"How to build motion design studio with Opus 5.5": the request is a small part of the result; most comes from the setup
around it.
- Paper-diorama style (SKILL.md step 11): `templates/diorama/` is an engine, tools and a 45 s demo (averaging noisy
  measurements at a baker's bench): HTML/SVG + rough.js rendered by Playwright, parallel segment render, a free Piper or
  paid OpenAI voice with transcript checks, word-timed cues, synthesized SFX; `references/style-diorama.md` records the
  fixed look, the story method, the commands and the lessons, so the style can be made again without re-deciding it.
- House rules and the critique loop (references/motion.md, linked from SKILL.md steps 5, 8 and 10): banned generic looks
  (centred title on gradient, fade-only entrances, decorative corner labels and borders), hook in 2 s, something new every
  2-4 s, key words readable on a phone, springs, continuity; score the frames 1-10 on seven criteria, fix the 3 worst,
  repeat until all are 8+, log in docs/review_log.md (template in templates/).
- `rx.py sheets <video> [--at t ...]`: contact sheet, phone-size sheet (360 px wide) and 12-frame strips around fast moves.
  `rx.py promo` makes them after every render.
- `rx.py reference <video>`: frames every 0.5 s, contact sheets, cut times and shot lengths, for a style guide that copies
  a reference's grammar and never its content. Intake asks for an optional reference.
- Beat grid: `rx.py beats <track>` measures bpm, beats, downbeats, hits and a drop guess (numpy only; within 7 ms on test
  tracks). `rx.py music` and `"music": {"synth": {...}}` make original music in code (kick, clap, hats, bass, pad, riser,
  impact) with its exact grid: no licence questions. The template now uses it by default.
- Launch pages: springs (`P.sp`, `P.track`, presets snappy/base/heavy/playful), `P.swapAlpha`, `P.rng`, `P.beat`/`P.bar`,
  `P.format`. Sound-effect cues can sit on the grid (`{"downbeat": 2, ...}`). `--format vertical|square` renders the same
  timeline in other shapes; `--sub N` blends sub-frames for motion blur. `Math.random` is re-seeded per frame, so every
  frame is the same in every render.
- Manim: `spring(preset)` rate function and `spring_time(preset)` in base.py.
- Fix: the launch renderer hung when the scaled frame had an odd side (ffmpeg refused it and the pipe never drained); output
  is now scaled to exact even sizes and an ffmpeg failure stops the render with its message.
- voice.md: any other TTS (a web tool, a TTS connector or MCP server, a cloned voice the user owns) goes through `manual`.
- Long tracks: `rx.py music --sections intro:4,build:4,drop:8,...` (and `"sections"` in promo.json) arranges intro, builds with a snare roll, drops, grooves, breaks with their own chords, and lifts with a lead melody; the grid lists the sections and drops.
- Vertical shorts (SKILL.md step 12, `references/shorts.md`, `templates/short/`): a complete 35.5 s example (averaging noisy readings) at 540x960
  (final render 1080x1920) as HyperFrames compositions; PixiJS/p5.js canvases driven by a GSAP timeline; GL Transitions
  between snapshot stills (`work/stills.sh`); gpt-audio-1.5 voice with transcript checks; Parakeet word times merged with
  the script text for captions; CC0 sampled score (Lemo-Opuscar sampler: VSCO 2 CE, VCSL); voice/music premix
  (`work/mix.sh`); lint and contrast checks. `setup.sh` fetches GSAP, p5.js, PixiJS and gl-transitions at exact versions
  (not bundled) and builds `transitions.js` with only the shaders the compositions use.
- Diorama languages: text follows the render language (English left to right with Latin digits, Persian right to left
  with Persian digits); another language means rerunning the experiments, not translating their results.
- Diorama voice tools: `work/pauses.py` (real silences at ⏸ marks), `work/proc_voice.py` stray-tail cut (keeps a tail
  that has words), `work/render_part.sh` for per-part drafts.
- `scripts/explainer/beat.py` (synth + measure, run by `rx.py music` and `rx.py beats`); `templates/review_log.md`
  (critique-loop scores).

## 0.3.0 (2026-11-03)
- Visual storytelling first: SKILL.md and scene-patterns.md plan each beat by what moves; on-screen text is labels.
  Captions are no longer burned in by default (`"captions": "srt"`; `"burn"` brings the strip back). Without burned
  captions, text-only beats last as long as their animation plus `"hold"` (default 0.8 s).
- Motion vocabulary in base.py: `fan`, `gather`, `collapse_to`, `ticker`, `value_axis`, `dot_plot`, `particles`,
  `push_in`/`pull_out`, `spotlight`.
- New demo `examples/how-a-network-sees/`: ResNet-18 (ImageNet weights) on CC0 photos fetched with a licence check;
  pixels, learned filters sweeping, feature maps, prediction, saliency, a 2/255 adversarial change. EN + FA.
- `bar_chart`: bars now start after the longest label (they covered long labels), and in right-to-left rows the value,
  not the name, sits at the bar's end.
- `rx.py promo`: short launch videos (motion graphics in an HTML timeline, captured frame by frame with Playwright, music +
  sound-effect cues, poster baked in). Template in templates/promo/, guide in references/promo.md, CC0 sound effects in
  assets/sfx/. `rx.py check` reports whether the engine is installed.
- Persian text: formulas with Persian digits ("n = ۶۴") stay one left-to-right run inside a Persian sentence.
- `rx.py assemble` printed minutes rounded up (3:52 as "4:52").
- LICENSE is now the plain MIT text, so GitHub detects it as MIT. The scope statement (MIT for this repository's own
  files; bundled skills and fonts under their own licences, manimgl-best-practices non-commercial) moved to
  THIRD_PARTY.md and the READMEs. Plugin manifests list all licences: `MIT AND CC-BY-NC-SA-4.0 AND OFL-1.1`.

## 0.2.0 (2026-11-02)
- Codex and ChatGPT: OpenAI plugin manifest (`.codex-plugin/plugin.json`), marketplace (`.agents/plugins/marketplace.json`),
  skill metadata (`skills/research-explainer/agents/openai.yaml`). `install.sh --codex` copies the skills to `~/.agents/skills`.
- SKILL.md: a mode for surfaces that cannot run commands (ChatGPT web/mobile): plan, ledger, narration and scene code,
  rendering left to a local agent.
- `rx.py status`: a short outline of the project and the next step.
- `rx.py request`: log a missing feature (feature_requests.md); GitHub issue templates for requests and bugs.
- `rx.py selftest`: builds the demo in English and Persian the way an agent would and checks every output.
- Errors now say how to fix them (e.g. "did you mean s02_average?"); common wrong narration field names are accepted with a note.
- `rx.py --help` states what each write command replaces.

## 0.1.0 (2026-11-02)
- First public version: intake, claims ledger, registered assets, Manim library with Persian support, voices
  (none / Piper / manual / OpenAI), build, contact sheets, slides template, demo, Claude Code plugin.
