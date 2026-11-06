"""measure_voice.py [--wav VOICE.wav] [--lang en]: measure the narrator before composing (music-diorama.md section 3)
-> work/music/voice_profile.json, and a printed summary.

Measures, on speech frames only: f0 p5 / median / p95 (YIN), the long-term average spectrum (LTAS) in octave bands, its
centroid, the share of energy at 1-4 kHz, pauses per minute, and words per minute from timeline.json. Derives:
  - no_sustain_zone: MIDI(f0 p5) .. MIDI(2 x f0 p95), rounded outward (fundamental + first harmonic): music.py holds no
    sustained note there under speech;
  - body_band_hz: the band where the LTAS is strongest (the smallest run of 1/3-octave bands around the peak that holds
    70 % of the energy from 50 Hz to 8 kHz): music stays >= 18 dB under the voice there;
  - speech: voice-activity spans (10 ms resolution) that music.py uses for every "under speech" rule.
The voice is the --wav file, else the clips audio.py uses (voice/<lang>_final or voice/<lang>_proc, each placed at its
beat's start). A text-only video has no voice: the profile then holds an assumed zone (MIDI 50-75, a typical female
narrator) and the beats' spans as "speech", marked measured=false. Re-measure for every new narrator; never copy numbers.
Run with numpy + scipy (e.g. the Lemo-Opuscar venv):  python work/measure_voice.py"""
import argparse, json, math, pathlib, re, subprocess
import numpy as np
from scipy.signal import welch, resample_poly

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "work" / "music"; OUT.mkdir(parents=True, exist_ok=True)
TL = json.loads((ROOT / "timeline.json").read_text())
ap = argparse.ArgumentParser(); ap.add_argument("--wav"); ap.add_argument("--lang", default=TL.get("lang", "en"))
a = ap.parse_args()
SR = 48000

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)

def voice_track():
    if a.wav: return load(a.wav), a.wav
    vdir = next((d for d in (ROOT / f"voice/{a.lang}_final", ROOT / f"voice/{a.lang}_proc") if (d / "durations.json").exists()), None)
    if not vdir or not TL.get("voice"): return None, None
    x = np.zeros(int(TL["total"] * SR) + SR)
    for b in TL["beats"]:
        p = vdir / f"{b['id']}.wav"
        if p.exists():
            c = load(p); i = int(b["start"] * SR); j = min(len(x), i + len(c)); x[i:j] += c[: j - i]
    return x, str(vdir.relative_to(ROOT))

def midi(f): return 69 + 12 * math.log2(f / 440.0)

# ---------------- words per minute (timeline) ----------------
def syl(w):
    w = re.sub("[^a-z]", "", w.lower())
    if not w: return 0
    n = len(re.findall("[aeiouy]+", w))
    if w.endswith("e") and not w.endswith("le") and n > 1: n -= 1
    return max(1, n)
B = TL["beats"]
words = [w for b in B for w in b["text"].replace("⏸", " ").split() if re.search(r"\w", w)]
dur = sum(b["dur"] for b in B)
gaps = [B[i + 1]["start"] - B[i]["end"] for i in range(len(B) - 1)]
prof = dict(source=None, measured=False, wpm=round(len(words) / dur * 60, 1) if dur else None,
            syllables_per_s=round(sum(syl(w) for w in words) / dur, 2) if dur else None,
            beat_gaps_ge_1_5s=int(sum(g >= 1.5 for g in gaps)))

x, src = voice_track()
if x is None or not np.any(x):
    prof.update(no_sustain_zone=[50, 75], body_band_hz=[200, 1000],
                speech=[[b["start"], b["end"]] for b in B],
                note="no voice: assumed zone (typical female narrator) and the beats as speech; measure again once voiced")
    (OUT / "voice_profile.json").write_text(json.dumps(prof, indent=1))
    print("no voice (text-only): wrote an ASSUMED profile, zone MIDI 50-75; re-run after adding a voice"); raise SystemExit

# ---------------- voice activity (10 ms hop, 30 ms frames) ----------------
hop, fr = SR // 100, int(0.03 * SR)
n = max(1, (len(x) - fr) // hop)
c2 = np.concatenate([[0.0], np.cumsum(x * x)])
e = np.sqrt((c2[np.arange(n) * hop + fr] - c2[np.arange(n) * hop]) / fr + 1e-12)
db = 20 * np.log10(e + 1e-9)
thr = np.percentile(db[db > -80], 95) - 35 if np.any(db > -80) else -60
act = db > thr
for _ in range(2):                                      # close 30 ms flickers
    act[1:-1] |= act[:-2] & act[2:]
d = np.diff(np.r_[0, act.astype(int), 0]); s0 = np.where(d == 1)[0]; s1 = np.where(d == -1)[0]
speech = [[round(float(p) / 100, 2), round(float(q) / 100 + 0.03, 2)] for p, q in zip(s0, s1) if q - p >= 4]
sil = [speech[i + 1][0] - speech[i][1] for i in range(len(speech) - 1)]
span = (speech[-1][1] - speech[0][0]) if speech else 1.0
pauses = [g for g in sil if g >= 0.25]

# ---------------- f0 (YIN, vectorised, 16 kHz) ----------------
y = resample_poly(x, 1, 3); s2 = 16000
N, H = 640, 320; tmin, tmax = s2 // 500, s2 // 60
starts = np.arange(0, len(y) - N - tmax, H)
fr_db = np.array([20 * np.log10(np.sqrt(np.mean(y[i:i + N] ** 2)) + 1e-9) for i in starts]) if len(starts) else np.array([])
starts = starts[fr_db > thr + 10]
f0 = []
L = 1 << int(math.ceil(math.log2(N + tmax + N)))
for k in range(0, len(starts), 2000):
    W = np.stack([y[i:i + N + tmax] for i in starts[k:k + 2000]])
    F = np.fft.rfft(W, L, axis=1); F0 = np.fft.rfft(W[:, :N], L, axis=1)
    r = np.fft.irfft(np.conj(F0) * F, L, axis=1)[:, :tmax + 1]               # r[tau] = sum_j w_j w_{j+tau}, j < N
    cs = np.concatenate([np.zeros((len(W), 1)), np.cumsum(W * W, axis=1)], axis=1)
    Et = cs[:, N:N + tmax + 1] - cs[:, :tmax + 1]
    dd = np.maximum(cs[:, N:N + 1] + Et - 2 * r, 0); dd[:, 0] = 0
    cm = dd[:, 1:] * np.arange(1, tmax + 1) / np.maximum(np.cumsum(dd[:, 1:], axis=1), 1e-12)
    cm = np.concatenate([np.ones((len(W), 1)), cm], axis=1)
    for row in cm:
        idx = np.where(row[tmin:] < 0.15)[0]
        if not len(idx): continue
        t = idx[0] + tmin
        while t + 1 <= tmax and row[t + 1] < row[t]: t += 1
        f0.append(s2 / t)
f0 = np.array(f0)
if len(f0) < 50: raise SystemExit(f"only {len(f0)} voiced frames found in {src}: is it a voice stem?")
p5, p50, p95 = np.percentile(f0, [5, 50, 95])

# ---------------- LTAS on speech samples ----------------
mask = np.repeat(act, hop)[: len(x)]
xa = x[: len(mask)][mask]
f, P = welch(xa, SR, nperseg=8192)
tot = P.sum(); cent = float(np.sum(f * P) / tot)
octaves = {}
for fc in (63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000):
    octaves[str(fc)] = round(100 * P[(f >= fc / 2 ** .5) & (f < min(fc * 2 ** .5, SR / 2))].sum() / tot, 2)
share_1_4k = round(100 * P[(f >= 1000) & (f < 4000)].sum() / tot, 2)
th = [(1000 * 2 ** (k / 3)) for k in range(-13, 10)]                      # 1/3-octave centres 50 Hz .. 8 kHz
tp = np.array([P[(f >= c / 2 ** (1 / 6)) & (f < c * 2 ** (1 / 6))].sum() for c in th])
i0 = i1 = int(np.argmax(tp))
while tp[i0:i1 + 1].sum() < 0.7 * tp.sum():
    lo = tp[i0 - 1] if i0 > 0 else -1; hi = tp[i1 + 1] if i1 + 1 < len(tp) else -1
    if hi >= lo: i1 += 1
    else: i0 -= 1
body = [int(round(th[i0] / 2 ** (1 / 6), -1)), int(round(th[i1] * 2 ** (1 / 6), -1))]
zone = [int(math.floor(midi(p5))), int(math.ceil(midi(2 * p95)))]

prof.update(source=src, measured=True,
            f0_hz=dict(p5=round(p5, 1), median=round(p50, 1), p95=round(p95, 1)),
            f0_midi=dict(p5=round(midi(p5), 1), median=round(midi(p50), 1), p95=round(midi(p95), 1)),
            no_sustain_zone=zone, body_band_hz=body, ltas_centroid_hz=round(cent), ltas_octave_share_pct=octaves,
            share_1_4k_pct=share_1_4k, pauses_per_min=round(len(pauses) / (span / 60), 1),
            pause_median_s=round(float(np.median(pauses)), 2) if pauses else None,
            speech_active_s=round(sum(q - p for p, q in speech), 1), speech=speech)
(OUT / "voice_profile.json").write_text(json.dumps(prof, indent=1))
print(f"voice: {src}")
print(f"  f0 p5/median/p95 {p5:.0f}/{p50:.0f}/{p95:.0f} Hz (MIDI {midi(p5):.1f}/{midi(p50):.1f}/{midi(p95):.1f}); "
      f"centroid {cent:.0f} Hz; 1-4 kHz {share_1_4k} % of the energy")
print(f"  no-sustain zone MIDI {zone[0]}-{zone[1]}; body band {body[0]}-{body[1]} Hz")
print(f"  {prof['wpm']} wpm, {prof['syllables_per_s']} syllables/s, {prof['pauses_per_min']} pauses/min, "
      f"{prof['beat_gaps_ge_1_5s']} gaps >= 1.5 s between beats")
print("  octave shares %:", ", ".join(f"{k} {v}" for k, v in octaves.items()))
print("wrote work/music/voice_profile.json")
