# Slides from the same material

The deck reuses the claims ledger (same numbers, same status labels), the assets (same images), and the scene order.
Typically one slide per scene, with the beat captions as speaker notes.

## Where to build it
1. **Claude.ai Slides artifact** (if the Artifact tool lists a Slides type): start from it and follow its instructions;
   upload images as assets. Best for sharing a link.
2. **Self-contained HTML** (always available): copy `templates/deck.html`, fill one `<section>` per slide, put images next to
   it (or inline as data URIs). Arrow keys navigate, `p` prints all slides (save as PDF). Set `<html lang="fa" dir="rtl">`
   for Persian.
3. **PowerPoint**: if the user needs .pptx, use a pptx skill with the same content.

## Rules
- Every result slide: the number, its denominator, a status chip (final / development / planned / reported), and a source
  line at the bottom.
- One limits slide, before the closing slide.
- Persian: see persian.md (RLM around text blocks, LRI/PDI around Latin runs, row-reverse for rows, Vazirmatn).
- 16:9, large type (titles ≥ 56 px at 1920 wide, body ≥ 26 px), at most ~40 words of body text per slide.
- Check every slide rendered (screenshot or print preview) for overflow before delivering.
