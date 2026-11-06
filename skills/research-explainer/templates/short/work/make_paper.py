"""Seeded paper texture (fibres + soft mottling), 1080x1920, so the final 2x export stays sharp. Writes ../assets/paper.jpg
(bg.html uses it). Needs numpy and pillow."""
import pathlib
import numpy as np
from PIL import Image, ImageFilter
rng = np.random.default_rng(1405); W, H = 1080, 1920
base = np.array([243, 233, 210], np.float32)            # paper #F3E9D2
mott = rng.normal(0, 1, (H // 24, W // 24)).astype(np.float32)
mott = np.array(Image.fromarray(mott).resize((W, H), Image.BICUBIC)); mott = mott / np.abs(mott).max()
img = Image.new("L", (W, H), 0); px = img.load()
from PIL import ImageDraw
d = ImageDraw.Draw(img)
for _ in range(2600):                                     # short fibres
    x, y = rng.uniform(0, W), rng.uniform(0, H); a = rng.uniform(0, np.pi); L = rng.uniform(6, 26)
    d.line([(x, y), (x + L * np.cos(a), y + L * np.sin(a))], fill=int(rng.uniform(25, 60)), width=1)
fib = np.array(img.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
grain = rng.normal(0, 1, (H, W)).astype(np.float32)
out = base[None, None, :] + mott[..., None] * 5.5 - fib[..., None] * 16 + grain[..., None] * 2.2
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "paper.jpg"; OUT.parent.mkdir(exist_ok=True)
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT, quality=88)
print("ok")
