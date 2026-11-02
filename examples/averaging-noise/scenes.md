# Why averaging removes noise

## Overview
- Source: own experiment (experiments/averaging.py)   Audience: researchers outside signal processing   Length: ~1 min
- Languages: en, fa   Voice: none (text only) or piper
- Hook question: if each measurement is noisy, do many measurements give the clean signal back?
- The one sentence to remember: averaging divides independent noise by √n, but shared noise sets a floor.

## Scenes
### s00_title (3 s)
Title card, no narration.

### s01_noise (~15 s)
1. say: a test image and one noisy copy | show: clean and noisy side by side (assets clean, avg_01) | claims: -
2. say: noise σ = 0.25 on a 0-1 scale | show: red pill over the noisy image | claims: c1
3. say: can many measurements recover it? | show: "?" between the images

### s02_average (~12 s)
1. say: average 4, 16, 64 copies | show: avg_01..avg_64 in a row, n labels | claims: c4
2. say: the error image fades | show: resid_* under each, true scale (gain ×1) | claims: c2

### s03_chart (~15 s)
1. say: measured RMSE 0.25 → 0.125 → 0.0625 → 0.031 (20 trials) | show: measured curve with values, status tag, source line | claims: c2, c4
2. say: σ/√n, four times the copies halves the error | show: dashed theory curve | claims: c2

### s04_limit (~20 s)  (the limits scene)
1. say: only for independent noise | show: independent curve highlighted
2. say: shared noise (correlation 0.5) stops near 0.18 | show: correlated curve, value at n = 64 | claims: c3
3. say: floor 0.177 | show: dashed floor line | claims: c3

## Palette
accent = floor / key result, a (blue) = independent noise, b (red) = shared noise
