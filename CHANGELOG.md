# What changed

Newest first. Agents: read this after an update to learn new commands; every feature lands here and in SKILL.md in the
same commit.

## 0.3.0 (2026-11-03)
- Visual storytelling first: SKILL.md and scene-patterns.md plan each beat by what moves; on-screen text is labels.
  Captions are no longer burned in by default (`"captions": "srt"`; `"burn"` brings the strip back). Without burned
  captions, text-only beats last as long as their animation plus `"hold"` (default 0.8 s).
- Motion vocabulary in base.py: `fan`, `gather`, `collapse_to`, `ticker`, `value_axis`, `dot_plot`, `particles`,
  `push_in`/`pull_out`, `spotlight`.
- New demo `examples/how-a-network-sees/`: ResNet-18 (ImageNet weights) on CC0 photos fetched with a licence check;
  pixels, learned filters sweeping, feature maps, prediction, saliency, a 2/255 adversarial change. EN + FA.
- `bar_chart`: bars now start after the longest label (they covered long labels), and in right-to-left rows the value,
  not the name, sits at the bar's end.
- `rx.py promo`: short launch videos (motion graphics in an HTML timeline, captured frame by frame with Playwright, music +
  sound-effect cues, poster baked in). Template in templates/promo/, guide in references/promo.md, CC0 sound effects in
  assets/sfx/. `rx.py check` reports whether the engine is installed.
- Persian text: formulas with Persian digits ("n = ۶۴") stay one left-to-right run inside a Persian sentence.
- `rx.py assemble` printed minutes rounded up (3:52 as "4:52").
- LICENSE is now the plain MIT text, so GitHub detects it as MIT. The scope statement (MIT for this repository's own
  files; bundled skills and fonts under their own licences, manimgl-best-practices non-commercial) moved to
  THIRD_PARTY.md and the READMEs. Plugin manifests list all licences: `MIT AND CC-BY-NC-SA-4.0 AND OFL-1.1`.

## 0.2.0 (2026-11-02)
- Codex and ChatGPT: OpenAI plugin manifest (`.codex-plugin/plugin.json`), marketplace (`.agents/plugins/marketplace.json`),
  skill metadata (`skills/research-explainer/agents/openai.yaml`). `install.sh --codex` copies the skills to `~/.agents/skills`.
- SKILL.md: a mode for surfaces that cannot run commands (ChatGPT web/mobile): plan, ledger, narration and scene code,
  rendering left to a local agent.
- `rx.py status`: a short outline of the project and the next step.
- `rx.py request`: log a missing feature (feature_requests.md); GitHub issue templates for requests and bugs.
- `rx.py selftest`: builds the demo in English and Persian the way an agent would and checks every output.
- Errors now say how to fix them (e.g. "did you mean s02_average?"); common wrong narration field names are accepted with a note.
- `rx.py --help` states what each write command replaces.

## 0.1.0 (2026-11-02)
- First public version: intake, claims ledger, registered assets, Manim library with Persian support, voices
  (none / Piper / manual / OpenAI), build, contact sheets, slides template, demo, Claude Code plugin.
