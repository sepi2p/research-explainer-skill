"""Seeded simulation behind the demo short: averaging noisy readings of one quantity. Writes ../assets/data.js.

Every number on screen comes from here (numpy, fixed seed, no API calls):
  * 20 readings of a quantity whose true value is 1.00, each with independent Gaussian noise of standard deviation 0.25
    (rounded to 2 decimals, as a display would show them); their average and how far it and the worst reading miss;
  * the error (RMSE) of the average of n readings, n = 1, 4, 16, 64, over TRIALS simulated trials, for independent
    noise and for noise with correlation RHO = 0.5 between readings (one shared part plus one part of their own), with
    the theory 0.25/sqrt(n) and the floor of the correlated case, 0.25*sqrt(RHO).
Usage: python3 work/make_data.py     (numpy only). Change TRUE, SIGMA, RHO, SEED for your own demo, then re-time.
"""
import json, pathlib
import numpy as np

TRUE, SIGMA, RHO, SEED, N_CARDS, TRIALS, NS = 1.0, 0.25, 0.5, 0, 20, 1_000_000, [1, 4, 16, 64]
CHUNK = 100_000                                                   # trials per batch (memory)
rng = np.random.default_rng(SEED)

# the 20 readings on the cards (2 decimals, like a display); the average is taken over the shown values
readings = np.round(TRUE + rng.normal(0, SIGMA, N_CARDS), 2)
mean = float(np.round(readings.mean(), 2))
worst = int(np.argmax(np.abs(readings - TRUE)))

# error of the average of n readings over many trials
ind, cor, theory, cor_theory = {}, {}, {}, {}
for n in NS:
    se_i = se_c = 0.0
    for _ in range(TRIALS // CHUNK):
        own = rng.normal(0, SIGMA, (CHUNK, n))
        se_i += float(np.sum(own.mean(1) ** 2))
        shared = rng.normal(0, SIGMA, (CHUNK, 1))                     # one part every reading shares ...
        noise = np.sqrt(RHO) * shared + np.sqrt(1 - RHO) * rng.normal(0, SIGMA, (CHUNK, n))   # ... and one of its own
        se_c += float(np.sum(noise.mean(1) ** 2))
    ind[n], cor[n] = np.sqrt(se_i / TRIALS), np.sqrt(se_c / TRIALS)
    theory[n] = SIGMA / np.sqrt(n)
    cor_theory[n] = SIGMA * np.sqrt(RHO + (1 - RHO) / n)

r4 = lambda d: {str(k): round(float(v), 4) for k, v in d.items()}
D = {
    "true": TRUE, "sigma": SIGMA, "seed": SEED,
    "readings": readings.tolist(),
    "mean": mean, "mean_miss": round(abs(mean - TRUE), 2),
    "worst": {"index": worst, "value": float(readings[worst]), "miss": round(abs(float(readings[worst]) - TRUE), 2)},
    "error": {"ns": NS, "trials": TRIALS, "rho": RHO, "independent": r4(ind), "correlated": r4(cor),
              "theory": r4(theory), "correlated_theory": r4(cor_theory), "floor": round(SIGMA * np.sqrt(RHO), 4)},
}
out = pathlib.Path(__file__).resolve().parent.parent / "assets" / "data.js"
out.write_text("// Seeded simulation written by work/make_data.py (numpy, seed %d, %d trials per n); no recorded runs, no API calls.\n"
               "// Every number the short shows comes from here: python3 work/make_data.py rebuilds it.\n" % (SEED, TRIALS)
               + "window.DATA = " + json.dumps(D, indent=1) + ";\n")
print(json.dumps(D, indent=1))
