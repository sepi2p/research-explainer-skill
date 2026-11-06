#!/usr/bin/env bash
# Snapshot the two still frames the page curl (t1: kitchen -> explanation) blends into ../assets/t1_from.png, t1_to.png.
# The captions host and the transition host are hidden while the stills are taken, then index.html is restored.
# Run again after changing the look (assets/pstyle.js) or the layout around the cut. The times are the start and the end of
# the t1 host in index.html (read from it); TIMES="from to" overrides them.
set -euo pipefail
cd "$(dirname "$0")/.."
export DO_NOT_TRACK=1
T1=$(node -e '
const m = require("fs").readFileSync("index.html", "utf8").match(/id="t1"[\s\S]*?data-start="([\d.]+)"\s+data-duration="([\d.]+)"/);
if (!m) { console.error("stills.sh: no t1 host with data-start and data-duration in index.html"); process.exit(1); }
const r = (x) => String(Math.round(x * 1000) / 1000);
console.log(r(+m[1]) + " " + r(+m[1] + +m[2]));')
read -r A B <<< "${TIMES:-$T1}"
cp index.html work/index.bak
trap 'cp work/index.bak index.html' EXIT
sed -i 's|<div id="captions" data-composition-id="captions"|<div id="captions" data-hidden data-composition-id="captions"|; s| data-composition-src="compositions/t1.html"| data-composition-src="compositions/t1.html" data-hidden|' index.html
[ "$(grep -c 'data-hidden' index.html)" -ge 2 ] || { echo "stills.sh: could not hide the captions and transition hosts" >&2; exit 1; }
rm -rf work/snap_t
npx --yes hyperframes@0.9.19 snapshot --at "$A,$B" --no-end --keep -o work/snap_t
cp "work/snap_t/at-${A}s.png" assets/t1_from.png
cp "work/snap_t/at-${B}s.png" assets/t1_to.png
echo "stills at ${A}s and ${B}s copied to assets/t1_from.png, assets/t1_to.png"
