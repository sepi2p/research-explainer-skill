# Instructions for AI agents

You are installing or using **research-explainer**, a skill that builds 3Blue1Brown-style research explainer videos with
Manim (English and Persian). Follow these steps in order. Ask the user before any `sudo` command, any paid API use, and any
download larger than about 500 MB.

## Install (Claude Code)

1. **Check the platform.** Linux and macOS are supported. On Windows, use WSL (Ubuntu) and follow the Linux steps inside it.
2. **System tools.** Check with `ffmpeg -version`, `pkg-config --modversion pangocairo`, `uv --version`. Install only what
   is missing, after the user agrees:
   - Debian/Ubuntu: `sudo apt install -y ffmpeg libcairo2-dev libpango1.0-dev pkg-config python3-dev`
   - macOS (Homebrew): `brew install ffmpeg cairo pango pkg-config`
   - uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `pipx install uv`)
3. **Manim.** `uv tool install manim`, then check with `manim --version` (expect "Manim Community v0.19" or newer).
   If `manim` is not on PATH, it is in `~/.local/bin/manim`.
4. **The skill.** Either way works; prefer A inside Claude Code.
   - A (plugin): run `claude plugin marketplace add sepi2p/research-explainer-skill` and then
     `claude plugin install research-explainer@research-explainer-skill` (add `--scope project` for one project only).
     Then install the fonts: `python3 <plugin skill dir>/scripts/rx.py fonts`. The skill folder is under
     `~/.claude/plugins/cache/research-explainer-skill/research-explainer/<version>/skills/research-explainer/`.
   - B (script):
     ```bash
     git clone https://github.com/sepi2p/research-explainer-skill.git
     cd research-explainer-skill && ./install.sh          # --project: this project only; --codex: ~/.agents/skills
     ```
     This copies `research-explainer`, `manim-composer`, `manimce-best-practices` and `manimgl-best-practices` into
     `~/.claude/skills/`, and installs the Inter and Vazirmatn fonts.
5. **Verify.** `python3 <skill dir>/scripts/rx.py check` must end with `ready`. Lines starting
   with `(optional)` may show `--`; that only means those features are unavailable.
6. **Optional extras** (ask the user):
   - free voice: `uv tool install piper-tts`. Voices download on first use.
   - paid OpenAI voice: the user creates `~/.config/openai/key` themselves (`chmod 600`). **Never ask for the key in the
     chat, never print it, and never write it anywhere else.**
   - LaTeX for `MathTex`: `sudo apt install texlive-latex-extra` (Linux) or `brew install --cask mactex-no-gui` (macOS).
7. **Smoke test** (about 1 minute; needs the cloned repo, or the plugin folder, which contains examples/ too):
   ```bash
   cd examples/averaging-noise
   python3 ../../skills/research-explainer/scripts/rx.py build en --voice none --quality l
   ```
   It must print a line ending in `.srt`. The video is in `examples/averaging-noise/build/`.
8. Tell the user it is installed and that a **new Claude Code session** is needed for the skill to appear. Then tell them
   how to start: "make an explainer video of <paper/project>".

## Use

Load `skills/research-explainer/SKILL.md` and follow it. In short: intake questions, then the claims ledger, real
assets, a scene plan the user approves, narration and scenes, `rx.py build`, contact-sheet review, and delivery.
Accuracy rules are in `references/accuracy.md`; follow them strictly.

## Troubleshooting
| symptom | fix |
|---|---|
| `pangocairo` / `cairo` build error while installing manim | install the system libraries in step 2, then `uv tool install --force manim` |
| `font Vazirmatn` missing in check | `rx.py fonts`; on Linux also `fc-cache -f` |
| scene fails only during parallel renders | rx.py retries it alone automatically; if it persists, run with `JOBS=1` |
| `MathTex` errors | LaTeX is missing: install it, or use `T()` text instead |
| Persian label still in English | `rx.py strings fa`, then add it to `strings_fa.json` |
