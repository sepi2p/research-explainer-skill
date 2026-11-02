"""Experiment behind the demo video: averaging n noisy copies of an image.
Measures the error (RMSE) after averaging for independent noise and for noise with a shared part (correlation 0.5),
and saves the images and numbers the scenes show. Deterministic (seed 0). Run from the project folder:
    python3 experiments/averaging.py
then register the outputs:  rx.py asset-add assets/<file> --kind measured --by "experiments/averaging.py seed 0"
"""
import json, pathlib
import numpy as np
from PIL import Image

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"
rng = np.random.default_rng(0)
H = W = 64
y, x = np.mgrid[0:H, 0:W] / (H - 1)
clean = np.stack([0.15 + 0.7 * x, 0.15 + 0.7 * y, 0.5 + 0.35 * np.sin(6 * x) * np.cos(6 * y)], -1)
clean[20:44, 20:44] = [0.95, 0.85, 0.2]          # a yellow square, so the eye has an edge to judge
SIGMA, NS, TRIALS, RHO = 0.25, [1, 4, 16, 64], 20, 0.5


def save(a, name):
    Image.fromarray((np.clip(a, 0, 1) * 255).round().astype(np.uint8)).save(OUT / f"{name}.png")


def rmse(a):
    return float(np.sqrt(np.mean((a - clean) ** 2)))


res = {"sigma": SIGMA, "trials": TRIALS, "rho": RHO, "ns": NS, "independent": {}, "correlated": {}, "theory": {}}
for n in NS:
    ind, cor = [], []
    for t in range(TRIALS):
        noise = rng.normal(0, SIGMA, (n, H, W, 3))
        ind.append(rmse(clean + noise.mean(0)))
        shared = rng.normal(0, SIGMA, (H, W, 3))       # one part every copy shares, one part each copy has alone
        own = rng.normal(0, SIGMA, (n, H, W, 3))
        corr = np.sqrt(RHO) * shared + np.sqrt(1 - RHO) * own
        cor.append(rmse(clean + corr.mean(0)))
        if t == 0:
            avg = clean + noise.mean(0)
            save(avg, f"avg_{n:02d}")
            save(0.5 + (avg - clean) * 1.0, f"resid_{n:02d}")   # error image at gain 1 around mid-grey
    res["independent"][str(n)] = round(float(np.mean(ind)), 4)
    res["correlated"][str(n)] = round(float(np.mean(cor)), 4)
    res["theory"][str(n)] = round(SIGMA / np.sqrt(n), 4)
res["correlated_floor"] = round(SIGMA * np.sqrt(RHO), 4)
save(clean, "clean")
OUT.mkdir(exist_ok=True)
(OUT / "data.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
