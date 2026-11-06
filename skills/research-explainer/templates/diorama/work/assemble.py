"""assemble.py <silent video> <out.mp4> [soundtrack.wav]: mux the soundtrack (default work/audio/mix.wav, from
work/audio.py) with two-pass loudnorm to -14 LUFS, then a 4x-oversampled limiter at -2 dBFS so the true peak stays
<= -1 dBTP after the AAC encode (YouTube's upload check); AAC 192k. Prints the result's loudness and true peak.
LUFS=-20 python3 work/assemble.py ... for a quieter soundtrack (e.g. sound effects only). A text-only video needs no
assembly: the silent render is the video."""
import os, sys, json, re, subprocess, pathlib
V, OUT = sys.argv[1], sys.argv[2]
I = os.environ.get("LUFS", "-14")
A = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path(__file__).parent / "audio" / "mix.wav"
if not A.exists(): raise SystemExit(f"no soundtrack at {A}: run work/audio.py first (or keep the silent render)")
r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(A), "-af", f"loudnorm=I={I}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True)
m = json.loads(re.search(r"\{[^{}]*\}", r.stderr[r.stderr.rfind("Parsed_loudnorm"):], re.S).group(0))
ln = (f"loudnorm=I={I}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
      # loudnorm alone can still overshoot after the lossy encode: limit at 4x the sample rate (true peaks), 0.79 = -2 dBFS
      "aresample=192000,alimiter=limit=0.79:attack=1:release=50:level=0:latency=1,aresample=48000")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", V, "-i", str(A), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", ln,
                "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", OUT, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
lufs, tp = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1], re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", r.stderr)[-1]
print(OUT, lufs, "LUFS, true peak", tp, "dBTP" + ("" if tp == "-inf" or float(tp) <= -1.0 else "  (above -1 dBTP: lower the limit)"))
