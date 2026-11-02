"""The experiment behind the demo: what a pretrained ImageNet classifier (torchvision ResNet-18, IMAGENET1K_V1 weights)
does with one real photo, and how a change of at most 2/255 per pixel value changes its answer.

Writes into assets/ (all from this one run; CPU, seed 0, deterministic):
  photo.png              the 224x224 crop the network sees (resize 256, centre crop 224)
  filters.png            the 64 learned first-layer filters (7x7 RGB), 8x8 grid
  filter_<k>.png, fmap_conv1_<k>.png   the 3 filters that respond most to this photo, and their feature maps
  stage_<s>_<i>.png      the 6 strongest channels after each stage (conv1, layer1..layer4), magma colours
  saliency.png           where the answer is most sensitive (|input gradient|, max over colour, blurred), as a heat overlay
  adv.png, delta.png     the adversarial photo (saved as 8-bit and re-checked from the file) and its change x gain
  gallery_<name>.png     other photos with the network's top answer
  data.json              predictions, shapes, pixel patch, pooled features, attack settings and results
Run (needs torch + torchvision; the ResNet-18 weights download once, ~45 MB):
    python3 experiments/fetch_images.py && python3 experiments/network.py
"""
import json, pathlib
import numpy as np
import torch, torchvision as tv
import torch.nn.functional as F
from PIL import Image, ImageFilter
from matplotlib import colormaps

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "sources" / "images", ROOT / "assets"
OUT.mkdir(exist_ok=True)
torch.manual_seed(0)
torch.use_deterministic_algorithms(True)
W = tv.models.ResNet18_Weights.IMAGENET1K_V1
net = tv.models.resnet18(weights=W).eval()
CATS = W.meta["categories"]
MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
crop = tv.transforms.Compose([tv.transforms.Resize(256), tv.transforms.CenterCrop(224)])
HERO, GALLERY = "dog2", ["fish2", "cat", "cat2"]
TARGET = "goldfish"                  # the attack asks for this class
EPS, STEPS, ALPHA = 2 / 255, 40, 0.25 / 255


def load(name):
    return crop(Image.open(SRC / f"{name}.jpg").convert("RGB"))


def to_t(img):
    return torch.from_numpy(np.asarray(img, dtype=np.float32) / 255).permute(2, 0, 1)[None]


def logits(x):                       # x in [0, 1]
    return net((x - MEAN) / STD)


def top(x, k=5):
    p = logits(x).softmax(1)[0]
    v, i = p.topk(k)
    return [{"label": CATS[j], "p": round(float(s), 4)} for s, j in zip(v, i)]


def save(a, name):                   # a: HxWx3 in [0, 1]
    Image.fromarray((np.clip(a, 0, 1) * 255).round().astype(np.uint8)).save(OUT / name)


def heat(m):                         # 2-D map -> magma colours, normalised to its own range
    m = (m - m.min()) / (m.max() - m.min() + 1e-12)
    return colormaps["magma"](m)[..., :3]


res = {"model": "torchvision resnet18 IMAGENET1K_V1", "hero": HERO}
img = load(HERO)
img.save(OUT / "photo.png")
x = to_t(img)
with torch.no_grad():
    res["top5"] = top(x)

# a patch of real pixel values (8-bit) around the nose, for the zoom-in
py, px = 96, 104
res["patch"] = {"y": py, "x": px, "size": 6, "rgb": np.asarray(img)[py:py + 6, px:px + 6].tolist()}

# first-layer filters
w1 = net.conv1.weight.detach()                       # 64 x 3 x 7 x 7
tiles = []
for k in range(64):
    f = w1[k].permute(1, 2, 0).numpy()
    tiles.append((f - f.min()) / (f.max() - f.min() + 1e-12))
G = np.ones((8 * 8 + 9, 8 * 8 + 9, 3)) * 0.08
for k, f in enumerate(tiles):
    r, c = divmod(k, 8)
    G[1 + r * 9:1 + r * 9 + 7, 1 + c * 9:1 + c * 9 + 7] = f
save(G, "filters.png")

# activations at every stage
acts = {}
def hook(name):
    def f(_, __, out):
        acts[name] = out.detach()[0]
    return f
net.relu.register_forward_hook(hook("conv1"))
for s in ["layer1", "layer2", "layer3", "layer4"]:
    getattr(net, s).register_forward_hook(hook(s))
net.avgpool.register_forward_hook(hook("pooled"))
with torch.no_grad():
    logits(x)
a1 = acts["conv1"]
best = a1.mean((1, 2)).argsort(descending=True)[:3].tolist()
res["conv1_best"] = best
for k in best:
    save(tiles[k], f"filter_{k}.png")
    save(heat(a1[k].numpy()), f"fmap_conv1_{k}.png")
res["stages"] = []
for s in ["conv1", "layer1", "layer2", "layer3", "layer4"]:
    a = acts[s]
    order = a.mean((1, 2)).argsort(descending=True)[:6].tolist()
    for i, c in enumerate(order):
        save(heat(a[c].numpy()), f"stage_{s}_{i}.png")
    res["stages"].append({"name": s, "channels": a.shape[0], "h": a.shape[1], "w": a.shape[2]})
res["pooled"] = [round(float(v), 3) for v in acts["pooled"].flatten()]

# saliency: |d logit(top class) / d input|, max over colour, blurred a little
xs = x.clone().requires_grad_(True)
cls = int(logits(xs).argmax())
logits(xs)[0, cls].backward()
g = xs.grad[0].abs().amax(0).numpy()
g = np.asarray(Image.fromarray((g / g.max() * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), dtype=np.float32) / 255
hm = heat(g)
alpha = np.clip(g / np.percentile(g, 99), 0, 1)[..., None] * 0.85
save(np.asarray(img, dtype=np.float32) / 255 * (1 - alpha) + hm * alpha, "saliency.png")

# targeted attack (PGD, L-inf 2/255), then saved as 8-bit and checked again from the file
t = CATS.index(TARGET)
delta = torch.zeros_like(x, requires_grad=True)
for _ in range(STEPS):
    loss = F.cross_entropy(logits((x + delta).clamp(0, 1)), torch.tensor([t]))
    loss.backward()
    with torch.no_grad():
        delta -= ALPHA * delta.grad.sign()
        delta.clamp_(-EPS, EPS)
    delta.grad.zero_()
adv8 = ((x + delta).clamp(0, 1)[0].permute(1, 2, 0).detach().numpy() * 255).round().astype(np.uint8)
Image.fromarray(adv8).save(OUT / "adv.png")
xa = to_t(Image.open(OUT / "adv.png"))
d8 = (np.asarray(Image.open(OUT / "adv.png"), dtype=np.int16) - np.asarray(img, dtype=np.int16))
gain = 0.5 / (np.abs(d8).max() / 255)
save(0.5 + d8 / 255 * gain, "delta.png")
with torch.no_grad():
    res["attack"] = {"method": "targeted PGD, L-inf", "target": TARGET, "eps_255": int(round(EPS * 255)), "steps": STEPS,
                     "max_change_255": int(np.abs(d8).max()), "changed_values_pct": round(float((d8 != 0).mean() * 100), 1),
                     "gain": round(float(gain), 1), "top5": top(xa),
                     "psnr_db": round(float(10 * np.log10(255 ** 2 / np.mean(d8.astype(np.float64) ** 2))), 1)}

res["gallery"] = []
for n in GALLERY:
    im = load(n)
    im.save(OUT / f"gallery_{n}.png")
    with torch.no_grad():
        res["gallery"].append({"name": n, "top1": top(to_t(im), 1)[0]})
(OUT / "data.json").write_text(json.dumps(res, indent=1))
print(json.dumps({k: v for k, v in res.items() if k not in ("pooled", "patch")}, indent=1))
