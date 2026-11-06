"""proc_voice.py [--lang en] [--stray] [beat ...]: clean the raw clips voice/<lang>/<beat>.wav ->
voice/<lang>_proc/<beat>.wav and write voice/<lang>_proc/durations.json (timeline.py then uses these lengths).
Trims leading/trailing silence (-45 dB), optionally speeds up (TEMPO=1.06 sped an OpenAI voice up by 6 %; default
1.0) and normalises each clip to -18 LUFS. --stray: also cut a stray sound that a voice model sometimes adds after
the script (a burst of at most 0.6 s after at least 0.4 s of silence); the tail is transcribed first (OpenAI, paid)
so that a real last word is kept. After it: (wordtimes.py, pauses.py), timeline.py."""
import argparse, json, os, subprocess, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
nar = json.loads((ROOT / "narration.json").read_text())
ap = argparse.ArgumentParser(); ap.add_argument("--lang", default=nar.get("lang", "en")); ap.add_argument("--stray", action="store_true"); ap.add_argument("beats", nargs="*")
a = ap.parse_args()
V, O = ROOT / f"voice/{a.lang}", ROOT / f"voice/{a.lang}_proc"; O.mkdir(parents=True, exist_ok=True)
TEMPO = float(os.environ.get("TEMPO", "1.0"))
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse")
NORM = (f"atempo={TEMPO}," if TEMPO != 1.0 else "") + "loudnorm=I=-18:TP=-2:LRA=7,aresample=48000"
# two passes: with TEMPO = 1.0, loudnorm directly after the reversed trim can deadlock ffmpeg on some clips
def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                        capture_output=True, text=True).stdout)
def stray_tail(p):
    """End of the speech when the clip ends in a short burst after a pause, else None."""
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(p), "-af", "silencedetect=noise=-35dB:d=0.4", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    st = [float(l.split("silence_start: ")[1].split()[0]) for l in r.splitlines() if "silence_start: " in l]
    en = [float(l.split("silence_end: ")[1].split()[0]) for l in r.splitlines() if "silence_end: " in l]
    if not st or len(en) < len(st): return None
    return st[-1] + 0.1 if 0 < dur(p) - en[-1] <= 0.6 else None
def tail_is_speech(p, cut):
    sys.path.insert(0, str(pathlib.Path(__file__).parent)); from narrate import transcribe
    tmp = p.with_name("_tail.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, cut - 0.1):.3f}", "-i", str(p), str(tmp)], check=True)
    txt = transcribe(tmp.read_bytes(), a.lang); tmp.unlink()
    return any(c.isalpha() for c in txt)
ids = a.beats or [b["id"] for s in nar["scenes"] for b in s["beats"]]
dp = O / "durations.json"; out = json.loads(dp.read_text()) if dp.exists() else {}
for i in ids:
    if not (V / f"{i}.wav").exists(): raise SystemExit(f"missing {V / (i + '.wav')}: record it, or run voice_piper.py / narrate.py voice")
    tmp = O / f"_trim_{i}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(V / f"{i}.wav"), "-af", TRIM, str(tmp)], check=True, timeout=120)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af", NORM, "-ac", "1", "-ar", "48000", str(O / f"{i}.wav")], check=True, timeout=120)
    tmp.unlink()
    cut = stray_tail(O / f"{i}.wav") if a.stray else None
    if cut and tail_is_speech(O / f"{i}.wav", cut):
        print(f"{i}: short sound after a pause is a spoken word; kept"); cut = None
    if cut:
        tmp = O / f"_{i}.wav"; (O / f"{i}.wav").rename(tmp)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-t", f"{cut:.3f}", str(O / f"{i}.wav")], check=True); tmp.unlink()
        print(f"{i}: cut a stray sound after {cut:.2f}s; listen to it")
    out[i] = round(dur(O / f"{i}.wav"), 3)
dp.write_text(json.dumps(out, indent=1))
print(f"voice/{a.lang}_proc: {len(ids)} clips, total {sum(out[i] for i in ids):.1f}s")
