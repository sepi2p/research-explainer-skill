"""Paint a plain watercolor paper wash for the explanation scenes and the end card (gpt-image-2, 1088x1920).
Usage: python3 paint_wash.py work/wash.png, then save it as assets/bg_wash.jpg (1080x1920). Key from $OPENAI_API_KEY or ~/.config/openai/key."""
import os, json, base64, urllib.request, pathlib, sys
KEY = os.getenv("OPENAI_API_KEY") or pathlib.Path.home().joinpath(".config/openai/key").read_text().strip()   # never printed
out = pathlib.Path(sys.argv[1])
PROMPT = ("A sheet of cold-press watercolor paper with a very soft, pale, warm watercolor wash: cream and a hint of peach at the top, a faint sage-green "
          "wash near the bottom, almost white in the middle where text will go, subtle pigment granulation and gentle blooms, slightly darker soft edges. "
          "Completely empty: no objects, no people, no text, no logos. Vertical 9:16.")
body = {"model": "gpt-image-2", "prompt": PROMPT, "size": "1088x1920", "quality": "high", "n": 1}
r = urllib.request.Request("https://api.openai.com/v1/images/generations", data=json.dumps(body).encode(),
    headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
with urllib.request.urlopen(r, timeout=900) as f: d = json.loads(f.read())
out.write_bytes(base64.b64decode(d["data"][0]["b64_json"])); print("ok", json.dumps(d.get("usage")))
