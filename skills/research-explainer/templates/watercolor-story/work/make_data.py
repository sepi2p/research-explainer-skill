"""Every number the short shows, from one seeded simulation (numpy, no API): a made-up bakery scale whose reading of a
500 g bag wobbles with independent Gaussian noise (sigma 0.25 g), and the same scale in a draught that pushes every
reading of a session the same way (a shared part, correlation 0.5 between readings).
Writes ../assets/data.js (window.DATA) and prints the error table. Run: python3 work/make_data.py"""
import json, pathlib
import numpy as np
H = pathlib.Path(__file__).resolve().parent
TRUE, SIGMA, RHO, NS, TRIALS = 500.0, 0.25, 0.5, [1, 4, 16, 64], 200000
rng = np.random.default_rng(1405)

def readings(n, shared=False):
    """n readings of the bag in one session; with shared=True a draught adds one push that every reading shares"""
    if not shared: return TRUE + rng.normal(0, SIGMA, n)
    return TRUE + np.sqrt(RHO) * rng.normal(0, SIGMA) + np.sqrt(1 - RHO) * rng.normal(0, SIGMA, n)

# the story: the apprentice weighs the bag 16 times (the scale shows 0.1 g)
story = readings(16)
shown = [round(float(x), 1) for x in story]
avg = float(story.mean())
# scene "one reading": 80 single readings for the dot plot
singles = [round(float(x), 3) for x in readings(80)]
# scene "averages": 40 sessions per n, each dot = the average of one session, independent and in a draught
dots = {str(n): [round(float(readings(n).mean()), 4) for _ in range(40)] for n in NS}
draught = {str(n): [round(float(readings(n, True).mean()), 4) for _ in range(40)] for n in NS}
# the error (root mean square distance of the average from 500 g) over TRIALS sessions
def rmse(n, shared):
    own = rng.normal(0, SIGMA, (TRIALS, n))
    e = (np.sqrt(RHO) * rng.normal(0, SIGMA, (TRIALS, 1)) + np.sqrt(1 - RHO) * own if shared else own).mean(1)
    return round(float(np.sqrt(np.mean(e ** 2))), 4)
err = {str(n): rmse(n, False) for n in NS}
err_d = {str(n): rmse(n, True) for n in NS}
theory = {str(n): round(SIGMA / np.sqrt(n), 4) for n in NS}
floor = round(SIGMA * np.sqrt(RHO), 4)
# the claims this short makes (examples/averaging-noise/claims.json in the skill repo): fail loudly if a number drifts
for n in NS: assert abs(err[str(n)] - theory[str(n)]) < 0.04 * theory[str(n)] + 0.001, (n, err[str(n)], theory[str(n)])
assert 0.17 < err_d["64"] < 0.19 and abs(floor - 0.1768) < 1e-3
D = {"true": TRUE, "sigma": SIGMA, "rho": RHO, "ns": NS, "trials": TRIALS, "story": shown, "avg": round(avg, 3),
     "avg_shown": f"{avg:.1f}", "singles": singles, "dots": dots, "draught": draught, "err": err, "err_draught": err_d,
     "theory": theory, "floor": floor,
     # what the screen prints: three significant figures, in grams
     "err_txt": {n: f"{v:#.3g}" for n, v in err.items()}, "err_draught_txt": {n: f"{v:#.3g}" for n, v in err_d.items()},
     "floor_txt": f"{floor:#.3g}"}
(H.parent / "assets" / "data.js").write_text("window.DATA = " + json.dumps(D) + ";\n")
print("story readings:", shown)
print(f"average of 16: {avg:.3f} g (shown {avg:.1f} g)")
print("n     independent  theory   draught (rho 0.5)")
for n in NS: print(f"{n:<5} {err[str(n)]:<12} {theory[str(n)]:<8} {err_d[str(n)]}   shown: {D['err_txt'][str(n)]} g / {D['err_draught_txt'][str(n)]} g")
print("draught floor 0.25*sqrt(0.5) =", floor)
