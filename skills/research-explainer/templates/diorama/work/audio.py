"""audio.py: the soundtrack -> work/audio/mix.wav (48 kHz stereo) + stems (voice, music, sfx) + cues.json.
  - voice: the clips timeline.py used (voice/<lang>_final or _proc), each placed at its beat's start (none: text-only)
  - music: the original score work/music/score.wav when it exists (work/music.py: stereo, already shaped, normalised
    here to its reference bed from score_meta.json), else an optional bed of your own licensed track,
    work/music/bed.(wav|mp3|flac|m4a), looped with crossfades; either is ducked ~18 dB under speech and ~8 dB in pauses
    (no file: no music). With a voice and music it prints voice minus music under speech (median, p5, and at 1-4 kHz).
  - SFX: synthesized here (numpy only), placed on narration cues by the SFX table below; edit it for your video.
    A cue that is not in its beat's text is listed at the end instead of crashing. Then, when work/audio/motion_events.json
    exists (node work/probe_motion.mjs), a quiet automatic sound on each visible motion the table does not cover.
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
def load(path, ch=1):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64); return x if ch == 1 else x.reshape(-1, ch)
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

# ---------------- music: the composed score, else a bed (optional) ----------------
music = np.zeros(N)
duck = 10 ** (np.where(smooth(speech, 0.25) > 0.05, -18, -8) / 20) if TL.get("voice") else np.full(N, 10 ** (-6 / 20))
score = ROOT / "work/music/score.wav"
bed = None if score.exists() else next((p for ext in ("wav", "mp3", "flac", "m4a") for p in [ROOT / f"work/music/bed.{ext}"] if p.exists()), None)
if score.exists():
    src = load(score, 2)[:N]; meta = ROOT / "work/music/score_meta.json"
    ref = json.loads(meta.read_text()).get("ref_rms") if meta.exists() else None
    if not ref:                                                    # no meta: the RMS of the score where it plays
        p = np.mean(src ** 2, 1); ref = float(np.sqrt(np.mean(p[p > 1e-7]))) if np.any(p > 1e-7) else 1.0
    music = np.zeros((N, 2)); music[:len(src)] = src / ref * 0.12  # the reference bed (energy 5) at the old bed's level
    music *= smooth(duck, 0.3)[:, None]
    if abs(len(src) - int(T * SR)) > 1: print(f"score.wav is {len(src) / SR:.3f} s, the video {T:.3f} s: run work/music.py again")
    bed = score
    print(f"music: {score.relative_to(ROOT)} (composed score)")
elif bed:
    src = load(bed); src /= (np.sqrt(np.mean(src ** 2)) or 1); xf = int(2.0 * SR); pos = 0
    while pos < N:
        L = min(len(src), N - pos); piece = src[:L].copy()
        if pos > 0: piece[:min(xf, L)] *= np.linspace(0, 1, min(xf, L))
        if pos + L < N and L > xf: piece[-xf:] *= np.linspace(1, 0, xf)
        music[pos:pos + L] += piece; pos += L - (xf if pos + L < N else 0)
    fade = np.minimum(1, np.arange(N) / (1.5 * SR)) * np.minimum(1, (T * SR - np.arange(N)).clip(0) / (2.0 * SR))
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
def wood(): n = int(0.12 * SR); t = np.arange(n) / SR; return (np.sin(2 * np.pi * 820 * t) + 0.5 * np.sin(2 * np.pi * 1650 * t)) * np.exp(-t * 55) * 0.5
def bonk(): n = int(0.3 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * (300 + 200 * np.exp(-t * 30)) * t) * np.exp(-t * 16) * 0.6
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

# ---------------- automatic SFX: a quiet sound on every visible motion the table above does not cover ----------------
# From work/audio/motion_events.json (node work/probe_motion.mjs: paper components appearing, ribbon pins, camera
# moves, the rung climb into each scene); without that file nothing happens. An event within NEAR = 0.22 s of a
# hand-placed cue is left to that cue; at most 10 sounds a second; a quick run (events < 0.25 s apart) turns into soft
# rising ticks from its third event; a camera move of at least MOVE_MIN s (faster than MOVE_PEAK screen px/s) gets a
# quiet whoosh. Re-run the probe after every timing change. AUTO: (sound, gain) per component, well under the hand cues.
MOT = OUT / "motion_events.json"; n_auto = 0
if MOT.exists():
    import bisect
    M = json.loads(MOT.read_text())
    hand = sorted(c["t"] for c in cues)
    def near(t, w): i = bisect.bisect_left(hand, t - w); return i < len(hand) and hand[i] <= t + w
    def sticky(): th = thump(90) * 0.4; fl = flip(); return th + np.pad(fl, (0, len(th) - len(fl)))
    AUTO = {"Slip": (flip, 0.24), "Torn": (flip, 0.2), "Sticky": (sticky, 0.3), "Stamp": (slam, 0.4), "TermCard": (flip, 0.28),
            "Chip": (lambda: pop(1100), 0.22), "Bubble": (lambda: pop(750), 0.2), "Check": (lambda: bell(1046.5, 1.0, 0.5), 0.2),
            "Cross": (bonk, 0.26), "Plot": (flip, 0.24), "Point": (lambda: pop(700), 0.18), "Line": (lambda: tick(2200), 0.2),
            "Pin": (wood, 0.3)}
    NEAR, MOVE_MIN, MOVE_PEAK = 0.22, 0.4, 300
    def A(t, fn, g, name):
        global n_auto
        S(t, fn, g, "auto " + name); n_auto += 1
    ev = sorted([(e["t"], e["key"].split("|")[0]) for e in M.get("appear", [])] + [(p["t"], "Pin") for p in M.get("pins", [])])
    last, run, placed = -9.0, 0, []
    for t, comp in ev:
        if t > T - 0.5 or comp not in AUTO or near(t, NEAR): continue      # a hand-placed cue covers it
        run = run + 1 if t - last < 0.25 else 0; last = t
        if placed and t - placed[-1] < 0.1: continue                         # at most 10 a second
        if run >= 2: A(t, lambda r=run: tick(1700 + 80 * min(r, 20)), 0.18, "cascade")
        else: fn, g = AUTO[comp]; A(t, fn, g, comp.lower())
        placed.append(t)
    for s in M.get("shots", []):                                             # the rung climb: the picture slides down
        if s["t"] < T - 0.5 and not near(s["t"], NEAR): A(s["t"], lambda: whoosh(0.9, False), 0.12, "shot")
    hand = sorted(hand + [s["t"] for s in M.get("shots", [])])
    for k, m in enumerate(M.get("moves", [])):
        if m["dur"] < MOVE_MIN or m["peak"] < MOVE_PEAK or m["t"] > T - 0.5 or near(m["t"], NEAR): continue   # cuts and drifts: no sound
        d = min(1.6, max(0.6, m["dur"] * 0.9)); g = float(np.clip(0.1 + 0.05 * np.log10(m["peak"] / 500), 0.1, 0.22))
        A(m["t"], lambda d=d, k=k: whoosh(d, k % 2 == 0), g, "camera")

# ---------------- mix ----------------
mix = (voice + sfx)[:, None] + (music if music.ndim == 2 else music[:, None])   # voice and SFX in the centre
peak = np.abs(mix).max() or 1.0
mix = mix / peak * 0.89
def write(p, x):
    y = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    if y.ndim == 1: y = np.repeat(y[:, None], 2, 1)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())
write(OUT / "mix.wav", mix[: int(T * SR)])
for name, x in (("voice", voice), ("music", music), ("sfx", sfx)): write(OUT / f"stem_{name}.wav", x[: int(T * SR)] / peak * 0.89)
(OUT / "cues.json").write_text(json.dumps(cues, indent=1))
print(f"work/audio/mix.wav: {T:.1f}s, {len(cues)} sfx ({n_auto} automatic" + ("" if MOT.exists() else ": no work/audio/motion_events.json") + ")" + (", voice" if TL.get("voice") else ", no voice") + (", music" if bed else ", no music"))
if missing: print("cues not found (edit the SFX table):", missing)
if TL.get("voice") and np.any(music):           # brief check: voice minus music under speech, 0.4 s windows
    W = int(0.4 * SR); n = int(T * SR) // W; mu = music if music.ndim == 2 else music[:, None]
    v = voice[: n * W].reshape(n, W); m = mu[: n * W].mean(1).reshape(n, W); sp = speech[: n * W].reshape(n, W).mean(1) > 0.9
    vd = 10 * np.log10(np.mean(v ** 2, 1) + 1e-12); md = 10 * np.log10(np.mean(m ** 2, 1) + 1e-12)
    ok = sp & (vd > -50); ok &= vd > (np.median(vd[ok]) - 10 if ok.any() else -50)   # speech frames: not the pauses inside a clip
    if ok.any():
        d = (vd - md)[ok]; bd = []; F = np.fft.rfftfreq(W, 1 / SR); bm = (F >= 1000) & (F < 4000)
        for i in np.where(ok)[0]:                   # 1-4 kHz band levels
            bd.append(10 * np.log10(np.sum(np.abs(np.fft.rfft(v[i])[bm]) ** 2) + 1e-12) - 10 * np.log10(np.sum(np.abs(np.fft.rfft(m[i])[bm]) ** 2) + 1e-12))
        print(f"voice minus music under speech: median {np.median(d):.1f} dB, p5 {np.percentile(d, 5):.1f} dB "
              f"(want >= 18 / >= 14); at 1-4 kHz median {np.median(bd):.1f} dB (want >= 12)")
