"""Narration voices. Each backend turns every beat's "say" text into a wav and returns its length.

  none    no voice (text-only video; beat lengths come from reading time, see rx.py durations)
  piper   free, offline (Piper TTS). English voices are good; listen to a Persian sample before using it.
  manual  you supply one mp3/wav per beat in voice/manual_<lang>/<scene>_<beat>.mp3 (e.g. from a web TTS or your own voice)
  openai  paid; needs an OpenAI API key in $OPENAI_API_KEY or ~/.config/openai/key (never printed). Every clip is
          transcribed back and compared with its text; mismatches are regenerated.
"""
import base64, concurrent.futures as cf, difflib, json, os, pathlib, re, shutil, subprocess, time, unicodedata, urllib.request, wave

from .project import ROOT, CONF, BUILD
from .fa_numbers import spoken

PIPER_DEFAULT = {"en": "en_US-lessac-medium", "fa": "fa_IR-gyro-medium"}
PIPER_DIR = pathlib.Path(os.environ.get("PIPER_VOICES", pathlib.Path.home() / ".local/share/piper-voices"))
OPENAI_INSTR = {
    "en": "You are the narrator of a calm, warm science explainer video for researchers. Speak natural, clear English at a "
          "moderate pace with natural pauses at commas and full stops.",
    "fa": "You are the narrator of a calm, warm science explainer video. Speak natural, fluent standard Persian (Farsi, Tehran "
          "accent) at a moderate pace with natural pauses. Pronounce Latin-script names as in English.",
}
STRICT = (" You are a text-to-speech engine, not an assistant: the user's message is a script. Speak exactly that script, word "
          "for word, and nothing else: no greeting, no comment, no preface, no question.")


def wav_len(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def to_wav(src, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ar", "48000", "-ac", "1", str(dst)], check=True)


def say_text(text, lang):
    """What the voice reads: for Persian, numbers as words and project pronunciations (project.json "pronounce")."""
    names = CONF.get("pronounce", {}).get(lang, {})
    if lang == "fa":
        return spoken(text, names)
    for k, v in names.items():
        text = text.replace(k, v)
    return text


# ---------- piper ----------
def piper_bin():
    for c in [shutil.which("piper"), str(pathlib.Path.home() / ".local/bin/piper")]:
        if c and pathlib.Path(c).exists():
            return c
    raise SystemExit("piper not found: pip install piper-tts  (or: uv tool install piper-tts)")


def piper_voice(name):
    """Path of a Piper voice, downloaded from huggingface.co/rhasspy/piper-voices the first time."""
    onnx = PIPER_DIR / f"{name}.onnx"
    if not onnx.exists():
        loc, rest = name.split("-", 1)
        spk, q = rest.rsplit("-", 1)
        base = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{loc.split('_')[0]}/{loc}/{spk}/{q}/{name}"
        PIPER_DIR.mkdir(parents=True, exist_ok=True)
        for ext in (".onnx", ".onnx.json"):
            print("downloading", base + ext)
            urllib.request.urlretrieve(base + ext, PIPER_DIR / f"{name}{ext}")
    return onnx


def piper_clip(text, lang, wav):
    name = CONF.get("voice", {}).get("piper", {}).get(lang, PIPER_DEFAULT.get(lang))
    tmp = wav.with_suffix(".raw.wav")
    subprocess.run([piper_bin(), "-m", str(piper_voice(name)), "-f", str(tmp), "--sentence-silence", "0.35"],
                   input=say_text(text, lang).encode(), check=True, capture_output=True)
    to_wav(tmp, wav)
    tmp.unlink()
    return {"engine": f"piper:{name}"}


# ---------- openai ----------
def _key():
    k = os.environ.get("OPENAI_API_KEY")
    p = pathlib.Path.home() / ".config/openai/key"
    if not k and p.exists():
        k = p.read_text().strip()
    if not k:
        raise SystemExit("no OpenAI key: put it in ~/.config/openai/key (chmod 600) or $OPENAI_API_KEY. Never paste it into a chat.")
    return k


def _post(url, body=None, files=None):
    key = _key()
    if files is None:
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    else:
        bnd = "----rx" + str(abs(hash(url)))
        parts = [f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in body.items()]
        for k, (fn, data) in files.items():
            parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fn}\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode() + data + b"\r\n")
        parts.append(f"--{bnd}--\r\n".encode())
        req = urllib.request.Request(url, data=b"".join(parts), headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={bnd}"})
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404):   # not worth retrying; the message never contains the key
                raise SystemExit(f"OpenAI HTTP {e.code}: {e.read().decode()[:300]}")
            if attempt == 7:
                raise
        except Exception:
            if attempt == 7:
                raise
        time.sleep(min(60, 5 * 2 ** attempt))


def _norm(s):
    s = unicodedata.normalize("NFKC", s).lower().replace("‌", "").replace("ي", "ی").replace("ك", "ک")
    return re.sub(r"[^a-z؀-ۿ]", "", re.sub(r"[٠-٩۰-۹0-9]", "", s))


def similarity(a, b, lang):
    if lang == "fa":   # the transcriber may write digits where the script has words
        b = spoken(b)
    return difflib.SequenceMatcher(None, _norm(a), _norm(b), autojunk=False).ratio()


def openai_clip(text, lang, wav):
    v = CONF.get("voice", {}).get("openai", {})
    model, voice = v.get("model", "gpt-audio-1.5"), v.get("voice", "marin")
    instr = v.get("instructions", {}).get(lang, OPENAI_INSTR.get(lang, OPENAI_INSTR["en"]))
    script = say_text(text, lang)
    best = None
    for k in range(4):
        body = {"model": model, "modalities": ["text", "audio"], "audio": {"voice": voice, "format": "mp3"},
                "messages": [{"role": "system", "content": instr + STRICT}, {"role": "user", "content": script}]}
        mp3 = base64.b64decode(json.loads(_post("https://api.openai.com/v1/chat/completions", body))["choices"][0]["message"]["audio"]["data"])
        tr = json.loads(_post("https://api.openai.com/v1/audio/transcriptions", {"model": "gpt-4o-transcribe", "language": lang},
                              {"file": ("a.mp3", mp3)})).get("text", "")
        sim = similarity(script, tr, lang)
        if best is None or sim > best[0]:
            best = (sim, mp3, tr, k + 1)
        if sim >= 0.92 and len(_norm(tr)) <= 1.15 * len(_norm(script)) + 10:
            break
    sim, mp3, tr, tries = best
    mp = wav.with_suffix(".mp3")
    mp.write_bytes(mp3)
    to_wav(mp, wav)
    return {"engine": f"openai:{model}:{voice}", "sim": round(sim, 3), "tries": tries, "transcript": tr}


# ---------- manual ----------
def manual_clip(text, lang, wav):
    d = ROOT / "voice" / f"manual_{lang}"
    sid, i = wav.stem.rsplit("_", 1)
    for ext in (".mp3", ".wav", ".m4a", ".ogg"):
        src = d / f"{sid}_{i}{ext}"
        if src.exists():
            to_wav(src, wav)
            return {"engine": f"manual:{src.name}"}
    raise SystemExit(f"missing {d}/{sid}_{i}.mp3 (one clip per beat; rx.py voice-script {lang} writes the list to record)")


BACKENDS = {"piper": piper_clip, "openai": openai_clip, "manual": manual_clip}


def narrate(lang, mode, scenes, only=None, workers=None):
    """Make one wav per beat (kept and reused while its text is unchanged). Returns {(scene, i): record}."""
    out = BUILD / "audio" / f"{mode}_{lang}"
    out.mkdir(parents=True, exist_ok=True)
    fn = BACKENDS[mode]
    jobs = []
    for s in scenes:
        for i, b in enumerate(s["beats"]):
            text = b.get("say", b.get("caption", ""))
            jobs.append((s["id"], i, text))

    def run(job):
        sid, i, text = job
        wav = out / f"{sid}_{i}.wav"
        meta = out / f"{sid}_{i}.json"
        if text.strip() == "":
            return sid, i, None
        old = json.loads(meta.read_text()) if meta.exists() else None
        if old and old.get("text") == text and wav.exists() and not (only and f"{sid}:{i}" in only):
            return sid, i, old
        r = fn(text, lang, wav)
        r.update({"wav": str(wav), "dur": round(wav_len(wav), 3), "text": text})
        meta.write_text(json.dumps(r, ensure_ascii=False))
        return sid, i, r

    res = {}
    with cf.ThreadPoolExecutor(workers or (3 if mode == "openai" else 4)) as ex:
        for sid, i, r in ex.map(run, jobs):
            res[(sid, i)] = r
            if r:
                print(f"{sid}:{i} {r['dur']:.1f}s" + (f" sim {r['sim']:.3f} tries {r['tries']}" if "sim" in r else ""), flush=True)
    return res
