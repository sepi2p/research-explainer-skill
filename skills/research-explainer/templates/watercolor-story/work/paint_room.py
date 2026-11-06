"""Repaint the empty set (work/empty_room.png from empty_room.sh) as a watercolor, 2 variants at 1088x1920, so the painting
lines up with the animation. Usage: python3 paint_room.py work/empty_room.png work/painted
Then pick one: python3 -c "from PIL import Image; Image.open('work/painted/room_1.png').convert('RGB').resize((1080,1920)).save('assets/bg_set.jpg', quality=92)"
OpenAI image edit (gpt-image-2, quality high). Key from $OPENAI_API_KEY or ~/.config/openai/key. Edit PROMPT for another set."""
import os, sys, json, base64, uuid, urllib.request, pathlib
KEY = os.getenv("OPENAI_API_KEY") or pathlib.Path.home().joinpath(".config/openai/key").read_text().strip()   # never printed
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); out.mkdir(exist_ok=True)
PROMPT = ("Repaint this empty bakery kitchen as a loose, hand-painted watercolor illustration on cold-press paper: soft transparent washes, "
  "visible pigment granulation and blooms, a few fine ink lines, white paper showing through, warm natural morning light coming from the window. "
  "Keep everything exactly where it is in the reference: the two wooden shelves on the upper left with glass jars of flour and sugar, a blue bowl, "
  "loaves of bread and a bread basket, the round kitchen clock, the window with saffron curtains, a cloud, green hills and a pot of herbs on the sill "
  "at the upper right, the pale green tiled splashback across the middle and the terracotta floor tiles at the bottom. The kitchen is EMPTY: no people, "
  "no counter, no table, no furniture in front. Keep the lower half (splashback, plain wall and floor) open and simple, because paper cut-out characters "
  "and a counter will be placed in front of it. No text, no logos. Vertical 9:16 composition.")
def edit(size):
    bnd = "----rx" + uuid.uuid4().hex
    fields = {"model": "gpt-image-2", "prompt": PROMPT, "size": size, "quality": "high", "n": "2"}
    parts = [f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in fields.items()]
    parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"room.png\"\r\nContent-Type: image/png\r\n\r\n".encode() + src.read_bytes() + b"\r\n")
    parts.append(f"--{bnd}--\r\n".encode())
    r = urllib.request.Request("https://api.openai.com/v1/images/edits", data=b"".join(parts),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": f"multipart/form-data; boundary={bnd}"})
    with urllib.request.urlopen(r, timeout=900) as f: return json.loads(f.read())
# one paid call, n=2 variants (two images billed); no fallback size: another aspect would not line up with the set
try:
    d = edit("1088x1920")
except urllib.error.HTTPError as e:
    sys.exit(f"paint_room.py: HTTP {e.code}: {e.read().decode()[:300]}")
for i, x in enumerate(d["data"]): (out / f"room_{i}.png").write_bytes(base64.b64decode(x["b64_json"]))
print("ok 1088x1920", json.dumps(d.get("usage")), "-> pick one, resize to 1080x1920 (see the header), compare its wall/floor lines with work/empty_room.png")
