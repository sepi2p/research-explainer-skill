#!/usr/bin/env bash
# Snapshot the still frames the GL transitions blend (t1: s2 -> s3, t2: s3 -> s4) into ../assets/t*_from|to.png.
# The captions host and both transition hosts are hidden (data-hidden) while the stills are taken, then index.html is
# restored. Run again after any layout change in the scenes around a transition.
# Times: TIMES="t1_from t1_to t2_from t2_to" in seconds (default: the demo's 9.9 10.5 18.1 18.65, i.e. the start and
# the end of each transition host in index.html).
set -euo pipefail
cd "$(dirname "$0")/.."
export DO_NOT_TRACK=1
read -r A B C D <<< "${TIMES:-9.9 10.5 18.1 18.65}"
for f in t1_from t1_to t2_from t2_to; do
  [ -f "assets/$f.png" ] || { echo "stills.sh: assets/$f.png missing: run ./setup.sh first (placeholders)" >&2; exit 1; }
done
cp index.html work/index.bak
trap 'cp work/index.bak index.html' EXIT
sed -i 's|<div id="captions" data-composition-id="captions"|<div id="captions" data-hidden data-composition-id="captions"|; s| data-composition-src="compositions/t1.html"| data-composition-src="compositions/t1.html" data-hidden|; s| data-composition-src="compositions/t2.html"| data-composition-src="compositions/t2.html" data-hidden|' index.html
[ "$(grep -c 'data-hidden' index.html)" -ge 3 ] || { echo "stills.sh: could not hide the captions and transition hosts" >&2; exit 1; }
rm -rf work/snap_t
npx --yes hyperframes@0.9.19 snapshot --at "$A,$B,$C,$D" --no-end --keep -o work/snap_t
cp "work/snap_t/at-${A}s.png" assets/t1_from.png
cp "work/snap_t/at-${B}s.png" assets/t1_to.png
cp "work/snap_t/at-${C}s.png" assets/t2_from.png
cp "work/snap_t/at-${D}s.png" assets/t2_to.png
echo "stills copied to assets/t1_from.png t1_to.png t2_from.png t2_to.png"
