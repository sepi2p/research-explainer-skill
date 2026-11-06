#!/usr/bin/env bash
# Premix the voice and the score into ../assets/mix.wav (the one audio clip index.html plays).
#   voice: two-pass loudnorm to -16 LUFS (linear) -> assets/voice_n.wav
#   music: MUSIC_DB (default -6.3 dB) -> assets/music_n.wav
#   mix:   sum, alimiter at 0.79 (about -2 dBTP), padded/cut to the film length (index.html "main" data-duration)
# Then render a draft, measure the MP4 (ffmpeg -i draft.mp4 -af ebur128=peak=true -f null -) and set data-volume on the
# <audio id="mix"> element: the HyperFrames render came out ~3 dB louder than this WAV (0.79 gave -15.0 LUFS).
set -euo pipefail
cd "$(dirname "$0")/../assets"
[ -f voice.wav ] || { echo "mix.sh: assets/voice.wav missing (run work/assemble_voice.py)" >&2; exit 1; }
[ -f music.wav ] || { echo "mix.sh: assets/music.wav missing (run work/music.py)" >&2; exit 1; }
MUSIC_DB=${MUSIC_DB:--6.3}
DUR=$(sed -n 's/.*data-composition-id="main"[^>]*data-duration="\([0-9.]*\)".*/\1/p' ../index.html | head -1)
[ -n "$DUR" ] || { echo "mix.sh: no data-duration on the main composition in index.html" >&2; exit 1; }
J=$(ffmpeg -hide_banner -nostats -i voice.wav -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
MI=$(echo "$J" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
ffmpeg -v error -y -i voice.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11:$MI:linear=true,aresample=48000" -ar 48000 voice_n.wav
ffmpeg -v error -y -i music.wav -af "volume=${MUSIC_DB}dB" music_n.wav
ffmpeg -v error -y -i voice_n.wav -i music_n.wav -filter_complex \
  "[0][1]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.79:attack=3:release=60:level=false,apad=whole_dur=$DUR" \
  -ar 48000 -t "$DUR" mix.wav
for f in voice_n.wav music_n.wav mix.wav; do
  printf '%-12s ' "$f"; ffmpeg -hide_banner -nostats -i "$f" -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary/,$p' | grep -E '^\s+(I|Peak):' | tr -s ' ' | tr '\n' ' '; echo
done
