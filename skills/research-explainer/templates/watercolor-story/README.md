# Watercolor story short (template)

A 40.4 s vertical short (540x960 drafts, 1080x1920 final) that tells a small story with characters, then explains the
idea behind it. The example, "The wobbly scale": in a small bakery an apprentice weighs one bag of flour and the scale
shows a new number every time; the baker laughs and says to weigh it 16 times and take the average; the narrator then
explains why that works (each reading wobbles by about 0.25 g, and averaging n readings divides that by √n) and where it
stops (a draught from the window pushes every reading the same way, and that shared push never averages out).
**The bakery and its two bakers are made up** (labelled on screen); every number on screen comes from
`work/make_data.py`, a small seeded simulation (numpy, no API calls). One narrator voice tells the story; the
characters' words are speech bubbles.

The look is described in `../../references/style-watercolor.md`. In short: an image model paints what does not move
(the kitchen, a paper wash); the engine draws and animates everything that moves (rough.js puppets, the counter, the
scale and the bag, the reading dabs, the chart) and paints it with an SVG watercolor filter; text, captions, the scale's
display and the notepad stay crisp.

## Choose a look (one line)

    cp assets/styles/watercolor.js assets/pstyle.js   # painted set + painted puppets + paper wash (default)
    cp assets/styles/cutout.js     assets/pstyle.js   # painted set + paper cut-out puppets (white edge, soft shadow)
    cp assets/styles/ink.js        assets/pstyle.js   # the series' hand-drawn ink on paper; the set is drawn too
    work/stills.sh                                    # then remake the page-curl stills

(`assets/styles/empty.js` is the fourth look: the set with nobody in it, the reference `work/empty_room.sh` renders for
the painter.)

## Run it

    ./setup.sh                                         # libraries, paper, placeholder stills, a silent mix (PYTHON=... picks the python)
    npx --yes hyperframes@0.9.19 preview               # look at it
    work/stills.sh                                     # real stills for the page curl
    npx --yes hyperframes@0.9.19 render --quality draft -o renders/draft.mp4
    npx --yes hyperframes@0.9.19 render --resolution portrait -o renders/final_1080x1920.mp4   # only when approved

The voice and the music are not shipped (`assets/*.wav` are ignored): until you voice your own script, `setup.sh`
writes a silent `assets/mix.wav` and the captions, bubbles and mouths run on the shipped word times.

## The example, scene by scene

| Host | Time (s) | What happens | Narration |
|---|---|---|---|
| `sA` | 0-13.95 | the kitchen: the apprentice lifts the bag and puts it back, the display hunts and settles (499.7, 499.6, 499.3, 500.3); his question is a bubble from frame 0; the camera pushes in on him, pans to the baker, who laughs and raises a finger; the notepad comes up with the 16 readings and their average, 500.0 g | N1, N2, N3 |
| `t1` | 13.65-14.25 | GL page curl between two stills | |
| `sB1` | 13.95-17.6 | "Wobble": 80 single readings fly out of the scale onto a number line and stack into a bell; the card turns into the typical wobble, ± 0.25 g, with its bracket | B1 |
| `sB2` | 17.6-34.0 | "Average": rows of session averages for 1, 4, 16, 64 readings tighten, each error halves (0.251, 0.125, 0.0624, 0.0312 g) and the chart follows 0.25 g ÷ √n; "Draught": a window blows, every row widens, the errors stop near 0.18 g (0.250, 0.199, 0.182, 0.179) above the floor 0.177 g | B2, B3, B4 |
| `s6` | 34.0-40.4 | end card: ÷ √n, the takeaway "Averaging beats random noise, not shared noise.", the 64-reading summary, the end line (a composition variable) and the credit | B5 |

The narration (`work/script.py`): "A new apprentice weighs a bag of flour. Why does the scale show a new number every
time?" / "The baker laughs. Weigh it sixteen times, and take the average." / "Sixteen readings later: five hundred point
zero." / "Here's why: each reading wobbles by about a quarter gram." / "Average four, and the wobble halves. Sixteen, it
halves again. Sixty-four, again." / "But a draught from the window pushes every reading the same way." / "That shared
push never averages out: the error stays near zero point one eight grams." / "Averaging beats random noise, not shared
noise."

## Make your own story (the order matters)

1. **Script**: `work/script.py` (lines, delivery notes, `KEY_TERMS` that must be heard exactly; one narrator voice).
   Write numbers as spoken words; make the picture match every word ("one slice" means one slice on screen) and give
   each character the expression its line needs (no default smile on an angry question).
2. **Data**: `work/make_data.py` -> `assets/data.js`: every number the scenes print or plot, from one seeded run. It
   asserts the claims it makes (the 1/√n errors, the draught floor), so a changed number fails loudly.
3. **Voice** (paid, OpenAI gpt-audio-1.5 "marin", checked by gpt-4o-transcribe): `python3 work/voice.py` (or
   `python3 work/voice.py N3` to retake one line); trim and join with planned gaps: `work/assemble_voice.py`;
   re-check: `work/check_voice.py`. `voice.py` retakes a line until its first two words and its key terms are heard
   right, not only until the overall similarity passes; when two transcribers disagree (gpt-4o-transcribe vs Parakeet),
   listen or retake. `GAP` in `assemble_voice.py` is keyed by line id: set it for your lines (the last value, `TAIL`,
   is the silence after the last line: at least the end card's reading time).
4. **Word times**: `npx --yes hyperframes@0.9.19 transcribe assets/voice.wav --engine parakeet` (it writes
   `transcript.json` next to its input: run it on assets/voice.wav, not on a single clip in the same folder), then
   `python3 work/make_captions.py` (captions.js and the bubbles' words.js; `SHOW` and `MERGE` turn spoken numbers into
   digits, e.g. "zero point one eight" -> 0.18) and `work/mouth.py` (mime tracks: a character's mouth follows the
   narrator only while that character's bubble is up; set the windows in `mouth.py`). `make_captions.py` clamps word
   starts to their line's start, because Parakeet starts lines 0.1-0.35 s early.
5. **Scenes**: `compositions/sA.html` (the kitchen, the weighing, the notepad close-up), `sB1` (one reading wobbles),
   `sB2` (averages, then the draught), `s6` (end card); `index.html` holds the hosts' start times and the film length.
   The demo's times are literal; for a new script write every cue as `CUES.at("sA", "N2", "average")` (assets/cues.js,
   from the narrator's word times) so a new voice take re-times the scenes, and keep `HOST` in cues.js equal to the
   host starts in `index.html` (`python3 work/check_hosts.py` checks the starts, the film length and the captions' `END`).
   The film length also lives in `work/music.py` (`DUR`) and the `mix.sh` argument; delete `assets/mix.wav` (or run
   mix.sh) after changing it, since setup.sh only writes a silent mix once. The camera is a keyframe table (`CAMK` in
   `sA.html`) read in the redraw. Captions stop where the end card starts (`END` in `captions.html`).
   `compositions/bg.html` paints the props under the explanation scenes (here bread, whisks, a flour bag): replace them
   for your story.
6. **Paint the set** (paid, gpt-image-2): change the drawn set in `assets/puppets.js` (`kitchenBack`; the counter, the
   scale and the bag are puppets in front of the people) if you need another place, then `work/empty_room.sh` ->
   `python3 work/paint_room.py work/empty_room.png work/painted` (edit its PROMPT; 2 variants) -> save the one that
   lines up best as `assets/bg_set.jpg` (the command is in the script's header);
   `python3 work/paint_wash.py work/wash.png` -> `assets/bg_wash.jpg` (1080x1920; the wash is topic-neutral, so you can
   keep the shipped one). One paint call bills both variants; if the painter shifts a band of the set, retry or keep
   puppets in front of that band.
   To compare looks first: `python3 work/explore_styles.py <frame.png> work/looks`.
7. **Music** (CC0 samples, Lemo-Opuscar): `python3 work/music.py` (see its header; put its accents on `words.json`
   times so they follow the voice, as the scenes do),
   then `bash work/mix.sh 40.4`.
8. **Check**: `npx --yes hyperframes@0.9.19 lint`, `... check`, snapshots of every beat (also out of order, for the
   camera), `work/stills.sh`, then frames from the rendered MP4.

## Files

- `assets/puppets.js`: the apprentice, the baker (two-link arms that reach a target), the kitchen set, the counter, the
  scale with its crisp display, the bag of flour, a window whose curtains a draught can blow. Pure `(seed, state) -> SVG`.
- `assets/styles/*.js`: the looks; `assets/pstyle.js` is a copy of the chosen one.
- `assets/fonts.js`: registers the handwriting font (Caveat, OFL) once from `assets/fonts/`; the CSS uses `var(--hand)`.
- `assets/data.js`, `captions.js`, `words.js`, `mouth.js`, `bg_set.jpg`, `bg_wash.jpg`: the example's data, word times
  and paintings. The paintings are generated images (gpt-image-2) made for this template: sets and paper only, never
  data.
