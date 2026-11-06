#!/bin/bash
# render_part.sh NAME "scene stems,comma-separated" T0 T1 [JOBS]: draft 480p render of one part of the video (seconds
# T0..T1) from a private page that loads only the given scene files (others may be mid-edit). With work/audio/mix.wav
# present, the matching slice of the soundtrack is muxed in (loudness-normalised to -14 LUFS); otherwise the part is
# silent. x264 crf 27 -> build/parts/NAME.mp4 (small enough to send in a chat).
set -e
cd "$(dirname "$0")/../video"
NAME=$1; STEMS=$2; T0=$3; T1=$4; JOBS=${5:-8}
OUT=../build/parts; mkdir -p $OUT .preview; TMP=$OUT/tmp_$NAME; rm -rf "$TMP"; mkdir -p "$TMP"
PAGE=.preview/part_$NAME.html
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
TOTAL=$(python3 -c "import json;print(json.load(open('../timeline.json'))['total'])")
A=$(python3 -c "print(round($T0*30))"); B=$(python3 -c "print(round($T1*30))")
pids=()
for j in $(seq 0 $((JOBS-1))); do
  a=$((A+(B-A)*j/JOBS)); b=$((A+(B-A)*(j+1)/JOBS))
  node render_seg.mjs "$PAGE" "$TMP/s$j.mp4" --duration "$TOTAL" --fps 30 --from $a --to $b --width 854 --height 480 > "$TMP/log$j.txt" 2>&1 &
  pids+=($!)
done
fail=0; for p in "${pids[@]}"; do wait $p || fail=1; done
[ $fail = 0 ] || { tail -5 "$TMP"/log*.txt; exit 1; }
for j in $(seq 0 $((JOBS-1))); do echo "file 's$j.mp4'"; done > "$TMP/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy "$TMP/video.mp4"
if [ -f ../work/audio/mix.wav ]; then
  DUR=$(python3 -c "print($T1-$T0)")
  ffmpeg -v error -y -ss $T0 -t $DUR -i ../work/audio/mix.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 "$TMP/audio.wav"
  ffmpeg -v error -y -i "$TMP/video.mp4" -i "$TMP/audio.wav" -map 0:v -map 1:a -c:v libx264 -crf 27 -preset slow -pix_fmt yuv420p \
    -c:a aac -b:a 128k -movflags +faststart -shortest "$OUT/$NAME.mp4"
else
  ffmpeg -v error -y -i "$TMP/video.mp4" -c:v libx264 -crf 27 -preset slow -pix_fmt yuv420p -movflags +faststart "$OUT/$NAME.mp4"
fi
rm -rf "$TMP"
echo "$OUT/$NAME.mp4 $(du -h $OUT/$NAME.mp4 | cut -f1) $(ffprobe -v error -show_entries format=duration -of csv=p=0 $OUT/$NAME.mp4)s"
