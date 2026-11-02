"""The project being built: its folder, project.json, and the build paths. Works without Manim."""
import json, os, pathlib

ROOT = pathlib.Path(os.environ.get("EXPLAINER_PROJECT", os.getcwd())).resolve()
CONF_FILE = ROOT / "project.json"
CONF = json.loads(CONF_FILE.read_text()) if CONF_FILE.exists() else {}
BUILD = ROOT / "build"
ASSETS = ROOT / "assets"
LANG = os.environ.get("VIDEO_LANG", (CONF.get("languages") or ["en"])[0])
RTL = LANG in ("fa", "ar", "ur", "he")


def narration_file(lang):
    return ROOT / f"narration_{lang}.json"


def load_json(p, default=None):
    p = pathlib.Path(p)
    return json.loads(p.read_text()) if p.exists() else default


def durations():
    """The beat lengths for this render (set by rx.py through DURATIONS); falls back to the narration with 3 s beats."""
    p = os.environ.get("DURATIONS")
    if p and pathlib.Path(p).exists():
        d = load_json(p)
    else:
        n = load_json(narration_file(LANG), {"scenes": []})
        d = {"scenes": [{"id": s["id"], "beats": [{"dur": 3.0, "caption": b.get("caption", b.get("say", ""))} for b in s["beats"]]}
                        for s in n["scenes"]]}
    return {s["id"]: s for s in d["scenes"]}
