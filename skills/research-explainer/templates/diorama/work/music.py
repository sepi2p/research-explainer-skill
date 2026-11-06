"""music.py: an original score for the video, composed in code from CC0 samples (references/music-diorama.md)
-> work/music/score.wav (48 kHz 24-bit stereo, the exact video length, UNDUCKED: audio.py ducks it), music_bed.wav +
music_accents.wav (stems), credits.txt and score_meta.json (lint, checks, the reference level audio.py normalises to).

Reads timeline.json, work/music/cuemap.json (make_cuemap.py), work/music/voice_profile.json (measure_voice.py) and
work/audio/cues.json (audio.py's SFX, when present). Order:  audio.py -> measure_voice.py -> make_cuemap.py -> music.py
-> audio.py (now with the score) -> assemble.py.

The sound: a small acoustic workshop band (pizz bass, harp, marimba, pizz strings, glockenspiel, a clarinet or flute in
the narrator's pauses). How it is built:
  - one free-running 4/4 grid per chapter (66-80 bpm, from the chapter change + 1 beat), never locked to the words;
  - chords from a plan per section function (recipes below), diatonic with sus2/sus4/add9, changing every 2-4 bars;
    key changes between chapters are checked for cross-relations and bridged with a pivot chord;
  - the pulse plays WRITTEN 2-bar contoured figures (rise, arch, fall, ...), voice-led from chord to chord; under speech
    it plays half of them, above the voice's no-sustain zone (or softer when the instrument cannot go that high);
  - composed gap phrases (2-4 notes, from the theme's pentatonic) in every pause of 1.5 s or more;
  - motifs: M1 the theme (hook, payoffs, recap, outro), M2 the ladder (chapter k plays k notes), M3 doubt (sus4 -> sus2);
  - lint: dropouts (aside, dry line), no sustain in the no-sustain zone over speech, <= 2 onsets/s above 120 Hz under
    speech, no onset within 80 ms of an avoid-class SFX, bass only around error hits and sour pitched SFX, pulse out in
    SFX cascades, nothing else above 120 Hz while M2 sounds;
  - render per chapter in parallel, 1 s equal-power crossfades at chapter changes, a small wooden room, high-pass 35 Hz,
    a fixed -5 dB bell at 2.5 kHz; then each section's level is set to its energy (the arc lives in the score).
Deterministic: the same inputs and SEED give the same file.

Needs Lemo-Opuscar (MIT, https://github.com/lemomo-ai/lemo-opuscar) and two of its CC0 sample packs:
  git clone https://github.com/lemomo-ai/lemo-opuscar ~/lemo-opuscar
  cd ~/lemo-opuscar && sh tools/fetch.sh instruments vsco2ce && sh tools/fetch.sh instruments vcsl
Set LEMO_OPUSCAR if it is somewhere else (default ~/lemo-opuscar). Python: numpy, scipy, soundfile, soxr (its venv works).
Run:  nice -n 10 ~/lemo-opuscar/.venv/bin/python work/music.py      (DRY=1: compose + lint + checks only, no render)"""
import sys, os, re, json, math, bisect, pathlib, time
import numpy as np

# ================================ CONFIG (per video) ================================================================
SEED = 20261107               # one seed per video -> bit-identical renders
HOME = "D"                    # home key, major. Tune it to the chapter chime: its partials should be diatonic here
KEY_CYCLE = [0, 0, 5]         # semitones over HOME per chapter (0 = home, 5 = the IV key); hook, recap, outro stay home
BPM_CYCLE = [72, 76, 72, 66, 76, 80]   # chapter tempi (66-80 under speech; never 95-105)
LADDER_ROOT = 86              # M2's first note (MIDI; the chime's pitch, D6 here); M2 rises in the major pentatonic
CHIME_DECAY = 1.4             # M2 starts this long after a chapter chime (1.0 s when its first note is A6 or higher;
#                               0.15 s after a scene change without a chime)
PITCHED_SFX = {"end chime": [88], "auto check": [84]}   # SFX name in cues.json -> MIDI (fundamental + strong partials);
#                               not diatonic in its section's key -> bass only for 1 s around it (or retune the SFX)
JOBS = int(os.getenv("JOBS", "4"))   # parallel chapter renders
# Orchestration, rotated per chapter and every ~75 s inside long chapters (re-orchestrate, against fatigue)
ORCH = [dict(pulse="marimba", colour="harp", gap="clarinet"),
        dict(pulse="violas_pizz", colour="harp", gap="flute"),
        dict(pulse="violins_pizz", colour="mbira", gap="clarinet"),
        dict(pulse="marimba", colour="vibraphone", gap="recorder"),
        dict(pulse="violas_pizz", colour="mbira", gap="ocarina")]
DATA_ROT = ["harp", "mbira", "violins_pizz"]   # one-layer bed for dense data, rotated every 40 s
# Section recipes: function -> (layers in the order they enter as energy rises, chord plans to rotate through).
# Layers: bass (1+3), walk (bass + passing note), bass1 (beat 1), pulse (written figures), colour (bar pluck, high),
# pad (low cellos), bowed (bowed-vibe fifths above the zone), shaker (2+4, quarters only), sparkle (glock, gaps only),
# root5 (data: root + fifth, high), mbira (rising singles), pizz (light pizz on 2).  Chords: scale degree + colour.
RECIPES = {
    "hook":    (["bass", "pulse", "colour", "shaker", "sparkle"], [["1", "4", "1", "5"], ["1", "6", "4", "5"]]),
    "story":   (["bass", "pulse", "colour", "pad"], [["1", "6", "4", "5"], ["1", "2", "5", "1"], ["6", "4", "1", "5"], ["1", "4", "2", "5"]]),
    "naming":  (["bass", "colour", "pad", "pulse"], [["4", "1", "6", "5"], ["4", "5", "1", "6"]]),
    "payoff":  (["walk", "pulse", "colour", "pad", "bowed", "sparkle"], [["1", "6", "4", "5"], ["4", "5", "1", "1add9"]]),
    "problem": (["bass1", "bowed", "colour"], [["6", "5sus4", "4", "5sus2"], ["4", "2sus4", "6", "5sus4"]]),   # M3, unresolved
    "data":    (["root5", "bass1"], [["1", "4", "6", "5"], ["6", "4", "1", "5"], ["4", "1", "2", "5"]]),
    "recap":   (["bass", "pad", "pulse", "colour", "sparkle", "bowed"], [["1", "4", "6", "5"], ["4", "1", "5", "6"]]),
    "teaser":  (["bowed", "mbira", "bass1"], [["1", "4", "7", "1", "5", "4add9"]]),
    "cta":     (["bass", "pizz"], [["1", "6"]]),
    "outro":   (["bass1"], [["1"]]),
    "hold":    ([], [["1", "6", "4", "2", "5"]]),
    "aside":   ([], [["1"]]),
}
NLAYERS = {0: 0, 1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3, 8: 4, 9: 5, 10: 6}      # energy -> layers (brief section 4)
TARGET = {1: -6.0, 2: -4.0, 3: -2.5, 4: -1.0, 5: 0.0, 6: 0.5, 7: 1.0, 8: 1.5, 9: 2.0, 10: 2.5}   # dB re the energy-5 bed
TARGET_FN = {"hold": 3.0, "cta": 0.0}          # holds sit 2-4 dB over the reference bed (brief section 6)
# =====================================================================================================================

HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parent; MUS = ROOT / "work" / "music"
LIB = pathlib.Path(os.getenv("LEMO_OPUSCAR", "~/lemo-opuscar")).expanduser().resolve()
if not (LIB / "core" / "audio" / "sampler.py").exists():
    sys.exit(f"Lemo-Opuscar not found at {LIB}: git clone https://github.com/lemomo-ai/lemo-opuscar there, or set "
             "LEMO_OPUSCAR to its folder; then fetch the samples: sh tools/fetch.sh instruments vsco2ce (and vcsl)")
if not all((LIB / "core" / "audio" / "instruments" / p).is_dir() for p in ("vsco2ce", "vcsl")):
    sys.exit(f"sample packs missing in {LIB}/core/audio/instruments: cd {LIB} && sh tools/fetch.sh instruments vsco2ce "
             "&& sh tools/fetch.sh instruments vcsl (CC0, about 670 MB together)")
if not (MUS / "cuemap.json").exists(): sys.exit("no work/music/cuemap.json: run work/make_cuemap.py first")
TL = json.loads((ROOT / "timeline.json").read_text())
CM = json.loads((MUS / "cuemap.json").read_text())
CF = ROOT / "work" / "audio" / "cues.json"
CUES = json.loads(CF.read_text()) if CF.exists() else []
PF = MUS / "voice_profile.json"
VP = json.loads(PF.read_text()) if PF.exists() else None
sys.path.insert(0, str(LIB)); os.chdir(LIB)        # the library is imported from its repo root
import soundfile as sf
from scipy.signal import butter, sosfilt, lfilter
from core.audio import sampler as S
from core.audio.sfx import SR

T = float(TL["total"]); NS = int(round(T * SR))
rng = np.random.default_rng(SEED)
BEATS = TL["beats"]; FIRST, LAST = BEATS[0]["start"], BEATS[-1]["end"]
LINT = {}
def bump(k, n=1): LINT[k] = LINT.get(k, 0) + n

# ---------------------------------------------------------------- the voice ---------------------------------------------
if VP is None:
    print("no work/music/voice_profile.json (run work/measure_voice.py): assuming zone MIDI 50-75 and the beats as speech")
    VP = dict(measured=False, no_sustain_zone=[50, 75], speech=[[b["start"], b["end"]] for b in BEATS])
elif not VP.get("measured"): print("voice profile is ASSUMED (text-only video): zone MIDI 50-75")
ZL, ZH = VP["no_sustain_zone"]
UP_LO, UP_HI = ZH + 1, min(88, max(ZH + 11, 86))   # under speech: plucked colour above the zone, below ~1.3 kHz
MID = (60, 76)                                    # gaps: the pulse's own register
PAD = (36, min(45, ZL - 1)) if ZL - 1 >= 38 else None   # low cellos only below the zone
SPEECH = []                                       # pauses < 1.5 s closed: "nothing" in short pauses
for a, b in sorted(VP["speech"]):
    if SPEECH and a - SPEECH[-1][1] < 1.5: SPEECH[-1][1] = max(SPEECH[-1][1], b)
    else: SPEECH.append([a, b])
SP0 = [s[0] for s in SPEECH]
GAPS = [(SPEECH[i][1], SPEECH[i + 1][0]) for i in range(len(SPEECH) - 1)]
def in_speech(t):
    i = bisect.bisect_right(SP0, t) - 1; return i >= 0 and t < SPEECH[i][1]
def overlaps_speech(a, b):
    i = max(0, bisect.bisect_right(SP0, a) - 1)
    while i < len(SPEECH) and SPEECH[i][0] < b:
        if SPEECH[i][1] > a: return True
        i += 1
    return False
def next_speech_start(t):
    i = bisect.bisect_right(SP0, t); return SPEECH[i][0] if i < len(SPEECH) else T + 10

# ---------------------------------------------------------------- SFX classes --------------------------------------------
HITS = CM["hits"]
LOCKED = sorted(h["t"] for h in HITS if h.get("sfx_class") == "locked")
AVOID = sorted(c["t"] for c in CUES if not any(abs(c["t"] - l) < 1e-3 for l in LOCKED))
def avoid_hits(t, w=0.08):
    i = bisect.bisect_left(AVOID, t - w); out = []
    while i < len(AVOID) and AVOID[i] <= t + w: out.append(AVOID[i]); i += 1
    return out
STAMPS = [h["t"] for h in HITS if h["kind"] == "naming"]
ERRORS = [h["t"] for h in HITS if h["kind"] == "error"]
CASCADES = [(h["t"], h.get("end", h["t"])) for h in HITS if h["kind"] == "cascade"]
ROWS = sorted(h["t"] for h in HITS if h["kind"] == "row")
CHAPTER_LOCK = {h["t"]: h.get("sfx_class") == "locked" for h in HITS if h["kind"] == "chapter"}
DROPS = CM["dropouts"]

# ---------------------------------------------------------------- harmony ------------------------------------------------
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
MODES = {"major": [0, 2, 4, 5, 7, 9, 11], "minor": [0, 2, 3, 5, 7, 8, 10], "dorian": [0, 2, 3, 5, 7, 9, 10]}
PENTA = {"major": [0, 2, 4, 7, 9], "minor": [0, 3, 5, 7, 10], "dorian": [0, 3, 5, 7, 10]}
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
def key(spec):
    m = re.fullmatch(r"\s*([A-G])([#b]?)(m?)\s*(major|minor|dorian)?\s*", spec)
    if not m: raise SystemExit(f"cannot read key {spec!r} (use e.g. D, G, Bm, B dorian)")
    tonic = (PC[m.group(1)] + {"#": 1, "b": -1, "": 0}[m.group(2)]) % 12
    mode = m.group(4) or ("minor" if m.group(3) else "major")
    return dict(name=f"{NAMES[tonic]} {mode}", tonic=tonic, mode=mode, sc=[(tonic + i) % 12 for i in MODES[mode]],
                penta=[(tonic + i) % 12 for i in PENTA[mode]])
def shift(k, semis, mode=None): return key(f"{NAMES[(k['tonic'] + semis) % 12]} {mode or k['mode']}")
HOMEK = key(HOME)

class Chord:
    def __init__(self, k, spec):
        m = re.fullmatch(r"([1-7])(sus2|sus4|add9|7)?", spec); d, col = int(m.group(1)) - 1, m.group(2) or ""
        sc = k["sc"]; t = [sc[d], sc[(d + 2) % 7], sc[(d + 4) % 7]]
        if (t[2] - t[0]) % 12 != 7:                       # never diminished: use the IV chord instead
            d = 3; t = [sc[3], sc[5], sc[0]]; col = ""
        if col == "sus4" and (sc[(d + 3) % 7] - t[0]) % 12 == 5: t[1] = sc[(d + 3) % 7]
        elif col in ("sus2", "sus4") and (sc[(d + 1) % 7] - t[0]) % 12 == 2: t[1] = sc[(d + 1) % 7]; col = "sus2"
        elif col == "add9": t.append(sc[(d + 1) % 7])
        elif col == "7": t.append(sc[(d + 6) % 7])
        self.key, self.root, self.pcs, self.deg = k, t[0], t, d + 1
        self.name = NAMES[t[0]] + ("m" if (t[1] - t[0]) % 12 == 3 else "") + col
    def __eq__(self, o): return isinstance(o, Chord) and self.pcs == o.pcs
    def __hash__(self): return hash(tuple(self.pcs))
    def __repr__(self): return self.name
def cross(c1, c2):
    """a cross-relation: a semitone clash between the two chords where one note is foreign to the other chord's key"""
    return any((a - b) % 12 in (1, 11) and (a not in c2.key["sc"] or b not in c1.key["sc"]) for a in c1.pcs for b in c2.pcs)
def pivot(k_old, c_next):
    """a chord of the old key that leads into c_next without a cross-relation (prefers V of the new key's area)"""
    for spec in ("5", "1", "4", "6", "2", "5sus4", "1sus2"):
        c = Chord(k_old, spec)
        if not cross(c, c_next): return c
    return None
def place(pc, lo, hi, near=None):
    c = [m for m in range(lo, hi + 1) if m % 12 == pc] or [m for m in range(lo - 12, hi + 13) if m % 12 == pc]
    return min(c, key=lambda m: abs(m - near)) if near is not None else c[0]
def tones(ch, lo, hi): return [m for m in range(lo, hi + 1) if m % 12 in ch.pcs]
def broot(ch): return place(ch.root, 33, 45)
def bfifth(ch): return place(ch.pcs[2], 33, 45, near=broot(ch) + 5)
_RANGE = {}
def irange(inst, lo, hi):
    if inst not in _RANGE: I = S.load(inst); _RANGE[inst] = (int(I.lo), int(I.hi))
    a, b = _RANGE[inst]; return (max(lo, a), min(hi, b)) if max(lo, a) <= min(hi, b) else (a, b)

# ---------------------------------------------------------------- sections, chapters --------------------------------------
SEC = [dict(s) for s in CM["sections"]]
for i, s in enumerate(SEC): s["i"] = i
SECT = [s["start"] for s in SEC]
def sec_at(t): return SEC[max(0, bisect.bisect_right(SECT, t) - 1)]
CHAPS = sorted({s["chapter"] for s in SEC})
CH0 = {k: min(s["start"] for s in SEC if s["chapter"] == k) for k in CHAPS}
CH1 = {k: max(s["end"] for s in SEC if s["chapter"] == k) for k in CHAPS}
for s in SEC:                                      # keys: section override, else the chapter's cycle; teaser in dorian
    k = s["chapter"]
    if s.get("key"): s["K"] = key(s["key"])
    elif s["function"] == "teaser": s["K"] = shift(HOMEK, 9, "dorian")
    elif s["function"] in ("hook", "recap", "outro") or k == 0: s["K"] = HOMEK
    else: s["K"] = shift(HOMEK, KEY_CYCLE[k % len(KEY_CYCLE)])
for i, s in enumerate(SEC):                        # a call to action bridges into the next section's key
    if s["function"] == "cta" and i + 1 < len(SEC): s["K"] = SEC[i + 1]["K"]
CHBPM = {}
for k in CHAPS:
    s0 = next(s for s in SEC if s["chapter"] == k)
    CHBPM[k] = int(s0.get("bpm") or (66 if s0["function"] == "teaser" else BPM_CYCLE[k % len(BPM_CYCLE)]))
for s in SEC:
    lay, plans = RECIPES.get(s["function"], RECIPES["story"])
    s["layers"], s["prog"] = lay, plans[int(rng.integers(len(plans)))] if len(plans) > 1 else plans[0]
    s["chords"] = [Chord(s["K"], c) for c in s["prog"]]
HOLDS = [s for s in SEC if s["function"] == "hold"]
def drop_at(t, kinds):
    return next((d for d in DROPS if d["kind"] in kinds and d["start"] <= t < d["end"]), None)

# ---------------------------------------------------------------- events -------------------------------------------------
EV = []
def E(t, inst, pitch, dur, vel, pan=0.0, role="pulse", prio=3, stem="bed", locked=False, release=None, attack=None, tag=""):
    if t < 0 or t >= T - 0.05: return None
    vel = float(np.clip(vel * rng.uniform(.95, 1.05), .02, 1.0))          # velocities +-5 %
    e = dict(t=float(t), inst=inst, pitch=pitch, dur=dur, vel=vel, pan=float(pan), role=role, prio=prio, stem=stem,
             locked=locked, release=release, attack=attack, tag=tag)
    EV.append(e); return e
TRIM = {"contrabass_pizz": .62, "cellos": .9, "cellos_pizz": .55, "violas_pizz": 1.4, "violins_pizz": 1.4, "harp": 1.0,   # per-instrument
        "glockenspiel": .65, "clarinet": .32, "flute": .40, "recorder": .45, "ocarina": .6, "marimba": 1.45,           # level trims (a note
        "vibraphone": 2.2, "vibraphone_bowed": 1.2, "mbira": 1.5, "upright": 2.4, "shaker": 1.0, "hand_chimes": .9}   # at vel .4 ~ -34 dB)
SUSTAIN = {"cellos", "clarinet", "flute", "recorder", "ocarina", "vibraphone_bowed"}
def midi_of(e): return e["pitch"] if isinstance(e["pitch"], (int, float)) else None
def high(e): m = midi_of(e); return m is None or m > 46.9       # above 120 Hz (or unpitched): counts for density
def pl(t, inst, m, vel, pan, role="pulse", prio=3, ring=None, stem="bed"):
    """a pluck: inside the no-sustain zone it is damped to 0.6 s in all; above or below it may ring"""
    if m is None: return None
    if ZL <= m <= ZH: return E(t, inst, m, .38, vel, pan, role, prio, stem=stem, release=.2)
    return E(t, inst, m, ring or .9, vel, pan, role, prio, stem=stem,
             release=.6 if inst in ("harp", "glockenspiel", "vibraphone", "mbira") else None)

FIGS = [  # written 2-bar figures: (beat 0-7, chord-tone step); contours, not a random walk
    [(0, 0), (1, 1), (2, 2), (3, 3), (4, 2), (5, 3), (6, 4), (7, 3)],      # rise
    [(0, 0), (1, 2), (2, 3), (3, 4), (4, 3), (5, 2), (6, 1), (7, 2)],      # arch
    [(0, 4), (1, 3), (2, 2), (3, 1), (4, 2), (5, 1), (6, 0)],              # fall, a breath on 8
    [(0, 2), (1, 1), (2, 2), (3, 3), (4, 2), (6, 1), (7, 0)],              # turn
    [(0, 0), (2, 2), (3, 1), (4, 0), (6, 3), (7, 2)],                      # sway
    [(0, 1), (1, 2), (2, 4), (4, 3), (5, 2), (6, 1), (7, 2)],              # call
]
class Grid:
    def __init__(self, t0, bpm, t_end, chap):
        self.t0, self.B, self.t_end, self.chap = t0, 60.0 / bpm, t_end, chap
        self.bar = 4 * self.B; n = max(0, int(math.ceil((t_end - 0.05 - t0) / self.B)))
        self.beats = [(t0 + i * self.B, i) for i in range(n)]
        self.order = list(rng.permutation(len(FIGS))); self.last = 67; self.base = None
GRIDS = []
for k in CHAPS:
    t0 = FIRST if k == 0 else CH0[k] + 60 / CHBPM[k]
    cuts = [(h["start"], h["end"]) for h in HOLDS if CH0[k] <= h["start"] < CH1[k]]
    a = t0
    for h0, h1 in cuts:
        if h0 > a + 1: GRIDS.append(Grid(a, CHBPM[k], h0, k))
        a = h1                                          # the chapter's grid returns at the first word after the hold
    GRIDS.append(Grid(a, CHBPM[k], CH1[k], k))
GRIDS = [g for g in GRIDS if g.beats]
def grid_at(t): return next((g for g in GRIDS if g.t0 - 1e-6 <= t < g.t_end), None)
def first_db(t):
    g = grid_at(t)
    if g is None: return None
    return next((b for b, i in g.beats if i % 4 == 0 and b >= t - 1e-6), None)
DOWNBEATS = sorted(b for g in GRIDS for b, i in g.beats if i % 4 == 0)
def next_db(t): i = bisect.bisect_left(DOWNBEATS, t); return DOWNBEATS[i] if i < len(DOWNBEATS) else t + 3

# chord per bar: a change every 2-4 bars (2 for doubt), restart at section entries, forced change after a stamp
def chord_timeline(g):
    out, cur, idx, left = {}, None, 0, 0
    for t, i in g.beats:
        if i % 4: continue
        s = sec_at(t + 1e-3); bar = i // 4
        forced = any(t - g.bar < st + 0.3 <= t for st in STAMPS)
        if s is not cur:
            cur, idx = s, 0; left = 2 if s["function"] == "problem" else int(rng.choice([2, 3, 4], p=[.5, .3, .2]))
        else:
            left -= 1
            if left <= 0 or forced:
                idx += 1; left = 2 if s["function"] == "problem" else int(rng.choice([2, 3, 4], p=[.5, .3, .2]))
        out[bar] = s["chords"][idx % len(s["chords"])]
    return out
for g in GRIDS: g.chords = chord_timeline(g)
# cross-relations: across key changes, replace the outgoing bar by a pivot chord of its own key
BARS = sorted(((g.t0 + bar * g.bar, g, bar) for g in GRIDS for bar in g.chords), key=lambda x: x[0])
for (t1, g1, b1), (t2, g2, b2) in zip(BARS, BARS[1:]):
    c1, c2 = g1.chords[b1], g2.chords[b2]
    if cross(c1, c2):
        p = pivot(c1.key, c2)
        if p is not None: g1.chords[b1] = p; bump("pivot chord: cross-relation")
def chord_at(t):
    g = grid_at(t)
    if g is None: return sec_at(t)["chords"][0]
    return g.chords.get(int((t - g.t0 + 1e-6) // g.bar)) or sec_at(t)["chords"][0]
def orch(t, s): return ORCH[(s["chapter"] + int(max(0, t - CH0[s["chapter"]]) // 75)) % len(ORCH)]

M1WIN, M1LOG = [], []
def in_m1(t): return any(a <= t < b for a, b in M1WIN)

# ---------------------------------------------------------------- the bed (layers) ---------------------------------------
def energy_at(t, s):
    e = s["energy"]
    return min(e, 3) if drop_at(t, ("thin",)) else e
def lay(name, t, bi, bar, ch, s, g, newchord):
    o = orch(t, s); sp = in_speech(t)
    if name in ("bass", "walk", "bass1"):
        if bi == 0: E(t, "contrabass_pizz", broot(ch), 1.1, .5, 0, "bass", 5, release=.3)
        elif bi == 2 and name != "bass1": E(t, "contrabass_pizz", bfifth(ch), 1.1, .46, 0, "bass", 5, release=.3)
        elif bi == 3 and name == "walk" and rng.random() < .35:
            E(t, "contrabass_pizz", place(ch.pcs[1], 33, 45, broot(ch)), .6, .4, 0, "bass", 4, release=.2)
    elif name == "pulse":
        if in_m1(t): return
        inst = o["pulse"]; u = bar // 2; fig = FIGS[g.order[u % len(FIGS)]]; inv = (u // len(FIGS)) % 2 == 1
        pos = (bar % 2) * 4 + bi; st = [k for b, k in fig if b == pos]
        mx = max(k for _, k in fig); ts = tones(ch, *irange(inst, *MID))
        if pos == 0 or g.base is None:                 # voice-lead: the figure starts next to the last note
            near = min(range(len(ts)), key=lambda j: abs(ts[j] - g.last)); g.base = int(np.clip(near - 1, 0, max(0, len(ts) - 1 - mx)))
        if not st or (sp and pos % 2): return          # under speech: half of the figure
        k_ = mx - st[0] if inv else st[0]; m = ts[min(len(ts) - 1, g.base + k_)]; g.last = m
        vel = .42 * (1.08 if pos in (0, 4) else 1.0)
        if sp and ZL <= m <= ZH:                       # under speech: an octave above the zone, or softer
            if m + 12 <= irange(inst, 0, UP_HI + 2)[1]: m += 12
            else: vel *= .6
        pl(t, inst, m, vel, -.3 if inst == "marimba" else .3)
    elif name == "colour" and bi == 0 and (bar % 2 == 0 or s["energy"] >= 7):
        inst = o["colour"]; lo, hi = irange(inst, UP_LO + 2, UP_LO + 14)
        target = lo + [2, 5, 8, 4][(bar // 2) % 4]     # a slow contour over 8 bars
        ts = tones(ch, lo, hi)
        if ts: pl(t, inst, min(ts, key=lambda m: abs(m - target)), .38, .3, "colour", 4, ring=1.6)
    elif name == "pad" and newchord and PAD:
        E(t, "cellos", place(ch.root, *PAD), 2 * g.bar - .3, .26, -.1, "sus", 6, attack=.8, release=.6)
    elif name == "bowed" and newchord:
        lo = max(UP_LO, 76) if UP_LO <= 83 else UP_LO
        for q, p in enumerate(sorted({place(ch.pcs[0], lo, lo + 8), place(ch.pcs[2], lo, lo + 8)})):
            E(t + .05, "vibraphone_bowed", p, 2 * g.bar - .6, .30 * (1 - .06 * q), .2 - .4 * q, "sus", 6, stem="pad", attack=.6, release=.9)
    elif name == "shaker" and bi in (1, 3):
        E(t, "shaker", "down" if bi == 1 else "up", None, .085, .4, "pulse", 2)
    elif name == "sparkle" and bi == 0 and bar % 4 == 3 and not overlaps_speech(t - .1, t + 1.2):
        ts = tones(ch, 86, 98)
        if ts: pl(t, "glockenspiel", ts[(bar // 4) % len(ts)], .32, .35, "colour", 4, ring=1.2, stem="acc")
    elif name == "root5" and bi in (0, 2):
        inst = DATA_ROT[int(max(0, t - s["start"]) // 40) % len(DATA_ROT)]
        lo, hi = irange(inst, UP_LO + 2, UP_LO + 13); r = place(ch.root, lo, hi)
        p = r if bi == 0 else (r + 7 if r + 7 <= hi else r - 5)
        pl(t, inst, p, .38, .3 if bi else -.3, "colour", 4, ring=1.4)
    elif name == "mbira" and bi == 3 and bar % 2 == 1:
        k = int(max(0, t - s["start"]) // g.bar); lo = min(UP_LO + 2 + k, UP_HI - 6)
        ts = tones(ch, *irange("mbira", lo, lo + 9))
        if ts: pl(t, "mbira", ts[0], .4, -.45, "colour", 4)
    elif name == "pizz" and bi == 1:
        ts = tones(ch, *irange("violins_pizz", UP_LO, UP_LO + 9))
        if ts: pl(t, "violins_pizz", ts[bar % len(ts)], .36, .3)

# ---------------------------------------------------------------- motifs -------------------------------------------------
M1_STEPS, M1_BEATS, M1_LEN = [0, 1, 2, 3, 4, 3], [0, 1.5, 2, 4, 7, 8], [1.5, .5, 2, 3, 1, 6]   # 1 2 3 5 6 5, 4 bars
def m1_pitches(K, tonic):
    off = [(p - K["tonic"]) % 12 for p in K["penta"]]; return [tonic + off[d] for d in M1_STEPS]
def m1(t0, B, K, near, insts, vel, legato=False, n=6, pans=(-.3, .3), label=""):
    if t0 is None: return
    tonic = place(K["tonic"], near - 6, near + 6, near); ps = m1_pitches(K, tonic)
    for q, (b, p) in enumerate(list(zip(M1_BEATS, ps))[:n]):
        L = M1_LEN[q] * B; inst = insts[q % len(insts)]
        if legato: E(t0 + b * B, inst, p, L * .93, vel, pans[0], "mel", 8, stem="acc", attack=.04, release=.25)
        else: pl(t0 + b * B, inst, p, vel * (1.08 if q == 5 else 1), pans[q % 2], "mel", 8, ring=min(2.5, L), stem="acc")
    M1WIN.append((t0 - .05, t0 + (M1_BEATS[n - 1] + 1) * B)); M1LOG.append((t0, tuple(insts[:n]), label))
LADDER = [LADDER_ROOT + o for o in (0, 2, 4, 7, 9, 12, 14, 16, 19)]
M2WIN = []
def m2(t0, n, step=.5, vel=.3):
    for j in range(n):
        last = j == n - 1
        E(t0 + step * j, "glockenspiel", LADDER[j], 1.2 if last else .7, vel * (1.5 if last else 1), .25 - .05 * j, "m2", 10,
          stem="acc", release=1.4 if last else .8, tag="m2")
    M2WIN.append((t0 - .01, t0 + step * (n - 1) + .5))

# ---------------------------------------------------------------- compose ------------------------------------------------
for g in GRIDS:
    for t, i in g.beats:
        s = sec_at(t + 1e-4)
        if s["function"] in ("aside", "hold") or (s["function"] == "outro" and t > LAST): continue
        bi, bar = i % 4, i // 4; ch = g.chords.get(bar)
        if ch is None: continue
        prev = g.chords.get(bar - 1)
        newchord = bi == 0 and (prev != ch or sec_at(t - g.bar + 1e-3) is not s)
        for name in s["layers"][:NLAYERS[energy_at(t, s)]]: lay(name, t, bi, bar, ch, s, g, newchord)

# M2: chapter k plays k notes (complete only at the recap and the outro; the teaser stops one short)
for k in CHAPS[1:]:
    s = next(x for x in SEC if x["chapter"] == k); n = len(LADDER) if s["function"] in ("recap", "outro") else min(k, len(LADDER) - 1)
    if s["function"] == "teaser": n = len(LADDER) - 1
    if s["function"] == "recap" and ROWS: continue      # the rows climb the ladder instead
    lk = any(v and abs(h - CH0[k]) < 2e-3 for h, v in CHAPTER_LOCK.items())   # no chime: M2 starts on the change itself
    m2(CH0[k] + ((1.0 if LADDER[0] >= 93 else CHIME_DECAY) if lk else .15), n)

def after_m2(t):
    for a_, b_ in sorted(M2WIN):
        if a_ <= t < b_ + .3: t = b_ + .3
    return t

# M1: the hook in full (hocket), a fragment in each chapter's first story, payoffs one step brighter, the recap
hook = next((s for s in SEC if s["function"] == "hook"), None)
if hook and grid_at(FIRST): m1(first_db(FIRST), grid_at(FIRST).B, hook["K"], 74, [ORCH[0]["pulse"], "harp"], .5, label="hook")
seen = set()
for s in SEC:
    g = grid_at(s["start"] + 2.5); f = s["function"]
    if g is None or f in ("aside", "hold", "outro", "cta", "hook"): continue
    if f == "payoff": m1(first_db(after_m2(s["start"] + .5)), g.B, s["K"], 88, ["glockenspiel"], .40, label="payoff")
    elif f == "recap": m1(first_db(after_m2(s["start"] + .5)), g.B, s["K"], 86, ["upright"], .44, label="recap")
    elif f in ("story", "naming") and s["chapter"] not in seen and s["chapter"] > 0:
        seen.add(s["chapter"]); o = orch(s["start"], s)
        m1(first_db(after_m2(s["start"] + 2 * g.bar)), g.B, s["K"], UP_LO + 6, [o["colour"]], .42, n=3, label="fragment")

# chapter changes: a cadence on the change (locked on a chime), an approach chord in the gap before it
for k in CHAPS[1:]:
    tc = CH0[k]; s = sec_at(tc + 1e-3); ch = s["chords"][0]; lk = any(v and abs(h - tc) < 2e-3 for h, v in CHAPTER_LOCK.items())
    E(tc, "contrabass_pizz", broot(ch), 1.6, .42, 0, "bass", 9, stem="acc", locked=lk, release=.5, tag="cad")
    E(tc, "harp", place(ch.root, 38, 46), 1.6, .32, -.2, "bass", 9, stem="acc", locked=lk, release=.8, tag="cad")
    for q, p in enumerate(tones(ch, UP_LO + 2, UP_LO + 15)[:2]):
        E(tc, "harp", p, .6, .29 - .03 * q, .3 - .15 * q, "harm", 9, stem="acc", locked=lk, release=.5, tag="cad")
    gp = [g_ for g_ in GAPS if g_[0] < tc < g_[1]]
    prev = chord_at(tc - .3)
    ap = Chord(ch.key, "5") if not cross(prev, Chord(ch.key, "5")) else pivot(prev.key, ch)
    if gp and ap is not None and sec_at(tc - .3)["function"] not in ("aside", "problem"):
        ta = max(gp[0][0] + .25, tc - 1.05)
        if tc - ta >= .45:
            E(ta, "contrabass_pizz", broot(ap), .8, .36, 0, "bass", 7, stem="acc", release=.3)
            for q, p in enumerate(tones(ap, UP_LO, UP_LO + 10)[:2]): E(ta + .03 * q, "harp", p, .5, .26, -.2 + .4 * q, "harm", 7, stem="acc", release=.3)

# naming reveals: nothing on the stamp, a harp roll on its tail (+0.3 s)
for st in STAMPS:
    if sec_at(st)["function"] in ("aside",) or drop_at(st, ("aside", "dry")): continue
    ch = chord_at(st + .3)
    lo = sorted({place(ch.root, 33, 45), place(ch.pcs[2], 38, 46)}); hi = tones(ch, UP_LO + 2, UP_LO + 15)[:2]
    for q, p in enumerate(lo + hi):
        E(st + .3 + .055 * q, "harp", p, 1.2 if p > 46 else 1.0, .38 + .02 * q, -.4 + .25 * q, "harm", 7, stem="acc", release=1.2)

# SFX cascades: the pulse goes out (lint), a held chord carries the stretch (low cello + bowed vibe above the zone)
for a, b in CASCADES:
    s = sec_at(a)
    if s["function"] in ("aside", "hold") or drop_at(a, ("aside", "dry")): continue
    ch = chord_at(a); t0 = a - .1; d = max(1.0, next_db(b + .2) - t0)
    if PAD: E(t0, "cellos", place(ch.root, *PAD), d, .22, -.1, "sus", 6, attack=.5, release=.8, tag="cascade")
    E(t0, "vibraphone_bowed", place(ch.pcs[2], max(UP_LO, 76), max(UP_LO, 76) + 8), d, .24, .2, "sus", 6, stem="pad",
      attack=.5, release=.9, tag="cascade")                  # a low sustain + one soft high note (brief: under speech)

# gap phrases: every pause of 1.5-6 s gets a short composed answer from the theme's pentatonic
PHRASES = [[(0, 2, 1), (1, 4, 2)], [(0, 4, 1), (1, 2, 1), (2, 0, 2)], [(0, 0, 1), (1, 1, 1), (2, 2, 2)],
           [(0, 4, 1), (1, 5, 1), (2, 4, 2)], [(0, 2, 1), (1, 1, 1), (2, 0, 1), (3, -1, 2)], [(0, 0, 1), (1, 2, 1), (2, 4, 1), (3, 5, 2)]]
REG_W = {"clarinet": (62, 77), "flute": (72, 86), "recorder": (72, 86), "ocarina": (70, 84), "marimba": (72, 84)}
pi = int(rng.integers(len(PHRASES)))
for a, b in GAPS:
    if not 1.5 <= b - a <= 6 or a >= LAST: continue
    s = sec_at(a + .1)
    if s["function"] in ("aside", "hold", "outro") or drop_at(a + .1, ("aside", "dry")) or drop_at(b - .1, ("aside", "dry")): continue
    end = b - .25
    for tc in CH0.values():
        if a < tc < b: end = min(end, tc - .1)          # lead into the chapter change, never across it
    if any(x < end and y > a for x, y in M2WIN): continue
    g = grid_at(a + .3)
    if g is None: continue
    h = g.B / 2; t0 = g.t0 + math.ceil((a + .25 - g.t0) / h) * h
    inst = orch(a, s)["gap"]; lo, hi = irange(inst, *REG_W.get(inst, (64, 79)))
    ch = chord_at(t0); K = s["K"]
    la, lb = irange(inst, lo - 5, hi + 5); lad = [m for m in range(la, lb + 1) if m % 12 in K["penta"]]
    ph = PHRASES[pi % len(PHRASES)]; pi += 1 + int(rng.integers(2))
    start = min(range(len(lad)), key=lambda j: abs(lad[j] - place(ch.pcs[int(rng.integers(2))], lo, hi, (lo + hi) // 2)))
    notes = []
    for q, (o_, stp, ln) in enumerate(ph):
        tn = t0 + o_ * h; L = ln * h
        if tn + min(L, .35) > end: break
        m = lad[int(np.clip(start + stp, 0, len(lad) - 1))]
        if q == len(ph) - 1: m = min(tones(ch, m - 4, m + 4) or [m], key=lambda x: abs(x - m))   # end on a chord tone
        notes.append((tn, m, min(L, end - tn)))
    if len(notes) < 2: continue
    for q, (tn, m, L) in enumerate(notes):
        if inst in SUSTAIN: E(tn, inst, m, L * .92, .38 + .02 * q, .15, "mel", 8, stem="acc", attack=.04, release=.25, tag="gap")
        else: pl(tn, inst, m, .4, .15, "mel", 8, ring=1.0, stem="acc")
    bump("gap phrases")

# term-wall rows (locked): low root + a high chord tone + the next ladder note, +1 dB per row
for q, tr in enumerate(ROWS):
    s = sec_at(tr); ch = s["chords"][q % len(s["chords"])]; gd = 10 ** (q / 20); li = min(len(LADDER) - 1, len(LADDER) - len(ROWS) + q)
    E(tr, "contrabass_pizz", broot(ch), 1.8, .5 * gd, 0, "bass", 10, stem="acc", locked=True, release=.5, tag="row")
    E(tr, "harp", place(ch.root, 38, 46), 2.0, .42 * gd, -.2, "bass", 10, stem="acc", locked=True, release=1.0, tag="row")
    E(tr, "glockenspiel", LADDER[li], 1.4, .36 * gd, -.3, "m2", 10, stem="acc", locked=True, release=1.2, tag="row")
    if q == 0 and len(LADDER) > len(ROWS):            # the lower rungs climb into the first row
        m2(tr - .5 * (len(LADDER) - len(ROWS)) - .1, len(LADDER) - len(ROWS), .5, .28)

# silence-only holds: the grid takes the slips' period, downbeats locked on them; clarinet sings M1 over walking pizz
for hs in HOLDS:
    sl = sorted(h["t"] for h in HITS if h["kind"] == "hold-bar" and hs["start"] <= h["t"] <= hs["end"])
    g = grid_at(hs["start"] - .5) or GRIDS[0]
    bar = float(np.median(np.diff(sl))) if len(sl) >= 2 else g.bar
    db = sl if len(sl) >= 2 else [hs["start"] + .3 + j * bar for j in range(int((hs["end"] - hs["start"] - .3) // bar))]
    db = [d for d in db if d < hs["end"] - .5]
    if not db: continue
    K = hs["K"]; plan = [Chord(K, c) for c in hs["prog"]]; bl = bar / 4
    for j, d0 in enumerate(db):
        ch = plan[j % len(plan)] if j < len(db) - 1 else Chord(K, "5")      # a half cadence into the voice's return
        walk = [broot(ch), place(ch.pcs[1], 33, 47, broot(ch) + 4), place(ch.pcs[2], 33, 47, broot(ch) + 7), place(ch.pcs[1], 33, 47, broot(ch) + 4)]
        for q in range(4 if j < len(db) - 1 else 1):
            E(d0 + q * bl, "contrabass_pizz", walk[q], .62, .5 if q == 0 else .42, 0, "bass", 9 if q == 0 else 6,
              locked=q == 0 and len(sl) >= 2, release=.2, tag="holdbar" if q == 0 else "")
        E(d0, "harp", place(ch.root, 38, 46), 1.4, .36, -.2, "bass", 9, stem="acc", locked=len(sl) >= 2, release=.6)
        for q, p in enumerate(tones(ch, 62, 78)[:3]): E(d0 + .03 * q, "harp", p, 1.2, .32, -.3 + .2 * q, "harm", 7, stem="acc", release=.6)
    if len(db) >= 4: m1(db[0], bl, K, 62, ["clarinet"], .4, legato=True, label="hold")

# outro: music only after the last word: M1 reprise (clarinet + harp), M2 in full, the final cadence 1.5 s before the end
outro = next((s for s in SEC if s["function"] == "outro"), None)
fin = T - 1.5; o0 = LAST + .4; B0 = 60 / CHBPM[SEC[-1]["chapter"]]; Kf = (outro or SEC[-1])["K"]
if outro and fin - o0 >= 12:
    m1(o0, B0, Kf, 62, ["clarinet"], .4, legato=True, label="outro")
    for b, p in zip(M1_BEATS, m1_pitches(Kf, place(Kf["tonic"], 56, 68, 62))): E(o0 + b * B0, "harp", p + 12, 1.2, .32, -.3, "harm", 8, stem="acc", release=1.0)
    for q, (bb, c) in enumerate(((0, "1"), (4, "4"), (8, "6"), (12, "4"))):
        ch = Chord(Kf, c); E(o0 + bb * B0, "contrabass_pizz", broot(ch), 1.6, .44, 0, "bass", 7, stem="acc", release=.4)
    m2s = max(o0 + 15 * B0, fin - 5.0)
    if m2s + 4.5 <= fin: m2(m2s, len(LADDER), .5, .3)
elif outro and fin - o0 >= 5: m2(o0, min(len(LADDER), int((fin - o0 - .5) / .5)), .5, .3)
chf = Chord(Kf, "1")
E(fin, "contrabass_pizz", broot(chf), 1.4, .5, 0, "bass", 10, stem="acc", release=.3, tag="final")
if PAD: E(fin, "cellos", place(chf.root, *PAD), 1.1, .28, -.1, "sus", 10, stem="acc", attack=.15, release=.3)
for q, p in enumerate(sorted(set(tones(chf, 50, 74)[::2] + [place(chf.root, 76, 88)]))):
    E(fin + .04 * q, "harp", p, 1.2, .32 + .015 * q, -.4 + .1 * q, "harm", 10, stem="acc", release=.4)

# ---------------------------------------------------------------- lint ---------------------------------------------------
PITCH_WIN = []
for c in CUES:
    if c["sfx"] in PITCHED_SFX:
        K = sec_at(c["t"])["K"]
        if any(int(m) % 12 not in K["sc"] for m in PITCHED_SFX[c["sfx"]]): PITCH_WIN.append((c["t"] - .5, c["t"] + .5))
def lint(evs):
    out = []
    for e in evs:                                       # dropouts
        t = e["t"]; d = drop_at(t + .2, ("aside",)) or drop_at(t, ("aside",))
        if d: bump("drop: aside"); continue
        g = grid_at(t) or GRIDS[0]
        dd = next((x for x in DROPS if x["kind"] == "dry" and x["start"] - 2 * g.bar <= t < x["end"]), None)
        if dd and not (e["role"] == "bass" and t < dd["start"] - g.bar): bump("drop: dry line"); continue
        out.append(e)
    evs, out = out, []
    BO = [(a, b, True) for a, b in PITCH_WIN] + [(h - .5, next_db(h + .35), False) for h in ERRORS]
    CW = [(a - .1, next_db(b + .2)) for a, b in CASCADES]
    for e in evs:                                       # bass-only windows, pulse out in cascades
        t = e["t"]; rel = e["release"] if e["release"] is not None else (S.load(e["inst"]).rel if e["inst"] != "shaker" else .2)
        end = t + (e["dur"] or .3) + rel
        if e["role"] != "bass" and not e["locked"]:
            w = next((w for w in BO if t < w[1] and end > w[0]), None)
            if w:
                if t >= w[0]: bump("drop: bass-only window"); continue
                room_ = w[0] - t - .05
                if room_ < .35: bump("drop: bass-only window"); continue
                e["release"] = min(rel, .3); e["dur"] = max(.05, room_ - e["release"]); bump("trim: bass-only window")
        if e["role"] in ("pulse", "bass") and not e["locked"] and e["stem"] == "bed" and any(a <= t < b for a, b in CW):
            bump("drop: pulse in cascade"); continue
        out.append(e)
    evs, out = out, []
    for e in evs:                                       # avoid-class SFX: no onset within +-80 ms
        if e["locked"] or not avoid_hits(e["t"]): out.append(e); continue
        t = e["t"]; h = avoid_hits(t); moved = None
        if max(h) + .085 - t <= .2 and not avoid_hits(max(h) + .085): moved = max(h) + .085
        elif t - (min(h) - .085) <= .12 and not avoid_hits(min(h) - .085): moved = min(h) - .085
        else: moved = next((t + dt for dt in np.arange(.09, .26, .01) if not avoid_hits(t + dt)), None)
        if moved is None: bump("drop: avoid SFX"); continue
        e["t"] = float(moved); bump("nudge: avoid SFX"); out.append(e)
    evs = sorted(out, key=lambda e: e["t"])
    for e in evs:                                       # registers under speech
        m = midi_of(e)
        if m is None or e["locked"] or not in_speech(e["t"]) or e["role"] in ("bass", "m2", "sus"): continue
        if m > UP_HI and e["role"] in ("pulse", "harm", "colour"):
            while m > UP_HI and m - 12 >= UP_LO: m -= 12
            if m != e["pitch"]: e["pitch"] = m; bump("octave down: register cap under speech")
        elif ZL <= m <= ZH and e["role"] in ("pulse", "colour", "harm") and e["inst"] not in SUSTAIN:
            if m + 12 <= irange(e["inst"], 0, UP_HI + 2)[1]: e["pitch"] = m + 12; bump("octave up: mid pluck under speech")
            elif e["vel"] > .3: e["vel"] *= .6; bump("softer: mid pluck under speech")
    out = []
    for e in evs:                                       # the no-sustain zone over speech
        m = midi_of(e)
        if m is not None and ZL <= m <= ZH:
            t = e["t"]; rel = e["release"] if e["release"] is not None else S.load(e["inst"]).rel; end = t + e["dur"] + rel
            if e["inst"] in SUSTAIN and overlaps_speech(t, end):
                room_ = (next_speech_start(t) if not in_speech(t) else t) - t - .25
                if room_ < .3: bump("drop: sustain in zone over speech"); continue
                e["dur"] = room_; e["release"] = .25; bump("trim: sustain in zone before speech")
            elif e["dur"] + rel > .6 and overlaps_speech(t, end):
                e["dur"] = min(e["dur"], .38); e["release"] = min(rel, .6 - e["dur"]); bump("damp: ring in zone over speech")
        elif m is not None and e["inst"] == "cellos" and m > 45 and overlaps_speech(e["t"], e["t"] + e["dur"]):
            bump("drop: cello above the bass register over speech"); continue
        out.append(e)
    evs = []                                            # M2 sounds alone above 120 Hz: sustains wait for it, the rest goes
    for e in out:
        w = next(((a, b) for a, b in M2WIN if a <= e["t"] <= b), None)
        if w is None or e["role"] == "m2" or e["locked"] or not high(e): evs.append(e); continue
        if e["role"] == "sus" and e["dur"] - (w[1] - e["t"]) > 1.0:
            t2 = next((w[1] + dt for dt in np.arange(0, .3, .01) if not avoid_hits(w[1] + dt)), None)
            if t2 is not None:
                e["dur"] -= t2 - e["t"]; e["t"] = float(t2); bump("delay: sustain after M2"); evs.append(e); continue
        bump("drop: under M2")
    acc_t, final = [], []                               # density: <= 2 onsets per 1 s above 120 Hz under speech
    for e in sorted(evs, key=lambda e: (-e["prio"] - (100 if e["locked"] else 0), e["t"])):
        if not high(e) or not in_speech(e["t"]): final.append(e); continue
        t = e["t"]; j0, j1 = bisect.bisect_left(acc_t, t - 1.0), bisect.bisect_right(acc_t, t + 1.0)
        win = sorted(acc_t[j0:j1] + [t])
        if e["locked"] or all(win[q + 2] - win[q] >= 1.0 for q in range(len(win) - 2)): bisect.insort(acc_t, t); final.append(e)
        else: bump("drop: density > 2/s under speech")
    return sorted(final, key=lambda e: e["t"])
EVL = lint(EV)

def checks(evs):
    R = {}
    rl = lambda e: e["release"] if e["release"] is not None else (S.load(e["inst"]).rel if e["inst"] != "shaker" else .2)
    hs = sorted(e["t"] for e in evs if high(e) and in_speech(e["t"]))
    R["max_onsets_per_1s_under_speech"] = max((bisect.bisect_left(hs, t + 1.0) - i for i, t in enumerate(hs)), default=0)
    R["zone_sustain_over_speech"] = sum(1 for e in evs if midi_of(e) is not None and ZL <= midi_of(e) <= ZH and
                                        e["dur"] + rl(e) > .6 + 1e-6 and overlaps_speech(e["t"], e["t"] + e["dur"] + rl(e)))
    R["onsets_within_80ms_of_avoid_sfx"] = sum(1 for e in evs if not e["locked"] and avoid_hits(e["t"], .0799))
    R["shaker_max_vel"] = round(max((e["vel"] for e in evs if e["inst"] == "shaker"), default=0), 3)
    lk = [e for e in evs if e["locked"]]
    R["locked_max_err_ms"] = round(1000 * max((min(abs(e["t"] - l) for l in LOCKED) for e in lk), default=0), 3) if LOCKED else None
    R["events_in_aside"] = sum(1 for e in evs if drop_at(e["t"], ("aside",)))
    R["cross_relations"] = sum(cross(g1.chords[b1], g2.chords[b2]) for (_, g1, b1), (_, g2, b2) in zip(BARS, BARS[1:]))
    chroma = {}
    for k in CHAPS:
        h = np.zeros(12)
        for e in evs:
            m = midi_of(e)
            if m is not None and CH0[k] <= e["t"] < CH1[k]: h[int(m) % 12] += e["vel"] * min(2.0, e["dur"] or .5)
        K = max((s["K"] for s in SEC if s["chapter"] == k), key=lambda K_: sum(s["end"] - s["start"] for s in SEC if s["chapter"] == k and s["K"] == K_))
        KKM = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])     # Krumhansl-Kessler
        KKm = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        prof = KKM if K["mode"] == "major" else KKm.copy()
        if K["mode"] == "dorian": prof[[8, 9]] = prof[[9, 8]]                                       # raised 6th
        chroma[f"ch{k} {K['name']}"] = round(float(np.corrcoef(h, np.roll(prof, K["tonic"]))[0, 1]), 3) if h.any() else None
    R["chroma_corr_key_profile"] = chroma        # > 0.6 wanted per chapter
    rep = 0
    for g in GRIDS:
        blocks = {}
        for b0 in range(0, len(g.beats), 32):
            ta = g.beats[b0][0]; sig = tuple(sorted((round(e["t"] - ta, 2), e["inst"], str(e["pitch"])) for e in evs if ta <= e["t"] < ta + 8 * g.bar))
            if sig: blocks[sig] = blocks.get(sig, 0) + 1
        rep = max([rep] + list(blocks.values()))
    R["max_identical_8bar_block_count"] = rep
    R["m1_same_orchestration_within_5min"] = sum(1 for i, (t, o, _) in enumerate(M1LOG) for t2, o2, _ in M1LOG[i + 1:] if o == o2 and abs(t2 - t) < 300)
    return R
CHK = checks(EVL)
print(f"voice zone MIDI {ZL}-{ZH} ({'measured' if VP.get('measured') else 'ASSUMED'}), under-speech colour {UP_LO}-{UP_HI}; "
      f"{len(GRIDS)} grids, {len(SEC)} sections, keys " + ", ".join(sorted({s['K']['name'] for s in SEC})))
print("lint:", json.dumps(LINT)); print("checks:", json.dumps(CHK))
print(f"{len(EVL)} events after lint ({len(EV)} composed)")
if os.getenv("DRY"): sys.exit(0)

# ---------------------------------------------------------------- render -------------------------------------------------
TAIL = 6.0
def master_eq(x):
    """music bus: high-pass 35 Hz, a fixed -5 dB bell at 2.5 kHz (Q 0.8); linear, so applied per chapter before the sum"""
    x = sosfilt(butter(2, 35, "high", fs=SR, output="sos"), x, axis=0)
    A = 10 ** (-5 / 40); w0 = 2 * np.pi * 2500 / SR; al = np.sin(w0) / (2 * .8)
    b = [1 + al * A, -2 * np.cos(w0), 1 - al * A]; a = [1 + al / A, -2 * np.cos(w0), 1 - al / A]
    return lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=0)
def render_job(args):
    k, stem, c0, c1, evs = args
    S.seed(SEED * 10 + k * 3 + ("bed", "acc", "pad").index(stem))
    ev2 = [dict(t=e["t"] - c0, inst=e["inst"], pitch=e["pitch"], dur=e["dur"], vel=e["vel"], pan=e["pan"],
                gain=TRIM.get(e["inst"], 1.0), release=e["release"], attack=e["attack"]) for e in evs]
    n = c1 - c0 + TAIL
    x = S.render(ev2, dur=n, master=False) if ev2 else np.zeros((int(n * SR), 2), np.float32)
    if stem == "pad": x = sosfilt(butter(4, 1200, "low", fs=SR, output="sos"), x, axis=0).astype(np.float32)
    x = S.room(x, size=.35, mix=.25 if stem == "acc" else .18, predelay=.02, damp=.6)
    return k, stem, master_eq(x.astype(np.float64)).astype(np.float32)

def kw(x):  # K-weighting at 48 kHz (BS.1770)
    s1 = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, .73248077421585], x, axis=0)
    return lfilter([1, -2, 1], [1, -1.99004745483398, .99007225036621], s1, axis=0)

if __name__ == "__main__":
    from multiprocessing import Pool
    t_0 = time.time(); jobs = []
    for k in CHAPS:
        c0, c1 = CH0[k], CH1[k]
        for stem in ("bed", "acc", "pad"):              # bed + pad: owned by the chapter (crossfaded); accents: never cut
            jobs.append((k, stem, c0, c1, [e for e in EVL if (c0 <= e["t"] < c1 or (k == CHAPS[-1] and e["t"] >= c1)) and
                                           ("pad" if e["inst"] == "vibraphone_bowed" else e["stem"]) == stem]))
    with Pool(JOBS) as P: res = P.map(render_job, jobs, chunksize=1)
    bed = np.zeros((NS, 2), np.float32); acc = np.zeros((NS, 2), np.float32); XF = int(1.0 * SR)
    for k, stem, x in res:
        s0 = int(round(CH0[k] * SR))
        if stem in ("bed", "pad"):
            w = np.ones(len(x), np.float32)
            if k != CHAPS[-1]:                           # out over [next chapter, +1 s], equal power
                a_ = int(round(CH1[k] * SR)) - s0; w[a_:a_ + XF] = np.cos(np.linspace(0, np.pi / 2, len(w[a_:a_ + XF]))); w[a_ + XF:] = 0
            if k != CHAPS[0]: w[:XF] *= np.sin(np.linspace(0, np.pi / 2, XF)).astype(np.float32)
            x = x * w[:, None]
        e_ = min(NS, s0 + len(x)); (acc if stem == "acc" else bed)[s0:e_] += x[:e_ - s0]
    del res
    print(f"render {time.time() - t_0:.1f} s")

    # ---- section levels to the energy plan (K-weighted median of 0.4 s blocks), relative to the energy-5 bed ----
    def lev(a, b, y=None):
        i0, i1 = int(a * SR), int(b * SR)
        if i1 - i0 < int(.4 * SR): return None
        pre = min(i0, SR // 2); z = kw(((bed + acc) if y is None else y)[i0 - pre:i1].astype(np.float64))[pre:]
        blk = int(.4 * SR); nb = len(z) // blk; ms = (z[:nb * blk] ** 2).reshape(nb, blk, 2).mean(1).sum(1); ms = ms[ms > 1e-10]
        return float(np.median(10 * np.log10(ms))) if len(ms) else None   # the bed's level, not its accents
    lv = {s["id"]: lev(s["start"] + .3, min(s["end"], LAST if s["function"] != "outro" else T) - .3) for s in SEC}
    refs = [lv[s["id"]] for s in SEC if s["energy"] == 5 and s["function"] not in ("hold", "outro", "aside") and lv[s["id"]] is not None]
    if not refs: refs = [v for s in SEC for v in [lv[s["id"]]] if v is not None and s["function"] not in ("hold", "aside")]
    ref = float(np.median(refs)) if refs else -30.0
    gains = {}
    for s in SEC:
        tg = TARGET_FN.get(s["function"], TARGET.get(s["energy"]))
        gains[s["id"]] = 0.0 if tg is None or lv[s["id"]] is None else float(np.clip(tg - (lv[s["id"]] - ref), -6, 6))
    tf = np.arange(0, T, .01); tt = np.array([s["start"] for s in SEC])
    gdb = np.array([gains[s["id"]] for s in SEC])[np.clip(np.searchsorted(tt, tf, "right") - 1, 0, len(SEC) - 1)]
    k_ = int(1.5 / .01); gdb = np.convolve(np.pad(gdb, k_, mode="edge"), np.ones(k_) / k_, "same")[k_:-k_]   # 1.5 s ramps
    # ---- shaping: asides, dry lines, thin stretches, the start and the end ----
    def ramp(a, b, up): r = np.clip((tf - a) / (b - a), 0, 1); return r if up else 1 - r
    sh = np.ones_like(tf)
    for d in DROPS:
        a, b = d["start"], d["end"]
        if d["kind"] == "aside":
            m = np.where((tf >= a) & (tf < b), ramp(a, a + .5, False), 1); m = np.where((tf >= b) & (tf < b + .8), ramp(b, b + .8, True), m)
        elif d["kind"] == "dry":
            g = grid_at(a) or GRIDS[0]; p = a - 2 * g.bar
            m = np.where((tf >= p) & (tf < a), ramp(p, a, False) ** 2, 1); m = np.where((tf >= a) & (tf < b), 0, m)
            m = np.where((tf >= b) & (tf < b + .3), ramp(b, b + .3, True), m)
        else:
            m = np.where((tf >= a) & (tf < b), 10 ** (-3 / 20), 1)
            m = np.convolve(np.pad(m, 50, mode="edge"), np.ones(100) / 100, "same")[50:-50]
        sh = np.minimum(sh, m)
    sh = np.where(tf < FIRST - .05, 0, sh); sh = np.where(tf >= T - .9, np.minimum(sh, ramp(T - .9, T, False) ** 1.5), sh)
    g_ = 10 ** (gdb / 20) * sh
    for i0 in range(0, NS, 10 * SR):
        i1 = min(NS, i0 + 10 * SR); gs = np.interp(np.arange(i0, i1) / SR, tf, g_).astype(np.float32)[:, None]
        bed[i0:i1] *= gs; acc[i0:i1] *= gs
    mix = bed + acc
    pk = float(np.abs(mix).max()) or 1.0; norm = np.float32(10 ** (-1.0 / 20) / pk)    # sample peak -1 dBFS; audio.py sets the level
    mix *= norm; bed *= norm; acc *= norm
    assert len(mix) == NS
    # ---- reference level for audio.py, loudness range (EBU-style, 3 s windows) without the dropouts ----
    rs = [s for s in SEC if s["energy"] == 5 and s["function"] not in ("hold", "outro", "aside")] or [s for s in SEC if s["function"] not in ("hold", "aside")]
    seg = np.concatenate([mix[int(s["start"] * SR):int(s["end"] * SR)] for s in rs]); ref_rms = float(np.sqrt(np.mean(seg ** 2)))
    z = kw(mix.astype(np.float64)); p = (z ** 2).sum(1); cs = np.concatenate([[0], np.cumsum(p)])
    st = np.arange(0, NS - 3 * SR, SR // 10); stl = -0.691 + 10 * np.log10((cs[st + 3 * SR] - cs[st]) / (3 * SR) + 1e-20)
    def shaped(a, b):                                   # a 3 s window touching a dropout (or a dry line's 2-bar lead-in)
        return any(d["start"] - (2 * (grid_at(d["start"]) or GRIDS[0]).bar if d["kind"] == "dry" else 0) < b and d["end"] + .8 > a for d in DROPS)
    keep = np.array([not shaped(t_, t_ + 3) and FIRST <= t_ and t_ + 3 <= LAST for t_ in st / SR]) & (stl > -70)
    lra = None
    if keep.sum() > 10:
        v = stl[keep]; v = v[v > 10 * np.log10(np.mean(10 ** (v / 10))) - 20]; lra = round(float(np.percentile(v, 95) - np.percentile(v, 10)), 1)
    MUS.mkdir(parents=True, exist_ok=True)
    sf.write(MUS / "score.wav", mix, SR, subtype="PCM_24")
    sf.write(MUS / "music_bed.wav", bed, SR, subtype="PCM_24"); sf.write(MUS / "music_accents.wav", acc, SR, subtype="PCM_24")
    used = sorted({e["inst"] for e in EVL}); lic = {n: S.LIC[S._lic(n)] for n in used}
    assert all(lic[n][1] == "CC0 1.0" for n in used), "non-CC0 instrument used"
    lines = ["Music: original score composed in code (work/music.py), rendered with the Lemo-Opuscar sampler (MIT,",
             "github.com/lemomo-ai/lemo-opuscar) from CC0 sample libraries.", "", "Instruments and sources:"]
    lines += [f"  {n:18s} {lic[n][0]}  [{lic[n][1]}]  ({S.REG[n]['desc']})" for n in used]
    lines += ["", "Credit lines:"] + ["  " + l for l in S.credits(used)]
    (MUS / "credits.txt").write_text("\n".join(lines) + "\n")
    meta = dict(seed=SEED, total=T, samples=NS, ref_rms=ref_rms, lra_lu=lra, norm_db=round(float(20 * np.log10(norm)), 2),
                voice_zone=[ZL, ZH], voice_measured=bool(VP.get("measured")), instruments=used, lint=LINT, checks=CHK, events=len(EVL),
                sections=[dict(id=s["id"], function=s["function"], start=s["start"], end=s["end"], key=s["K"]["name"],
                               bpm=CHBPM[s["chapter"]], energy=s["energy"], chords=[str(c) for c in s["chords"]], gain_db=round(gains[s["id"]], 2))
                          for s in SEC])
    (MUS / "score_meta.json").write_text(json.dumps(meta, indent=1))
    print(f"wrote work/music/score.wav ({NS / SR:.2f} s, {NS} samples), LRA {lra} LU (<= 6 wanted), credits.txt, score_meta.json")
