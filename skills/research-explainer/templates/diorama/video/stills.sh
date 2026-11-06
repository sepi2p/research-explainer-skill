#!/bin/bash
# stills.sh "t1,t2,..." [outdir]: render stills of the whole page at 854x480 for review (+ a contact sheet)
cd "$(dirname "$0")"
OUT=${2:-../work/stills}; mkdir -p "$OUT"
node render_seg.mjs index.html - --width 854 --height 480 --stills "$1" --stills-dir "$OUT" 2>&1 | grep -v "^$" | head -20
${PY:-python3} ../work/sheet.py "$OUT" 3 >/dev/null && echo "sheet: $OUT/sheet.png"
