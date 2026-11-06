#!/usr/bin/env bash
# Render the set with nobody in it (assets/styles/empty.js) at 1080x1920 into work/empty_room.png: the reference that
# work/paint_room.py repaints as watercolor, so the painting lines up with the animation. assets/pstyle.js is restored.
set -euo pipefail
cd "$(dirname "$0")/.."
export DO_NOT_TRACK=1
cp assets/pstyle.js work/pstyle.bak; cp index.html work/index.bak
trap 'cp work/pstyle.bak assets/pstyle.js; cp work/index.bak index.html' EXIT
cp assets/styles/empty.js assets/pstyle.js
sed -i 's|<div id="captions" data-composition-id="captions"|<div id="captions" data-hidden data-composition-id="captions"|' index.html
rm -rf work/snap_empty
npx --yes hyperframes@0.9.19 snapshot --at 2.8 --no-end --keep --zoom 0,0,540,960 --zoom-scale 2 -o work/snap_empty
cp work/snap_empty/at-2.8s.png work/empty_room.png
echo "work/empty_room.png: now run  python3 work/paint_room.py work/empty_room.png work/painted  and pick one"
