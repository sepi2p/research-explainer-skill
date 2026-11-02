# Pipeline details

## Commands (run in the project folder)
| command | does |
|---|---|
| `rx.py status [lang]` | short outline of the project and the next step |
| `rx.py check` / `rx.py fonts` | tools, fonts, optional voice/GPU/key / install bundled fonts |
| `rx.py request ...` | log a missing feature in feature_requests.md |
| `rx.py selftest` | build the demo (en+fa, 480p) and check all outputs |
| `rx.py new DIR --title T --langs en,fa --voice MODE` | project skeleton from templates/project |
| `rx.py claims` / `rx.py assets` | accuracy gates (numbers have sources; assets registered and unchanged) |
| `rx.py render LANG [--quality l/m/h] [--scenes ids] [--dry]` | parallel Manim renders (JOBS=4 by default) |
| `rx.py durations LANG --voice MODE` | beat lengths: voice clips, or reading time (none) from the dry run |
| `rx.py assemble LANG --voice MODE [--no-music]` | concat, music, loudness, .srt, small share copy |
| `rx.py qc LANG --voice MODE` | contact sheet per scene in build/qc/ |
| `rx.py build LANG --voice MODE` | all of the above in order |

## How timing works
Each beat lasts `dur + PAD` (PAD 0.25 s) or longer if its animation runs longer. Voiced: dur = clip length. Text only:
`rx.py render --dry` renders every beat with dur ≈ 0, measuring each animation; then dur = max(reading time + 1.5 s,
animation + 0.8 s, min_dur). Captions inside a beat change in proportion to their length. The renderer records each beat's
start time (build/timings/), which the .srt writer uses, so subtitles match the picture exactly.

## Iterating
- While coding a scene: `rx.py render en --quality l --scenes s03_chart` then look at a frame:
  `ffmpeg -ss 5 -i build/render_en_none/videos/<file>/480p15/<Class>.mp4 -frames:v 1 /tmp/f.png`.
- After editing narration: re-run durations (only changed beats are re-voiced), then render the affected scenes, then assemble.

## Troubleshooting
- A scene fails only when rendered in parallel: Manim's text cache race. rx.py deletes empty cache files and re-renders
  failures one at a time automatically.
- `beats played [...] narration has N`: the scene must call self.beat(i) once for every beat, in order.
- MathTex errors: LaTeX missing; use T() for formulas or install texlive.
- Persian label shows in English: `rx.py strings fa`, add to strings_fa.json.
- Wrong order in a Persian line with Latin: the Latin run is isolated automatically; if punctuation lands on the wrong
  side, split the label into two T() objects or rephrase.
