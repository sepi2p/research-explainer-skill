"""pauses.py [--lang en]: real pauses at the script's ⏸ marks, for a voice that ignores them (a model voice).
Reads the cleaned clips (voice/<lang>_proc) and their per-character times (chartimes.json from wordtimes.py), cuts
each clip at the quietest point between the words around every ⏸ and inserts silence so the gap is about GAP seconds
(at least MIN_ADD added). Writes voice/<lang>_final/<beat>.wav, durations.json and chartimes.json (character times
shifted by the inserted silence); timeline.py prefers _final over _proc. A leading ⏸ adds LEAD_PAUSE of silence first.
Idempotent: always starts from voice/<lang>_proc. (voice_piper.py already turns ⏸ into silence: skip this step.)"""
import argparse, json, pathlib, re, wave
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
_nar = json.loads((ROOT / "narration.json").read_text())
_ap = argparse.ArgumentParser(); _ap.add_argument("--lang", default=_nar.get("lang", "en")); LANG = _ap.parse_args().lang
P, O = ROOT / f"voice/{LANG}_proc", ROOT / f"voice/{LANG}_final"; O.mkdir(parents=True, exist_ok=True)
GAP, MIN_ADD, LEAD_PAUSE, SR = 0.6, 0.22, 0.35, 48000
nar = {b["id"]: b[LANG] for s in _nar["scenes"] for b in s["beats"]}
CT = json.loads((P / "chartimes.json").read_text())

def read(p):
    with wave.open(str(p)) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2, p
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
def write(p, x):
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.clip(x, -32768, 32767).astype(np.int16).tobytes())

def quietest(x, a, b):
    """Sample index of the quietest 20 ms window between times a and b (a 60 ms margin each side if room)."""
    a, b = max(0.0, a), min(len(x) / SR, b)
    if b - a < 0.06: return int((a + b) / 2 * SR)
    win = int(0.02 * SR); best, bi = None, int(a * SR)
    for s in range(int(a * SR), int(b * SR) - win, win // 2):
        e = float(np.mean(x[s:s + win] ** 2))
        if best is None or e < best: best, bi = e, s + win // 2
    return bi

out_d, out_ct = {}, {}
for i, text in nar.items():
    x, ct = read(P / f"{i}.wav"), list(CT[i])
    marks = [m.start() for m in re.finditer("⏸", text)]
    cuts = []                                   # (sample index in the original clip, seconds to insert)
    for k in marks:
        before = [j for j in range(k) if text[j].strip() and text[j] != "⏸"]
        after = [j for j in range(k + 1, len(text)) if text[j].strip() and text[j] != "⏸"]
        if not before:
            cuts.append((0, LEAD_PAUSE)); continue
        if not after: continue
        ta, tb = ct[before[-1]], ct[after[0]]
        idx = quietest(x, ta, tb)
        cuts.append((idx, max(MIN_ADD, GAP - max(0.0, tb - ta))))
    y, last, shift_at = [], 0, []
    for idx, add in sorted(cuts):
        y.append(x[last:idx]); y.append(np.zeros(int(add * SR), np.float32)); last = idx; shift_at.append((idx / SR, add))
    y.append(x[last:]); y = np.concatenate(y) if y else x
    # character times: every character after a cut moves by the silence inserted before it
    nct = [t + sum(add for at, add in shift_at if t >= at - 1e-6 and not (at == 0 and t < 0)) for t in ct]
    write(O / f"{i}.wav", y)
    out_d[i] = round(len(y) / SR, 3); out_ct[i] = [round(t, 3) for t in nct]
    if cuts: print(f"{i}: {len(cuts)} pause(s), +{sum(a for _, a in cuts):.2f}s")
(O / "durations.json").write_text(json.dumps(out_d, indent=1))
(O / "chartimes.json").write_text(json.dumps(out_ct))
print(f"{len(out_d)} clips, total {sum(out_d.values()):.1f}s")
