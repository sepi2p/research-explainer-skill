"""srt.py [lang ...]: subtitles (.srt) from the beat timeline: each beat split into sentences, timed by length (or by
the spoken times in the beat's "ct" when the voice was word-aligned). Default: every language the beats carry.
Writes work/subs_<lang>.srt."""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "timeline.json").read_text())
def ts(x):
    h, r = divmod(x, 3600); m, s = divmod(r, 60); return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"
def split(text):
    parts = re.split(r"(?<=[.!?؟])\s+", text.strip())
    out = []
    for p in parts:   # long sentences: split at a comma near the middle
        if len(p) > 70 and ("،" in p or "," in p):
            sep = "،" if "،" in p else ","
            bits = p.split(sep); half = len(bits) // 2
            out += [sep.join(bits[:half]) + sep, sep.join(bits[half:]).strip()]
        else: out.append(p)
    return [p for p in out if p]
def clean(t): return " ".join(t.replace("⏸", " ").split())
langs = sys.argv[1:] or sorted({TL["lang"]} | {k for b in TL["beats"] for k in ("en", "fa") if k in b})
for lang in langs:
    n, lines = 1, []
    for b in TL["beats"]:
        text = b["text"] if lang == TL["lang"] else b.get(lang)
        if not text or not b["dur"]: continue
        parts = split(text)
        if lang == TL["lang"] and b.get("ct") and len(b["ct"]) == len(text):   # real spoken times
            starts, pos = [], 0
            for p in parts:
                i = text.find(p.split()[0] if p.split() else p, pos); pos = max(pos, i); starts.append(b["start"] + b["ct"][max(0, i)])
            starts[0] = b["start"]; ends = starts[1:] + [b["end"]]
            for p, a, e in zip(parts, starts, ends):
                lines.append(f"{n}\n{ts(a)} --> {ts(max(a + 0.5, e - 0.05))}\n{clean(p)}\n"); n += 1
            continue
        t, tot = b["start"], sum(len(p) for p in parts)
        for p in parts:
            d = b["dur"] * len(p) / tot
            lines.append(f"{n}\n{ts(t)} --> {ts(t + d - 0.05)}\n{clean(p)}\n"); n += 1; t += d
    (ROOT / f"work/subs_{lang}.srt").write_text("\n".join(lines))
    print(f"work/subs_{lang}.srt: {n - 1} cues")
