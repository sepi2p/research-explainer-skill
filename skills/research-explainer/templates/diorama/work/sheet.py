"""sheet.py <dir> [cols]: contact sheet of the PNG stills in <dir> (writes <dir>/sheet.png), labels each with its time."""
import sys, glob, os
from PIL import Image, ImageDraw
d = sys.argv[1]; cols = int(sys.argv[2]) if len(sys.argv) > 2 else 3
fs = sorted(f for f in glob.glob(os.path.join(d, "t*.png")))
ims = [Image.open(f).convert("RGB") for f in fs]
if not ims: sys.exit("no stills in " + d)
W, H = ims[0].size; rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (W * cols, H * rows), "white"); dr = ImageDraw.Draw(sheet)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * W, (i // cols) * H
    sheet.paste(im, (x, y)); dr.rectangle([x, y, x + 74, y + 18], fill="black"); dr.text((x + 4, y + 3), os.path.basename(f)[1:-4] + "s", fill="white")
sheet.save(os.path.join(d, "sheet.png")); print(os.path.join(d, "sheet.png"), sheet.size)
