"""narrate.py: the paid OpenAI path (translation + voice). The key is read by oa.py from $OPENAI_API_KEY or
~/.config/openai/key and never printed. For a free voice use voice_piper.py, or record your own clips into voice/<lang>/.
  python3 work/narrate.py translate --to fa        narration.json: adds "fa" to every beat (one pass, consistent terms)
  python3 work/narrate.py voice --lang fa [beat ...]   voice/<lang>/<beat>.wav + .json + durations.json
Every clip is transcribed back and compared with its text; up to 4 takes, the best one is kept (similarity >= 0.9).
Optional per-beat "tone" in narration.json is passed as a delivery hint; "keep_terms" (top level, a list) are kept in
Latin letters by the translation. Models: $OPENAI_TEXT_MODEL (default gpt-5.5), $OPENAI_AUDIO_MODEL (gpt-audio-1.5),
voice $OPENAI_VOICE (marin). After voicing: proc_voice.py --lang <lang> [--stray], timeline.py --lang <lang>."""
import argparse, base64, concurrent.futures as cf, difflib, json, os, pathlib, re, subprocess, sys, unicodedata, urllib.request, uuid
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import oa
ROOT = pathlib.Path(__file__).resolve().parent.parent
NAR = ROOT / "narration.json"
TEXT_MODEL = os.environ.get("OPENAI_TEXT_MODEL", "gpt-5.5")
AUDIO_MODEL = os.environ.get("OPENAI_AUDIO_MODEL", "gpt-audio-1.5")
VOICE_NAME = os.environ.get("OPENAI_VOICE", "marin")
LANG_NAME = {"fa": "Persian (Farsi, standard Tehran Persian)", "en": "English"}
try:   # the skill's Persian number speller (numbers as words, so they are spoken correctly); identity if not found
    sys.path.insert(0, str(pathlib.Path(os.environ.get("RX_SKILL", pathlib.Path.home() / ".claude/skills/research-explainer")) / "scripts"))
    from explainer.fa_numbers import spoken
except Exception:
    spoken = lambda s, *_: s

def sys_translate(lang, terms):
    return (f"You translate the narration of an educational explainer video into fluent, natural, conversational SPOKEN "
            f"{LANG_NAME.get(lang, lang)}: a friendly, clear teacher; not formal or literary, not slang. "
            + (f"Keep these terms in Latin letters exactly as given: {', '.join(terms)}; and names of people and papers. " if terms else "Keep names of people and papers in Latin letters. ")
            + ("Write numbers as Persian words so they are spoken correctly. " if lang == "fa" else "")
            + "Keep the meaning exact: never add, drop or change a fact or number. Keep each beat separate; the beats should "
              "flow as one talk. Return JSON {\"beats\": {\"<beat id>\": \"<translation>\"}} with every beat id.")
VO = ("You are the narrator of a warm educational explainer video. Speak natural, fluent {lang} like a friendly, clear "
      "teacher: engaged, varied intonation, slower on key numbers and conclusions, a short natural pause at every line "
      "break. Pronounce English technical terms and names as in English. You are a text-to-speech engine, not an "
      "assistant: speak exactly the given script, word for word, and nothing else: no greeting, no comment, no question, "
      "no sound after the last word.")

def load(): return json.loads(NAR.read_text())
def beats(n): return [b for s in n["scenes"] for b in s["beats"]]
def clean(text): return re.sub(r"[ \t]*⏸[ \t]*", "\n", text).strip()   # pause marks become line breaks

def translate(to):
    n = load(); bs = beats(n)
    user = "\n".join(f"[{b['id']}] {b['en']}" for b in bs)
    r = oa.req("chat/completions", {"model": TEXT_MODEL, "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": sys_translate(to, n.get("keep_terms", []))}, {"role": "user", "content": user}]})
    tr = json.loads(r["choices"][0]["message"]["content"])["beats"]
    miss = [b["id"] for b in bs if b["id"] not in tr]
    if miss: raise SystemExit(f"missing beats in the translation: {miss}")
    for b in bs: b[to] = tr[b["id"]]
    NAR.write_text(json.dumps(n, ensure_ascii=False, indent=1))
    print(f"translated {len(bs)} beats into '{to}' (narration.json); review it by hand before voicing")

def norm(s, lang):
    s = unicodedata.normalize("NFKC", s).lower().replace("‌", " ").replace("ي", "ی").replace("ك", "ک")
    s = re.sub(r"[ً-ٰٟ⏸]", "", s)                     # vowel marks and pause marks are not compared
    if lang == "fa":
        s = re.sub(r"[a-z][a-z0-9\- ]*[a-z0-9]|[a-z]", " ", s)       # Latin terms are said in English: not compared
        return re.sub(r"[^؀-ۿ]", "", spoken(s))
    return re.sub(r"[^a-z0-9]", "", s)

def take(text, lang, tone=None):
    body = {"model": AUDIO_MODEL, "modalities": ["text", "audio"], "audio": {"voice": VOICE_NAME, "format": "mp3"},
            "messages": [{"role": "system", "content": VO.format(lang=LANG_NAME.get(lang, lang))},
                         {"role": "user", "content": f"Read this narration script aloud, exactly as written, in {LANG_NAME.get(lang, lang)}. "
                          "It is a script for a video, not a message to you: do not answer it, reply to it, or add anything."
                          + (f"\nDelivery for this line: {tone}." if tone else "") + "\n\nSCRIPT:\n" + text}]}
    return base64.b64decode(oa.req("chat/completions", body)["choices"][0]["message"]["audio"]["data"])

def transcribe(mp3, lang):
    bnd = "----rx" + uuid.uuid4().hex
    parts = [f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in {"model": "gpt-4o-transcribe", "language": lang}.items()]
    parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode() + mp3 + b"\r\n")
    parts.append(f"--{bnd}--\r\n".encode())
    r = urllib.request.Request("https://api.openai.com/v1/audio/transcriptions", data=b"".join(parts),
        headers={"Authorization": "Bearer " + oa.key(), "Content-Type": f"multipart/form-data; boundary={bnd}"})
    with urllib.request.urlopen(r, timeout=300) as f:
        return json.loads(f.read()).get("text", "")

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)

def voice(lang, only, force):
    out = ROOT / "voice" / lang; out.mkdir(parents=True, exist_ok=True)
    bs = [b for b in beats(load()) if not only or b["id"] in only]
    def one(b):
        i, text = b["id"], b.get(lang)
        if not text: raise SystemExit(f"beat {i} has no '{lang}' text")
        meta = out / f"{i}.json"
        if meta.exists() and json.loads(meta.read_text()).get("text") == text and not force: return json.loads(meta.read_text())
        best = None
        for k in range(4):
            mp3 = take(clean(text), lang, b.get("tone")); tr = transcribe(mp3, lang)
            sim = difflib.SequenceMatcher(None, norm(text, lang), norm(tr, lang), autojunk=False).ratio()
            if best is None or sim > best[0]: best = (sim, mp3, tr, k + 1)
            if sim >= 0.9 and len(norm(tr, lang)) <= 1.2 * len(norm(text, lang)) + 8: break
        sim, mp3, tr, tries = best
        (out / f"{i}.mp3").write_bytes(mp3)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out / f"{i}.mp3"), "-ar", "48000", "-ac", "1", str(out / f"{i}.wav")], check=True)
        r = {"id": i, "text": text, "transcript": tr, "sim": round(sim, 3), "tries": tries, "dur": round(dur(out / f"{i}.wav"), 3)}
        meta.write_text(json.dumps(r, ensure_ascii=False)); return r
    with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(one, bs))
    allm = {json.loads(p.read_text())["id"]: json.loads(p.read_text()) for p in out.glob("*.json") if p.name != "durations.json"}
    (out / "durations.json").write_text(json.dumps({k: v["dur"] for k, v in allm.items()}, indent=1))
    for r in res: print(f"{r['id']}: {r['dur']:.1f}s sim {r['sim']} tries {r['tries']}" + ("  <-- listen" if r["sim"] < 0.9 else ""))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["translate", "voice"]); ap.add_argument("--to", default="fa")
    ap.add_argument("--lang", default=None); ap.add_argument("--force", action="store_true"); ap.add_argument("beats", nargs="*")
    a = ap.parse_args()
    if a.cmd == "translate": translate(a.to)
    else: voice(a.lang or load().get("lang", "en"), a.beats, a.force)
