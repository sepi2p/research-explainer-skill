"""The demo's experiment: a wobbly scale weighs a 2 kg bag of flour; every reading has Gaussian noise (sigma 0.25 kg).
Measures the error (RMSE over many sessions) of the average of n readings, for independent noise and for noise with a
shared part (correlation 0.5 between readings: a draught that pushes every reading of a session the same way).
Deterministic (seed 0), numpy only, no network. Writes data/readings.json; work/make_data.py turns it into video/data.js.
    python3 data/readings.py        (any Python 3 with numpy)
"""
import json, pathlib
import numpy as np

TRUE, SIGMA, RHO = 2.0, 0.25, 0.5          # kg; noise sd per reading; correlation between two readings of a session
NS, SESSIONS, SEED = [1, 4, 16, 64], 20000, 0
rng = np.random.default_rng(SEED)


def rmse(est):
    return float(np.sqrt(np.mean((est - TRUE) ** 2)))


out = {"true": TRUE, "sigma": SIGMA, "rho": RHO, "ns": NS, "sessions": SESSIONS, "seed": SEED,
       "independent": [], "shared": [], "theory": [], "shared_theory": [],
       "shared_floor": round(SIGMA * np.sqrt(RHO), 4)}
for n in NS:
    own = rng.normal(0, SIGMA, (SESSIONS, n))                       # independent: every reading has its own wobble
    out["independent"].append(round(rmse(TRUE + own.mean(1)), 4))
    shared = rng.normal(0, SIGMA, (SESSIONS, 1))                    # one draught per session, the same for all its readings
    own2 = rng.normal(0, SIGMA, (SESSIONS, n))
    noise = np.sqrt(RHO) * shared + np.sqrt(1 - RHO) * own2         # each reading still has sd 0.25; any two correlate 0.5
    out["shared"].append(round(rmse(TRUE + noise.mean(1)), 4))
    out["theory"].append(round(SIGMA / np.sqrt(n), 4))
    out["shared_theory"].append(round(SIGMA * np.sqrt(RHO + (1 - RHO) / n), 4))

# one example session of 64 independent readings: what the scale prints, and the running average
session = TRUE + rng.normal(0, SIGMA, 64)
out["session"] = {"readings": [round(float(v), 2) for v in session],
                  "running_mean": [round(float(v), 3) for v in np.cumsum(session) / np.arange(1, 65)],
                  "mean64": round(float(session.mean()), 2)}

path = pathlib.Path(__file__).with_name("readings.json")
path.write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "session"}, indent=1))
print("session: first readings", out["session"]["readings"][:6], "mean of 64", out["session"]["mean64"])
