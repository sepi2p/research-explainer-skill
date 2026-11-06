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

## Visual storytelling first
The motion carries the explanation; text names things. Test: with the sound off and no subtitles, can a viewer follow the
story from the motion alone? If not, the beat needs a better visual, not more words.
- **Continuity**: the same object travels through the story (a photo becomes pixels, pixels become maps, maps become a
  barcode, the barcode becomes bars). Transform it; don't cut to a new picture.
- **Many things**: show the many (64 filters, 512 numbers, 20 trials) as real many-objects that pop in, fan out, then
  gather into the one result.
- **Process**: show a mechanism running (a filter sweeping the image while the output paints itself; dots flowing through
  stages), not a diagram of it.
- **Numbers move**: counters tick to their value (`ticker`); data points fly from where they come from to where they land
  on the chart (`collapse_to`).
- **Camera**: move in on what matters (`push_in`, or a magnifier: a small box on the image grows into a large panel).
- **Words**: on screen at once at most ~6 words, as labels next to what they name. Sentences go to voice or subtitles.

## Motion vocabulary (scripts/explainer/base.py)
| helper | motion |
|---|---|
| `fan(mobs)` | a fanned stack: "there are many of these" |
| `gather(mobs, target)` | many fly into one and become it (copies -> average, maps -> vector) |
| `collapse_to(mob, point)` | an image/group shrinks into a data point on a chart |
| `ticker(tracker, fmt)` | a number that counts as a ValueTracker animates |
| `value_axis` + `dot_plot` | samples dropping onto a number line |
| `particles(n, ...)` | seeded clouds: noise, populations, data flowing (with `MoveAlongPath`) |
| `push_in` / `pull_out` | camera into a region and back |
| `spotlight(mob, others)` | dim the rest, ring the one |
| `spring(preset)`, `spring_time(preset)` | rate function with mass: snappy, base, heavy (no overshoot), playful |
| Manim: `TransformMatchingShapes`, `ReplacementTransform`, `FadeIn/FadeOut(target_position=...)`, `LaggedStart`, `ShowPassingFlash`, `Circumscribe`, `always_redraw` + `ValueTracker` | morphs, flights, sweeps, live-updating geometry |

The worked example is `examples/how-a-network-sees/` (a ResNet-18 on CC0 photos: pixels, filters sweeping, feature maps,
prediction bars, saliency, an adversarial change): read its `scenes/main.py` before writing a new video.

House rules (banned looks, pace, phone-size text, the critique loop): [motion.md](motion.md).

## Rules of thumb
- One point per beat, one visual per point. If a beat has no visual change, merge it or add one.
- Show, then name: animate the mechanism first, then give it its term or formula.
- Transform objects instead of replacing them (the same image moves from "input" to "model" to "output").
- Real before schematic: show the real image, then the abstraction of it.
- Keep colours semantic across the video (one colour per actor/method), declared once in project.json "palette".
- Numbers appear where the eye already is (next to the bar or point), not in a legend far away.
- Text on screen is short labels; sentences belong to voice or subtitles.
- Subtitles: 1-2 sentences per beat. Persian chunks ≤112 characters, English ≤150 (split automatically). They go to the
  .srt; burned into the picture only with `"captions": "burn"` in project.json (then beats last long enough to read them).

## Library helpers (scripts/explainer/base.py)
| helper | use |
|---|---|
| `Beat`, `self.beat(i, fn)` | one beat: its animation, sound and subtitle timing |
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
