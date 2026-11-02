#!/usr/bin/env bash
# Install the research-explainer skill and its bundled Manim skills for Claude Code, plus the fonts.
#   ./install.sh            copy into ~/.claude/skills (all your projects)
#   ./install.sh --project  copy into ./.claude/skills of the current folder (this project only)
#   ./install.sh --link     symlink instead of copy (for editing the skill)
#   ./install.sh --no-gl    skip manimgl-best-practices (CC BY-NC-SA, only needed for ManimGL)
#   ./install.sh --codex    install into ~/.agents/skills (OpenAI Codex; untested)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.claude/skills"; MODE=copy; GL=1
for a in "$@"; do case "$a" in
  --project) DEST="$PWD/.claude/skills";; --codex) DEST="$HOME/.agents/skills";; --link) MODE=link;; --no-gl) GL=0;;
  *) echo "unknown option $a"; exit 1;; esac; done
mkdir -p "$DEST"
for s in research-explainer manim-composer manimce-best-practices manimgl-best-practices; do
  [ "$s" = manimgl-best-practices ] && [ $GL = 0 ] && continue
  rm -rf "${DEST:?}/$s"
  if [ $MODE = link ]; then ln -s "$HERE/skills/$s" "$DEST/$s"; else cp -r "$HERE/skills/$s" "$DEST/$s"; fi
  echo "installed $s -> $DEST/$s"
done
FD="$HOME/.local/share/fonts/research-explainer"
if [ "$(uname)" = Darwin ]; then FD="$HOME/Library/Fonts"; fi
mkdir -p "$FD"; cp "$HERE"/skills/research-explainer/assets/fonts/*.{ttf,otf} "$FD"/
command -v fc-cache >/dev/null && fc-cache -f >/dev/null || true
echo "fonts (Inter, Vazirmatn) -> $FD"
echo
echo "System tools (install yourself if 'check' reports them missing):"
echo "  Linux:  sudo apt install ffmpeg libcairo2-dev libpango1.0-dev pkg-config python3-dev   then: uv tool install manim"
echo "  macOS:  brew install ffmpeg cairo pango pkg-config                                    then: uv tool install manim"
echo "  free voice (optional): uv tool install piper-tts"
echo
python3 "$DEST/research-explainer/scripts/rx.py" check || true
