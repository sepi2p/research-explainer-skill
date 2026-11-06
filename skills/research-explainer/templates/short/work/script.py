# Narration for the demo short "Averaging noisy readings" (one claim per line, ~85 words for ~33 s). Every number comes
# from the seeded simulation in make_data.py (assets/data.js): sigma 0.25; worst of the 20 readings misses by 0.58, their
# average by 0.05; error of the average 0.250 / 0.125 / 0.063 / 0.031 at n = 1 / 4 / 16 / 64; with correlation 0.5 it
# stays near 0.18 (0.178 at 64, floor 0.177).
# A new script needs new timings: GAP in assemble_voice.py, the scene times in index.html and compositions/*.html,
# OFF/END in captions.html, SHOW in make_captions.py, and the accent times in music.py.
LINES = [
    ("V1", "Measure the same thing twenty times, and you get twenty different answers. Which one is right?"),
    ("V2", "Each reading is the true value plus random noise, with a spread of 0.25."),
    ("V3", "Average them, and the noise starts to cancel."),
    ("V4", "Single readings miss by as much as 0.58. Their average misses by 0.05."),
    ("V5", "Four readings: half the error. Sixteen: a quarter. Sixty-four: an eighth."),
    ("V6", "But only if the noise is independent."),
    ("V7", "If readings share half their noise, the error stalls near 0.18, even with sixty-four."),
    ("V8", "Averaging cancels random noise, not shared noise."),
]
TONE = {"V1": "a real, curious question that hooks the listener; rising on 'Which one is right?'",
        "V2": "clear and matter-of-fact",
        "V3": "upbeat turn: the fix",
        "V4": "contrast: a little dramatic on 'as much as', then pleased on 'Their average'",
        "V5": "rhythmic, three quick beats",
        "V6": "a quick warning, brisk, no slowing down",
        "V7": "dry, a little surprised on 'even with sixty-four'",
        "V8": "warm, punchy sign-off at a brisk pace, no slowing down"}
