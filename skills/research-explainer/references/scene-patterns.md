# Scene patterns

Plan with `manim-composer` (bundled), code with `manimce-best-practices` (bundled). These are the extra patterns that made
research explainers work for researchers.

## Arc for one paper (5-15 min)
1. **Title** (no narration, 3 s; `"min_dur": 3.0` on an empty beat).
2. **Hook**: the problem in one concrete example (a real image, a real failure). End with a question.
3. **Why it is hard / what exists**: prior approaches, each with its known weakness (from the sources, cited).
4. **The idea**: the one insight, shown visually before any formula.
5. **How it works**: 2-4 steps, with a `STEPS = (names, active)` tracker in the corner so viewers know where they are.
6. **Real run**: one recorded example end to end (real inputs, real outputs, real numbers from the logs).
7. **Results**: charts from data.json, every one with `tag(status)` and `source_note(...)`.
8. **Where it is not best / limits**: from the ledger caveats.
9. **What remains**: planned work in words only (status "planned", no numbers).
10. **Close**: the one sentence to remember, over the image from the hook.

Collection of papers: hook = the shared question; one scene per approach (same visual template so they compare); a
comparison scene that only places numbers side by side when settings match (else a table with a "settings differ" note).

Own experiments/study: hook = the question you asked; method; what you measured and how; results with status; what
surprised you; limits; next steps.

## Rules of thumb
- One point per beat, one visual per point. If a beat has no visual change, merge it or add one.
- Show, then name: animate the mechanism first, then give it its term or formula.
- Transform objects instead of replacing them (the same image moves from "input" to "model" to "output").
- Real before schematic: show the real image, then the abstraction of it.
- Keep colours semantic across the video (one colour per actor/method), declared once in project.json "palette".
- Numbers appear where the eye already is (next to the bar or point), not in a legend far away.
- Text on screen is short labels; sentences belong in the caption strip.
- Captions: 1-2 sentences per beat. Persian chunks ≤112 characters, English ≤150 (split automatically).

## Library helpers (scripts/explainer/base.py)
| helper | use |
|---|---|
| `Beat`, `self.beat(i, fn)` | one narration beat with caption and timing |
| `T(s, size, color)` | all text (Persian aware); `L("en", fa="...")` for inline translations |
| `tlines([...])` | lines aligned to the reading start |
| `img`, `framed`, `array_img` | real images (nearest-neighbour for small images) |
| `amplified(diff)` | invisible differences made visible; print the gain |
| `bar_chart`, `curve`, Manim `Axes` | charts from `data()` |
| `tag(status)`, `source_note(s)` | status label and source line on every result |
| `pill`, `panel`, `note` | labels, boxes, small print |
| `steps_tracker(names, active)` / `STEPS` | where we are in a multi-step method |
| `clear_stage()`, `outro()` | fade between beats / end of scene |

Axes: avoid Manim's default number labels (they need LaTeX); place `T()` labels yourself as in the demo.
