# Paper-diorama style

Use this when the user asks for the paper-diorama / cut-paper / doodle-diorama style, or for "the same style as" a video
made with it. Start from [`templates/diorama/`](../templates/diorama/): the engine, the tools and a 45 s demo
(averaging noisy measurements at a baker's bench) that renders as is. Its `README.md` lists every file and command; the
engine guide for whoever writes scenes is `templates/diorama/video/ENGINE.md`. The style decisions below are fixed: do
not re-run research or pitch rounds to choose a look again.

This style is **not Manim**: it is an HTML/SVG page where every frame is a pure function of time, captured by headless
Chromium (Playwright, from the skill's `promo/node_modules`). Fonts and the Persian number speller
(`scripts/explainer/fa_numbers.py`) come from the rest of the skill.

## 1. The look in one paragraph

A warm, hand-drawn **cut-paper diorama** on cream paper, with parallax paper layers, gently boiling ink lines (rough.js,
re-seeded 8 times a second), dust in a light shaft, a puppet animated on twos, and crisp **graph-paper slips that carry
only real data** (recorded runs or seeded computations). The camera never cuts: it glides, zooms through a frame in the
set until the frame is the screen (a **frame shot**), and climbs a ladder between chapters. Every idea is built in plain
words on a yellow sticky note first, then **stamped with its real name**, turned into a term card and flown onto the
ladder.

## 2. Fixed decisions (copy, don't re-decide)

| Thing | Value |
|---|---|
| Canvas | logical 854 × 480 (SVG viewBox), 30 fps; render 854×480 for drafts, 1920×1080 for the final |
| Engine | `renderFrame(t)` builds one SVG string; no state between frames except pure memo caches; `Math.random` re-seeded per frame |
| Hand-drawn lines | rough.js 4.6.6 (MIT), roughness 1.1, bowing 0.8, stroke 2 px, `curveFitting` 0.95; **boil**: seed = hash(objectId) ^ floor(t·8) |
| Data | **never boiled**: plain rects, paths and text for slips, charts, scores and map points |
| Palette (`E.C`) | paper `#F3E9D2`, paperShade `#E6D7B8`, ink `#1F2A44`, brick `#B5533C`, saffron `#E9A23B`, teal `#2A9D8F`, steel `#4F6FA8`, pistachio `#7FA650`, pomegranate `#C8372D`, night `#16213A`, graph `#FBFAF6` + grid `#C9D6E3`, sticky `#F6D365`, schematic `#8A8F98`, wood `#A87C52`/`#7A5434`, cream `#FBF3E2` |
| Colour meaning | saffron = the focus (the frame, the current rung, the main pointer); teal = the method that helps; steel = stored data; pistachio = success; **pomegranate = wrong/error only** (never decoration, never to circle a correct fact) |
| Fonts | English **Inter** 500/600; Persian **Vazirmatn** 400/700 (the skill bundles Regular and Bold; `render_seg.mjs` maps 900 to Bold); code, ids, numbers on slips **JetBrains Mono** (ligatures off); **Caveat** for hand notes |
| Minimum sizes (at 854×480) | body 18 px, slip text 15 px, citations/footers 12 px; a slip shows ≤ 12 words |
| Languages | text follows the render language (`E.LANG`, `E.RTL`, `E.num`, label table `E.L`); Persian is right-to-left with Persian digits everywhere except code, ids and citations |
| Texture | static grain tile at 7 % multiply; warm radial vignette; flat offset shadows (3 px, 22 %) |
| Always-alive motion | line boil 8 fps; dust motes; puppet breathing and blinks every 2.5–5 s; camera micro-drift ±4 px / ±3 px at 0.05 Hz; map points breathe ±6 % |
| Rhythm | something meaningful changes on every narration clause (at least every 2–3 s); a bigger change each chapter |
| Characters | ≤ 3 animated; on twos (12 fps) with seeded ±0.5° jitter; camera and data at 30 fps; no walking, no hand contact: objects move by themselves (fly along threads, slide through slots) |
| Easing | objects: spring k 170, d 18 (`E.SPR.obj`); snap 400/34; heavy 120/24; camera: cubic in-out 0.6–1.6 s; UI cards 0.3–0.5 s |
| Transitions | no hard cuts. Between chapters the "rung climb": the old scene slides down while the new one arrives from above (0.45 s each side), the chapter label slides in for ~2.2 s |
| HUD | ladder at screen right (current rung saffron, finished ink, locked grey with a padlock; a rung cracks when its question breaks it); hidden inside frame shots |
| Sound | optional: synthesized SFX on word cues (`work/audio.py`), a music bed the user owns, ducked under the voice; mix −14 LUFS / −1.5 dBTP |

## 3. Signature devices (these make it "this style")

1. **Frame shot.** The camera zooms through a frame in the set (a chart board, a window, a screen) until its edges match
   the screen; inside is only real data, no HUD. Leaving is the reverse zoom.
2. **Two-paper contract.** Graph paper (the `Slip`/`Plot` components: crisp, a stamp, a mono footer with the source:
   model and date, or script and seed) takes **only a data key** from `window.DATA`, never literal text. Torn cream paper
   (boils) is for metaphors and schematics. A legend in the set says which is which ("made-up world · real numbers").
3. **Naming reveal** (≤ 7 per video): a sticky note slaps up with the plain-words idea (≤ 6 words); on the spoken name
   (a word-timed cue) a stamp slams (scale 1.3 → 1, 2 px shake); the note flips into a term card (term, citation line,
   year) and flies to the current rung. Quick names use a chip without a stamp.
4. **The ladder.** Each chapter is a rung: problem → idea → name → the next question cracks the rung. The top rung can be
   locked (the next video).
5. **Logical vs historical order** (optional): a term wall lays the cards out in the order the viewer invented them, with
   a line to their real years; label the axes and say what the zig-zag means.
6. **A teaser where the problem changes kind**, then a short end screen.
7. **Running gags** give the puppet a personality (a gauge always at maximum, a stopped watch): one or two, reused.

**Cast.** One full puppet with a set of poses and expressions (the demo's Pip: 10 poses, 5 expressions); other roles are
objects with a single behaviour (a book that riffles, a compass that measures). The viewer is the sticky notes.

## 4. Story method

- **Hook in the first 10 s** with a real, surprising case shown more than once (a measurement that never repeats, a
  confident wrong answer repeated 20 of 20 times). The payoff line is the title.
- **Problem → solution ladder.** Every rung starts from a real failing case, builds the fix in plain words, proves it
  with real numbers, then names it ("…and that is called X"). Name ideas after the viewer understands them.
- **Made-up world, real numbers.** The world and its documents are invented and labelled as such; every number on graph
  paper comes from a recorded run or a seeded script (source in the footer). Record the numbers before locking the
  narration, and let real surprises change the script.
- **Depth check per concept.** For every major idea, show on screen: a concrete failing case, why the obvious fix is not
  enough, the mechanism drawn, a case where the fix works, and its limit or cost. A grid or map gets a real example in
  every cell; never hold empty boxes for more than ~3 s.
- **Script rules** (apply to every script before voicing):
  1. Define every code, name or term before using it, or use a general word.
  2. Show a newcomer's strengths before its weaknesses.
  3. Establish a premise on screen before explaining it.
  4. Analogies get a pause and an explicit bridge ("…the same happens to meaning").
  5. Explain mechanisms scientifically (numbers, what goes in, what comes out), not poetically.
  6. Say what each metaphor object stands for the first time it appears.
  7. Each chapter gets an intro and each trick its own problem.
  8. Recap and teaser chapters need substance, not one line each.
  9. Concrete wording: "the next video", not "part 2"; plain words for jargon unless defined.
  10. An aside needs an audible break (the music stops under it).
  11. Fix pronunciation in the script itself (diacritics on ambiguous Persian words; spelled-out numbers).
  A script that follows these rules grows; ask the user whether a long version stays one video or becomes two.
- **Caps**: ≤ 7 full reveals, ≤ 3 animated characters, ≤ 12 words per slip, one idea per beat.
- Accuracy rules as in [accuracy.md](accuracy.md); keep a citations table when the video names papers or years.

## 5. Production

Commands, files and the scene contract are in `templates/diorama/README.md` and `video/ENGINE.md`. In order: story
(`narration.json`, one idea per beat) → real data (`data/<name>.py` → `work/make_data.py` → `video/data.js`) → timing
(`work/timeline.py`; text-only by reading time, or from voice clips) → world and cast (`components/set.js`,
`components/chars.js`) → scenes (`video/scenes/*.js`, registered in `index.html` and the configuration block of
`main.js`) → stills per scene (`stills_scene.sh`) → drafts (480p, `render_part.sh` per part, `render_par.sh` for all) →
sound (optional) → final 1080p only after the user approves the draft.

**Review loop.** Per scene, score 1–10 on the motion house rules (references/motion.md) and fix the three worst until all
are ≥ 8. For the whole video, contact sheets every second (`work/sheet.py`): overlaps, cut-off labels, empty frames,
text under the captions, slips on screen too briefly to read. One accuracy pass: narration vs data vs citations.

## 6. Lessons (pitfalls)

- **The voice model answers instead of reading.** Wrap the text: "Read this narration script aloud, exactly as written…",
  and check every take by transcription.
- **Transcript similarity** must ignore spelling differences of terms and numbers (compare spoken forms).
- **Repeated sentences slip past a similarity check**: look at the word-time tail of every clip.
- **Stray sound after the script**: the voice model can add a short burst after the last word; `proc_voice.py --stray`
  cuts a tail after a pause unless it contains words (keep a one-word ending).
- **ffmpeg can deadlock** on `loudnorm` right after a reversed `silenceremove` with nothing between them: add a filter
  (e.g. `atempo=1.0`) between them.
- **Check counts against the data**, not against an intermediate (a search pool is not the number of documents).
- **Scenes in parallel**: one agent per scene file works when they share a brief, the ENGINE.md contract and a
  beat-by-beat visual plan; merge, then one pass over the whole video for continuity.
- **Shared-state bugs**: register shared tables in core.js before scenes load; validate pose and expression names.
- **Readability slips**: payoff slips shown for < 2 s; text typed in 1 s before the camera leaves; labels under the
  captions. Hold every slip ≥ 0.5 s + 0.3 s per word.
- **A 2-D map of embeddings**: choose the projection by trustworthiness and print the method on the slip.
- **Another language = rerun, not translate**: rerun the experiments in that language so graph paper shows real outputs
  in it; translate only the narration.
- **Music** you cannot hear: measure it (ebur128), keep it 8–12 dB under the voice, and ask the user to listen.
