"""How a beat's caption is split into on-screen chunks and timed. Shared by the scenes and the .srt writer."""
import re

PERSIAN = re.compile(r"[؀-ۿ]")


def split_caption(text, limit=150):
    """Whole sentences (or clauses) of at most about `limit` characters. Persian sets wider, so its chunks are shorter."""
    text = (text or "").strip()
    if not text:
        return [""]
    if PERSIAN.search(text):
        limit = min(limit, 112)
    out = []
    for p in re.split(r"(?<=[.?!؟])\s+", text):
        if len(p) > limit:   # a long sentence: split at commas, colons or semicolons
            subs, cur = [], ""
            for w in re.split(r"(?<=[,:;،؛])\s+", p):
                if cur and len(cur) + len(w) + 1 > limit:
                    subs.append(cur); cur = w
                else:
                    cur = (cur + " " + w).strip()
            subs.append(cur)
            out += subs
        else:
            out.append(p)
    merged = []
    for p in out:
        if merged and len(merged[-1]) + len(p) + 1 <= limit:
            merged[-1] += " " + p
        else:
            merged.append(p)
    return merged


def chunk_times(chunks, dur):
    """Start time of each chunk within a beat, in proportion to its length."""
    n = [len(c) + 8 for c in chunks]
    tot = sum(n)
    t, out = 0.0, []
    for k in n:
        out.append(t)
        t += dur * k / tot
    return out
