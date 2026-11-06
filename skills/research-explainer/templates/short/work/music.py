"""Original score for the short, from CC0 sample libraries (Lemo-Opuscar sampler: VSCO 2 CE, VCSL).
Bed on a 112 bpm grid; accents at the exact times of the on-screen hits (scene starts S1..S5 below = index.html); the bed
ducks under the voice.
Writes ../assets/music.wav and credits.txt. Needs ../assets/voice.wav (assemble_voice.py) for the ducking.

Needs Lemo-Opuscar (MIT, https://github.com/lemomo-ai/lemo-opuscar) and two of its CC0 sample packs:
  git clone https://github.com/lemomo-ai/lemo-opuscar ~/lemo-opuscar
  cd ~/lemo-opuscar && sh tools/fetch.sh instruments vsco2ce && sh tools/fetch.sh instruments vcsl
Set LEMO_OPUSCAR if it is somewhere else (default ~/lemo-opuscar). Python: numpy, scipy, soundfile, soxr."""
import sys, os, json, pathlib, numpy as np, soundfile as sf
H = pathlib.Path(__file__).resolve().parent
LIB = pathlib.Path(os.environ.get("LEMO_OPUSCAR", "~/lemo-opuscar")).expanduser().resolve()
if not (LIB / "core" / "audio" / "sampler.py").exists():
    sys.exit(f"Lemo-Opuscar not found at {LIB}: git clone https://github.com/lemomo-ai/lemo-opuscar there, or set "
             "LEMO_OPUSCAR to its folder; then fetch the samples: sh tools/fetch.sh instruments vsco2ce (and vcsl)")
if not (LIB / "core" / "audio" / "instruments" / "vsco2ce").is_dir() or not (LIB / "core" / "audio" / "instruments" / "vcsl").is_dir():
    sys.exit(f"sample packs missing in {LIB}/core/audio/instruments: cd {LIB} && sh tools/fetch.sh instruments vsco2ce "
             "&& sh tools/fetch.sh instruments vcsl (CC0, about 670 MB together)")
sys.path.insert(0, str(LIB)); os.chdir(LIB)   # the library is imported from its repo root
from core.audio import sampler as S
from core.audio.sfx import SR
DUR = 35.5; B = 60 / 112; BAR = 4 * B           # DUR = the film length (index.html "main" data-duration)
S.seed(1405); rng = np.random.default_rng(1405)
CH = {"D": ["D", "F#", "A"], "Em": ["E", "G", "B"], "A": ["A", "C#", "E"], "Bm": ["B", "D", "F#"], "G": ["G", "B", "D"], "F#m": ["F#", "A", "C#"]}
def n(name, octv): return f"{name}{octv}"
# chord per bar; the section (which bed parts play) follows the scene times in index.html
PLAN = {0: "D", 1: "Em", 2: "D", 3: "Bm", 4: "G", 5: "A", 6: "Bm", 7: "G", 8: "D", 9: "A", 10: "Bm", 11: "G", 12: "Em", 13: "F#m",
        14: "G", 15: "A", 16: "D"}
S1, S2, S3, S4, S4B, S5 = 0.0, 4.95, 10.2, 18.35, 23.2, 30.95   # hook, readings, average, error chart, shared noise, end card
bed, acc = [], []
def E(lst, t, inst, pitch, dur, vel, pan=0.0, **kw):
    if t < DUR: lst.append(dict(t=float(t), inst=inst, pitch=pitch, dur=dur, vel=vel, pan=pan, **kw))
for bar, ch in PLAN.items():
    t0 = bar * BAR; root = CH[ch][0]
    lo = 2 if root in ("D", "E", "F#", "G") else 1
    sec = "hook" if t0 < S2 - 0.1 else "run" if t0 < S3 - 0.1 else "fix" if t0 < S4 - 0.1 else "law" if t0 < S4B else "problem" if t0 < S5 - 0.1 else "end"
    if sec == "end" and t0 >= 33.6: continue
    # double bass on beats 1 and 3
    for k, bt in enumerate((0, 2)):
        E(bed, t0 + bt * B, "contrabass_pizz", n(root if k == 0 else CH[ch][2], lo + (1 if k and CH[ch][2] in "ABC" else 0) if k else lo + 1), 0.5, 0.55, -0.1)
    if sec in ("run", "law"):
        for e8 in range(8):                       # pizzicato chord tones on the off-beats
            if e8 % 2 == 1:
                E(bed, t0 + e8 * B / 2, "violins_pizz", n(CH[ch][(e8 // 2) % 3], 4), 0.25, 0.30 if sec == "run" else 0.24, 0.35)
    if sec in ("hook", "fix", "law", "end"):
        arp = [CH[ch][0], CH[ch][1], CH[ch][2], CH[ch][1]]
        for e8 in range(8 if sec != "hook" else 4):
            E(bed, t0 + e8 * B / 2 * (1 if sec != "hook" else 2), "marimba", n(arp[e8 % 4], 4), 0.3, 0.22 if sec != "hook" else 0.28, -0.3)
    if sec == "problem":
        E(bed, t0, "cellos_pizz", n(root, 3), 0.6, 0.35, 0.2); E(bed, t0 + 2 * B, "cellos_pizz", n(CH[ch][2], 3), 0.6, 0.3, 0.2)
        E(bed, t0, "vibraphone", n(CH[ch][1], 4), 1.6, 0.18, 0.3)
    if sec == "fix":
        for e8 in range(8): E(bed, t0 + e8 * B / 2, "shaker", "down" if e8 % 2 == 0 else "up", None, 0.10 + 0.04 * (e8 % 2 == 0), 0.45)
    if sec == "run":
        E(bed, t0 + B, "woodblock", "a", None, 0.16, -0.4); E(bed, t0 + 3 * B, "woodblock", "b", None, 0.16, -0.4)

# ---- accents at on-screen hits (seconds from the start of the film; word times from assets/captions.js) ----
A = lambda *a, **k: E(acc, *a, **k)
A(0.0, "glockenspiel", "D6", 1.0, 0.35, 0.2); A(0.0, "marimba", "D4", 0.8, 0.4, -0.2); A(0.0, "marimba", "A4", 0.8, 0.3, 0.1)
for k in range(1, 20): A(k * 0.23, "woodblock", "c", None, 0.10 + 0.02 * (k % 2), 0.4 - 0.04 * k)      # the meter steps to each reading
A(1.28, "marimba", "F#5", 0.3, 0.3, 0.2); A(2.48, "marimba", "A5", 0.3, 0.3, 0.2)                     # the two "20"s
A(4.40, "vibraphone", "F5", 1.4, 0.32, 0.2); A(4.40, "vibraphone", "B4", 1.4, 0.3, -0.2); A(4.40, "cellos_pizz", "D2", 0.8, 0.5)   # "right?"
for k, p in enumerate(["A5", "F#5", "E5", "D5", "B4", "A4"]): A(S2 + k * 0.055, "harp", p, 0.5, 0.28, 0.3 - 0.12 * k)           # meter shrinks
A(S2 + 0.5, "woodblock", "a", None, 0.5, 0.3)                                                         # SIMULATED stamp
scale = ["D5", "E5", "F#5", "A5", "B5", "D6", "E6", "F#6", "A6", "B6"]
A(S2 + 0.36, "marimba", "D5", 0.3, 0.3, 0.4)                                                          # card #20 settles
for i in range(19):                                                                                   # each card lands on its own note
    land = S2 + 0.42 + i * 0.078 + 0.42 * 0.8
    A(land, "xylophone" if i % 2 else "marimba", scale[i % 10] if i < 10 else scale[min(9, i - 9)], 0.25, 0.24 + 0.01 * i, -0.5 + i * 0.05)
A(S2 + 2.45, "tambourine", None, None, 0.3, 0.3)                                                      # "random noise": the cards shiver
A(S2 + 3.2, "xylophone", "A5", 0.3, 0.3, 0.3); A(S2 + 3.78, "glockenspiel", "E6", 0.6, 0.26, 0.2)       # sigma chip, "0.25"
for k, p in enumerate(["A3", "D4", "F#4", "A4", "D5", "F#5", "A5", "D6"]): A(9.88 + k * 0.05, "harp", p, 0.6, 0.3, -0.4 + 0.1 * k)  # page curl
for k in range(22):                                                                                   # ink particles: a sparkle that thins out
    t = S3 + 0.55 + 1.5 * (k / 22) ** 1.4
    A(t, "glockenspiel", str(rng.choice(["A5", "B5", "D6", "E6", "F#6", "A6", "B6", "D7"])), 0.4, 0.11 + 0.11 * rng.random(), float(rng.uniform(-0.6, 0.6)))
A(S3 + 1.12, "vibraphone", "A5", 0.9, 0.28, 0.3)                                                      # true value line
for k, p in enumerate(["D6", "B5", "A5", "F#5", "D5"]): A(S3 + 2.04 + 0.1 * k, "harp", p, 0.5, 0.26, 0.3 - 0.12 * k)  # dots run together
A(S3 + 2.56, "marimba", "D4", 0.8, 0.45); A(S3 + 2.56, "bass_drum", None, None, 0.3)                   # the average lands
A(S3 + 2.68, "cellos_pizz", "D2", 0.6, 0.45)                                                          # "Single readings": worst dot
A(S3 + 4.55, "woodblock", "b", None, 0.45, 0.0); A(S3 + 4.55, "vibraphone", "B4", 0.6, 0.28, 0.3)      # "misses by 0.58"
A(S3 + 5.96, "glockenspiel", "D6", 1.2, 0.36, 0.2); A(S3 + 5.96, "glockenspiel", "F#6", 1.2, 0.28, -0.2)   # "Their average"
A(S3 + 7.05, "xylophone", "A6", 0.2, 0.3, 0.3); A(S3 + 7.17, "xylophone", "D7", 0.3, 0.28, 0.3)        # "misses by 0.05"
for p in ("A4", "D5"): A(18.08, "vibraphone_bowed", p, 0.8, 0.25, 0.0, attack=0.25)                   # ink bleed
A(18.1, "shaker", "roll", None, 0.25, -0.3)
for k, (grow, tag, p) in enumerate([(0.45, 1.09, "F#5"), (2.05, 2.77, "A5"), (3.33, 4.29, "D6")]):     # four, sixteen, sixty-four
    A(S4 + grow, "marimba", p, 0.4, 0.34, -0.2 + 0.2 * k); A(S4 + tag, "xylophone", p, 0.25, 0.3, 0.3)
for k, p in enumerate(["D4", "F#4", "A4", "D5", "F#5"]): A(S4 + 4.45 + 0.08 * k, "harp", p, 0.6, 0.26, 0.2)    # the 1/sqrt(n) curve
A(S4 + 4.55, "glockenspiel", "A5", 1.0, 0.3, 0.0)                                                     # formula
A(S4 + 6.21, "woodblock", "c", None, 0.32, 0.3)                                                       # "independent"
A(S4 + 7.8, "cellos_pizz", "B2", 0.6, 0.4, -0.2)                                                      # shared noise legend
for k, p in enumerate(["F#3", "E3", "D3", "C#3"]): A(S4 + 9.05 + 0.12 * k, "cellos_pizz", p, 0.4, 0.42, 0.1)   # the shared bars stall
A(S4 + 10.0, "bass_drum", None, None, 0.38); A(S4 + 10.0, "marimba", "F#3", 1.0, 0.45, -0.3); A(S4 + 10.0, "vibraphone", "C#5", 1.0, 0.26)  # floor
A(S4 + 11.7, "woodblock", "c", None, 0.32, 0.3); A(S4 + 11.82, "woodblock", "c", None, 0.28, 0.3)     # "even with sixty-four"
A(S5, "bass_drum", None, None, 0.42); A(S5, "tubular_bells", "D5", 2.5, 0.32); A(S5, "glockenspiel", "D6", 1.5, 0.35); A(S5, "marimba", "D3", 1.0, 0.45)  # end card
for k, t in enumerate([0.09, 0.73, 1.21, 1.53, 2.01, 2.25, 2.73]): A(S5 + t, "harp", ["D5", "E5", "F#5", "A5", "B5", "A5", "D6"][k], 0.6, 0.26, -0.3 + 0.1 * k)
for p, v in (("D2", .5), ("A2", .4)): A(S5 + 2.75, "contrabass_pizz", p, 1.0, v)
for p in ("D5", "F#5", "A5", "D6"): A(S5 + 2.75, "vibraphone", p, 2.2, 0.3)
for p in ("D4", "F#4", "A4"): A(S5 + 2.8, "vibraphone_bowed", p, 1.8, 0.2, 0.0, attack=0.3)

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
