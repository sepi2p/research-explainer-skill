"""timeline.py [--lang en] [--captions] [--cps 17]: the beat timeline -> video/timeline.js (window.TL) + timeline.json.

Beat lengths come from the voice clips when they exist (voice/<lang>_final/ from pauses.py, else voice/<lang>_proc/
from proc_voice.py: durations.json, plus chartimes.json for word-timed cues), otherwise from reading time
(text-only video: the narration is shown as captions). --captions also burns captions over a voiced video.
Scenes read the times with E.B('W1').start, E.cue('A3', 'standard error'), ... (video/engine/core.js)."""
import argparse, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
nar = json.loads((ROOT / "narration.json").read_text())
ap = argparse.ArgumentParser()
ap.add_argument("--lang", default=nar.get("lang", "en"))
ap.add_argument("--captions", action="store_true", help="draw the narration on screen even with a voice")
ap.add_argument("--cps", type=float, default=None, help="reading speed for text-only timing, characters per second")
a = ap.parse_args()
LANG = a.lang
CPS = a.cps or {"en": 17, "fa": 13}.get(LANG, 15)   # comfortable caption reading speed
LEAD = 0.5          # first word at 0.5 s
PAD = 0.25          # breath after every beat (plus the beat's own "pause")
SCENE_GAP = 1.0     # between scenes: the rung climb (main.js GAP must match)
END_HOLD = 1.6      # picture only after the last word
READ_EXTRA = 0.4    # text-only: time to take in a caption beyond its reading time

vdir = next((d for d in (ROOT / f"voice/{LANG}_final", ROOT / f"voice/{LANG}_proc") if (d / "durations.json").exists()), None)
D = json.loads((vdir / "durations.json").read_text()) if vdir else {}
CT = json.loads((vdir / "chartimes.json").read_text()) if vdir and (vdir / "chartimes.json").exists() else {}
beats, t, prev = [], LEAD, None
for s in nar["scenes"]:
    for b in s["beats"]:
        text = b.get(LANG)
        if text is None: raise SystemExit(f"beat {b['id']} has no '{LANG}' text in narration.json")
        if prev and s["id"] != prev: t += SCENE_GAP
        spoken = text.replace("⏸", " ")
        d = D.get(b["id"]) or round(max(1.6, len(" ".join(spoken.split())) / CPS + READ_EXTRA), 3)
        rec = {"id": b["id"], "scene": s["id"], "start": round(t, 3), "dur": d, "end": round(t + d, 3), "text": text}
        for k in ("en", "fa"):
            if k in b: rec[k] = b[k]
        if b["id"] in CT: rec["ct"] = CT[b["id"]]
        beats.append(rec)
        t += d + PAD + b.get("pause", 0) + b.get("hold", 0)
        prev = s["id"]
total = round(beats[-1]["end"] + END_HOLD, 2)
scenes = {}
for b in beats:
    sc = scenes.setdefault(b["scene"], {"start": b["start"], "end": b["end"]}); sc["end"] = b["end"]
TL = {"total": total, "lang": LANG, "voice": bool(vdir), "captions": (not vdir) or a.captions, "beats": beats, "scenes": scenes}
(ROOT / "video/timeline.js").write_text("window.TL = " + json.dumps(TL, ensure_ascii=False) + ";\n")
(ROOT / "timeline.json").write_text(json.dumps(TL, ensure_ascii=False, indent=1))
print(f"{LANG}, {'voice from ' + vdir.name if vdir else 'text only (reading time, captions on)'}: total {total:.1f}s")
for k, v in scenes.items(): print(f"  {k:12} {v['start']:6.2f} - {v['end']:6.2f}")
