"""Beat grid for launch videos, numpy only (run with the Python that has numpy; rx.py does this).

  python3 beat.py synth out.wav --duration 23 --bpm 120 [--drop 4] [--offset 0.8] [--seed 7] [--mood dark|bright]
  python3 beat.py synth out.wav --sections intro:4,build:4,drop:8,groove:8,break:4,build:2,lift:8 [--bpm 120]
      an original track synthesized in code (no licence questions), and out.beats.json with its exact grid
      (a short track has one drop; --sections arranges a long one: see SECTIONS)
  python3 beat.py measure track.mp3 [--out track.beats.json]
      bpm, beats, downbeats and hits measured from a track you supply

beats.json: {"bpm", "beats": [s...], "downbeats": [s...], "hits": [s...], "drop": s}
State changes go on beats, big moments on downbeats, sound effects on hits.
"""
import argparse, json, pathlib, subprocess, sys, wave
import numpy as np

SR = 48000


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- synth
# An arrangement is a list of sections, each a number of bars of one kind:
#   intro  pad only, filter opening            build  kick quarters swelling, hats, snare roll into the next drop
#   drop   everything (kick, clap, bass, hats, open hats, pluck arpeggio)
#   groove drop without open hats, quieter pluck (verses: room for the picture)
#   break  no kick or bass: pad and a soft pluck (tension, a quiet moment)
#   lift   drop plus a lead melody (the big moments)
#   outro  one bar: the last chord rings out over a final hit
# A section followed by a drop or lift ends with a riser, a snare roll and half a beat of silence.
SECTIONS = {   # pad filter (start, end) Hz, pad level, kick, clap, bass, 16th hats, open hats, pluck, lead
    "intro":  dict(cut=(400, 3000), pad=.9, kick=0, clap=0, bass=0, h16=0, ohat=0, pluck=0, lead=0),
    "build":  dict(cut=(1200, 3200), pad=.85, kick=1, clap=0, bass=0, h16=.5, ohat=0, pluck=.45, lead=0),
    "drop":   dict(cut=(3000, 3000), pad=.8, kick=1, clap=1, bass=1, h16=.7, ohat=1, pluck=1, lead=0),
    "groove": dict(cut=(2200, 2200), pad=.7, kick=1, clap=1, bass=1, h16=.45, ohat=0, pluck=.55, lead=0),
    "break":  dict(cut=(700, 1500), pad=1.0, kick=0, clap=0, bass=0, h16=.22, ohat=0, pluck=.5, lead=0),
    "lift":   dict(cut=(3600, 3600), pad=.8, kick=1, clap=1, bass=1, h16=.8, ohat=1, pluck=.75, lead=1),
    "outro":  dict(cut=(2500, 2500), pad=1.0, kick=0, clap=0, bass=0, h16=0, ohat=0, pluck=0, lead=0),
}
ENERGY = ("drop", "groove", "lift")
# lead phrase per chord (keyed by the chord root's pitch class): (start eighth, length in eighths, midi note)
LEAD = {9: [(0, 2, 76), (2, 2, 81), (4, 1, 79), (5, 1, 76), (6, 2, 74)],
        5: [(0, 3, 72), (3, 1, 74), (4, 2, 76), (6, 2, 77)],
        0: [(0, 2, 79), (2, 2, 76), (4, 2, 72), (6, 2, 76)],
        7: [(0, 3, 74), (3, 1, 71), (4, 4, 74)]}


def parse_sections(spec):
    """'intro:4,build:4,drop:8' or [["intro", 4], ...] -> [("intro", 4), ...]"""
    if isinstance(spec, str):
        spec = [p.split(":") for p in spec.replace(" ", "").split(",") if p]
    out = []
    for k, nb in spec:
        if k not in SECTIONS:
            raise SystemExit(f"unknown section '{k}': use {', '.join(SECTIONS)}")
        out.append((k, int(nb)))
    return out


def synth(duration=None, bpm=120, drop=None, seed=7, mood="dark", sections=None):
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    bar = 4 * beat
    if sections is None:   # the short default: intro, one drop, a ringing last bar
        intro = max(1, round((drop if drop is not None else 2 * bar) / bar))
        outro = max(intro + 1, int((duration - 2.0) // bar))
        sections = [("intro", intro), ("drop", outro - intro), ("outro", 1)]
    sections = parse_sections(sections)
    if sections[-1][0] != "outro":
        sections.append(("outro", 1))
    kinds, pos = [], []                      # per bar: kind, (index in section, section length, next kind)
    for si, (k, nb) in enumerate(sections):
        nxt = sections[si + 1][0] if si + 1 < len(sections) else None
        for i in range(nb):
            kinds.append(k); pos.append((i, nb, nxt))
    n_b = len(kinds)
    t_end = (n_b - 1) * bar
    if duration is None:
        duration = t_end + max(bar, 3.0)
    n = int((duration + 2.5) * SR)
    t = np.arange(n) / SR
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]] if mood == "dark" else \
           [[48, 52, 55], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
    alt = [[53, 57, 60], [55, 59, 62], [52, 55, 59], [57, 60, 64]]   # breaks: IV - V - iii - vi, a change of colour
    chord = lambda b: alt[b % 4] if kinds[min(b, n_b - 1)] == "break" else prog[b % 4]
    S = lambda b: SECTIONS[kinds[min(b, n_b - 1)]]
    rising = lambda b: b < n_b and pos[b][0] == pos[b][1] - 1 and pos[b][2] in ("drop", "lift")
    stop_at = lambda b: b * bar + bar - beat / 2           # half a beat of silence before a drop
    L = np.zeros(n); R = np.zeros(n)

    def env_at(i0, length, attack=0.003, decay=8.0):
        tt = np.arange(length) / SR
        return tt, np.minimum(1, tt / attack) * np.exp(-tt * decay)

    def add(sig, at, gl=1.0, gr=1.0):
        i0 = int(at * SR)
        if i0 >= n or i0 < 0:
            return
        m = min(len(sig), n - i0)
        L[i0:i0 + m] += sig[:m] * gl; R[i0:i0 + m] += sig[:m] * gr

    def silent(at, b):
        return rising(b) and at >= stop_at(b) - 1e-9

    # kicks: four on the floor in energy sections; swelling quarters in a build
    kicks = []
    for b in range(n_b - 1):
        k, (i, nb, _) = kinds[b], pos[b]
        if not S(b)["kick"]:
            continue
        for q in range(4):
            at = b * bar + q * beat
            if silent(at, b):
                continue
            g = 1.0 if k in ENERGY else 0.45 + 0.55 * (i + q / 4) / nb
            kicks.append((at, g))

    # sidechain: everything melodic ducks under each kick
    duck = np.ones(n)
    for at, g in kicks:
        i0 = int(at * SR); m = min(int(0.35 * SR), n - i0)
        if m > 0:
            duck[i0:i0 + m] = np.minimum(duck[i0:i0 + m], 1 - 0.65 * g * np.exp(-np.arange(m) / SR / 0.09))

    # pad: detuned saws (additive, band-limited); each section moves its filter from start to end
    pad = np.zeros((2, n))
    for b in range(n_b):
        s0 = b * bar
        i0, i1 = int(s0 * SR), min(n, int((s0 + bar + 0.4) * SR))
        if i0 >= n:
            continue
        tt = t[i0:i1] - s0
        sp = S(b); (i, nb, _) = pos[b]
        c0, c1 = sp["cut"]
        cutoff = c0 + (c1 - c0) * np.clip((i + tt / bar) / nb, 0, 1) ** 2
        e = np.minimum(1, tt / 0.04) * np.clip((bar + 0.4 - tt) / 0.4, 0, 1)
        if b == n_b - 1:
            e = np.minimum(1, tt / 0.01) * np.exp(-tt * 0.9)
        if rising(b):
            e = e * np.clip((bar - beat / 2 - tt) / 0.03, 0, 1)
        e = e * sp["pad"]
        for m in chord(b):
            for ch, det in ((0, -0.08), (1, 0.08)):
                f = hz(m + det)
                ph = rng.uniform(0, 2 * np.pi)
                for h in range(1, 14):
                    if f * h > 9000:
                        break
                    w = 1 / (1 + (f * h / cutoff) ** 4)
                    pad[ch, i0:i1] += e * w * np.sin(2 * np.pi * f * h * tt + ph * h) / h * 0.09
    L += pad[0] * duck; R += pad[1] * duck

    # bass: root on the off-beat eighths, sidechained
    bass = np.zeros(n)
    for b in range(n_b - 1):
        if not S(b)["bass"]:
            continue
        for e8 in range(1, 8, 2):
            at = b * bar + e8 * beat / 2
            f = hz(chord(b)[0] - 24)
            tt, e = env_at(0, int(beat / 2 * SR * 0.95), 0.004, 5)
            sig = sum(np.sin(2 * np.pi * f * h * tt) / h ** 1.6 for h in range(1, 6))
            i0 = int(at * SR); m = min(len(sig), n - i0)
            bass[i0:i0 + m] += (sig * e)[:m] * 0.55
    L += bass; R += bass

    # pluck arpeggio in 16ths; an octave up in the second half of every 8 bars of a section, an octave down in a break
    for b in range(n_b - 1):
        g = S(b)["pluck"]
        if not g:
            continue
        i = pos[b][0]
        for s16 in range(16):
            at = b * bar + s16 * beat / 4
            if silent(at, b):
                continue
            k = b * 16 + s16
            notes = chord(b) + [chord(b)[0] + 12]
            oct_ = -12 if kinds[b] == "break" else (12 if i % 8 >= 4 else 0)
            f = hz(notes[[0, 2, 1, 3, 2, 1, 3, 2][k % 8]] + 12 + oct_)
            tt, e = env_at(0, int(0.25 * SR), 0.002, 16)
            bright = 0.08 if kinds[b] == "break" else 0.3
            sig = (np.sin(2 * np.pi * f * tt) + bright * np.sin(4 * np.pi * f * tt)) * e * 0.11 * g
            pan = 0.5 + 0.35 * np.sin(k * 0.7)
            i0 = int(at * SR)
            if i0 + len(sig) <= n:
                sig = sig * duck[i0:i0 + len(sig)]
            add(sig, at, 1 - pan + 0.5, pan + 0.5)

    # lead: a bright saw with vibrato and a dotted-eighth echo, in lift sections
    lead = np.zeros((2, n))
    for b in range(n_b - 1):
        if not S(b)["lead"]:
            continue
        up = 12 if pos[b][0] % 8 >= 4 else 0                         # the answer phrase an octave up
        for e8, ln, mnote in LEAD[chord(b)[0] % 12]:
            mnote += up
            at = b * bar + e8 * beat / 2
            if silent(at, b):
                continue
            dur = ln * beat / 2 * 0.92
            tt = np.arange(int((dur + 0.12) * SR)) / SR
            vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * tt) * np.clip((tt - 0.15) / 0.1, 0, 1)
            f = hz(mnote) * vib
            phase = 2 * np.pi * np.cumsum(f) / SR
            sig = sum(np.sin(h * phase) / h for h in range(1, 9))
            e = np.minimum(1, tt / 0.01) * np.clip((dur + 0.12 - tt) / 0.12, 0, 1) * (0.75 + 0.25 * np.exp(-tt * 6))
            sig = sig * e * 0.07
            i0 = int(at * SR); m = min(len(sig), n - i0)
            for d, gl, gr in ((0, 1, 1), (0.75 * beat, 0.45, 0.2), (1.5 * beat, 0.12, 0.3)):
                j0 = i0 + int(d * SR); mm = min(m, n - j0)
                if mm > 0:
                    lead[0, j0:j0 + mm] += sig[:mm] * gl; lead[1, j0:j0 + mm] += sig[:mm] * gr
    L += lead[0] * (0.6 + 0.4 * duck); R += lead[1] * (0.6 + 0.4 * duck)

    # drums
    def kick():
        tt, e = env_at(0, int(0.45 * SR), 0.001, 7)
        f = 48 + 110 * np.exp(-tt * 28)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * e + 0.25 * np.exp(-tt * 300) * rng.standard_normal(len(tt))) * 0.95

    def hat(length=0.05, dec=70):
        x = rng.standard_normal(int(length * SR))
        x = x - np.convolve(x, np.ones(6) / 6, mode="same")   # crude high-pass
        return x * np.exp(-np.arange(len(x)) / SR * dec) * 0.16

    def clap():
        x = rng.standard_normal(int(0.25 * SR))
        spec = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR)
        spec *= np.exp(-((fr - 1500) / 900) ** 2)
        x = np.fft.irfft(spec, len(x))
        tt = np.arange(len(x)) / SR
        e = sum(np.exp(-np.clip(tt - d, 0, None) * 60) * (tt >= d) for d in (0, 0.011, 0.023)) + 0.6 * np.exp(-tt * 14)
        return x / np.abs(x).max() * e * 0.35

    K, C = kick(), clap()
    for at, g in kicks:
        add(K * g, at)
    for b in range(n_b - 1):
        sp = S(b)
        if sp["clap"]:
            for q in (1, 3):
                add(C, b * bar + q * beat, 0.9, 1.0)
        if sp["ohat"]:
            for e8 in range(1, 8, 2):
                add(hat(0.12, 22), b * bar + e8 * beat / 2, 0.8, 1.1)   # open hat on the off-beat
        for s16 in range(16):
            at = b * bar + s16 * beat / 4
            if silent(at, b):
                continue
            g = sp["h16"]
            if rising(b):                                                # hats swell into the drop
                g = 0.35 + 0.65 * s16 / 16
            if g:
                add(hat() * g, at, 1.1, 0.8)
        if rising(b) and kinds[b] != "intro":                            # snare roll: 8ths, then 16ths
            for s16 in range(16):
                at = b * bar + s16 * beat / 4
                if silent(at, b) or (s16 < 8 and s16 % 2):
                    continue
                add(C * (0.3 + 0.6 * s16 / 16), at, 0.9, 1.0)

    # riser into each drop: noise with a rising band + an upward sweep over the last bar
    for b in range(n_b):
        if not rising(b):
            continue
        i0 = int(b * bar * SR); i1 = int(stop_at(b) * SR)
        m = i1 - i0
        x = rng.standard_normal(m)
        p = np.linspace(0, 1, m)
        hp = x - np.convolve(x, np.ones(24) / 24, mode="same")
        sweep = np.sin(2 * np.pi * np.cumsum(200 + 1800 * p ** 2) / SR)
        r = (hp * 0.12 + sweep * 0.05) * p ** 2.2
        L[i0:i1] += r; R[i0:i1] += r

    def impact():
        tt = np.arange(int(1.8 * SR)) / SR
        f = 30 + 60 * np.exp(-tt * 9)
        boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.2)
        nz = rng.standard_normal(len(tt)) * np.exp(-tt * 9) * 0.4
        return (boom + nz) * 0.8
    starts, tb = [], 0
    for k, nb in sections:
        starts.append((k, tb * bar, nb)); tb += nb
    drops = [s for k, s, _ in starts if k in ("drop", "lift")]
    for k, s, _ in starts:
        if k in ("drop", "lift"):
            add(impact(), s)
        elif k == "break" and s > 0:
            add(impact() * 0.45, s)
    add(impact() * 0.8, t_end)
    add(K, t_end)

    # small room: FFT convolution with a decaying noise tail
    ir_n = int(1.3 * SR)
    ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR * 4.5)
    ir[0] = 0
    size = 1 << int(np.ceil(np.log2(n + ir_n)))
    IR = np.fft.rfft(ir, size)
    wetL = np.fft.irfft(np.fft.rfft(L, size) * IR, size)[:n]
    wetR = np.fft.irfft(np.fft.rfft(R, size) * IR, size)[:n]
    wg = 0.18 / (np.abs(wetL).max() + 1e-9) * np.abs(L).max()
    L += wetL * wg; R += wetR * wg

    x = np.stack([L, R], 1)
    x = np.tanh(x / (np.abs(x).max() + 1e-9) * 1.6) / np.tanh(1.6) * 0.89
    x = x[:int(duration * SR)]
    beats = [round(k * beat, 4) for k in range(int(duration / beat) + 1)]
    t_drop = drops[0] if drops else 0.0
    grid = {"bpm": bpm, "beats": beats, "downbeats": beats[::4], "drop": round(t_drop, 4), "end_hit": round(t_end, 4),
            "drops": [round(s, 4) for s in drops],
            "sections": [{"kind": k, "start": round(s, 4), "bars": nb} for k, s, nb in starts],
            "hits": sorted(set([round(s, 4) for s in drops] + [round(k, 4) for k, _ in kicks if round(k / beat) % 4 == 0]
                               + [round(t_end, 4)])),
            "source": f"synthesized by beat.py (bpm {bpm}, seed {seed}, mood {mood}); original, no third-party audio"}
    return x, grid


def write_wav(path, x):
    with wave.open(str(path), "w") as w:
        w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- measure
def load_mono(path, sr=22050):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64), sr


def measure(path):
    y, sr = load_mono(path)
    hop, win = 256, 1024
    LAG = 1.0 + win / 2 / hop   # flux k compares frames k and k+1; a frame's time is its window centre
    frames = np.lib.stride_tricks.sliding_window_view(y, win)[::hop] * np.hanning(win)
    mag = np.log1p(np.abs(np.fft.rfft(frames, axis=1)) * 10)
    flux = np.maximum(0, np.diff(mag, axis=0))
    low = flux[:, :24].sum(1)                     # below ~500 Hz: kicks, downbeats
    onset = flux.sum(1)
    onset = onset - np.convolve(onset, np.ones(16) / 16, mode="same")
    onset = np.maximum(onset, 0)
    fps = sr / hop
    # tempo: autocorrelation of the onset envelope, 70-180 BPM, prefer 90-150
    ac = np.correlate(onset, onset, mode="full")[len(onset) - 1:]
    lags = np.arange(len(ac))
    bpms = 60 * fps / np.maximum(lags, 1)
    ok = (bpms >= 70) & (bpms <= 180)
    weight = np.exp(-0.5 * (np.log2(bpms / 120) / 0.5) ** 2)
    lag = lags[ok][np.argmax((ac * weight)[ok])]
    # refine the period to a fraction of a frame
    period = lag
    best = -1
    for p in np.linspace(lag - 1, lag + 1, 41):
        idx = np.arange(0, len(onset) - 1, p)
        s = onset[np.round(idx).astype(int)].sum()
        if s > best:
            best, period = s, p
    # phase: the offset whose comb catches the most low-band (kick) energy, then the off-beat check with all bands
    lowe = np.maximum(low - np.convolve(low, np.ones(16) / 16, mode="same"), 0)
    drive = lowe / (lowe.max() + 1e-9) + 0.3 * onset / (onset.max() + 1e-9)
    phases = np.arange(int(np.ceil(period)))
    score = [drive[np.round(np.arange(ph, len(drive) - 1, period)).astype(int)].sum() for ph in phases]
    ph = phases[int(np.argmax(score))]
    # refine: snap every predicted beat to its local peak (+-60 ms) and fit period and phase by least squares
    idx = np.arange(ph, len(drive) - 1, period)
    r = int(0.06 * fps)
    peaks, ks = [], []
    for k, c in enumerate(idx):
        c = int(round(c)); a0, a1 = max(0, c - r), min(len(drive), c + r + 1)
        j = a0 + int(np.argmax(drive[a0:a1]))
        if drive[j] > 0.15 * drive.max():
            peaks.append(j); ks.append(k)
    ks, peaks = np.array(ks, float), np.array(peaks, float)
    for _ in range(3):                      # robust fit: drop beats more than 1.5 frames off the line, refit
        if len(peaks) < 8:
            break
        period, ph = np.polyfit(ks, peaks, 1)
        keep = np.abs(peaks - (ph + period * ks)) <= 1.5
        if keep.all():
            break
        ks, peaks = ks[keep], peaks[keep]
    beat_pos = np.arange(ph, len(drive) - 1, period)
    beat_pos = beat_pos[beat_pos >= 0]
    beat_idx = np.round(beat_pos).astype(int)
    beats = ((beat_pos + LAG) / fps).round(3)
    # downbeat: which of the 4 positions has the most low-frequency energy
    acc = [low[beat_idx[k::4]].sum() for k in range(4)]
    k0 = int(np.argmax(acc))
    # hits: strongest onsets, at least 0.25 s apart
    order = np.argsort(onset)[::-1]
    hits, gap = [], 0.25 * fps
    thr = np.percentile(onset, 99)
    for i in order:
        if onset[i] < thr:
            break
        if all(abs(i - j) > gap for j in hits):
            hits.append(i)
    # drop guess: the biggest rise in loudness (0.5 s after vs 0.5 s before), snapped to the nearest downbeat
    half = int(0.5 * sr)
    c = np.concatenate([[0], np.cumsum(y ** 2)])
    pos = np.arange(half, len(y) - half, hop)
    rise = np.sqrt((c[pos + half] - c[pos]) / half) - np.sqrt((c[pos] - c[pos - half]) / half)
    drop = float(pos[int(np.argmax(rise))] / sr) if len(pos) else 0.0
    downs = beats[k0::4]
    if len(downs):
        near = downs[int(np.argmin(np.abs(downs - drop)))]
        if abs(near - drop) < 60 / (60 * fps / period) * 1.0:
            drop = float(near)
    return {"bpm": round(60 * fps / period, 2), "beats": beats.tolist(), "downbeats": beats[k0::4].tolist(),
            "hits": sorted(((np.array(hits) + LAG) / fps).round(3).tolist()), "drop": round(drop, 3),
            "duration": round(len(y) / sr, 3), "source": f"measured from {pathlib.Path(path).name} by beat.py"}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("synth"); s.add_argument("out"); s.add_argument("--duration", type=float, help="seconds (default: the length of --sections)")
    s.add_argument("--bpm", type=float, default=120); s.add_argument("--drop", type=float)
    s.add_argument("--seed", type=int, default=7); s.add_argument("--mood", default="dark", choices=["dark", "bright"])
    s.add_argument("--offset", type=float, default=0.0, help="seconds of silence before the first downbeat")
    s.add_argument("--sections", help="arrangement, e.g. intro:4,build:4,drop:8,break:4,build:2,lift:8 (bars); see SECTIONS")
    m = sub.add_parser("measure"); m.add_argument("track"); m.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "synth":
        off = max(0.0, a.offset)
        if a.duration is None and not a.sections:
            raise SystemExit("give --duration or --sections")
        x, grid = synth(None if a.duration is None else a.duration - off, a.bpm, a.drop, a.seed, a.mood, a.sections)
        if off > 0:   # the grid starts at `offset` (the first downbeat); earlier beats stay as pickups in "beats"
            x = np.concatenate([np.zeros((int(off * SR), 2)), x])
            b = 60.0 / a.bpm
            pick = [round(off - k * b, 4) for k in range(int(off / b), 0, -1)]
            for k in ("beats", "downbeats", "hits"):
                grid[k] = [round(v + off, 4) for v in grid[k]]
            grid["beats"] = pick + grid["beats"]
            grid["drop"] = round(grid["drop"] + off, 4); grid["end_hit"] = round(grid["end_hit"] + off, 4)
            grid["drops"] = [round(v + off, 4) for v in grid["drops"]]
            for sec in grid["sections"]:
                sec["start"] = round(sec["start"] + off, 4)
            grid["offset"] = off
        out = pathlib.Path(a.out)
        write_wav(out, x)
        bj = out.with_suffix(".beats.json")
        bj.write_text(json.dumps(grid, indent=1))
        print(f"{out}: {len(x) / SR:.1f}s at {a.bpm:g} BPM, first downbeat {grid['downbeats'][0]}s, drop at {grid['drop']}s, end hit at {grid['end_hit']}s; grid in {bj}")
    else:
        g = measure(a.track)
        out = pathlib.Path(a.out) if a.out else pathlib.Path(a.track).with_suffix(".beats.json")
        out.write_text(json.dumps(g, indent=1))
        print(f"{out}: {g['bpm']} BPM, {len(g['beats'])} beats, first downbeat {g['downbeats'][0] if g['downbeats'] else '-'}s, "
              f"loudest jump (drop?) at {g['drop']}s")


if __name__ == "__main__":
    sys.exit(main())
