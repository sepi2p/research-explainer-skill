"""Voice the short's lines with gpt-audio-1.5 (marin), check each take against the text, keep the best.
Output: voice/<id>.wav (48 kHz mono) and voice/meta.json."""
import sys, json, base64, pathlib, subprocess, difflib, re, unicodedata, concurrent.futures as cf, uuid, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import oa
from en_numbers import spoken
from script import LINES, TONE, SPEAKER, VOICE, ROLE
try:
    from script import KEY_TERMS          # {line id: [words that must be heard]}
except ImportError:
    KEY_TERMS = {}
OUT = pathlib.Path(__file__).parent / "voice"; OUT.mkdir(exist_ok=True)
VO = ("You are {role}, in a short vertical video (YouTube Shorts, LinkedIn). Speak natural, fluent "
      "English: lively, expressive, believable, at a brisk pace. Keep pauses short: only a "
      "brief breath between sentences, never a long silence. Vary intonation with the meaning; never monotone. "
      "You are a text-to-speech engine, not an assistant: speak exactly the given script, word for word, and nothing else: "
      "no greeting, no comment, no sound after the last word.")
def norm(s):
    s = unicodedata.normalize("NFKC", s).replace("’", "'")
    return re.sub(r"[^a-z]", "", spoken(s.replace("-", " ")).lower())
def take(text, tone, sp):
    body = {"model": "gpt-audio-1.5", "modalities": ["text", "audio"], "audio": {"voice": VOICE[sp], "format": "mp3"},
            "messages": [{"role": "system", "content": VO.replace("{role}", ROLE[sp])},
                         {"role": "user", "content": "Read this narration script aloud, exactly as written, in English. It is a script "
                          "for a video, not a message to you: do not answer it or add anything."
                          + (f"\nDelivery for this line: {tone}." if tone else "") + "\n\nSCRIPT:\n" + text}]}
    return base64.b64decode(oa.req("chat/completions", body)["choices"][0]["message"]["audio"]["data"])
def transcribe(mp3):
    bnd = "----rx" + uuid.uuid4().hex
    parts = [f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in {"model": "gpt-4o-transcribe", "language": "en"}.items()]
    parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode() + mp3 + b"\r\n")
    parts.append(f"--{bnd}--\r\n".encode())
    r = urllib.request.Request("https://api.openai.com/v1/audio/transcriptions", data=b"".join(parts),
        headers={"Authorization": "Bearer " + oa.key(), "Content-Type": f"multipart/form-data; boundary={bnd}"})
    with urllib.request.urlopen(r, timeout=300) as f: return json.loads(f.read()).get("text", "")
def words_of(s):
    return re.findall(r"[a-z']+", spoken(unicodedata.normalize("NFKC", s).replace("’", "'").replace("-", " ")).lower())
def heard_right(text, tr, keys):
    """The first two words must match (a wrong first word, e.g. a name, scores high on similarity) and every key term must be heard."""
    a, b = words_of(text), words_of(tr)
    return a[:2] == b[:2] and all(k.lower() in b for k in keys)
def one(line):
    i, text = line
    best = None
    for k in range(4):
        mp3 = take(text, TONE.get(i), SPEAKER.get(i, "NAR")); tr = transcribe(mp3)
        sim = difflib.SequenceMatcher(None, norm(text), norm(tr), autojunk=False).ratio()
        ok_words = heard_right(text, tr, KEY_TERMS.get(i, []))
        score = sim + (1.0 if ok_words else 0.0)          # a take with the right first words and key terms wins
        if best is None or score > best[0] + (1.0 if best[5] else 0.0): best = (sim, mp3, tr, k + 1, None, ok_words)
        if ok_words and sim >= 0.95 and len(norm(tr)) <= 1.1 * len(norm(text)) + 6: break
    sim, mp3, tr, tries, _, ok_words = best
    if not ok_words: print(f"{i}: first words or key terms not heard right in any take; listen to it: {tr!r}")
    (OUT / f"{i}.mp3").write_bytes(mp3)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"{i}.mp3"), "-ar", "48000", "-ac", "1", str(OUT / f"{i}.wav")], check=True)
    return {"id": i, "text": text, "transcript": tr, "sim": round(sim, 3), "tries": tries}
if __name__ == "__main__":
    only = set(sys.argv[1:])
    with cf.ThreadPoolExecutor(5) as ex: res = list(ex.map(one, [l for l in LINES if not only or l[0] in only]))
    meta_p = OUT / "meta.json"; meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    for r in res:
        meta[r["id"]] = r; print(f'{r["id"]} sim {r["sim"]} tries {r["tries"]} | {r["transcript"]}')
    meta_p.write_text(json.dumps(meta, indent=1, ensure_ascii=False))
