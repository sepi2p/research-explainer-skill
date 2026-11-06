#!/bin/bash
# render_par.sh page.html out.mp4 DURATION JOBS [extra args]: split the frames over JOBS headless browsers, then join
set -e
PAGE=$1; OUT=$2; DUR=$3; JOBS=${4:-4}; shift 4
FPS=30; N=$(python3 -c "print(round($DUR*$FPS))")
TMP=$(dirname "$OUT")/segs; rm -rf "$TMP"; mkdir -p "$TMP"
HERE=$(cd "$(dirname "$0")" && pwd)
pids=()
for j in $(seq 0 $((JOBS-1))); do
  a=$((N*j/JOBS)); b=$((N*(j+1)/JOBS))
  node "$HERE/render_seg.mjs" "$PAGE" "$TMP/s$j.mp4" --duration "$DUR" --fps $FPS --from $a --to $b "$@" > "$TMP/log$j.txt" 2>&1 &
  pids+=($!)
done
fail=0; for p in "${pids[@]}"; do wait $p || fail=1; done
[ $fail = 0 ] || { tail -5 "$TMP"/log*.txt; exit 1; }
for j in $(seq 0 $((JOBS-1))); do echo "file 's$j.mp4'"; done > "$TMP/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy "$OUT"
echo "rendered $OUT ($N frames, $JOBS jobs)"
