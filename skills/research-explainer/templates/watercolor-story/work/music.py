"""Original score for the watercolor story short (timed to the bakery example's cues), from CC0 sample libraries (Lemo-Opuscar sampler: VSCO 2 CE, VCSL).
Bed on a 112 bpm grid; accents at the exact times of the on-screen hits; the bed ducks under the voice.
Writes ../assets/music.wav and credits.txt. Needs ../assets/voice.wav (assemble_voice.py) for the ducking.

Needs Lemo-Opuscar (MIT, https://github.com/lemomo-ai/lemo-opuscar) and two of its CC0 sample packs:
  git clone https://github.com/lemomo-ai/lemo-opuscar ~/lemo-opuscar
  cd ~/lemo-opuscar && sh tools/fetch.sh instruments vsco2ce && sh tools/fetch.sh instruments vcsl
Set LEMO_OPUSCAR if it is somewhere else (default ~/lemo-opuscar). Python: numpy, scipy, soundfile, soxr."""
import sys, os, json, pathlib, numpy as np, soundfile as sf
H = pathlib.Path(__file__).resolve().parent
LIB = pathlib.Path(os.getenv("LEMO_OPUSCAR", "~/lemo-opuscar")).expanduser().resolve()
if not (LIB / "core" / "audio" / "sampler.py").exists():
    sys.exit(f"Lemo-Opuscar not found at {LIB}: git clone https://github.com/lemomo-ai/lemo-opuscar there, or set "
             "LEMO_OPUSCAR to its folder; then fetch the samples: sh tools/fetch.sh instruments vsco2ce (and vcsl)")
if not (LIB / "core" / "audio" / "instruments" / "vsco2ce").is_dir() or not (LIB / "core" / "audio" / "instruments" / "vcsl").is_dir():
    sys.exit(f"sample packs missing in {LIB}/core/audio/instruments: cd {LIB} && sh tools/fetch.sh instruments vsco2ce "
             "&& sh tools/fetch.sh instruments vcsl (CC0, about 670 MB together)")
sys.path.insert(0, str(LIB)); os.chdir(LIB)   # the library is imported from its repo root
from core.audio import sampler as S
from core.audio.sfx import SR
H = pathlib.Path(__file__).resolve().parent
DUR = 40.4; B = 60 / 112; BAR = 4 * B
S.seed(1405); rng = np.random.default_rng(1405)
CH = {"D": ["D", "F#", "A"], "Em": ["E", "G", "B"], "A": ["A", "C#", "E"], "Bm": ["B", "D", "F#"], "G": ["G", "B", "D"], "F#": ["F#", "A#", "C#"]}
def n(name, octv): return f"{name}{octv}"
PLAN = {0: "D", 1: "Bm", 2: "G", 3: "A", 4: "D", 5: "G", 6: "Em", 7: "A", 8: "D", 9: "Bm", 10: "G", 11: "Bm", 12: "G", 13: "Em", 14: "F#",
        15: "Bm", 16: "D", 17: "G", 18: "D"}
bed, acc = [], []
def E(lst, t, inst, pitch, dur, vel, pan=0.0, **kw):
    if t < DUR: lst.append(dict(t=float(t), inst=inst, pitch=pitch, dur=dur, vel=vel, pan=pan, **kw))
for bar, ch in PLAN.items():
    t0 = bar * BAR; root = CH[ch][0]
    lo = 2 if root in ("D", "E", "F#", "G") else 1
    # the question / the baker and the notepad / the explanation / the draught / its floor / the end card
    sec = "hook" if t0 < 5.84 else "run" if t0 < 13.65 else "fix" if t0 < 23.6 else "problem" if t0 < 28.24 else "answer" if t0 < 34.0 else "end"
    if sec == "end" and t0 >= 37.5: continue
    for k, bt in enumerate((0, 2)):
        E(bed, t0 + bt * B, "contrabass_pizz", n(root if k == 0 else CH[ch][2], lo + (1 if k and CH[ch][2] in "ABC" else 0) if k else lo + 1), 0.5, 0.5, -0.1)
    if sec in ("run", "fix", "answer"):
        for e8 in range(8):
            if e8 % 2 == 1: E(bed, t0 + e8 * B / 2, "violins_pizz", n(CH[ch][(e8 // 2) % 3], 4), 0.25, 0.28 if sec != "answer" else 0.22, 0.35)
    if sec in ("hook", "fix", "answer", "end"):
        arp = [CH[ch][0], CH[ch][1], CH[ch][2], CH[ch][1]]
        for e8 in range(8 if sec != "hook" else 4):
            E(bed, t0 + e8 * B / 2 * (1 if sec != "hook" else 2), "marimba", n(arp[e8 % 4], 4), 0.3, 0.22 if sec != "hook" else 0.25, -0.3)
    if sec == "problem":
        E(bed, t0, "cellos_pizz", n(root, 3), 0.6, 0.32, 0.2); E(bed, t0 + 2 * B, "cellos_pizz", n(CH[ch][2], 3), 0.6, 0.28, 0.2)
        E(bed, t0, "vibraphone", n(CH[ch][1], 4), 1.6, 0.18, 0.3)
    if sec in ("fix", "run"):
        for e8 in range(8): E(bed, t0 + e8 * B / 2, "shaker", "down" if e8 % 2 == 0 else "up", None, 0.09 + 0.04 * (e8 % 2 == 0), 0.45)

A = lambda *a, **k: E(acc, *a, **k)
A(0.0, "glockenspiel", "D6", 1.0, 0.3, 0.2); A(0.0, "marimba", "D4", 0.8, 0.36, -0.2); A(0.0, "marimba", "A4", 0.8, 0.28, 0.1)
A(0.1, "xylophone", "A5", 0.3, 0.28, 0.3)                                                    # the apprentice's question
for lift, land in ((1.2, 1.85), (2.5, 3.15), (3.8, 4.45)):                                    # the bag off the scale and back
    A(lift, "shaker", "up", None, 0.12, 0.3); A(land, "woodblock", "a", None, 0.16, -0.2); A(land + 0.3, "xylophone", "E6", 0.15, 0.14, 0.3)
A(4.6, "cellos_pizz", "D3", 0.4, 0.3); A(4.85, "cellos_pizz", "B2", 0.5, 0.3)                 # head scratch: "every time?"
for k, p in enumerate(["A5", "F#5", "D5", "A4"]): A(5.84 + k * 0.06, "harp", p, 0.5, 0.2, 0.3 - 0.15 * k)       # over to the baker
for k, p in enumerate(["F#5", "A5", "D6", "A5", "F#5", "A5"]): A(6.2 + k * 0.16, "marimba", p, 0.2, 0.2, 0.2)   # he laughs
A(7.12, "xylophone", "A5", 0.3, 0.3, 0.3); A(7.12, "glockenspiel", "D6", 0.8, 0.25, -0.2)   # his bubble
A(7.35, "glockenspiel", "A6", 0.6, 0.24, 0.2)                                                # the raised finger
for k, p in enumerate(["A3", "D4", "F#4", "A4", "D5", "F#5", "A5", "D6"]): A(10.45 + k * 0.05, "harp", p, 0.5, 0.26, -0.4 + 0.1 * k)  # the notepad comes up
for k in range(12):                                                                          # twelve quick weighings
    t = 10.81 + 0.11 * k; A(t, "woodblock", "a" if k % 2 else "b", None, 0.08, 0.35)
    A(t + 0.05, "glockenspiel", ["D5", "E5", "F#5", "A5", "B5", "D6"][k % 6], 0.2, 0.07 + 0.004 * k, -0.5 + k * 0.08)
for p in ("D5", "F#5", "A5"): A(12.08, "vibraphone", p, 1.2, 0.28)                            # the average: 500.0 g
A(12.08, "glockenspiel", "D6", 1.2, 0.34, 0.2); A(12.08, "glockenspiel", "F#6", 1.2, 0.26, -0.2); A(12.08, "marimba", "D4", 0.8, 0.36)
for k, p in enumerate(["A3", "D4", "F#4", "A4", "D5", "F#5", "A5", "D6"]): A(13.65 + k * 0.05, "harp", p, 0.6, 0.28, -0.4 + 0.1 * k)  # page curl
for i in range(0, 80, 4):                                                                     # readings fly onto the line
    t = 13.95 + 0.3 + 2.3 * (i / 79) ** 0.55
    A(t, "glockenspiel", str(rng.choice(["A5", "B5", "D6", "E6", "F#6", "A6"])), 0.3, 0.1 + 0.06 * rng.random(), float(rng.uniform(-0.6, 0.6)))
A(15.55, "vibraphone", "F#5", 1.0, 0.26); A(15.55, "cellos_pizz", "D3", 0.5, 0.3)          # the typical wobble
A(17.6, "marimba", "D4", 0.6, 0.32)                                                           # averages
for t, p in ((18.24, "A5"), (20.08, "D6"), (21.92, "F#6")):                                   # rows of 4, 16, 64 readings
    A(t, "marimba", p.replace("6", "5") if p.endswith("6") else p.replace("5", "4"), 0.5, 0.34); A(t + 0.05, "glockenspiel", p, 0.6, 0.28, 0.2)
    for k in range(5): A(t + 0.04 * k, "harp", ["D5", "F#5", "A5", "D6", "F#6"][k], 0.3, 0.12, -0.3 + 0.15 * k)
for t, p in ((19.52, "E6"), (21.04, "D6"), (22.8, "B5")): A(t, "xylophone", p, 0.2, 0.26, 0.3)  # "halves", "halves again", "again"
for p in ("A4", "D5"): A(21.05, "vibraphone_bowed", p, 1.4, 0.2, 0.0, attack=0.3)            # the 1/sqrt(n) curve
A(23.6, "bass_drum", None, None, 0.35); A(23.6, "cellos_pizz", "B1", 0.8, 0.42)               # "But": the draught
A(24.4, "shaker", "roll", None, 0.18, 0.4)
for p in ("B3", "F#4"): A(24.4, "vibraphone_bowed", p, 3.4, 0.16, 0.0, attack=0.8)            # wind
for k, p in enumerate(["D6", "B5", "A5", "F#5", "D5", "B4"]): A(25.8 + k * 0.12, "harp", p, 0.5, 0.2, 0.3 - 0.12 * k)  # every row widens
A(26.5, "woodblock", "c", None, 0.3, -0.2)                                                    # the errors stop halving
for k, t in enumerate((29.5, 29.75, 30.0, 30.25)): A(t, "cellos_pizz", "B2", 0.4, 0.34 - 0.02 * k, 0.2)   # "never averages out"
A(31.9, "tubular_bells", "B3", 2.0, 0.24)                                                     # the floor
A(32.24, "glockenspiel", "B5", 0.8, 0.3); A(32.24, "vibraphone", "F#5", 1.0, 0.26)            # 0.18 g
A(34.05, "bass_drum", None, None, 0.42); A(34.05, "tubular_bells", "D5", 2.5, 0.32); A(34.05, "glockenspiel", "D6", 1.5, 0.34); A(34.05, "marimba", "D3", 1.0, 0.45)  # end card
for k, t in enumerate([34.16, 35.04, 35.52, 36.0, 36.64, 36.88, 37.52]): A(t, "harp", ["D5", "E5", "F#5", "A5", "B5", "D6", "F#6"][k], 0.6, 0.26, -0.3 + 0.1 * k)
A(35.9, "xylophone", "A5", 0.2, 0.2, 0.3)
for p, v in (("D2", .5), ("A2", .4)): A(37.7, "contrabass_pizz", p, 1.0, v)
for p in ("D5", "F#5", "A5", "D6"): A(37.7, "vibraphone", p, 2.5, 0.3)
for p in ("D4", "F#4", "A4"): A(37.75, "vibraphone_bowed", p, 2.2, 0.2, 0.0, attack=0.3)

bed_x = S.render(bed, dur=DUR, master=False); acc_x = S.render(acc, dur=DUR, master=False)
# duck the bed under the voice: -6 dB where the voice is speaking
v, sr = sf.read(H.parent / "assets" / "voice.wav", dtype="float32"); assert sr == SR
v = np.pad(np.abs(v), (0, max(0, len(bed_x) - len(v))))[:len(bed_x)]
win = int(0.05 * SR); env = np.convolve(v, np.ones(win) / win, mode="same")
env = np.clip(env / (np.percentile(env[env > 1e-4], 70) + 1e-9), 0, 1)
att, rel = np.exp(-1 / (0.06 * SR / 64)), np.exp(-1 / (0.35 * SR / 64))
e = env[::64]; sm = np.zeros_like(e); s = 0.0
for i, x in enumerate(e): s = att * s + (1 - att) * x if x > s else rel * s + (1 - rel) * x; sm[i] = s
g = 1 - 0.5 * np.repeat(sm, 64)[:len(bed_x)]
mix = bed_x * g[:, None] + acc_x * 1.15
mix = S.room(mix, size=0.35, mix=0.14)
fade = np.ones(len(mix)); fl = int(1.2 * SR); fade[-fl:] = np.linspace(1, 0, fl) ** 1.5
mix = mix * fade[:, None]
mix = mix / (np.abs(mix).max() + 1e-9) * 0.7
sf.write(H.parent / "assets" / "music.wav", mix.astype(np.float32), SR)
used = sorted({x["inst"] for x in bed + acc})
(H / "credits.txt").write_text("\n".join(S.credits(used)) + "\n")
print("instruments:", ", ".join(used)); print(open(H / "credits.txt").read())
