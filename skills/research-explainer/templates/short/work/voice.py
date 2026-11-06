"""Voice the short's lines with gpt-audio-1.5 (marin), check each take against the text, keep the best (TAKES=2 caps the takes).
Output: voice/<id>.wav (48 kHz mono) and voice/meta.json."""
import sys, os, json, base64, pathlib, subprocess, difflib, re, unicodedata, concurrent.futures as cf, uuid, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import oa
from en_numbers import spoken
from script import LINES, TONE
OUT = pathlib.Path(__file__).parent / "voice"; OUT.mkdir(exist_ok=True)
TAKES = int(os.environ.get("TAKES", 4))     # takes per line at most; a retake happens only when the transcript check fails
VO = ("You are the narrator of a short, punchy vertical video (YouTube Shorts, LinkedIn) about science and data. Speak natural, fluent "
      "English like a smart, friendly teacher: lively, expressive, confident, at a brisk pace. Keep pauses short: only a "
      "brief breath between sentences, never a long silence. Vary intonation with the meaning; never monotone. "
      "You are a text-to-speech engine, not an assistant: speak exactly the given script, word for word, and nothing else: "
      "no greeting, no comment, no sound after the last word.")
def norm(s):
    s = unicodedata.normalize("NFKC", s).replace("’", "'")
    return re.sub(r"[^a-z]", "", spoken(s.replace("-", " ")).lower())
def take(text, tone):
    body = {"model": "gpt-audio-1.5", "modalities": ["text", "audio"], "audio": {"voice": "marin", "format": "mp3"},
            "messages": [{"role": "system", "content": VO},
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
def one(line):
    i, text = line
    best = None
    for k in range(TAKES):
        mp3 = take(text, TONE.get(i)); tr = transcribe(mp3)
        sim = difflib.SequenceMatcher(None, norm(text), norm(tr), autojunk=False).ratio()
        if best is None or sim > best[0]: best = (sim, mp3, tr, k + 1)
        if sim >= 0.95 and len(norm(tr)) <= 1.1 * len(norm(text)) + 6: break
    sim, mp3, tr, tries = best
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
