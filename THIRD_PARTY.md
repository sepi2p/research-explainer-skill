# Licences in this repository

The MIT licence in [LICENSE](LICENSE) covers everything in this repository except the third-party components listed
below, which keep their own licences (each folder carries its licence file). In particular, `skills/manimgl-best-practices`
is CC BY-NC-SA 4.0: non-commercial use only, attribution required, adaptations under the same licence. Skip it with
`install.sh --no-gl`; the research-explainer pipeline does not need it.

## Third-party components

| component | path | licence | origin |
|---|---|---|---|
| manim-composer (skill) | skills/manim-composer | MIT (repository licence, copied as LICENSE.txt) | github.com/adithya-s-k/manim_skill @ cef0450 |
| manimce-best-practices (skill) | skills/manimce-best-practices | MIT | github.com/adithya-s-k/manim_skill @ cef0450 |
| manimgl-best-practices (skill) | skills/manimgl-best-practices | CC BY-NC-SA 4.0 (adapted from 3b1b/videos); non-commercial use only | github.com/adithya-s-k/manim_skill @ cef0450 |
| Inter (font) | skills/research-explainer/assets/fonts/Inter-* | SIL Open Font License 1.1 | github.com/rsms/inter |
| Kenney sound effects | skills/research-explainer/assets/sfx | CC0 1.0 | kenney.nl (Impact Sounds, Interface Sounds, UI Audio) |
| Vazirmatn (font) | skills/research-explainer/assets/fonts/Vazirmatn-* | SIL Open Font License 1.1 | github.com/rastikerdar/vazirmatn |
| Rough.js 4.6.6 | skills/research-explainer/templates/diorama/video/lib/rough.js; templates/watercolor-story/assets/lib/rough.js (patched: `Math.random()` replaced by a seeded fallback for deterministic renders) | MIT (LICENSE_roughjs.txt) | github.com/rough-stuff/rough |
| JetBrains Mono (font) | skills/research-explainer/templates/diorama/video/fonts/JetBrainsMono* | SIL Open Font License 1.1 | github.com/JetBrains/JetBrainsMono |
| Caveat (font) | skills/research-explainer/templates/diorama/video/fonts/Caveat*, skills/research-explainer/templates/short/assets/fonts/Caveat.ttf, skills/research-explainer/templates/watercolor-story/assets/fonts/Caveat.ttf | SIL Open Font License 1.1 (OFL_caveat.txt) | github.com/googlefonts/caveat |

| Watercolor paintings (generated) | skills/research-explainer/templates/watercolor-story/assets/bg_set.jpg, bg_wash.jpg; docs/style_watercolor.jpg (frames of the demo) | made for this repository with OpenAI gpt-image-2 by its author; released under the repository licence | generated from a frame of the template's own drawn set (a made-up bakery) |

The three skills are unmodified copies of that commit. manimgl-best-practices is optional (`install.sh --no-gl` skips it);
the research-explainer pipeline uses Manim Community Edition only.

## Fetched by `templates/short/setup.sh` and `templates/watercolor-story/setup.sh` (not in this repository)

The vertical-short template does not ship these browser libraries; `setup.sh` installs them from npm at these exact
versions and copies their builds into `assets/lib/` (which that template's `.gitignore` keeps out of git).

| library | version | licence | origin |
|---|---|---|---|
| GSAP | 3.15.0 | GreenSock Standard "no charge" licence, gsap.com/standard-license (free to use; not an open-source licence) | npm `gsap`, gsap.com |
| p5.js | 1.11.11 | LGPL-2.1 | npm `p5`, github.com/processing/p5.js |
| PixiJS | 8.22.0 | MIT | npm `pixi.js`, github.com/pixijs/pixijs |
| gl-transitions | 2.5.0 | MIT (the collection); each shader has its own: InvertedPageCurl by Hewlett-Packard, BSD 3 Clause; InkBleed by gre, MIT. `transitions.js` keeps each shader's author and licence. | npm `gl-transitions`, gl-transitions.com |

## Not bundled, installed by the user

- Manim Community Edition (MIT), Playwright (Apache-2.0, for `rx.py promo` and the diorama renderer), FFmpeg (LGPL/GPL),
  Piper TTS and its voices (each voice has its own licence, see its model card on huggingface.co/rhasspy/piper-voices).
- HyperFrames CLI 0.9.19 (Apache-2.0, github.com/heygen-com/hyperframes), run with `npx` for vertical shorts; it
  downloads a headless Chrome and the Inter and JetBrains Mono fonts (OFL) on first use.
- NVIDIA Parakeet TDT 0.6B v3 (CC-BY-4.0, huggingface.co/nvidia/parakeet-tdt-0.6b-v3), word times for the shorts:
  `hyperframes models install parakeet` downloads an int8 ONNX conversion
  (huggingface.co/csukuangfj/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8) and runs it with sherpa-onnx (Apache-2.0).
- Lemo-Opuscar (MIT, github.com/lemomo-ai/lemo-opuscar) and two of its sample packs, VS Chamber Orchestra: Community
  Edition (VSCO 2 CE) and the Versilian Community Sample Library (VCSL), both CC0 1.0 by Versilian Studios: the sampler
  behind `templates/short/work/music.py`, `templates/watercolor-story/work/music.py` and
  `templates/diorama/work/music.py` (optional: without it the diorama has no score, or uses your own `work/music/bed.*`).
- Data, audio and image scripts: numpy, scipy, soundfile (BSD-3-Clause), soxr (LGPL-2.1-or-later), Pillow (MIT-CMU); the diorama's free voice uses
  Piper TTS (listed above).
- OpenAI models (gpt-audio-1.5, gpt-4o-transcribe, whisper-1, gpt-5.5, gpt-4.1-mini, text-embedding-3-small, gpt-image-2) are used
  through the user's own API account under OpenAI's terms. The demo data in `templates/diorama/video/data.js`,
  `templates/short/assets/data.js` and `templates/watercolor-story/assets/data.js` are seeded simulations of averaging
  noisy measurements (no recorded runs).

## Audio

The only audio files in this repository are the Kenney CC0 sound effects above. The background music of the Manim
explainers and launch videos is synthesised in code at build time (`scripts/explainer/music.py`, `beat.py`). The
vertical-short score is built from recorded CC0 samples (VSCO 2 CE, VCSL) that the user downloads; the score itself is
not shipped. `templates/diorama/work/audio_v2.py` mixes music tracks the user supplies and has the right to use; none
are shipped. No voice clips or mixes are shipped with the templates.
