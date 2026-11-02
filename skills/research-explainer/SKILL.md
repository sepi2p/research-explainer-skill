---
name: research-explainer
description: |
  Make a scientifically accurate, 3Blue1Brown-style explainer video (and optionally a matching slide deck) about research:
  a paper, a collection of papers, or the user's own experiments, project or study. English and/or Persian (Farsi), with a
  choice of no voice (text only), a free voice, the user's own recordings, or a paid OpenAI voice. Can run experiments to
  produce real images, charts and figures. Use when the user asks for an explainer, research video, paper video, video
  abstract, "3b1b style" video of their work, a talk video, or slides from the same material, in English or Persian.
---

# Research explainer

Turns research into a narrated (or text-only) animated video in the 3Blue1Brown style, built with Manim Community Edition,
where every number on screen is traceable to a source and every image comes from real data. The same claims and assets can
become a slide deck.

Bundled companions (install.sh puts them next to this skill): `manim-composer` (scene planning), `manimce-best-practices`
(Manim CE code), `manimgl-best-practices` (only if the user wants ManimGL). Read them when planning and coding scenes.

Everything below happens in a **project folder** (one per video). `scripts/rx.py` runs the pipeline; run it from the
project folder: `python3 <skill>/scripts/rx.py <command>`.

## 0. Setup check (first time only)

Run `rx.py check`. Required: manim, ffmpeg, fonts Inter + Vazirmatn. Optional: LaTeX, piper, OpenAI key, GPU. If something
is missing, show the user the one-line fix it prints; `install.sh` in the repo installs fonts and skills.

## 1. Intake: ask before doing anything

Ask these with your question tool (AskUserQuestion in Claude Code), a few at a time, recommended option first. Full list and
follow-ups: [references/intake.md](references/intake.md).

1. **What is the video about?** (a) one paper, (b) a collection of papers (a survey or a line of work), (c) their own
   experiments / project / study (code, results, notes), (d) a mix. Ask for the files or paths.
2. **Audience and length.** Specialists, researchers in nearby fields, students, or the public; 3, 5-8, 10-15 minutes.
3. **Language.** English, Persian, or both (each language is a full render; Persian text is right-to-left with Persian digits).
4. **Voice.**
   - none: text only, captions paced for reading (about 12 characters/s Persian, 15 English); quiet music; free
   - free: Piper, offline. Good in English; Persian is understandable but robotic
   - own recordings: the user records one clip per beat (or uses a web TTS) from a script we generate; free
   - paid: OpenAI voice (default gpt-audio-1.5, voice marin), billed by OpenAI per use (check their current pricing). Needs an API key
     in `~/.config/openai/key` or `$OPENAI_API_KEY`. **Never ask the user to paste a key into the chat**; tell them where to
     put it and read it only from there.
5. **Experiments.** May we run code to make real figures (their code, or small new experiments)? GPU available? Any run
   longer than about 10 minutes needs their go-ahead.
6. **Outputs.** Video only, video + slides, slides only. Resolution (720p is usually enough).
7. **Status of the work.** Which results are final, which are preliminary or planned; anything unpublished that must not
   appear; anything that must appear (a caveat, a funder, a co-author).

Write the answers into `project.json` (`source_type`, `audience`, `languages`, `voice.mode`, ...).

## 2. Create the project

`rx.py new <dir> --title "<title>" --langs en,fa --voice none|piper|manual|openai`, then copy the sources into
`<dir>/sources/`. Layout:

```
project.json          scenes list, languages, voice, palette, pronunciations
sources/              papers, notes, result files (read-only inputs)
claims.json           the claims ledger: every claim and number, its status and source
experiments/          scripts that make assets (each one deterministic, seeded)
assets/               images and data.json the scenes show; assets/manifest.json says where each came from
scenes.md             the scene plan the user approves
narration_<lang>.json beats per scene: "say" (spoken), "caption" (on screen), optional "text" (shorter, text-only video)
strings_<lang>.json   translations of on-screen labels (Persian)
scenes/*.py           Manim scenes (from explainer.base import *)
build/                everything generated (renders, audio, videos, .srt, contact sheets)
```

## 3. Read the sources and build the claims ledger

Read the sources completely: every page of each paper (including appendix and tables), the user's code, logs and result
files. Then write `claims.json`: one entry per claim the video could make, with `statement`, `values`, `status`
(final / reported / development / in progress / planned / preliminary / illustration), `source` (paper + page/table/figure,
or file + line, or run id) and `caveat`. Rules in [references/accuracy.md](references/accuracy.md). The key ones:

- Report what the source reports, with its own definitions. Don't merge metrics, don't round in a direction that flatters,
  don't drop the denominator ("18 of 20 test items", not "90%").
- Keep the caveats and the cases where the method is not best. Researchers trust a video that shows its limits.
- For a collection of papers, each number is attributed to its paper; never combine numbers measured under different
  settings into one chart without saying so on screen.
- Unclear or contradictory sources: ask the user; never guess a number.

Show the user the ledger (a short table) and get corrections before planning scenes.

## 4. Assets: real data, made by experiments

Every image or chart that shows data comes from a script in `experiments/` that reads the sources (their data, their
model, their logs, or the paper's reported numbers) and writes into `assets/`. Register each file:
`rx.py asset-add assets/x.png --kind measured|reported|illustration|generated --by "<script + args + seed, or citation>"`.
`rx.py assets` verifies the hashes. Details, including when to re-run the user's experiments, GPU use, and how to show
changes too small to see (amplified differences with the gain printed on screen), in [references/experiments.md](references/experiments.md).

Generated images (e.g. OpenAI image models) are allowed only for characters, icons and metaphors, never for data, results
or anything a viewer could mistake for an experimental output; mark them `generated`.

## 5. Plan the scenes (scenes.md) and get approval

Use the `manim-composer` method: hook question, narrative arc, one point per beat, a visual for every point. Our additions
are in [references/scene-patterns.md](references/scene-patterns.md) (status tags, source lines, step tracker, amplified
differences, "where we are not best" scene, closing). For each scene list: purpose, beats (what is said, what is shown),
which claims (ids) and assets it uses. **Show scenes.md to the user and wait for approval before coding.**

## 6. Write narration and scenes

- `narration_<lang>.json`: scenes -> beats. One beat = one or two sentences = one animation step. Numbers in the narration
  must match the ledger (`rx.py claims` fails otherwise). Persian: write natural Persian, not a word-by-word translation;
  see [references/persian.md](references/persian.md).
- `scenes/*.py`: one class per scene, `class S03Chart(Beat): SCENE_ID = "s03_chart"`, then `self.beat(i, fn)` for every beat
  in order. Read numbers with `data()`; never type a measured number into scene code. Use `T()` for all text, `tag()` for
  status, `source_note()` for the source line, `framed()/img()` for real images, `amplified()` for invisible differences.
  The library is `scripts/explainer/base.py`; read it once.
- Register every scene in `project.json` -> `scenes` (`id`, `file`, `class`), in playing order.

## 7. Build

```
rx.py claims                         # every number has a source; fix all ERRORs
rx.py assets                         # every asset registered and unchanged
rx.py render <lang> --quality l      # quick preview render (480p) while coding; then rx.py qc <lang>
rx.py build <lang> --voice <mode>    # final: voice/reading times, render (720p), assemble, contact sheets
rx.py strings fa                     # Persian labels still in English -> add to strings_fa.json, render again
```

Text-only builds do a dry run first to measure each beat's animation, then give each beat the longer of its reading time
and its animation. Voiced builds take beat lengths from the clips. Outputs in `build/`: `<slug>_<lang>_<mode>.mp4`
(full quality), `_share.mp4` (small, for messaging apps), `.srt`. More in [references/pipeline.md](references/pipeline.md);
voices in [references/voice.md](references/voice.md).

## 8. Check before delivering

1. Look at every contact sheet in `build/qc/<lang>_<mode>/` (open the PNGs): overlaps, cut-off text, wrong direction in
   Persian, empty frames, unreadable labels. Fix and re-render the affected scenes only (`--scenes id ...`).
2. Voiced: any clip whose transcript differed from its text is listed by `rx.py durations`; listen or regenerate it
   (`--only scene:i`).
3. Accuracy pass: re-read the narration against the ledger, one claim at a time. If you can, give the narration, the ledger
   and the sources to a separate reviewer agent and ask it to find claims that overstate, drop a caveat, or mislabel status.
4. Report to the user: length, size, languages, voice, what was checked, anything you could not verify.

## 9. Slides (optional)

Same ledger, same assets, same order. See [references/slides.md](references/slides.md): a Slides artifact when the
environment offers one, otherwise `templates/deck.html` (a single HTML file, right-to-left ready, prints to PDF) or a
.pptx via a pptx skill.

## Working style

- Ask when the science is unclear; decide yourself on layout, colours and pacing.
- Preview at low quality, final at 720p; render scenes in parallel (rx.py does) and re-render only what changed.
- Never print secrets. Never publish or upload anything without the user's explicit request.
