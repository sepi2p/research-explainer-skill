"""Caption groups from the script text, timed with the Parakeet words (matched by position via difflib).
Writes ../assets/captions.js. Numbers are shown as digits."""
import json, pathlib, re, difflib, sys
H = pathlib.Path(__file__).parent; sys.path.insert(0, str(H))
from en_numbers import spoken
lines = json.loads((H / "lines.json").read_text())
pk = json.loads((H.parent / "assets" / "transcript.json").read_text())
SHOW = {"four": "4", "sixteen": "16", "sixty-four": "64"}          # spoken numbers shown as digits
MERGE = [("five hundred point zero", "500.0"), ("zero point one eight", "0.18")]   # several spoken words shown as one number
def n(w): return re.sub(r"[^a-z]", "", spoken(w.replace("-", " ")).lower())
words = []
for l in lines:
    toks = l["text"].split()
    for k, tok in enumerate(toks):
        core = re.sub(r"[^\w'-]", "", tok).lower()
        disp = re.sub(re.escape(re.sub(r"[^\w'-]", "", tok)), SHOW[core], tok) if core in SHOW else tok
        words.append({"line": l["id"], "k": k, "n": n(tok), "text": disp, "ls": l["start"], "le": l["end"]})
# merge a spoken number ("zero point one eight") into one shown word ("0.18") before matching: Parakeet writes it as digits
for spoken_seq, shown in MERGE:
    seq = [n(x) for x in spoken_seq.split()]; k = len(seq); i = 0
    while i + k <= len(words):
        ws = words[i:i + k]
        if [w["n"] for w in ws] == seq and len({w["line"] for w in ws}) == 1:
            tail = re.sub(r"^[\w'-]+", "", ws[-1]["text"])          # keep the punctuation after the last word
            words[i:i + k] = [dict(ws[0], text=shown + tail, n="".join(seq))]
        i += 1
pw = [w for w in pk if n(w["text"])]
sm = difflib.SequenceMatcher(None, [w["n"] for w in words], [n(w["text"]) for w in pw], autojunk=False)
for a, b, size in sm.get_matching_blocks():
    for j in range(size): words[a + j]["start"], words[a + j]["end"] = pw[b + j]["start"], pw[b + j]["end"]
# fill words the transcriber skipped: spread them between their timed neighbours in the same line
for i, w in enumerate(words):
    if "start" in w: continue
    j = i
    while j < len(words) and "start" not in words[j] and words[j]["line"] == w["line"]: j += 1
    t0 = words[i - 1]["end"] if i and words[i - 1]["line"] == w["line"] else w["ls"]
    t1 = words[j]["start"] if j < len(words) and words[j]["line"] == w["line"] and "start" in words[j] else w["le"]
    m = j - i
    for q in range(m):
        words[i + q]["start"] = round(t0 + (t1 - t0) * q / m, 3); words[i + q]["end"] = round(t0 + (t1 - t0) * (q + 1) / m, 3)
    print("filled:", " ".join(words[i + q]["text"] for q in range(m)))
# Parakeet tends to start a line's first words 0.1-0.35 s before the audio: clamp to the line start (+0.03 s) and keep order
for i, w in enumerate(words):
    lo = w["ls"] + 0.03 if (i == 0 or words[i - 1]["line"] != w["line"]) else words[i - 1]["start"]
    if w["start"] < lo: w["start"] = round(lo, 3)
    if w["end"] < w["start"] + 0.05: w["end"] = round(w["start"] + 0.05, 3)
groups, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    end_sent = bool(re.search(r"[.?!:,]$", w["text"]))
    gap = nxt is not None and nxt["start"] - w["end"] >= 0.15
    if len(cur) >= 3 or end_sent or gap or nxt is None or nxt["line"] != w["line"]:
        groups.append({"text": " ".join(x["text"] for x in cur), "start": round(cur[0]["start"], 3), "end": round(cur[-1]["end"], 3),
                       "words": [{"text": x["text"], "start": x["start"], "end": x["end"]} for x in cur]}); cur = []
for g in groups: print(f'{g["start"]:6.2f}-{g["end"]:6.2f}  {g["text"]}')
(H.parent / "assets" / "captions.js").write_text("window.CAPTIONS = " + json.dumps(groups, indent=0) + ";\n")
(H.parent / "assets" / "words.js").write_text("window.WORDS = " + json.dumps([{k: w[k] for k in ("line", "text", "start", "end")} for w in words]) + ";\n")
(H / "words.json").write_text(json.dumps([{k: w[k] for k in ("line", "text", "start", "end")} for w in words], indent=0))
