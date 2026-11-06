# Intake questions

Ask with the question tool, 1-4 questions per round, recommended option first. Skip anything the user already said.
Record answers in project.json.

## Round 1: what and for whom
- **Source**: one paper / several papers / my own experiments or project / a mix.
  - Paper: ask for the PDF (and supplement). Is it published? Are they an author? (Non-authors: we explain, we don't claim.)
  - Collection: which papers, and what question ties them together (that question is the video's hook).
  - Own work: where is the code, the results, the notes? Which runs are final? Is anything confidential?
- **Audience**: specialists in the field / researchers in nearby fields (default) / students / general public.
- **Length**: ~3 min (one idea), 5-8 min (one paper), 10-15 min (full method with results and limits).

## Round 2: form
- **Language**: English / Persian / both. Both = two full renders; the Persian one is written natively, not machine translated.
- **Voice**: none (text only) / free (Piper) / own recordings / paid OpenAI (key in ~/.config/openai/key).
  If paid: confirm they accept the cost; the OpenAI model and voice can be changed in project.json. Offer two short samples
  before narrating everything (rx.py durations with only one scene listed in project.json, or a single-beat test project).
- **Outputs**: video / video + slides / slides only. Resolution 720p (default) or 1080p.

## Round 3: science
- May we run experiments? Their code (which entry point, environment, GPU?), or small new ones (toy reproductions,
  visualisations of a mechanism). Time budget per run; anything over ~10 min needs a yes.
- Which numbers are final, which preliminary, which planned. Anything that must not appear (unpublished results,
  collaborators' data, private names) and anything that must (caveats, acknowledgements).
- Key figure(s) they want in the video, and the one sentence a viewer should remember.

## Round 4 (optional): look
- **Reference**: a video, a frame or a folder of images whose look they like (their own earlier video, a channel, a
  launch film). We take its grammar, never its content: `rx.py reference <video>` -> `docs/style_guide.md`, shown to them
  before any code (references/motion.md). No reference: the 3b1b dark palette and the house rules.
- **Look** (show `docs/style_watercolor.jpg` and the demo frames): the 3b1b dark style (default, Manim), the paper diorama
  (`references/style-diorama.md`), or a watercolor story short with painted sets and animated characters
  (`references/style-watercolor.md`; also as paper cut-out or hand-drawn ink). To try looks on their own frame first:
  `templates/watercolor-story/work/explore_styles.py` (paid, OpenAI images).
- **Launch video**: shape (landscape for posts and READMEs, vertical for stories and reels, square), and music (their own
  track that they may use, or original music synthesized in code).

## Defaults when the user doesn't care
Researchers in nearby fields; 5-8 min per paper; English; text only (no cost); 720p; dark 3b1b palette; status tags on
every result; a "limits" scene before the end.

## Subtitles
Ask once: subtitles as a separate .srt file (default: the whole frame stays picture; players and platforms show them on
demand) or burned into the video (`"captions": "burn"`: a strip under the picture, and text-only beats last long enough
to read). Visual storytelling is the default either way: plan the motion first.
