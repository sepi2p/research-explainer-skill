#!/bin/bash
# stills_scene.sh <scene file stem(s), comma-separated> "t1,t2,..." [outdir]
# Renders 854x480 stills from a private page that loads the shared engine + only the given scene files, so a
# half-written scene in another file cannot break your preview (other scenes show as "missing scene"), and writes a
# contact sheet sheet.png. Example: ./stills_scene.sh s1_reading "1,3.5,6" ../work/stills/s1_reading
cd "$(dirname "$0")"
STEMS=$1; TIMES=$2; OUT=${3:-../work/stills/$(echo $1 | cut -d, -f1)}
mkdir -p "$OUT" .preview
PAGE=.preview/$(echo $STEMS | tr ',' '_').html
python3 - "$STEMS" "$PAGE" <<'PY'
import sys, re, pathlib
stems, page = sys.argv[1].split(','), pathlib.Path(sys.argv[2])
h = pathlib.Path('index.html').read_text()
def keep(m):
    src = m.group(1)
    if src.startswith('scenes/') and src[7:-3] not in stems: return ''
    return m.group(0)
h = re.sub(r'<script src="([^"]+)"></script>', keep, h)
h = h.replace('src="', 'src="../').replace("url('fonts/", "url('../fonts/")
page.write_text(h)
PY
node render_seg.mjs "$PAGE" - --width 854 --height 480 --stills "$TIMES" --stills-dir "$OUT" 2>&1 | grep -v "^$" | head -20
${PY:-python3} ../work/sheet.py "$OUT" 3 >/dev/null && echo "sheet: $OUT/sheet.png"
