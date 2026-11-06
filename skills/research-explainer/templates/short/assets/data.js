// Seeded simulation written by work/make_data.py (numpy, seed 0, 1000000 trials per n); no recorded runs, no API calls.
// Every number the short shows comes from here: python3 work/make_data.py rebuilds it.
window.DATA = {
 "true": 1.0,
 "sigma": 0.25,
 "seed": 0,
 "readings": [
  1.03,
  0.97,
  1.16,
  1.03,
  0.87,
  1.09,
  1.33,
  1.24,
  0.82,
  0.68,
  0.84,
  1.01,
  0.42,
  0.95,
  0.69,
  0.82,
  0.86,
  0.92,
  1.1,
  1.26
 ],
 "mean": 0.95,
 "mean_miss": 0.05,
 "worst": {
  "index": 12,
  "value": 0.42,
  "miss": 0.58
 },
 "error": {
  "ns": [
   1,
   4,
   16,
   64
  ],
  "trials": 1000000,
  "rho": 0.5,
  "independent": {
   "1": 0.2499,
   "4": 0.1249,
   "16": 0.0626,
   "64": 0.0312
  },
  "correlated": {
   "1": 0.2499,
   "4": 0.1976,
   "16": 0.1823,
   "64": 0.1784
  },
  "theory": {
   "1": 0.25,
   "4": 0.125,
   "16": 0.0625,
   "64": 0.0312
  },
  "correlated_theory": {
   "1": 0.25,
   "4": 0.1976,
   "16": 0.1822,
   "64": 0.1782
  },
  "floor": 0.1768
 }
};
