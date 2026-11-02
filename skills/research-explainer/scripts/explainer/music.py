"""Soft ambient music bed, synthesised with numpy (no third-party audio, no licence issues). Usage: python3 music.py <seconds> <out.wav>"""
import sys, wave, numpy as np
sec = float(sys.argv[1]); out = sys.argv[2]
sr = 44100
t = np.arange(int(sec * sr)) / sr
def hz(midi): return 440.0 * 2 ** ((midi - 69) / 12)
# A minor pad progression: Am  F  C  G  (low register), 8 s per chord, 2.5 s crossfades
chords = [[57, 60, 64, 67], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]
seg = 8.0; xf = 2.5
L = np.zeros_like(t); R = np.zeros_like(t)
rng = np.random.default_rng(7)
n_seg = int(np.ceil(sec / seg)) + 1
for k in range(n_seg):
    ch = chords[k % len(chords)]
    s0 = k * seg - xf; s1 = k * seg + seg + xf
    env = np.clip(np.minimum((t - s0) / xf, (s1 - t) / xf), 0, 1)
    env = env * env * (3 - 2 * env)  # smoothstep
    if not env.any():
        continue
    for m in ch:
        f = hz(m - 12)
        for side, det in ((L, -0.25), (R, 0.25)):
            ph = rng.uniform(0, 2 * np.pi)
            side += env * (np.sin(2 * np.pi * (f + det) * t + ph) * 0.50
                           + np.sin(2 * np.pi * (2 * f + det) * t + ph) * 0.16
                           + np.sin(2 * np.pi * (3 * f) * t + ph) * 0.05)
# slow breathing
breath = 0.85 + 0.15 * np.sin(2 * np.pi * 0.07 * t)
L *= breath; R *= breath
# gentle plucks on the chord root every 2 s, an octave up, decaying
pl = np.zeros_like(t)
for k in range(int(sec / 2.0)):
    st = k * 2.0 + 0.5
    ch = chords[int(st // seg) % len(chords)]
    f = hz(ch[(k // 2) % len(ch)])
    i0 = int(st * sr); n = int(1.6 * sr)
    if i0 + n > len(t): n = len(t) - i0
    tt = np.arange(n) / sr
    pl[i0:i0 + n] += np.exp(-tt * 3.2) * np.sin(2 * np.pi * f * tt) * 0.35 * (1 - np.exp(-tt * 200))
L += pl * 0.9; R += pl * 1.1
# fade in/out, normalise to -14 dBFS peak
fade = np.clip(np.minimum(t / 3.0, (sec - t) / 4.0), 0, 1)
L *= fade; R *= fade
pk = max(np.abs(L).max(), np.abs(R).max())
g = 10 ** (-14 / 20) / pk
x = np.stack([L * g, R * g], 1)
with wave.open(out, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((x * 32767).astype(np.int16).tobytes())
print(f"wrote {out}: {sec:.1f}s, peak {20*np.log10(np.abs(x).max()):.1f} dBFS")
