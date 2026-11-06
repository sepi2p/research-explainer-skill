#!/usr/bin/env bash
# Set up the vertical-short template so it previews and renders as is (the demo short "Averaging noisy readings").
#   1. npm-installs the exact browser libraries in work/ (gsap 3.15.0, p5 1.11.11, pixi.js 8.22.0, gl-transitions 2.5.0)
#      and copies their minified builds into assets/lib/ (not bundled in the repo: see THIRD_PARTY.md for their licences);
#   2. builds assets/lib/transitions.js (window.GLT) from gl-transitions.json with only the transitions the compositions
#      use (window.GLT["Name"] in compositions/*.html): name -> glsl, defaultParams, paramsTypes, author, license;
#   3. makes assets/paper.jpg (work/make_paper.py) if it is missing;
#   4. makes placeholder stills for the GL transitions (assets/t1_from.png ...) and a silent assets/mix.wav if they are
#      missing, so the page loads before the real stills (work/stills.sh) and the real mix (work/mix.sh) exist.
# Needs node + npm, ffmpeg, python3 (PYTHON=... picks another one; numpy + pillow for the paper texture).
# Run from anywhere: ./setup.sh
set -euo pipefail
cd "$(dirname "$0")"
for c in node npm ffmpeg python3; do command -v "$c" >/dev/null || { echo "setup.sh: $c is needed" >&2; exit 1; }; done

echo "== npm install (work/)"
(cd work && npm install --no-audit --no-fund --no-package-lock --loglevel=error)
node -e '
const want = {"gsap": "3.15.0", "p5": "1.11.11", "pixi.js": "8.22.0", "gl-transitions": "2.5.0"};
for (const [n, v] of Object.entries(want)) {
  const got = require("./work/node_modules/" + n + "/package.json").version;
  if (got !== v) { console.error(`setup.sh: ${n} is ${got}, expected ${v}`); process.exit(1); }
}'

echo "== assets/lib"
mkdir -p assets/lib
cp work/node_modules/gsap/dist/gsap.min.js assets/lib/gsap.min.js
cp work/node_modules/p5/lib/p5.min.js assets/lib/p5.min.js
cp work/node_modules/pixi.js/dist/pixi.min.js assets/lib/pixi.min.js
node -e '
const fs = require("fs");
const all = require("./work/node_modules/gl-transitions/gl-transitions.json");
const used = new Set();
for (const f of fs.readdirSync("compositions").filter((f) => f.endsWith(".html")))
  for (const m of fs.readFileSync("compositions/" + f, "utf8").matchAll(/window\.GLT\["([^"]+)"\]/g)) used.add(m[1]);
const out = {};
for (const name of [...used].sort()) {
  const t = all.find((x) => x.name === name);
  if (!t) { console.error("setup.sh: no transition named " + name + " in gl-transitions.json"); process.exit(1); }
  out[name] = { glsl: t.glsl, defaultParams: t.defaultParams, paramsTypes: t.paramsTypes, author: t.author, license: t.license };
}
fs.writeFileSync("assets/lib/transitions.js", "window.GLT = " + JSON.stringify(out) + ";\n");
console.log("transitions.js:", Object.entries(out).map(([n, t]) => `${n} (${t.author}, ${t.license})`).join(", ") || "none");'

PY=${PYTHON:-python3}
if [ ! -f assets/paper.jpg ]; then
  echo "== assets/paper.jpg"
  if "$PY" -c "import numpy, PIL" 2>/dev/null; then
    "$PY" work/make_paper.py
  else
    echo "  $PY has no numpy/pillow: flat paper colour for now (set PYTHON to a Python with both, delete"
    echo "  assets/paper.jpg and run ./setup.sh again for the seeded texture)"
    ffmpeg -v error -y -f lavfi -i "color=c=0xF3E9D2:s=1080x1920" -frames:v 1 -q:v 3 assets/paper.jpg
  fi
fi

# placeholders: a hidden transition host still loads its two images, so they must exist before the first snapshot
for f in t1_from t1_to t2_from t2_to; do
  if [ ! -f "assets/$f.png" ]; then
    ffmpeg -v error -y -i assets/paper.jpg -vf scale=540:960 -frames:v 1 "assets/$f.png"
    echo "placeholder assets/$f.png (replace with work/stills.sh)"
  fi
done
if [ ! -f assets/mix.wav ]; then
  DUR=$(sed -n 's/.*data-composition-id="main"[^>]*data-duration="\([0-9.]*\)".*/\1/p' index.html | head -1)
  ffmpeg -v error -y -f lavfi -i "anullsrc=r=48000:cl=stereo" -t "${DUR:-35.5}" -c:a pcm_s16le assets/mix.wav
  echo "placeholder assets/mix.wav: ${DUR:-35.5} s of silence (replace with work/mix.sh)"
fi
echo "done. Preview: npx hyperframes preview   (README.md has the full pipeline)"
