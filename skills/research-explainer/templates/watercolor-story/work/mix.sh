#!/usr/bin/env bash
# Voice to -16 LUFS (two-pass loudnorm), music -6.3 dB, sum, limiter, pad to the film length. Usage: bash mix.sh 47.6
set -euo pipefail
DUR="${1:?film length in seconds}"
cd "$(dirname "$0")/../assets"
J=$(ffmpeg -hide_banner -i voice.wav -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
MI=$(echo "$J" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
ffmpeg -v error -y -i voice.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11:$MI:linear=true,aresample=48000" -ar 48000 voice_n.wav
ffmpeg -v error -y -i music.wav -af "volume=-6.3dB" music_n.wav
ffmpeg -v error -y -i voice_n.wav -i music_n.wav -filter_complex "[0][1]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.79:attack=3:release=60:level=false,apad=whole_dur=$DUR" -ar 48000 -t "$DUR" mix.wav
for f in voice_n.wav music_n.wav mix.wav; do echo -n "$f: "; ffmpeg -hide_banner -i $f -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+I:|^\s+Peak:" | tr -s ' ' | tr '\n' ' '; echo; done
