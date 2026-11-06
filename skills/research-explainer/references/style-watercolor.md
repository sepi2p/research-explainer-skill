# Style: watercolor story short

Use this when the user wants the **watercolor** look, a **story with characters** (a scene that shows the idea in real
life before explaining it), or "the same style as" a video made with it. Start from `templates/watercolor-story/` (a
complete 40.4 s example, `./setup.sh` fetches its libraries) and read `references/shorts.md` for the shorts pipeline it
builds on (HyperFrames, voice, captions, music, checks).

## 1. The look in one paragraph

A vertical short that opens on a small, warm scene painted in watercolor: soft transparent washes, pigment granulation,
light falling through a window, a few fine ink lines. The people and props in it move (they blink, mime their speech
bubbles, swing their legs, react) because they are drawn and animated by the engine and painted on the fly by an SVG
watercolor filter, while everything that never moves was painted once by an image model from an empty frame of the same
set, so the two line up exactly. After the scene, the explanation plays on a painted paper wash: the same painted puppets,
data drawn as watercolor dabs (in the example every simulated reading is a dab on a number line), soft paper cards. Text
stays crisp: captions, speech bubbles, the scale's display, the notepad, the numbers.

## 2. Fixed decisions (copy, don't re-decide)

| Thing | Value |
|---|---|
| Canvas | 540x960 drafts, final `render --resolution portrait` (1080x1920); HyperFrames compositions |
| Split | **painted once** (gpt-image-2): the empty set (1088x1920, quality high, 2 variants, pick one) and a plain paper wash. **drawn and painted live**: characters, furniture they touch (the counter), props (the scale, the bag of flour, a window whose curtains blow), data dabs |
| Puppets | `assets/puppets.js`: pure `(seed, state) -> SVG`, rough.js parts cached per boil seed (8 per second), characters on twos (12 fps) with ±0.5° jitter, faces crisp (eyes with a catch-light, brows, mouth) |
| Watercolor filter (`assets/styles/watercolor.js`) | displacement (fractal noise 0.035, 3 octaves, scale 5) -> wet rim (alpha minus its 2.4 px blur, colour minus 0.6 of it) -> pigment grain (noise 0.75, alpha 0.34) -> wash blotches (noise 0.012) ; fills mixed 20 % toward paper `#FFFBF2`; every filled path gets the filter |
| Ink | rough.js roughness 1.6, bowing 1.3, stroke 1.15 px `#5B4E46` at 80 % opacity; navy `#1F2A44` only for crisp faces and text |
| Bubbles | white paper `#FFFDF8`, no outline, soft shadow `2px 4px 7px rgba(58,42,26,0.38)`, karaoke words turn brick `#B5533C` on the narrator's word times |
| Map | each page a dab: a faint wide circle (alpha 55, 7.5 px) plus a dense small one (alpha 150, 3.4 px); colour per person; the closest five enlarge |
| Cards | `rgba(255,252,244,0.9)`, radius 12, soft shadow; no graph paper (story shorts carry made-up data), but every card or scene subtitle with numbers says where they come from ("simulated · seed 1405") |
| Camera | a keyframe table read inside the redraw (`CAMK`): never a GSAP tween on a camera object (it lags the redraw by one seek and breaks random-access snapshots) |
| Voice | one narrator (gpt-audio-1.5 marin) tells the story in the third person; characters "speak" in bubbles and mime while their bubble is up (`work/mouth.py` windows) |
| Honesty | a "DRAMATIZATION · MADE-UP BAKERY" tag in the story scene and a credit line on the end card; every number from a seeded script (`work/make_data.py`) that asserts its claims; a real product named in a story is only named, never imitated |
| Looks | `assets/styles/watercolor.js` (default), `cutout.js` (painted room + paper cut-outs: white cut edge, grain, shadow), `ink.js` (hand-drawn ink on paper, the room drawn too); `cp` one to `assets/pstyle.js`, then `work/stills.sh` |

## 3. Painting the set (the part that makes it look painted)

1. Draw the set in `assets/puppets.js` (`kitchenBack` in the example) at the positions the story needs. Furniture the
   characters touch (the counter, the scale) stays in the puppets, not in the painting, so it can sit in front of them.
2. `work/empty_room.sh` renders the empty set (no people, no furniture, no bubbles) at 1080x1920.
3. `python3 work/paint_room.py work/empty_room.png work/painted` asks for "the same room, every object where it is, empty,
   loose watercolor on cold-press paper, light from the window, the lower half open and simple" (see its PROMPT). Pick the
   variant whose wall, shelves, tiles and window match best; save it as `assets/bg_set.jpg`.
4. `python3 work/paint_wash.py work/wash.png` paints the paper wash (pale cream top, faint sage bottom, near-white middle
   for text) -> `assets/bg_wash.jpg`.
5. A push-in enlarges the painting (1.12x on the apprentice, 1.2x on the baker in the example): for the 1080x1920 final, paint a close-up of that
   part of the room if it looks soft.
6. Painted images are `generated` assets: sets and backgrounds only, never data, charts or anything a viewer could take
   for a record. To compare looks before choosing, `work/explore_styles.py` repaints one frame in five styles.

## 4. Story method (from the example's reviews)

- Open on a **personal, practical moment** the viewer recognises (an apprentice weighs one bag of flour and the scale
  shows a new number every time); show the practical answer first (weigh it 16 times, take the average: 500.0 g), then
  explain why it works and where it stops.
- The narrator tells the story; bubbles carry the characters' exact words; keep the first bubble on screen at frame 0
  (thumbnail). Captions run from the first word (muted autoplay).
- Sensitive stories (medical, money, personal): made-up people and records only, plausible values, no advice, and a credit line.
- Pauses only for impact: the longest one in the example is the page curl into the explanation (0.7 s).

## 5. Craft: what makes a story short work (beat by beat)

Proportions for a 50-55 s short (about 140 narrated words, one narrator):

| Part | Share | What happens on screen |
|---|---|---|
| Hook | 0-9 s | The key question is already in a speech bubble at frame 0 (it is the thumbnail). Characters in their places, one small sign of the problem in the set (a reading on a display, a note). The narrator sets it up in the third person ("X has one question: ..."); the bubble's words light up as the narrator says them. |
| Struggle | 9-10 s | A character can't answer: a shrug with worried brows, a thought cloud with a doodle of the past (a year, a small sketch), then the idea ("let me check ..."): the phone or tool comes up. |
| Capability or demonstration | 10-20 s | Show the thing working before explaining it. With a tool: a close-up scaled up from where it is in the character's hand while the room dims (60 %) and the camera pushes in slightly; the question is typed, a search shows a counter through the real size of the data and a fast ticker, the answer types in and its key facts light up **on the narrator's words**, a source chip pulses and the exact source slides up with the exact line highlighted. Without a tool: a close-up of the evidence (the demo's notepad of 16 readings with the average; an "inside the device" card with the live reading crossing its line). |
| Reaction | 20-24 s | Back to the room; the camera pushes in on the person who is surprised: wide eyes, brows up, an "O" mouth, a small jolt, glasses pop, surprise marks; their bubble asks the question the explanation answers ("How can it know that?!"). Others smile. |
| Explanation | 24-48 s | Page curl to the paper wash. One idea per beat, each with one moving picture and a short title ("Wobble", "Average", "Noisy", "Low line"): the single case first, then many cases (dozens to hundreds of dabs), then the rule with its numbers, then its limit (the demo's draught; a threshold that trades speed for false alarms). Patterns that work: values as watercolor dabs on a number line or over time; rows or a sweep that changes one setting while the counts recompute; a small chart card that builds point by point on the narrator's numbers; a callback to a prop from the story (the kettle steams, the toaster puffs). |
| End | 48-54 s | The name, the takeaway words revealed on their spoken times, one plain line of value, the end line (a composition variable), the credit line. Show the summary line first and the takeaway after it, hold the last line at least 2.4 s (reading time: 0.5 s + 0.3 s per word). |

Rules that made the difference:
- **Show the capability before explaining it**, then let a character ask "how?". Personal, practical stakes (a kitchen, a garden, a workshop, a household errand), not an experiment without context.
- **One narrator, third person**; the characters' exact words are in bubbles. Characters mime only while their own bubble is up (mouth follows the narrator's loudness in that window), blink on their own clocks, move on twos with a tiny jitter, and react on the beat (lean toward the phone, smile after the payoff).
- **Text on screen follows the voice**: bubble words and answer highlights turn on at the narrator's word times (`work/words.json`); numbers are spoken as words in the script ("twenty twenty-four") and shown as digits (merge "twenty twenty-four" -> "2024" in the captions).
- **Pauses only with a purpose**: gaps of 0.2-0.55 s between lines, pauses inside a line capped at 0.2 s; one purposeful silent beat (the search, 1.3-1.5 s) carried by visuals and music.
- **Label made-up things on screen** (a tag in the story scene, a credit on the end card); show a plain chat screen when a product is named.

## 6. Pitfalls we hit, and the fixes (check these before showing a draft)

| Symptom | Cause | Fix |
|---|---|---|
| The push-in shows the wrong framing in some frames | a GSAP tween on a camera object updates after the redraw (one seek late) | camera = keyframe table read inside the redraw (`CAMK`) |
| A whole scene freezes on its first frame | an inline script error, e.g. a `const` name declared twice (`KEYS`) | `npx hyperframes lint` after every edit (it reports `invalid_inline_script_syntax`) |
| A rule like `html[data-look=x] .bub {display:none}` does nothing in a sub-composition | HyperFrames scopes composition CSS | switch look-dependent elements from the composition's script |
| lint: non-deterministic code / motion that snaps | `Math.random` in a library; tweens on `top`/`height` | seeded rough.js fallback; animate transforms (`y`, `scaleY`, opacity) |
| Highlighted answer text is garbled ("at age 220 Apr") | highlight ranges not in text order | sort the ranges by their start index |
| Bodies look see-through in watercolor | `fill-opacity` on puppet fills | keep fills opaque; lighten the colour instead (20 % toward paper) |
| A bar or strip covers a bubble; a sheet covers the citation chip; map labels collide | layout not re-checked after changes | snapshot every beat (and the push-in out of order), move the bubble/scroll, paper pills beside clusters |
| The first word is heard wrong (a name) | TTS take | re-voice until the transcript starts with the right words; check acronyms too |
| A correct take fails the transcript check | numbers written differently ("2024" vs "twenty twenty-four") | compare spoken forms; listen when the score is between 0.9 and 0.95 |
| The painting does not line up with the puppets | the reference had furniture or people, or a different aspect | paint from `work/empty_room.sh` (empty, 1088x1920), pick the variant whose floor line and window match |
| Coloured strokes (stripes, handles) come out as thin brown lines | the watercolor look re-inks every rough.js stroke (`PSTYLE.rough`: `#5B4E46`, 1.15 px) | draw coloured details as filled shapes |
| Smoke or steam looks like stacked coins; a translucent shape is not painted | the watercolor filter only tags `<path d="..." fill="#hex"/>`; rough circles boil | plain circles under an SVG Gaussian-blur filter, opacity on the group |
| Bubble words and captions light up early | Parakeet starts a line's first words 0.1-0.35 s before the audio | `make_captions.py` clamps word starts to the line start |
| A wrong first word or key term passes the transcript check | one wrong word barely lowers the similarity | `voice.py` also requires the first two words and `KEY_TERMS`; a second opinion from Parakeet settles disagreements |
| `transcript.json` was overwritten | `hyperframes transcribe` writes it next to its input | transcribe only `assets/voice.wav`; copy single clips elsewhere first |
| A count on screen differs from the script's | the scenes recount from rounded values in data.js | compute every shown count from the shipped (rounded) values and assert it in make_data.py |
| A moving value shows an impossible number ("line 17" in an 18-50 range) | a hand-made spring overshoots | no overshoot on values with meaning; GSAP `power2/3` eases (the spring helpers of references/motion.md belong to the launch-video engine) |
| A chart's current dot runs ahead of its trail | the trail is sampled every 0.04 s but the dot at t | add the point at t to the trail |
| The end card's summary fails the reading-time check | it appears after the takeaway, too late to read | show the summary first, keep it short (0.5 s + 0.3 s per word on screen) |
| One image call cost two images; a retry came back at another size | n=2 bills both variants; a fallback size does not line up | `paint_room.py` makes one 1088x1920 call and stops on an error |

Levels that worked: voice -16 LUFS; the rendered score at a gain of -6.3 dB, which sits about 11 dB under the voice; a limiter
at 0.79; `data-volume` 0.79 -> about -15 LUFS
in the render. Small text on paper: brick `#9C4130`, teal `#1D6B62`/`#155A52`, placeholder grey `#6B7079`.

## 7. Re-timing for a new script

The demo's scenes use literal times. For a new script, write every cue as `CUES.at(host, line, word)` (`assets/cues.js`,
from the narrator's word times), so the next voice take re-times everything; keep `HOST` in cues.js equal to the host starts
in `index.html` and run `work/check_hosts.py` (starts, film length, captions `END`). The film length also lives in
`work/music.py` (`DUR`) and the `mix.sh` argument; `GAP` in `assemble_voice.py` and the windows in `mouth.py` are keyed by
line id; put music accents on `words.json` times too. Sizes at 540x960: key words (bubbles, titles, captions) 23-30 px and
more, data labels at least 14 px (the `check` floor); references/motion.md's percentages are for 16:9 landscape.

## 8. Review loop (how the example reached its quality)

1. Snapshot sheet of every beat (16-24 frames) after each round; look at every frame; fix the worst problems; repeat.
2. `check --json`: fix layout, contrast and reading-time findings (a fast ticker may stay as is; quoted evidence may be
   long if its key words are highlighted and spoken).
3. Render a draft (540x960), decode frames from the MP4 at the beats and inside the transitions, measure loudness.
4. Send the draft; apply every note in the next draft; export 1080x1920 only after the user approves.

## 9. Checks

`npx hyperframes lint` (rough.js is patched to a seeded fallback for `Math.random`), `check` (layout, contrast, reading
time: a deliberately flashing ticker may fail reading time), snapshots of every beat **and** of the push-in frames out of
order, the page-curl stills after any look change (`work/stills.sh`), then frames decoded from the rendered MP4.
