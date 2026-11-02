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

The three skills are unmodified copies of that commit. manimgl-best-practices is optional (`install.sh --no-gl` skips it);
the research-explainer pipeline uses Manim Community Edition only.

Not bundled, installed by the user: Manim Community Edition (MIT), Playwright (Apache-2.0, for `rx.py promo`), FFmpeg (LGPL/GPL), Piper TTS and its voices (each voice
has its own licence, see its model card on huggingface.co/rhasspy/piper-voices). The background music is synthesised by
scripts/explainer/music.py at build time (no recorded audio). OpenAI voices are used through the user's own API account
under OpenAI's terms.
