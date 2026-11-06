"""Trim each line, cap the pauses inside it, join the lines with planned gaps.
Writes ../assets/voice.wav and lines.json (start/end of every line in seconds)."""
import json, pathlib, numpy as np, soundfile as sf
from script import LINES
H = pathlib.Path(__file__).parent; SR = 48000
MAXP, KEEP = 0.26, 0.20          # a pause longer than MAXP inside a line is cut down to KEEP
GAP = {"N1": 0.35, "N2": 0.3, "N3": 0.7, "B1": 0.3, "B2": 0.45, "B3": 0.3, "B4": 0.45}   # after the line (N3: the page curl into the explanation)
LEAD, TAIL = 0.25, 1.6
def frames_db(x, win=0.01):
    n = int(win * SR); k = len(x) // n
    r = np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1) + 1e-12); return 20 * np.log10(r), n
def tighten(x, th=-40):
    db, n = frames_db(x); loud = db > th
    idx = np.where(loud)[0]; a, b = idx[0], idx[-1] + 1
    x = x[max(0, a * n - int(0.03 * SR)): min(len(x), b * n + int(0.06 * SR))]
    db, n = frames_db(x); quiet = db <= th
    out, i, cut = [], 0, 0.0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            run = (j - i) * n / SR
            if run > MAXP:   # keep KEEP seconds: half from each side, so the word edges stay intact
                h = int(KEEP / 2 * SR); out.append(x[i * n: i * n + h]); out.append(x[j * n - h: j * n]); cut += run - KEEP
            else: out.append(x[i * n: j * n])
            i = j
        else:
            j = i
            while j < len(quiet) and not quiet[j]: j += 1
            out.append(x[i * n: j * n]); i = j
    out.append(x[len(quiet) * n:])
    return np.concatenate(out), cut
track, t, lines, total_cut = [np.zeros(int(LEAD * SR), np.float32)], LEAD, [], 0
for i, text in LINES:
    x, sr = sf.read(H / "voice" / f"{i}.wav", dtype="float32"); assert sr == SR
    y, cut = tighten(x); total_cut += cut
    (H / "voice" / "tight").mkdir(exist_ok=True); sf.write(H / "voice" / "tight" / f"{i}.wav", y, SR)
    lines.append({"id": i, "text": text, "start": round(t, 3), "end": round(t + len(y) / SR, 3)})
    track.append(y); t += len(y) / SR
    g = GAP.get(i, TAIL); track.append(np.zeros(int(g * SR), np.float32)); t += g
v = np.concatenate(track)
(H.parent / "assets").mkdir(exist_ok=True); sf.write(H.parent / "assets" / "voice.wav", v, SR)
(H / "lines.json").write_text(json.dumps(lines, indent=1))
for l in lines: print(f'{l["id"]} {l["start"]:6.2f}-{l["end"]:6.2f}  {l["text"]}')
print(f"total {len(v)/SR:.2f}s, pauses cut {total_cut:.2f}s")
