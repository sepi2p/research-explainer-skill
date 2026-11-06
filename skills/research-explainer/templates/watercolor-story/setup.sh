#!/usr/bin/env bash
# Set up the watercolor story template so it previews and renders as is (the example "The wobbly scale" short).
#   1. npm-installs the exact browser libraries in work/ (gsap 3.15.0, p5 1.11.11, gl-transitions 2.5.0) and copies their
#      builds into assets/lib/ (not bundled in the repo: see THIRD_PARTY.md); rough.js (MIT, patched) is bundled;
#   2. builds assets/lib/transitions.js (window.GLT) with only the transitions the compositions use;
#   3. makes assets/paper.jpg (work/make_paper.py) if it is missing (the paper of the "ink" look);
#   4. makes placeholder stills for the page curl (assets/t1_from.png, t1_to.png) and a silent assets/mix.wav if they are
#      missing, so the page loads before the real stills (work/stills.sh) and the real mix (work/mix.sh) exist.
# Needs node + npm, ffmpeg, python3 (PYTHON=... picks another one; numpy + pillow for the paper texture).
set -euo pipefail
cd "$(dirname "$0")"
for c in node npm ffmpeg python3; do command -v "$c" >/dev/null || { echo "setup.sh: $c is needed" >&2; exit 1; }; done
echo "== npm install (work/)"
(cd work && npm install --no-audit --no-fund --no-package-lock --loglevel=error)
node -e '
const want = {"gsap": "3.15.0", "p5": "1.11.11", "gl-transitions": "2.5.0"};
for (const [n, v] of Object.entries(want)) {
  const got = require("./work/node_modules/" + n + "/package.json").version;
  if (got !== v) { console.error(`setup.sh: ${n} is ${got}, expected ${v}`); process.exit(1); }
}'
echo "== assets/lib"
mkdir -p assets/lib
cp work/node_modules/gsap/dist/gsap.min.js assets/lib/gsap.min.js
cp work/node_modules/p5/lib/p5.min.js assets/lib/p5.min.js
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
  if "$PY" -c "import numpy, PIL" 2>/dev/null; then "$PY" work/make_paper.py
  else ffmpeg -v error -y -f lavfi -i "color=c=0xF3E9D2:s=1080x1920" -frames:v 1 -q:v 3 assets/paper.jpg; fi
fi
for f in t1_from t1_to; do
  [ -f "assets/$f.png" ] || ffmpeg -v error -y -i assets/bg_wash.jpg -vf scale=540:960 -frames:v 1 "assets/$f.png"
done
DUR=$(grep -o 'data-composition-id="main" data-start="0" data-duration="[0-9.]*"' index.html | grep -o '[0-9.]*"$' | tr -d '"')
[ -f assets/mix.wav ] || ffmpeg -v error -y -f lavfi -i "anullsrc=r=48000:cl=stereo" -t "${DUR:-40.4}" assets/mix.wav
echo "== done. Preview: npx --yes hyperframes@0.9.19 preview   Render a draft: npx --yes hyperframes@0.9.19 render --quality draft -o renders/draft.mp4"
