"""make_cuemap.py: the music's cue map -> work/music/cuemap.json, from timeline.json (+ work/audio/cues.json when audio.py
has run). Edit the CONFIG block for your video, re-run, then run work/music.py.

Schema (music-diorama.md sections 4-5):
  total                     the video length (s)
  sections[]  {id, start, end, function, energy, notes, chapter, scene[, key, bpm]}
              one per scene (a scene change = a chapter change, cadence + 1 s crossfade), split further by SPLITS and
              carved by asides, holds and calls to action. function is one of the recipe names below; energy 0-10.
  hits[]      {t, kind, note[, sfx_class, end]}: start, chapter, naming (stamps), error, cascade (>= 4 SFX <= 0.3 s
              apart: pulse out), row (term-wall rows, locked), hold-bar (slips in a silence-only hold, locked), cta,
              end-screen, final (the last cadence, 1.5 s before the end)
  dropouts[]  {start, end, kind, why}: aside (music off), dry (a line said into silence), thin (one soft layer)
Recipes (section functions): hook, story, naming, payoff, problem, data, recap, teaser, cta, outro, hold, aside.
Hand edits to cuemap.json are lost on the next run: put them in CONFIG instead."""
import json, pathlib

# ================================ CONFIG (per video) ================================================================
# Scene id -> function. Missing scenes: the first is "hook", OUTRO_SCENE "outro", the rest "story".
SCENE_FUNCTION = {"s1_reading": "hook", "s2_average": "story", "s3_shared": "problem", "s4_takeaway": "payoff"}
SPLITS = {"A3": "naming"}      # beat id -> function: a new section from that beat on (inside its scene, no cadence)
ASIDE_BEATS = []               # beats where the narrator steps out of the story: music off (out 0.5 s, back 0.8 s after)
DRY_BEATS = []                 # lines said into silence: music thins over 2 bars before, < -40 dBFS while they are said
THIN = []                      # (first beat, last beat): dense numbers on screen, one soft layer
HOLDS = []                     # beats followed by a silence-only hold (their "pause"/"hold"): music carries it
CTA_BEATS = []                 # the subscribe ask: two light pizz bars that bridge into the next key
OUTRO_SCENE = None             # the end-screen scene (music only after its last word, cadence 1.5 s before the end)
TEASER_SCENE = None            # next-episode teaser: dorian, open end
RECAP_SCENE = None             # term wall / recap: fullest texture, a ladder note per row
KEYS = {}                      # section id -> key ("D", "G", "B dorian", ...) to override music.py's choice
BPM = {}                       # section id -> bpm (66-80 under speech)
ENERGY = {"hook": 6, "story": 4, "naming": 5, "payoff": 7, "problem": 4, "data": 3, "recap": 8, "teaser": 5,
          "cta": 5, "outro": 5, "hold": 6, "aside": 0}
ENERGY_OVERRIDE = {}           # section id -> energy
# SFX names in work/audio/cues.json (audio.py's table; automatic ones start with "auto ")
CHAPTER_SFX = ("rung chime", "chapter chime")      # a chime on each scene change: the cadence locks onto it
STAMP_SFX = ("stamp", "auto stamp")
ERROR_SFX = ("thunk", "bonk", "auto cross", "rung cracks")
ROW_SFX = ("wall row",)
HOLD_SLIP_SFX = ("auto slip", "slip")
CHAPTER_LEAD = 1.0             # a scene's chapter change sits this long before its first word (timeline.py SCENE_GAP)
# =====================================================================================================================

ROOT = pathlib.Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "timeline.json").read_text())
CF = ROOT / "work" / "audio" / "cues.json"
CUES = json.loads(CF.read_text()) if CF.exists() else []
T = TL["total"]; BEATS = TL["beats"]; BI = {b["id"]: i for i, b in enumerate(BEATS)}
for name, ids in (("SPLITS", list(SPLITS)), ("ASIDE_BEATS", ASIDE_BEATS), ("DRY_BEATS", DRY_BEATS), ("HOLDS", HOLDS),
                  ("CTA_BEATS", CTA_BEATS), ("THIN", [i for p in THIN for i in p])):
    bad = [i for i in ids if i not in BI]
    if bad: raise SystemExit(f"{name}: unknown beat ids {bad} (timeline.json has {', '.join(BI)})")

def nxt_start(bid):
    i = BI[bid]; return BEATS[i + 1]["start"] if i + 1 < len(BEATS) else T
def sfx(names): return sorted(c["t"] for c in CUES if c["sfx"] in names)

# ---------------- chapters: one per scene ----------------
scenes = list(dict.fromkeys(b["scene"] for b in BEATS))
chimes = sfx(CHAPTER_SFX)
chap = []                                              # (t, scene, locked)
for k, sc in enumerate(scenes):
    first = next(b for b in BEATS if b["scene"] == sc)
    if k == 0: chap.append((0.0, sc, False)); continue
    prev_end = BEATS[BI[first["id"]] - 1]["end"]
    t = max(prev_end + 0.1, first["start"] - CHAPTER_LEAD)
    near = [c for c in chimes if t - 1.5 <= c <= first["start"]]
    chap.append((min(near, key=lambda c: abs(c - t)), sc, True) if near else (round(t, 3), sc, False))

def func_of(sc, k):
    if sc in SCENE_FUNCTION: return SCENE_FUNCTION[sc]
    if sc == OUTRO_SCENE: return "outro"
    if sc == TEASER_SCENE: return "teaser"
    if sc == RECAP_SCENE: return "recap"
    return "hook" if k == 0 else "story"

# base sections: chapters, then splits inside them
cuts = [(t, func_of(sc, k), sc, k, f"{sc}") for k, (t, sc, _) in enumerate(chap)]
for bid, fn in SPLITS.items():
    b = BEATS[BI[bid]]; k = scenes.index(b["scene"]); prev = BEATS[BI[bid] - 1]["end"] if BI[bid] else 0
    cuts.append((round(max(prev + 0.05, b["start"] - 0.3), 3), fn, b["scene"], k, f"{b['scene']}.{bid}"))
cuts.sort()
secs = [dict(id=i, start=t, end=None, function=fn, scene=sc, chapter=k) for t, fn, sc, k, i in cuts]
for i, s in enumerate(secs): s["end"] = secs[i + 1]["start"] if i + 1 < len(secs) else T

def carve(a, b, fn, sid):
    """insert [a, b) with function fn; the section it cuts resumes after it (same function, id + '.after')"""
    global secs
    out = []
    for s in secs:
        if s["end"] <= a or s["start"] >= b: out.append(s); continue
        if s["start"] < a: out.append(dict(s, end=a))
        if not any(o["id"] == sid for o in out): out.append(dict(s, id=sid, start=a, end=b, function=fn))
        if s["end"] > b: out.append(dict(s, id=s["id"] + (".after" if s["start"] < a else ""), start=b))
    secs = out

drops, hits = [], []
for bid in ASIDE_BEATS:
    b = BEATS[BI[bid]]; a0, a1 = round(b["start"] - 0.1, 3), round(nxt_start(bid), 3)
    carve(a0, a1, "aside", f"{b['scene']}.aside.{bid}")
    drops.append(dict(start=a0, end=a1, kind="aside", why=f"aside {bid}: out within 0.5 s, back 0.8 s after the next beat starts"))
for bid in HOLDS:
    b = BEATS[BI[bid]]; h0, h1 = round(b["end"] + 0.1, 3), round(nxt_start(bid) - 0.05, 3)
    if h1 - h0 < 2: print(f"HOLDS {bid}: only {h1 - h0:.1f} s of silence after it; give the beat a 'pause' or 'hold'"); continue
    carve(h0, h1, "hold", f"{b['scene']}.hold.{bid}")
    sl = [t for t in sfx(HOLD_SLIP_SFX) if h0 <= t <= h1]
    for t in sl: hits.append(dict(t=t, kind="hold-bar", sfx_class="locked", note=f"hold after {bid}: a downbeat on this slip"))
for bid in CTA_BEATS:
    b = BEATS[BI[bid]]; c0 = round(max(b["start"] - 0.3, BEATS[BI[bid] - 1]["end"] + 0.05), 3)
    carve(c0, round(min(nxt_start(bid), b["end"] + 0.6), 3), "cta", f"{b['scene']}.cta.{bid}")
    hits.append(dict(t=b["start"], kind="cta", note=f"call to action {bid}"))
for bid in DRY_BEATS:
    b = BEATS[BI[bid]]
    drops.append(dict(start=b["start"], end=round(b["end"] + 0.5, 3), kind="dry", why=f"dry line {bid}"))
for b0, b1 in THIN:
    drops.append(dict(start=BEATS[BI[b0]]["start"], end=BEATS[BI[b1]]["end"], kind="thin", why=f"dense numbers {b0}-{b1}"))
secs = [s for s in secs if s["end"] - s["start"] > 0.05]

for s in secs:
    s["energy"] = ENERGY_OVERRIDE.get(s["id"], ENERGY.get(s["function"], 4))
    if s["id"] in KEYS: s["key"] = KEYS[s["id"]]
    if s["id"] in BPM: s["bpm"] = BPM[s["id"]]
    inb = [b["id"] for b in BEATS if s["start"] <= b["start"] < s["end"]]
    s["notes"] = f"beats {inb[0]}-{inb[-1]}" if inb else "no speech"
    s["start"], s["end"] = round(s["start"], 3), round(s["end"], 3)

# ---------------- hits ----------------
hits.append(dict(t=BEATS[0]["start"], kind="start", note="music enters with the first line"))
for k, (t, sc, locked) in enumerate(chap[1:], 1):
    hits.append(dict(t=t, kind="chapter", sfx_class="locked" if locked else "none",
                     note=f"chapter {k} ({sc}): cadence " + ("locked on the chime" if locked else "at the scene change (no chime SFX)")))
for t in sfx(STAMP_SFX): hits.append(dict(t=t, kind="naming", sfx_class="avoid", note="stamp: nothing on it, harp roll on its tail"))
for t in sfx(ERROR_SFX): hits.append(dict(t=t, kind="error", sfx_class="avoid", note="wrong answer: one layer from 0.5 s before"))
for t in sfx(ROW_SFX): hits.append(dict(t=t, kind="row", sfx_class="locked", note="term-wall row: harp chord + next ladder note"))
ts = sorted(c["t"] for c in CUES); run = ts[:1]
for t in ts[1:] + [1e9]:
    if t - run[-1] <= 0.3: run.append(t); continue
    if len(run) >= 4: hits.append(dict(t=run[0], end=run[-1], kind="cascade", sfx_class="avoid", note=f"{len(run)} SFX: pulse out, sustain only"))
    run = [t]
last = BEATS[-1]["end"]
hits.append(dict(t=last, kind="end-screen", note="last word: music only from here"))
hits.append(dict(t=round(T - 1.5, 3), kind="final", note="final cadence"))
hits.sort(key=lambda h: h["t"])

cm = dict(total=T, sections=secs, hits=hits, dropouts=sorted(drops, key=lambda d: d["start"]),
          chapters=[t for t, _, _ in chap[1:]], cues_json=CF.exists())
(ROOT / "work" / "music").mkdir(parents=True, exist_ok=True)
(ROOT / "work" / "music" / "cuemap.json").write_text(json.dumps(cm, indent=1, ensure_ascii=False))
assert all(abs(secs[i]["end"] - secs[i + 1]["start"]) < 1e-6 for i in range(len(secs) - 1))
print(f"work/music/cuemap.json: {T:.1f} s, {len(secs)} sections, {len(hits)} hits, {len(drops)} dropouts"
      + ("" if CF.exists() else " (no work/audio/cues.json yet: run audio.py first for stamps, errors, cascades, chimes)"))
for s in secs: print(f"  {s['start']:8.2f}-{s['end']:8.2f}  {s['function']:8s} e{s['energy']}  {s['id']}")
