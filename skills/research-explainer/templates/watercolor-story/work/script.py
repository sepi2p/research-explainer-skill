# "The wobbly scale" short: a made-up bakery (made-up people; every number comes from work/make_data.py, a seeded simulation).
# One voice: the narrator (NAR) tells the story; the apprentice's and the baker's words are speech bubbles on screen.
LINES = [
    ("N1", "A new apprentice weighs a bag of flour. Why does the scale show a new number every time?"),
    ("N2", "The baker laughs. Weigh it sixteen times, and take the average."),
    ("N3", "Sixteen readings later: five hundred point zero."),
    ("B1", "Here's why: each reading wobbles by about a quarter gram."),
    ("B2", "Average four, and the wobble halves. Sixteen, it halves again. Sixty-four, again."),
    ("B3", "But a draught from the window pushes every reading the same way."),
    ("B4", "That shared push never averages out: the error stays near zero point one eight grams."),
    ("B5", "Averaging beats random noise, not shared noise."),
]
SPEAKER = {}   # every line: NAR
VOICE = {"NAR": "marin"}
ROLE = {"NAR": "the narrator of a short, punchy explainer video about measurement and noise, like a smart, friendly teacher"}
TONE = {"N1": "storyteller opening, warm; a real, puzzled question at the end",
        "N2": "a smile in the voice on 'The baker laughs', then the baker's simple advice, kind and sure",
        "N3": "quick, then satisfied on 'five hundred point zero'",
        "B1": "a little secret shared, clear and calm",
        "B2": "brisk and rhythmic, one beat per number",
        "B3": "a twist: 'But' with a small pause, slightly mysterious",
        "B4": "firm; stress 'never'; say the number as 'zero point one eight'",
        "B5": "warm, punchy sign-off"}

# words that must be heard exactly (names, terms, numbers); voice.py retakes until they are: {line id: [words]}
KEY_TERMS = {}
