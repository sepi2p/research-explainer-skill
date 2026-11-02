# Experiments and assets

Goal: every picture of data is real and reproducible. A viewer (or reviewer) could re-run the script and get the same file.

## Kinds (rx.py asset-add --kind)
- **measured**: produced by running code on real data or a real model (the user's code, or our own experiment script).
- **reported**: re-plotted from numbers printed in a paper (cite page/table in --by). Plot exactly those numbers.
- **illustration**: a constructed example that explains a mechanism (a toy 2-D dataset, a schematic). Say "illustration".
- **generated**: image-model output (characters, icons). Never data.

## Rules
- One script per asset family in `experiments/`, deterministic (fixed seeds), writing to `assets/`. Numbers go to
  `assets/data.json` (or another json); scenes read them with `data()`.
- Prefer the user's own code and saved results (logs, checkpoints, CSVs). Re-run only what is needed for a figure; never
  change their method to make a figure look better.
- Small real samples beat big fake ones: 4 real images from their test set > 40 synthetic ones.
- Record provenance: `rx.py asset-add <file> --kind measured --by "experiments/x.py --seed 0 (model ckpt sha ...)"`. The
  manifest stores sha256, date (from the clock) and git commit.
- Ask before long runs (>10 min), before using paid APIs, and before downloading large datasets. Use the GPU when present.
- If a re-run does not match the paper or the user's numbers, stop and report the difference; do not pick the nicer one.

## Showing what the eye cannot see
- Small perturbations / differences: `amplified(diff)` returns an image with 0 at mid-grey and the gain used; print the gain
  on screen ("difference ×40"). Also show the true-scale version once, so viewers see it really is invisible.
- Tiny images (32x32): upscale with nearest neighbour (`nearest=True`), never smooth.
- Distributions: real histograms from saved values; state the number of samples.
- Trajectories over queries/epochs: real logged curves; mark events (success, detection) at the logged step.

## Typical experiment scripts
- `real_samples.py`: copy N named test images (by index) and the model's real predictions into assets/.
- `perturbation.py`: run the attack/method on those images with a seed, save before/after/difference and the scores.
- `results_table.py`: read result CSVs/logs, aggregate exactly as the paper does, write data.json.
- `reported_numbers.py`: hard-code a paper's table with page/table reference in comments, write data.json (kind reported).
