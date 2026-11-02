# What changed

Newest first. Agents: read this after an update to learn new commands; every feature lands here and in SKILL.md in the
same commit.

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
