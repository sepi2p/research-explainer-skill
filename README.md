# research-explainer

A Claude Code skill that turns a paper, a set of papers, or your own experiments into a **3Blue1Brown-style explainer
video** (and optionally a slide deck), in **English and/or Persian (Farsi)**, with every number traceable to a source and
every data image coming from a real run.

- **Sources**: one paper, a collection of papers, your own code/results/notes, or a mix.
- **Voice**: none (text only, captions paced for reading), free offline voice (Piper), your own recordings, or a paid
  OpenAI voice (your API key, stored in a file, never pasted into the chat).
- **Experiments**: Claude can run your code or small new experiments to produce real figures; each asset is registered
  with the script, seed and hash that produced it.
- **Accuracy gates**: a claims ledger (`claims.json`) with status (final / development / planned / reported ...) and source
  for every claim; the build refuses numbers in the narration that are not in the ledger or the measured data.
- **Persian done properly**: right-to-left layout, Persian digits, Vazirmatn font, mixed Persian/Latin lines ordered
  correctly, numbers spoken as words, reading-speed pacing.

Bundled: the `manim-composer`, `manimce-best-practices` and `manimgl-best-practices` skills by Adithya S Kolavi, and the
Inter and Vazirmatn fonts. See [THIRD_PARTY.md](THIRD_PARTY.md).

## Install

```bash
git clone <this repo> && cd research-explainer-skill
./install.sh            # skills -> ~/.claude/skills, fonts -> ~/.local/share/fonts, then a setup check
```
It prints what is still missing (Manim, FFmpeg, optional Piper/LaTeX). On Linux:
`sudo apt install ffmpeg libcairo2-dev libpango1.0-dev pkg-config python3-dev && uv tool install manim`.

## Use

In Claude Code, in the folder with your paper or project:

> Make an explainer video of my paper `paper.pdf` for researchers in nearby fields.

or

> I want a 10-minute Persian video about my experiments in `./runs`, no voice, and a matching slide deck.

Claude asks a few questions first (source, audience, length, language, voice, whether it may run experiments, what is
final), shows you the claims ledger and the scene plan for approval, then builds. You get
`build/<name>_<lang>_<voice>.mp4`, a smaller `_share.mp4` for messaging apps, and an `.srt`.

## Demo

`examples/averaging-noise/`: a 1-minute video built from a real (tiny) experiment, in English and Persian.
```bash
cd examples/averaging-noise
python3 experiments/averaging.py                       # needs numpy + pillow (manim's Python has both)
python3 ../../skills/research-explainer/scripts/rx.py build fa --voice none
python3 ../../skills/research-explainer/scripts/rx.py build en --voice piper
```

## Status
Tested with Claude Code on Linux (Manim CE 0.19-0.22). macOS should work (fonts go to ~/Library/Fonts); Windows is untested.
Other agents that read `SKILL.md` folders may work but are untested.

MIT for the skill and example; bundled components keep their licences.
