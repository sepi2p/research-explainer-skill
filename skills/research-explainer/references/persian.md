# Persian (Farsi) videos and slides

## Writing
- Write the Persian narration natively from the claims ledger, not by translating English sentences word for word.
- Keep technical names in Latin script (ResNet-18, CIFAR-10, JPEG); add them to project.json "keep_latin" if they appear
  alone as labels. Add how they are pronounced to "pronounce": {"fa": {"CIFAR-10": "سیفار ده"}} for the voice.
- Numbers: write digits in captions (they are converted to Persian digits ۰-۹ with ٫ as decimal point and ٬ for thousands);
  the voice reads them as words automatically (scripts/explainer/fa_numbers.py).
- Use the zero-width non-joiner (U+200C, نیم‌فاصله) correctly: می‌شود، نسخه‌ها، اندازه‌گیری.
- Reading speed for text-only videos: about 12 characters per second (rx.py uses reading_cps in project.json).
- Condensing for text-only: keep every number, status and caveat; cut adjectives and repetition. ~55% of the spoken length
  is typical. Put the shorter version in a beat's "text" field; "caption" stays for voiced versions.

## In Manim (handled by T())
- Text with Persian letters is rendered with Pango markup, a leading RLM (U+200F), and every Latin/math run wrapped in
  LRI ... PDI (U+2066 ... U+2069) in the Latin font. You do not have to do this by hand.
- Strings with no Persian letters ("n = 4", "0.25") stay left to right, with Persian digits.
- Arrows inside a Latin run read left to right: write "a.py → b.json", not "←".
- Labels: put translations in strings_fa.json ("exact" for fixed strings, "patterns" for strings with numbers), or inline
  with `L("label", fa="برچسب")`. After a render, `rx.py strings fa` lists labels still in English.
- Layout: `START` is RIGHT in Persian; use `aligned_edge=START`, and `RIGHT if not RTL else LEFT` for rows that follow the
  reading order. Charts keep their x axis left to right (the usual convention in Persian technical writing).
- Fonts: Vazirmatn for Persian, Inter for Latin (bundled in assets/fonts, installed by install.sh).

## In slides (HTML)
- `dir="rtl"` on the deck, `text-align: right`, `flex-direction: row-reverse` for rows that follow reading order.
- Wrap each text block in RLM at both ends (&#8207; ... &#8207;) and each Latin run in LRI ... PDI (&#8294; ... &#8297;)
  so mixed lines like "روی CIFAR-10 · ۱۳ از ۱۴" order correctly.
- Same fonts: Vazirmatn (Google Fonts has it) with Inter for Latin.
