"""voice_piper.py [--lang en] [--voice NAME] [beat ...]: a free, offline voice (Piper TTS) for every beat of
narration.json -> voice/<lang>/<beat>.wav (48 kHz mono) + voice/<lang>/durations.json. A ⏸ in the text becomes a real
pause (GAP seconds of silence). Then: proc_voice.py --lang <lang>, timeline.py --lang <lang>, audio.py.
Needs the piper binary (pip install piper-tts, or uv tool install piper-tts) and a voice model: the default for the
language is looked up in $PIPER_VOICES (default ~/.local/share/piper-voices) and downloaded from
huggingface.co/rhasspy/piper-voices the first time. English voices are good; listen to a Persian sample before using it."""
import argparse, json, os, pathlib, shutil, subprocess, urllib.request, wave
ROOT = pathlib.Path(__file__).resolve().parent.parent
nar = json.loads((ROOT / "narration.json").read_text())
ap = argparse.ArgumentParser(); ap.add_argument("--lang", default=nar.get("lang", "en")); ap.add_argument("--voice"); ap.add_argument("beats", nargs="*")
a = ap.parse_args()
DEFAULT = {"en": "en_US-lessac-medium", "fa": "fa_IR-gyro-medium"}
NAME = a.voice or DEFAULT.get(a.lang)
if not NAME: raise SystemExit(f"no default Piper voice for {a.lang}: pass --voice <piper voice name>")
VDIR = pathlib.Path(os.environ.get("PIPER_VOICES", pathlib.Path.home() / ".local/share/piper-voices"))
GAP, SR = 0.45, 48000
OUT = ROOT / "voice" / a.lang; OUT.mkdir(parents=True, exist_ok=True)

def piper_bin():
    for c in [shutil.which("piper"), str(pathlib.Path.home() / ".local/bin/piper")]:
        if c and pathlib.Path(c).exists(): return c
    raise SystemExit("piper not found: pip install piper-tts  (or: uv tool install piper-tts)")

def model(name):
    onnx = VDIR / f"{name}.onnx"
    if not onnx.exists():
        loc, rest = name.split("-", 1); spk, q = rest.rsplit("-", 1)
        base = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{loc.split('_')[0]}/{loc}/{spk}/{q}/{name}"
        VDIR.mkdir(parents=True, exist_ok=True)
        for ext in (".onnx", ".onnx.json"):
            print("downloading", base + ext); urllib.request.urlretrieve(base + ext, VDIR / f"{name}{ext}")
    return onnx

def speak(text, tmp):
    subprocess.run([piper_bin(), "-m", str(model(NAME)), "-f", str(tmp)], input=text.encode(), check=True, capture_output=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(tmp), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return raw                                  # 16-bit mono PCM bytes

durs = json.loads((OUT / "durations.json").read_text()) if (OUT / "durations.json").exists() else {}
for s in nar["scenes"]:
    for b in s["beats"]:
        if a.beats and b["id"] not in a.beats: continue
        text = b.get(a.lang)
        if not text: raise SystemExit(f"beat {b['id']} has no '{a.lang}' text")
        parts, tmp = [p.strip() for p in text.split("⏸")], OUT / "_tmp.wav"
        pcm = []
        for k, p in enumerate(parts):
            if k: pcm.append(bytes(2 * int(GAP * SR)))
            if p: pcm.append(speak(p, tmp))
        tmp.unlink(missing_ok=True)
        x = b"".join(pcm)
        with wave.open(str(OUT / f"{b['id']}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x)
        durs[b["id"]] = round(len(x) / 2 / SR, 3); print(f"{b['id']}: {durs[b['id']]:.2f}s")
(OUT / "durations.json").write_text(json.dumps(durs, indent=1))
print(f"voice/{a.lang}: {len(durs)} clips, {sum(durs.values()):.1f}s, piper {NAME}")
