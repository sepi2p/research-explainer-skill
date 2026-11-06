"""Trim each line, cap the pauses inside it, join the lines with planned gaps.
Writes ../assets/voice.wav and lines.json (start/end of every line in seconds)."""
import json, pathlib, subprocess, numpy as np, soundfile as sf
from script import LINES
H = pathlib.Path(__file__).parent; SR = 48000
MAXP, KEEP = 0.26, 0.20          # a pause longer than MAXP inside a line is cut down to KEEP
GAP = {"V1": 0.3, "V2": 0.5, "V3": 0.15, "V4": 0.5, "V5": 0.25, "V6": 0.3, "V7": 0.45}   # after the line (0.5: a GL transition)
LEAD, TAIL = 0.25, 1.5
SPEED = 1.1                      # tempo of every line (ffmpeg atempo, pitch kept); 1.0 keeps the voice as recorded
def load(path):
    if SPEED == 1.0:
        x, sr = sf.read(path, dtype="float32"); assert sr == SR; return x
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-af", f"atempo={SPEED}", "-ar", str(SR), "-ac", "1",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()
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
    x = load(H / "voice" / f"{i}.wav")
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
