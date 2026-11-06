"""Try looks before choosing one: repaint one clean frame of the set in several styles (watercolor, cardboard diorama, clay,
picture book, linocut) with the OpenAI image edit endpoint (gpt-image-2, quality medium, about 5 images per run).
Usage: python3 explore_styles.py <frame.png> <outdir>. Key from $OPENAI_API_KEY or ~/.config/openai/key. Edit STYLES and KEEP."""
import os, sys, json, base64, uuid, urllib.request, pathlib, concurrent.futures as cf, time
KEY = os.getenv("OPENAI_API_KEY") or pathlib.Path.home().joinpath(".config/openai/key").read_text().strip()   # never printed
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); out.mkdir(exist_ok=True)
KEEP = (" Keep exactly the same composition, camera, kitchen and counter layout, and the same two characters in the same poses: "
        "on the left a young apprentice baker with curly dark hair under a red kerchief, a blue shirt and a cream apron, one hand on a paper bag "
        "of flour that stands on a blue kitchen scale; on the right an older baker with a tall white chef's hat, a grey moustache, a saffron shirt "
        "and a white apron, both behind a wooden counter; shelves with jars and bread, a round clock and a window with saffron curtains behind "
        "them. Vertical 9:16 frame. No text, no letters, no speech bubbles, no logos.")
STYLES = {
  "watercolor": "Repaint this scene as a loose, hand-painted watercolor illustration on cold-press paper: soft transparent washes, visible pigment granulation and blooms, a few fine ink lines, white paper showing through, warm natural light from the window.",
  "cardboard": "Rebuild this scene as a handmade cardboard and paper-craft diorama photographed in a small studio: layered cut cardboard and coloured paper with visible thickness and rough cut edges, small real shadows between the layers, soft daylight, slight shallow depth of field.",
  "clay": "Recreate this scene as a frame from a stop-motion clay animation: plasticine characters with soft fingerprints and rounded forms, miniature handmade furniture and props, warm studio lighting, gentle depth of field.",
  "picturebook": "Repaint this scene as a children's picture-book illustration in gouache: flat matte colour shapes, soft dry-brush texture, simple friendly faces, a warm cosy palette.",
  "linocut": "Recreate this scene as a three-colour linocut print (warm red, teal and black ink on cream paper): bold carved lines, visible gouge marks and slightly uneven ink coverage.",
}
def edit(name, prompt, model):
    bnd = "----rx" + uuid.uuid4().hex
    fields = {"model": model, "prompt": prompt + KEEP, "size": "1024x1536", "quality": "medium", "n": "1"}
    parts = [f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in fields.items()]
    parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"frame.png\"\r\nContent-Type: image/png\r\n\r\n".encode() + src.read_bytes() + b"\r\n")
    parts.append(f"--{bnd}--\r\n".encode())
    r = urllib.request.Request("https://api.openai.com/v1/images/edits", data=b"".join(parts),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": f"multipart/form-data; boundary={bnd}"})
    with urllib.request.urlopen(r, timeout=600) as f: d = json.loads(f.read())
    (out / f"{name}.png").write_bytes(base64.b64decode(d["data"][0]["b64_json"]))
    return name, model, d.get("usage")
def one(item):
    name, prompt = item
    for model in ("gpt-image-2", "gpt-image-1.5"):
        try: return edit(name, prompt, model)
        except urllib.error.HTTPError as e: err = f"HTTP {e.code}: {e.read().decode()[:300]}"; print(name, model, err, flush=True)
        except Exception as e: print(name, model, repr(e)[:300], flush=True)
    return name, None, None
with cf.ThreadPoolExecutor(5) as ex:
    for name, model, usage in ex.map(one, STYLES.items()): print("done", name, model, json.dumps(usage), flush=True)
