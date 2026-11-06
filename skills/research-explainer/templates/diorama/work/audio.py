"""audio.py: the soundtrack -> work/audio/mix.wav (48 kHz stereo) + stems (voice, music, sfx) + cues.json.
  - voice: the clips timeline.py used (voice/<lang>_final or _proc), each placed at its beat's start (none: text-only)
  - music: an optional bed of your own licensed track, work/music/bed.(wav|mp3|flac|m4a), looped with crossfades,
    ducked ~18 dB under speech and ~8 dB in pauses (no file: no music)
  - SFX: synthesized here (numpy only), placed on narration cues by the SFX table below; edit it for your video.
    A cue that is not in its beat's text is listed at the end instead of crashing.
Run with any Python 3 that has numpy:  python3 work/audio.py   then   python3 work/assemble.py <silent.mp4> <out.mp4>"""
import json, pathlib, subprocess, wave
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "work" / "audio"; OUT.mkdir(parents=True, exist_ok=True)
SR = 48000
TL = json.loads((ROOT / "timeline.json").read_text())
T = TL["total"]; N = int(T * SR) + SR
B = {b["id"]: b for b in TL["beats"]}
rng = np.random.default_rng(7)
missing = []

def cue(bid, sub=None, off=0.0):
    """Time when beat `bid` reaches `sub` (word-aligned "ct" times when present, else by character position)."""
    if bid not in B: missing.append((bid, sub)); return None
    b = B[bid]; tx = b["text"]
    if not sub: return b["start"] + off
    i = tx.find(sub)
    if i < 0: missing.append((bid, sub)); return None
    if b.get("ct") and len(b["ct"]) == len(tx): return b["start"] + b["ct"][i] + off
    return b["start"] + b["dur"] * i / max(1, len(tx)) + off
def end(bid, off=0.0): return B[bid]["end"] + off if bid in B else None
def add(buf, t, sig, gain=1.0):
    if t is None: return
    i = int(t * SR)
    if i < 0: sig = sig[-i:]; i = 0
    j = min(len(buf), i + len(sig))
    if j > i: buf[i:j] += gain * sig[: j - i]
def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
def band(x, lo, hi):   # FFT band-pass (fine for short sounds)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))
def smooth(x, sec):    # moving average (envelopes)
    n = max(1, int(sec * SR)); c = np.cumsum(np.insert(x, 0, 0.0)); y = (c[n:] - c[:-n]) / n
    return np.concatenate([np.full(n - 1, y[0]), y])

# ---------------- voice ----------------
voice = np.zeros(N); speech = np.zeros(N)
if TL.get("voice"):
    vdir = next(d for d in (ROOT / f"voice/{TL['lang']}_final", ROOT / f"voice/{TL['lang']}_proc") if (d / "durations.json").exists())
    for b in TL["beats"]:
        p = vdir / f"{b['id']}.wav"
        if p.exists():
            x = load(p); add(voice, b["start"], x); speech[int(b["start"] * SR): int(b["start"] * SR) + len(x)] = 1.0
    print(f"voice: {vdir.relative_to(ROOT)}")

# ---------------- music bed (optional) ----------------
music = np.zeros(N)
bed = next((p for ext in ("wav", "mp3", "flac", "m4a") for p in [ROOT / f"work/music/bed.{ext}"] if p.exists()), None)
if bed:
    src = load(bed); src /= (np.sqrt(np.mean(src ** 2)) or 1); xf = int(2.0 * SR); pos = 0
    while pos < N:
        L = min(len(src), N - pos); piece = src[:L].copy()
        if pos > 0: piece[:min(xf, L)] *= np.linspace(0, 1, min(xf, L))
        if pos + L < N and L > xf: piece[-xf:] *= np.linspace(1, 0, xf)
        music[pos:pos + L] += piece; pos += L - (xf if pos + L < N else 0)
    fade = np.minimum(1, np.arange(N) / (1.5 * SR)) * np.minimum(1, (T * SR - np.arange(N)).clip(0) / (2.0 * SR))
    duck = 10 ** (np.where(smooth(speech, 0.25) > 0.05, -18, -8) / 20) if TL.get("voice") else np.full(N, 10 ** (-6 / 20))
    music *= 0.12 * fade * smooth(duck, 0.3)
    print(f"music: {bed.relative_to(ROOT)}")

# ---------------- SFX library (synthesized, short) ----------------
def env(n, att=0.003, k=30.0): t = np.arange(n) / SR; return np.minimum(1, t / att) * np.exp(-t * k)
def pop(f=900): n = int(0.09 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * (f + 600 * np.exp(-t * 60)) * t) * np.exp(-t * 45) * 0.6
def tick(f=3500): n = int(0.03 * SR); return band(rng.normal(0, 1, n), f * 0.7, f * 1.4) * env(n, 0.001, 220)
def thump(f0=60): n = int(0.35 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * (f0 + 30 * np.exp(-t * 30)) * t) * np.exp(-t * 14)
def slam():
    n = int(0.5 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 40)) * t) * np.exp(-t * 18) + band(rng.normal(0, 1, n), 60, 1800) * np.exp(-t * 35) * 0.6) * 0.9
def flip(): n = int(0.12 * SR); return band(rng.normal(0, 1, n), 1500, 6000) * env(n, 0.002, 30) * 0.35
def whoosh(dur=0.9, up=True):
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.normal(0, 1, n); out = np.zeros(n); seg = 4096
    for i in range(0, n, seg):
        p = i / n; fc = 300 + 2800 * (p if up else 1 - p); out[i:i + seg] = band(x[i:i + seg], fc * 0.6, fc * 1.4)
    return out * np.sin(np.pi * t / dur) ** 2 * 0.5
def bell(f, dur=1.6, gain=0.9):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for r, a, d in ((1, 1, 1.2), (2.0, 0.5, 0.9), (2.76, 0.35, 0.6), (5.4, 0.2, 0.35)): s += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    return s * np.minimum(1, t / 0.003) * gain * 0.5
def crack():
    n = int(0.6 * SR); s = np.zeros(n)
    for k in range(7):
        i = int(rng.uniform(0, 0.25) * SR); m = int(0.02 * SR); s[i:i + m] += band(rng.normal(0, 1, m), 2500, 9000) * np.exp(-np.arange(m) / SR * 150)
    return s * 0.8
def creak(): n = int(0.45 * SR); t = np.arange(n) / SR; return np.sign(np.sin(2 * np.pi * (90 + 40 * t) * t)) * band(rng.normal(0, 1, n), 200, 1200) * np.sin(np.pi * t / 0.45) * 0.25
def wind(dur):
    n = int(dur * SR); x = band(rng.normal(0, 1, n), 150, 900); t = np.arange(n) / SR
    g = 0.6 + 0.4 * np.sin(2 * np.pi * 0.31 * t) * np.sin(2 * np.pi * 0.13 * t + 1)
    return x / (np.abs(x).max() or 1) * g * np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 0.6) * 0.5

# ---------------- SFX cues for this video: (time, sound, gain, name) ----------------
# Times come from the narration (cue/end) with the same offsets the scenes use; keep the two in step when you edit.
sfx = np.zeros(N); cues = []
def S(t, fn, gain, name):
    if t is None: return
    add(sfx, t, fn() if callable(fn) else fn, gain); cues.append({"t": round(t, 3), "sfx": name})
S(0.55, lambda: thump(70), 0.7, "bag lands")                                         # s1: tDrop + spring
S(cue("W1", "never"), tick, 0.5, "print")
for i in range(1, 5): S(cue("W2", None, 0.15 + (i - 1) * 0.62), tick, 0.5, "print")
S(cue("W2", "quarter", -0.2), pop, 0.35, "slip")
t0 = cue("A1", None, 0.5)                                                              # s2: readings 6..64 print
for j in range(5, 64): S(t0 + 2.3 * ((j - 5) / 58) ** 0.62 if t0 is not None else None, lambda: tick(4200), 0.18, "print")
S(cue("A2", None, -1.6), lambda: whoosh(1.2, True), 0.45, "frame in")
for sub, off in (("Four", 0.25), ("sixteen", 0.2), ("0.06", 0.45)): S(cue("A2", sub, off), lambda: pop(700), 0.35, "point")
S(cue("A3", "root n", 0.55), lambda: whoosh(1.3, False), 0.4, "frame out")
S(cue("A3", "standard"), slam, 0.55, "stamp"); S(cue("A3", "standard", 0.45), flip, 0.6, "card flip")
S(cue("C1", None, 0.15), creak, 0.6, "window")                                        # s3
w0, w1 = cue("C1", None, 0.3), cue("E1", None, -0.6)
if w0 is not None and w1 is not None: S(w0, wind(w1 - w0 + 0.6), 0.35, "draught")
for sub, off in (("Then", 0.1), ("stalls", -0.1), ("even", 0.1), ("sixty", 0.2)): S(cue("C2", sub, off), lambda: pop(520), 0.35, "point")
S(cue("C2", "stalls"), crack, 0.5, "rung cracks")
S(cue("E1", None, -0.6), lambda: thump(110), 0.35, "window shuts")                      # s4
S(cue("E1", "own", -0.3), flip, 0.5, "note"); S(cue("E1", "not the shared", -0.1), flip, 0.5, "note")
S(end("E1", 0.4), lambda: bell(1318.5), 0.3, "end chime")

# ---------------- mix ----------------
mix = voice + music + sfx
peak = np.abs(mix).max() or 1.0
mix = mix / peak * 0.89
def write(p, x):
    y = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(y[:, None], 2, 1).tobytes())
write(OUT / "mix.wav", mix[: int(T * SR)])
for name, x in (("voice", voice), ("music", music), ("sfx", sfx)): write(OUT / f"stem_{name}.wav", x[: int(T * SR)] / peak * 0.89)
(OUT / "cues.json").write_text(json.dumps(cues, indent=1))
print(f"work/audio/mix.wav: {T:.1f}s, {len(cues)} sfx" + (", voice" if TL.get("voice") else ", no voice") + (", music" if bed else ", no music"))
if missing: print("cues not found (edit the SFX table):", missing)
