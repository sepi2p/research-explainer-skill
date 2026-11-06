"""wordtimes.py [--lang en]: real word timing for every beat. Transcribes each processed clip voice/<lang>_proc/<beat>.wav
with word timestamps (OpenAI whisper-1, paid, cached in whisper_words.json), aligns the transcript to the script
character by character and stores the spoken time of every script character in voice/<lang>_proc/chartimes.json
({beat: [seconds per character of the beat's text]}). timeline.py copies them into the beats, so E.cue(id, 'word')
returns the time the word is actually said (without them E.cue estimates from the character position)."""
import argparse, concurrent.futures as cf, difflib, json, os, pathlib, re, sys, unicodedata, urllib.request, uuid
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import oa
try:   # the skill's Persian number speller; identity if not found
    sys.path.insert(0, str(pathlib.Path(os.environ.get("RX_SKILL", pathlib.Path.home() / ".claude/skills/research-explainer")) / "scripts"))
    from explainer.fa_numbers import spoken
except Exception:
    spoken = lambda s, *_: s
ROOT = pathlib.Path(__file__).resolve().parent.parent

def words(i, wav, text, lang, cache):
    if i in cache and cache[i]["text"] == text: return cache[i]["words"]
    bnd = "----rx" + uuid.uuid4().hex
    fields = {"model": "whisper-1", "language": lang, "response_format": "verbose_json", "timestamp_granularities[]": "word"}
    parts = [f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in fields.items()]
    parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode() + wav + b"\r\n")
    parts.append(f"--{bnd}--\r\n".encode())
    r = urllib.request.Request("https://api.openai.com/v1/audio/transcriptions", data=b"".join(parts),
                               headers={"Authorization": "Bearer " + oa.key(), "Content-Type": f"multipart/form-data; boundary={bnd}"})
    with urllib.request.urlopen(r, timeout=300) as f: w = json.loads(f.read()).get("words", [])
    cache[i] = {"text": text, "words": w}
    return w

def norm_char(c, lang):
    c = unicodedata.normalize("NFKC", c).replace("ي", "ی").replace("ك", "ک").lower()
    if lang == "fa": return c if "ء" <= c <= "ي" or c in "پچژگکی" else ""
    return c if c.isalnum() else ""

def align(text, W, dur, lang):
    """Seconds (relative to the clip) at which each character of `text` is spoken, from whisper words W."""
    tchars, ttimes = [], []
    for w in W:
        ws = "".join(norm_char(c, lang) for c in (spoken(w["word"]) if lang == "fa" else w["word"]))
        for k, c in enumerate(ws):
            tchars.append(c); ttimes.append(w["start"] + (w["end"] - w["start"]) * (k + 0.5) / max(1, len(ws)))
    keep = [(k, norm_char(c, lang)) for k, c in enumerate(text) if norm_char(c, lang)]
    S, T = "".join(c for _, c in keep), "".join(tchars)
    sm = difflib.SequenceMatcher(None, S, T, autojunk=False)
    st = [None] * len(S)
    for a, b, n in sm.get_matching_blocks():
        for j in range(n): st[a + j] = ttimes[b + j]
    known = [(j, v) for j, v in enumerate(st) if v is not None] or [(0, 0.0)]
    pts = [(-1, 0.0)] + known + [(len(S), dur)]
    for (j0, v0), (j1, v1) in zip(pts, pts[1:]):           # gaps: linear interpolation, ends anchored at 0 and the clip end
        for j in range(j0 + 1, j1): st[j] = v0 + (v1 - v0) * (j - j0) / (j1 - j0)
    for j in range(1, len(st)): st[j] = max(st[j], st[j - 1])
    out, last, ki = [None] * len(text), 0.0, 0
    kept = {k: st[n] for n, (k, _) in enumerate(keep)}
    for k in range(len(text)):                              # spaces and punctuation take the time of the next spoken character
        if k in kept: last = kept[k]; out[k] = round(last, 3)
    nxt = dur
    for k in range(len(text) - 1, -1, -1):
        if out[k] is None: out[k] = round(nxt, 3)
        else: nxt = out[k]
    for k in range(1, len(out)): out[k] = max(out[k], out[k - 1])
    cover = sum(n for _, _, n in sm.get_matching_blocks()) / max(1, len(S))
    return out, cover

if __name__ == "__main__":
    nar = json.loads((ROOT / "narration.json").read_text())
    ap = argparse.ArgumentParser(); ap.add_argument("--lang", default=nar.get("lang", "en")); a = ap.parse_args()
    P = ROOT / f"voice/{a.lang}_proc"
    texts = {b["id"]: b[a.lang] for s in nar["scenes"] for b in s["beats"]}
    durs = json.loads((P / "durations.json").read_text())
    CACHE = P / "whisper_words.json"; cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    def run(i): return i, *align(texts[i], words(i, (P / f"{i}.wav").read_bytes(), texts[i], a.lang, cache), durs[i], a.lang)
    with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(run, list(texts)))
    CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    (P / "chartimes.json").write_text(json.dumps({i: out for i, out, _ in res}))
    for i, _, cover in res: print(f"{i:5} matched {cover:.2f}" + ("  <-- low match: listen" if cover < 0.7 else ""))
