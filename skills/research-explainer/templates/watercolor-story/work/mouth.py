"""Mime tracks: a character's mouth follows the narrator's loudness only while that character's speech bubble is up
(the narrator is the only voice). Windows come from the word times. Writes ../assets/mouth.js (30 fps)."""
import json, pathlib, numpy as np, soundfile as sf
H = pathlib.Path(__file__).parent
x, sr = sf.read(H.parent / "assets" / "voice.wav", dtype="float32")
W = json.loads((H / "words.json").read_text())
def span(line, first, last=None):
    ws = [w for w in W if w["line"] == line]; i = [w["text"].lower().strip(".,:?!") for w in ws].index(first)
    j = len(ws) - 1 if last is None else [w["text"].lower().strip(".,:?!") for w in ws].index(last, i)
    return ws[i]["start"], ws[j]["end"]
WIN = {"APP": [span("N1", "why", "time")],          # the apprentice's bubble: "Why does the scale show a new number every time?"
       "BAK": [span("N2", "weigh", "average")]}     # the baker's bubble: "Weigh it 16 times, and take the average."
FPS = 30; n = int(len(x) / sr * FPS) + 1; hop = sr // FPS
rms = np.array([np.sqrt((x[i * hop:(i + 1) * hop] ** 2).mean() + 1e-12) for i in range(n)])
v = np.clip((20 * np.log10(rms) + 42) / 24, 0, 1)
out = {"fps": FPS, "win": WIN}
for who, ws in WIN.items():
    m = np.zeros(n)
    for a, b in ws: m[int(a * FPS):int(b * FPS) + 1] = v[int(a * FPS):int(b * FPS) + 1]
    out[who] = [round(float(q), 2) for q in m]
(H.parent / "assets" / "mouth.js").write_text("window.MOUTH = " + json.dumps(out) + ";\n")
print(WIN)
