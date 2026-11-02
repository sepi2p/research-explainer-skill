#!/usr/bin/env python3
"""rx: build research explainer videos from a project folder (see SKILL.md).

  rx.py status [lang]                       short outline of the project and the next step (start here)
  rx.py check                               tools, fonts, voices, GPU, API key present (never printed)
  rx.py fonts                               install the bundled Inter and Vazirmatn fonts for this user
  rx.py new <dir> [--title T] [--langs en,fa] [--voice none|piper|manual|openai]
  rx.py claims                              every number in the narration must be in claims.json or assets/data.json
  rx.py assets                              every file in assets/ is registered in assets/manifest.json, hashes match
  rx.py asset-add <file> --kind measured|reported|illustration|generated --by "<command or citation>" [--note ...]
  rx.py strings <lang>                      on-screen strings that still need a translation (after a render)
  rx.py voice-script <lang>                 the per-beat script to record (manual voice mode)
  rx.py build <lang> [--voice MODE] [--quality l|m|h] [--scenes ID ...] [--no-music]   everything below in order
  rx.py durations <lang> --voice MODE       beat lengths (voice clips, or reading time for MODE=none)
  rx.py render <lang> [--voice MODE] [--quality l|m|h] [--scenes ID ...] [--dry]
  rx.py assemble <lang> [--voice MODE] [--quality ...] [--no-music]
  rx.py qc <lang> [--voice MODE] [--quality ...]   contact sheets: build/qc/<lang>_<mode>/<scene>.png

  rx.py promo [dir] [--lang fa] [--stills 1.5,9,20]   short launch video from an HTML timeline (promo/index.html + promo.json)

  rx.py request "<what you wanted>" --missing ... --proposal ... [--example ...]   log a missing feature
  rx.py selftest                            build the bundled demo the way an agent would and check the outputs

What each write does: `new` refuses a non-empty folder. `asset-add` replaces that file's record in assets/manifest.json.
`durations` replaces build/durations_<lang>_<mode>.json; voice clips are kept and re-made only for beats whose text changed.
`render` replaces that scene's video. `assemble` replaces the final mp4/srt. `promo` replaces <dir>/promo.mp4 and promo.jpg. `request` appends to feature_requests.md.
Nothing is ever uploaded or published.

Run from the project folder (or set EXPLAINER_PROJECT). Outputs land in build/.
"""
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("EXPLAINER_PROJECT", os.getcwd())
from explainer.project import ROOT, CONF, BUILD, ASSETS, narration_file, load_json  # noqa: E402
from explainer.captions import split_caption, chunk_times  # noqa: E402

QUAL = {"l": ("-ql", "480p15"), "m": ("-qm --fps 30", "720p30"), "h": ("-qh --fps 30", "1080p30")}
CPS = {"en": 15, "fa": 12}   # comfortable reading speed, characters per second (text-only videos)


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), **kw)


def manim_bin():
    for c in [shutil.which("manim"), str(pathlib.Path.home() / ".local/bin/manim")]:
        if c and pathlib.Path(c).exists():
            return c
    sys.exit("manim not found: uv tool install manim  (or pip install manim)")


def manim_python():
    """The Python that runs manim (it has numpy), read from the manim launcher's first line."""
    first = pathlib.Path(manim_bin()).read_text(errors="ignore").splitlines()[0]
    return first[2:].strip() if first.startswith("#!") and "python" in first else sys.executable


def voice_mode(a):
    return a.voice or CONF.get("voice", {}).get("mode", "none")


def scenes_conf():
    if not CONF:
        die(f"no project.json in {ROOT}", "run rx.py from the project folder, or: rx.py new <dir>")
    sc = CONF.get("scenes", [])
    if not sc:
        die("project.json has no scenes", 'add "scenes": [{"id": "s01_hook", "file": "scenes/main.py", "class": "S01Hook"}] in playing order')
    for s in sc:
        miss = [k for k in ("id", "file", "class") if k not in s]
        if miss:
            die(f"scene entry {s} lacks {miss}", 'each entry needs "id" (narration id), "file" (path to .py), "class" (Beat subclass)')
        if not (ROOT / s["file"]).exists():
            die(f"scene file {s['file']} not found", f"create it or fix \"file\" for scene {s['id']} in project.json")
    return sc


ALIASES = {"say": ("narration", "voice", "spoken", "speech", "script"), "caption": ("subtitle", "on_screen", "onscreen", "display"),
           "text": ("text_only", "short", "silent_caption")}


def die(msg, fix):
    sys.exit(f"ERROR: {msg}\nFIX: {fix}")


def narration(lang):
    import difflib
    f = narration_file(lang)
    n = load_json(f)
    if not n:
        die(f"{f.name} not found in {ROOT}", f"create it (see templates/project/narration_{'fa' if lang == 'fa' else 'en'}.json), or check the language code")
    if "scenes" not in n:
        die(f"{f.name} has no top-level \"scenes\" list", '{"scenes": [{"id": "s01_hook", "beats": [{"say": "...", "caption": "..."}]}]}')
    for sc in n["scenes"]:
        for b in sc.get("beats", []):
            for field, alts in ALIASES.items():   # accept common wrong names, and say so
                for alt in alts:
                    if alt in b and field not in b:
                        b[field] = b.pop(alt)
                        print(f"note: {f.name} {sc['id']}: field \"{alt}\" read as \"{field}\" (please rename)")
    ids = [s["id"] for s in n["scenes"]]
    for s in scenes_conf():
        if s["id"] not in ids:
            near = difflib.get_close_matches(s["id"], ids, 1)
            die(f"scene {s['id']} (project.json) has no narration in {f.name}",
                f"did you mean \"{near[0]}\"? Use the same id in both files." if near else f"add a scene with \"id\": \"{s['id']}\" to {f.name}")
    return n


def dur_file(lang, mode):
    return BUILD / f"durations_{lang}_{mode}.json"


def media_dir(lang, mode):
    return BUILD / f"render_{lang}_{mode}"


def slug():
    return CONF.get("slug") or re.sub(r"[^a-z0-9]+", "_", CONF.get("title", ROOT.name).lower()).strip("_") or "explainer"


# ---------------- check ----------------
def cmd_check(a):
    ok = True

    def line(name, good, detail=""):
        nonlocal ok
        ok &= bool(good) or name.startswith("(optional)")
        print(f"[{'ok' if good else '--'}] {name} " + (detail if (not good or name.startswith("(optional) GPU")) else ""))
    line("manim", shutil.which("manim") or (pathlib.Path.home() / ".local/bin/manim").exists(), "(uv tool install manim)")
    line("ffmpeg/ffprobe", shutil.which("ffmpeg") and shutil.which("ffprobe"), "(apt install ffmpeg)")
    fc = sh("fc-list", capture_output=True, text=True).stdout if shutil.which("fc-list") else ""
    for f in ("Inter", "Vazirmatn"):
        line(f"font {f}", f in fc, "(run: rx.py fonts)")
    line("(optional) LaTeX for MathTex", shutil.which("latex"), "(apt install texlive-latex-extra; else use Text for formulas)")
    line("(optional) piper (free voice)", shutil.which("piper") or (pathlib.Path.home() / ".local/bin/piper").exists(), "(uv tool install piper-tts)")
    key = os.environ.get("OPENAI_API_KEY") or (pathlib.Path.home() / ".config/openai/key").exists()
    line("(optional) OpenAI key (paid voice/images)", key, "(~/.config/openai/key, chmod 600; contents not shown)")
    gpu = shutil.which("nvidia-smi") and sh("nvidia-smi --query-gpu=name --format=csv,noheader", capture_output=True, text=True).stdout.strip()
    line("(optional) GPU for experiments", gpu, gpu or "")
    promo_ok = shutil.which("node") and (SKILL / "promo" / "node_modules" / "playwright").exists()
    line("(optional) launch-video engine (node + Playwright)", promo_ok, f"(cd {SKILL / 'promo'} && npm install && npx playwright install chromium)")
    print("ready" if ok else "missing required tools above")
    return 0 if ok else 1


def cmd_fonts(a):
    import platform
    dest = pathlib.Path.home() / ("Library/Fonts" if platform.system() == "Darwin" else ".local/share/fonts/research-explainer")
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in (SKILL / "assets" / "fonts").iterdir():
        if f.suffix in (".ttf", ".otf"):
            shutil.copy2(f, dest / f.name); n += 1
    if shutil.which("fc-cache"):
        sh(["fc-cache", "-f"], capture_output=True)
    print(f"installed {n} font files into {dest}")


# ---------------- status ----------------
def cmd_status(a):
    """A compact outline: what exists, what is missing, and the next command."""
    if not CONF:
        print(f"no project here ({ROOT}). Next: rx.py new <dir> --title ... --langs en,fa --voice none"); return
    langs = CONF.get("languages", ["en"])
    print(f"project: {CONF.get('title')} | languages {','.join(langs)} | voice {CONF.get('voice', {}).get('mode', 'none')} | {ROOT}")
    cl = load_json(ROOT / "claims.json", {"claims": []})["claims"]
    man = load_json(ASSETS / "manifest.json", {"assets": []})["assets"]
    print(f"claims: {len(cl)} ({', '.join(sorted({c.get('status', '?') for c in cl}))}) | assets registered: {len(man)}")
    nxt = []
    if not (ROOT / "scenes.md").exists() or "(paper / papers / own work)" in (ROOT / "scenes.md").read_text():
        nxt.append("write scenes.md and get the user's approval")
    for lang in ([a.lang] if getattr(a, "lang", None) else langs):
        n = load_json(narration_file(lang))
        if not n:
            print(f"  {lang}: no narration_{lang}.json"); nxt.append(f"write narration_{lang}.json"); continue
        nb = {s["id"]: len(s["beats"]) for s in n["scenes"]}
        mode = CONF.get("voice", {}).get("mode", "none")
        row = []
        for s in CONF.get("scenes", []):
            v = scene_video(s, lang, mode, "m")
            row.append(f"{s['id']}({nb.get(s['id'], '?')} beats{', rendered' if v.exists() else ''})")
        print(f"  {lang}: " + " ".join(row))
        outs = sorted(p.name for p in BUILD.glob(f"*_{lang}_*.mp4") if not p.name.endswith("_share.mp4")) if BUILD.exists() else []
        print(f"  {lang} outputs: {', '.join(outs) or 'none yet'}")
        if not outs:
            nxt.append(f"rx.py claims && rx.py build {lang}")
    reqs = ROOT / "feature_requests.md"
    if reqs.exists():
        print(f"open feature requests: {reqs.read_text().count('## ')} (feature_requests.md)")
    print("next: " + ("; ".join(nxt) if nxt else "review build/qc contact sheets, then deliver"))


def cmd_request(a):
    """Record something the skill could not do, so the maintainers can add it."""
    f = ROOT / "feature_requests.md"
    when = sh(["date", "-Iseconds"], capture_output=True, text=True).stdout.strip()
    block = (f"## {a.wanted}\n- date: {when}\n- missing: {a.missing}\n- proposal: {a.proposal}\n"
             + (f"- example: {a.example}\n" if a.example else "") + "\n")
    with open(f, "a") as fh:
        fh.write(block)
    print(f"logged in {f}")
    print("To send it to the maintainers (only with the user's OK): open an issue at "
          "https://github.com/sepi2p/research-explainer-skill/issues/new?template=feature_request.md and paste the block.")


def cmd_selftest(a):
    """Build the bundled demo at low quality in a temporary copy, the way an agent would, and check every output."""
    import tempfile
    demo = SKILL.parent.parent / "examples" / "averaging-noise"
    if not demo.exists():
        sys.exit(f"demo not found at {demo} (selftest needs the full repository or plugin folder)")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rx_selftest_"))
    shutil.copytree(demo, tmp / "demo", ignore=shutil.ignore_patterns("build"))
    rx = [sys.executable, str(HERE / "rx.py")]
    env = dict(os.environ, EXPLAINER_PROJECT=str(tmp / "demo"))
    ok = True

    def step(name, args, expect=0, contains=None):
        nonlocal ok
        r = subprocess.run(rx + args, cwd=tmp / "demo", env=env, capture_output=True, text=True)
        out = r.stdout + r.stderr
        good = r.returncode == expect and (contains is None or contains in out)
        ok &= good
        print(f"[{'ok' if good else 'FAIL'}] {name}" + ("" if good else f"\n{out[-1500:]}"))
    step("claims pass", ["claims"])
    nar = tmp / "demo" / "narration_en.json"
    orig = nar.read_text()
    nar.write_text(orig.replace("0.125", "0.115", 1))
    step("claims catch a wrong number", ["claims"], expect=1, contains="0.115")
    nar.write_text(orig)
    step("assets verified", ["assets"])
    for lang in ("en", "fa"):
        step(f"build {lang} text-only (480p)", ["build", lang, "--voice", "none", "--quality", "l"], contains=".srt")
        step(f"no untranslated labels ({lang})", ["strings", lang], contains="no missing")
    b = tmp / "demo" / "build"
    for f in ("averaging_noise_en_text.mp4", "averaging_noise_fa_text.mp4", "averaging_noise_fa_text.srt"):
        good = (b / f).exists() and (b / f).stat().st_size > 1000
        ok &= good
        print(f"[{'ok' if good else 'FAIL'}] output {f}")
    print(("PASS" if ok else "FAIL") + f"  (work folder {tmp}; contact sheets in {b / 'qc'})")
    return 0 if ok else 1


# ---------------- new ----------------
def cmd_new(a):
    d = pathlib.Path(a.dir).resolve()
    if d.exists() and any(d.iterdir()):
        sys.exit(f"{d} exists and is not empty")
    shutil.copytree(SKILL / "templates" / "project", d, dirs_exist_ok=True)
    langs = a.langs.split(",")
    conf = json.loads((d / "project.json").read_text())
    conf.update({"title": a.title or d.name, "languages": langs})
    conf["voice"]["mode"] = a.voice
    (d / "project.json").write_text(json.dumps(conf, indent=2, ensure_ascii=False))
    if "fa" not in langs:
        for f in ("narration_fa.json", "strings_fa.json"):
            (d / f).unlink(missing_ok=True)
    print(f"new project in {d}. Next: fill sources/, claims.json, scenes.md, then the scenes and narration (see SKILL.md).")


# ---------------- claims ----------------
NUM = re.compile(r"[0-9۰-۹]+(?:[٬,][0-9۰-۹]{3})*(?:[٫.][0-9۰-۹]+)?")


def norm_num(s):
    return s.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).replace("٬", "").replace(",", "").replace("٫", ".")


def leaf_numbers(x, out):
    if isinstance(x, bool):
        return out
    if isinstance(x, (int, float)):
        out.append(float(x))
    elif isinstance(x, dict):
        for v in x.values():
            leaf_numbers(v, out)
    elif isinstance(x, list):
        for v in x:
            leaf_numbers(v, out)
    return out


def cmd_claims(a):
    cl = load_json(ROOT / "claims.json", {"claims": []})
    errors, warn = [], []
    allowed = set()
    for c in cl["claims"]:
        for k in ("id", "statement", "status", "source"):
            if not c.get(k):
                errors.append(f"claim {c.get('id', '?')}: missing '{k}'")
        if c.get("status") not in ("final", "reported", "development", "in progress", "planned", "illustration", "preliminary"):
            errors.append(f"claim {c.get('id')}: status '{c.get('status')}' is not one of final/reported/development/in progress/planned/illustration/preliminary")
        for v in c.get("values", []):
            allowed.add(norm_num(str(v)))
    ignore = {norm_num(str(v)) for v in cl.get("ignore_numbers", [])}
    measured = []
    for p in ASSETS.glob("*.json"):
        if p.name != "manifest.json":
            leaf_numbers(load_json(p), measured)

    def matches(tok):
        if tok in allowed or tok in ignore:
            return True
        dec = len(tok.split(".")[1]) if "." in tok else 0
        x = float(tok)
        for v in measured:
            for scale in (1, 100):
                if abs(round(v * scale, dec) - x) < 1e-9:
                    return True
        return False

    for lang in CONF.get("languages", ["en"]):
        n = load_json(narration_file(lang))
        if not n:
            continue
        for s in n["scenes"]:
            for i, b in enumerate(s["beats"]):
                for field in ("say", "caption", "text"):
                    for m in NUM.finditer(b.get(field, "")):
                        tok = norm_num(m.group(0))
                        if not matches(tok):
                            (warn if (tok.isdigit() and int(tok) <= 10) else errors).append(
                                f"{lang} {s['id']}:{i} {field}: {m.group(0)} has no claim or measured value")
    for e in errors:
        print("ERROR", e)
    for w in warn:
        print("check", w, "(small integer: fine if it is a count like 'three steps')")
    print(f"{len(cl['claims'])} claims; {len(errors)} errors, {len(warn)} to check")
    return 1 if errors else 0


# ---------------- assets ----------------
def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def cmd_asset_add(a):
    man = load_json(ASSETS / "manifest.json", {"assets": []})
    p = pathlib.Path(a.file).resolve()
    rel = str(p.relative_to(ASSETS.resolve()))
    commit = sh(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or None
    when = sh(["date", "-Iseconds"], capture_output=True, text=True).stdout.strip()
    rec = {"file": rel, "kind": a.kind, "made_by": a.by, "note": a.note, "sha256": sha(p), "date": when, "commit": commit}
    man["assets"] = [r for r in man["assets"] if r["file"] != rel] + [rec]
    (ASSETS / "manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print("registered", rel, a.kind)


def cmd_assets(a):
    man = {r["file"]: r for r in load_json(ASSETS / "manifest.json", {"assets": []})["assets"]}
    bad = 0
    for p in sorted(ASSETS.rglob("*")):
        if p.is_dir() or p.name == "manifest.json":
            continue
        rel = str(p.relative_to(ASSETS))
        r = man.get(rel)
        if not r:
            print("UNREGISTERED", rel); bad += 1
        elif r["sha256"] != sha(p):
            print("CHANGED since registered (re-run its script and asset-add again):", rel); bad += 1
    for rel in man:
        if not (ASSETS / rel).exists():
            print("MISSING", rel); bad += 1
    kinds = {}
    for r in man.values():
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"{len(man)} registered {kinds}; {bad} problems")
    return 1 if bad else 0


# ---------------- strings / script ----------------
def cmd_strings(a):
    p = BUILD / f"missing_strings_{a.lang}.txt"
    if not p.exists():
        print("no missing strings recorded (render first)"); return 0
    seen = sorted({json.loads(l) for l in p.read_text().splitlines() if l.strip()})
    for s in seen:
        print(json.dumps(s, ensure_ascii=False))
    print(f"{len(seen)} strings need an entry in strings_{a.lang}.json (or an L(..., {a.lang}=...) in the scene)")


def cmd_voice_script(a):
    from explainer.voice import say_text
    n = narration(a.lang)
    out = BUILD / f"voice_script_{a.lang}.txt"
    BUILD.mkdir(exist_ok=True)
    lines = []
    for s in n["scenes"]:
        for i, b in enumerate(s["beats"]):
            t = b.get("say", b.get("caption", ""))
            if t.strip():
                lines += [f"# {s['id']}_{i}.mp3", say_text(t, a.lang), ""]
    out.write_text("\n".join(lines))
    print(f"wrote {out}: record one file per block into voice/manual_{a.lang}/")


# ---------------- durations ----------------
def anim_lengths(lang):
    """Minimum length of each beat's animation, from the dry run (beats of ~0 s)."""
    d = BUILD / "timings" / f"{lang}_dry"
    out = {}
    for s in scenes_conf():
        f = d / f"{s['id']}.json"
        if not f.exists():
            sys.exit(f"no dry-run timings for {s['id']}: run  rx.py render {lang} --dry")
        t = json.loads(f.read_text())
        st = [b["start"] for b in t["beats"]] + [t["end"]]
        out[s["id"]] = [max(0.0, st[k + 1] - st[k] - t.get("pad", 0.25)) for k in range(len(t["beats"]))]
    return out


def cmd_durations(a, mode=None, dry=False):
    lang, mode = a.lang, mode or voice_mode(a)
    n = narration(lang)
    out = {"lang": lang, "mode": "dry" if dry else mode, "scenes": []}
    if dry:
        for s in n["scenes"]:
            out["scenes"].append({"id": s["id"], "beats": [{"dur": 0.01, "caption": b.get("text", b.get("caption", ""))} for b in s["beats"]]})
        f = dur_file(lang, "dry")
    elif mode == "none":
        anim = anim_lengths(lang)
        cps = CONF.get("reading_cps", {}).get(lang, CPS.get(lang, 14))
        for s in n["scenes"]:
            beats = []
            for i, b in enumerate(s["beats"]):
                cap = b.get("text", b.get("caption", ""))   # "text": an optional shorter caption for text-only videos
                # burned captions: long enough to read; otherwise the picture sets the pace (animation + a short hold)
                read = (len(cap) / cps + 1.5 if cap.strip() else 0) if CONF.get("captions", "srt") == "burn" else 0
                hold = b.get("hold", 0.8)
                beats.append({"dur": round(max(read, anim[s["id"]][i] + hold, b.get("min_dur", 0)), 2), "caption": cap})
            out["scenes"].append({"id": s["id"], "beats": beats})
        f = dur_file(lang, mode)
    else:
        from explainer.voice import narrate
        res = narrate(lang, mode, n["scenes"], only=a.only)
        for s in n["scenes"]:
            beats = []
            for i, b in enumerate(s["beats"]):
                r = res[(s["id"], i)]
                rec = {"dur": max(r["dur"], b.get("min_dur", 0)) if r else max(1.5, b.get("min_dur", 0)), "caption": b.get("caption", b.get("say", ""))}
                if r:
                    rec.update({"wav": r["wav"]} | ({"sim": r["sim"]} if "sim" in r else {}))
                beats.append(rec)
            out["scenes"].append({"id": s["id"], "beats": beats})
        low = [(s["id"], k, b["sim"]) for s in out["scenes"] for k, b in enumerate(s["beats"]) if b.get("sim", 1) < 0.92]
        if low:
            print("clips whose transcript differs from the text (listen to these):", low)
        f = dur_file(lang, mode)
    BUILD.mkdir(exist_ok=True)
    f.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    tot = sum(b["dur"] for s in out["scenes"] for b in s["beats"])
    print(f"wrote {f.name}: {sum(len(s['beats']) for s in out['scenes'])} beats, {tot / 60:.1f} min of beats")


# ---------------- render ----------------
def cmd_render(a, dry=False):
    lang = a.lang
    mode = "dry" if dry else voice_mode(a)
    if dry:
        cmd_durations(a, dry=True)
    df = dur_file(lang, mode)
    if not df.exists():
        cmd_durations(a)
    flags, _ = QUAL["l" if dry else a.quality]
    md = media_dir(lang, mode)
    env = dict(os.environ, EXPLAINER_PROJECT=str(ROOT), VIDEO_LANG=lang, DURATIONS=str(df), TIMINGS_TAG=f"{lang}_{mode}",
               PYTHONPATH=str(HERE) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    if lang != "en":
        (BUILD / f"missing_strings_{lang}.txt").unlink(missing_ok=True)
    todo = [s for s in scenes_conf() if not a.scenes or s["id"] in a.scenes]
    logs = BUILD / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    jobs = int(os.environ.get("JOBS", "4"))

    def launch(s):
        log = open(logs / f"{lang}_{mode}_{s['id']}.log", "w")
        return subprocess.Popen(f"{manim_bin()} {flags} --disable_caching --media_dir {md} {ROOT / s['file']} {s['class']}",
                                shell=True, env=env, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)

    running, failed = [], []
    queue = list(todo)
    import time
    while queue or running:
        while queue and len(running) < jobs:
            s = queue.pop(0)
            running.append((s, launch(s)))
        time.sleep(0.5)
        for s, p in list(running):
            if p.poll() is not None:
                running.remove((s, p))
                if p.returncode:
                    failed.append(s)
    # parallel renders share the text cache and sometimes race: drop empty cache files and rerun failures one at a time
    for f in (md / "texts").glob("*") if (md / "texts").exists() else []:
        if f.stat().st_size == 0:
            f.unlink()
    still = []
    for s in failed:
        if launch(s).wait():
            still.append(s["id"])
    for s in todo:
        print(s["id"], "FAILED, see " + str(logs / f"{lang}_{mode}_{s['id']}.log") if s["id"] in still else "ok")
    if lang != "en" and (BUILD / f"missing_strings_{lang}.txt").exists():
        print(f"some on-screen strings have no {lang} translation: rx.py strings {lang}")
    if still:
        sys.exit(1)
    if dry:
        anim = anim_lengths(lang)
        print(f"dry run: animations need at least {sum(map(sum, anim.values())) / 60:.1f} min")


def scene_video(s, lang, mode, quality):
    return media_dir(lang, mode) / "videos" / pathlib.Path(s["file"]).stem / QUAL[quality][1] / f"{s['class']}.mp4"


# ---------------- assemble ----------------
def probe(p, what):
    return subprocess.check_output(["ffprobe", "-v", "error"] + what + ["-of", "csv=p=0", str(p)]).decode().strip()


def cmd_assemble(a):
    lang, mode = a.lang, voice_mode(a)
    silent = mode == "none"
    sc = scenes_conf()
    vids = [scene_video(s, lang, mode, a.quality) for s in sc]
    miss = [v.name for v in vids if not v.exists()]
    assert not miss, f"missing renders {miss}: rx.py render {lang} --voice {mode} --quality {a.quality}"
    work = BUILD / "work"
    work.mkdir(parents=True, exist_ok=True)
    fixed = []
    for s, v in zip(sc, vids):   # every piece needs an audio track for the concat
        if not probe(v, ["-select_streams", "a", "-show_entries", "stream=index"]):
            sv = work / f"{lang}_{mode}_{s['id']}_a.mp4"
            sh(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                "-c:v", "copy", "-c:a", "aac", str(sv)], check=True)
            v = sv
        fixed.append(v)
    lens = [float(probe(v, ["-show_entries", "format=duration"])) for v in fixed]
    total = sum(lens)
    lst = work / f"concat_{lang}_{mode}.txt"
    lst.write_text("".join(f"file '{v}'\n" for v in fixed))
    concat = work / f"concat_{lang}_{mode}.mp4"
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2", str(concat)], check=True)
    premix = work / f"premix_{lang}_{mode}.wav"
    target = -20 if silent else -16
    if a.no_music:
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(concat), "-vn", "-ar", "48000", str(premix)], check=True)
    else:
        music = work / "music_bed.wav"
        sh([manim_python(), str(HERE / "explainer" / "music.py"), str(total + 1.0), str(music)], check=True, capture_output=True)
        if silent:
            fc = "[0:a]volume=0.5[a]"
            sh(["ffmpeg", "-v", "error", "-y", "-i", str(music), "-filter_complex", fc, "-map", "[a]", "-t", f"{total:.3f}", "-ar", "48000", str(premix)], check=True)
        else:
            meas = sh(["ffmpeg", "-nostats", "-i", str(concat), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
            gain = -18.0 - float(re.findall(r"I:\s+(-?[\d.]+) LUFS", meas)[-1])
            fc = (f"[0:a]volume={gain:.2f}dB,acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=3dB[v];"
                  "[1:a]volume=0.22,apad[m];[v][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]")
            sh(["ffmpeg", "-v", "error", "-y", "-i", str(concat), "-i", str(music), "-filter_complex", fc, "-map", "[a]", "-ar", "48000", str(premix)], check=True)
    m = sh(["ffmpeg", "-nostats", "-i", str(premix), "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
           capture_output=True, text=True).stderr
    mj = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={mj['input_i']}:measured_TP={mj['input_tp']}:measured_LRA={mj['input_lra']}:"
          f"measured_thresh={mj['input_thresh']}:offset={mj['target_offset']}:linear=true")
    name = f"{slug()}_{lang}_{'text' if silent else mode}"
    out = BUILD / f"{name}.mp4"
    if a.no_music and silent:
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(concat), "-map", "0:v", "-c:v", "copy", "-an", "-movflags", "+faststart", str(out)], check=True)
    else:
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(concat), "-i", str(premix), "-af", ln, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)], check=True)
    share = BUILD / f"{name}_share.mp4"
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:v", "libx264", "-crf", "30", "-preset", "slow", "-c:a", "aac", "-b:a", "96k",
        "-movflags", "+faststart", str(share)], check=True)
    write_srt(lang, mode, sc, lens, BUILD / f"{name}.srt")
    mb = lambda p: p.stat().st_size / 1e6
    print(f"{out.name}: {int(total // 60)}:{total % 60:04.1f}, {mb(out):.1f} MB; {share.name}: {mb(share):.1f} MB (for messaging); {name}.srt")


def write_srt(lang, mode, sc, lens, path):
    d = {s["id"]: s for s in load_json(dur_file(lang, mode))["scenes"]}
    tim = BUILD / "timings" / f"{lang}_{mode}"

    def ts(x):
        return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}".replace(".", ",")
    lines, n, off = [], 1, 0.0
    for s, L in zip(sc, lens):
        rec = load_json(tim / f"{s['id']}.json")
        pad = rec.get("pad", 0.25) if rec else 0.25
        beats = d[s["id"]]["beats"]
        for j, b in enumerate(beats):
            t0 = off + (rec["beats"][j]["start"] if rec else 0)
            t1 = off + (rec["beats"][j + 1]["start"] if rec and j + 1 < len(beats) else min(t0 - off + b["dur"] + pad, L))
            chunks = split_caption(b.get("caption", ""))
            if not chunks[0]:
                continue
            starts = chunk_times(chunks, b["dur"])
            for k, c in enumerate(chunks):
                a0 = t0 + starts[k]
                e = t0 + starts[k + 1] if k + 1 < len(chunks) else t1
                lines += [str(n), f"{ts(a0)} --> {ts(e)}", c, ""]
                n += 1
        off += L
    path.write_text("\n".join(lines))


# ---------------- qc ----------------
def cmd_qc(a):
    lang, mode = a.lang, voice_mode(a)
    out = BUILD / "qc" / f"{lang}_{mode}"
    out.mkdir(parents=True, exist_ok=True)
    for s in scenes_conf():
        v = scene_video(s, lang, mode, a.quality)
        if not v.exists():
            print("not rendered:", s["id"]); continue
        d = float(probe(v, ["-show_entries", "format=duration"]))
        n = a.frames
        tmp = out / "tmp"
        tmp.mkdir(exist_ok=True)
        for f in tmp.glob("*.png"):
            f.unlink()
        for i in range(n):
            sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{d * (i + 0.5) / n:.2f}", "-i", str(v), "-frames:v", "1", str(tmp / f"{i:02d}.png")], check=True)
        sh(["ffmpeg", "-v", "error", "-y", "-pattern_type", "glob", "-i", str(tmp / "*.png"), "-filter_complex",
            f"scale=640:-1,tile=3x{(n + 2) // 3}:padding=6:color=white", str(out / f"{s['id']}.png")], check=True)
        print(f"{s['id']}: {d:.1f}s -> {out / (s['id'] + '.png')}")


# ---------------- build ----------------
def cmd_promo(a):
    """Render an HTML motion-graphics page frame by frame (promo/render.mjs, headless Chromium), mix music + sound effects
    from promo.json, bake the poster as frame 0. See references/promo.md."""
    d = (ROOT / a.dir).resolve()
    conf = load_json(d / "promo.json", None)
    if conf is None:
        die(f"no {d}/promo.json", "copy templates/promo/ into the project (see references/promo.md)")
    eng = SKILL / "promo"
    if not shutil.which("node"):
        die("node is not installed", "install Node.js 18+ (https://nodejs.org), then: cd " + str(eng) + " && npm install")
    if not (eng / "node_modules" / "playwright").exists():
        die("the promo engine needs Playwright", f"cd {eng} && npm install && npx playwright install chromium")
    page = d / conf.get("page", "index.html")
    dur, fps = float(conf["duration"]), int(conf.get("fps", 30))
    W, H = int(conf.get("width", 1280)), int(conf.get("height", 720))
    work = d / "work"
    work.mkdir(exist_ok=True)
    q = ["--query", f"?lang={a.lang}"] if a.lang else []
    suf = f"_{a.lang}" if a.lang else ""
    base = ["node", str(eng / "render.mjs"), str(page)]
    if a.stills:
        sh(base + ["-"] + q + ["--stills", a.stills, "--stills-dir", str(work / f"stills{suf}"), "--width", str(W), "--height", str(H)], check=True, cwd=d)
        print("stills in", work / f"stills{suf}")
        return
    silent = work / f"video{suf}.mp4"
    sh(base + [str(silent)] + q + ["--duration", str(dur), "--fps", str(fps), "--width", str(W), "--height", str(H)], check=True, cwd=d)
    # audio: music from an offset, sound-effect cues at their times, then loudness to -14 LUFS (typical for social video)
    ins, parts = [], []
    m = conf.get("music")
    if m and not a.no_music:
        mf = pathlib.Path(m["file"]).expanduser()
        if not mf.is_absolute():
            mf = d / mf
        if not mf.exists():
            die(f"music file not found: {mf}", "set music.file in promo.json to a track you may use (see references/promo.md)")
        ins += ["-ss", str(m.get("start", 0)), "-i", str(mf)]
        fo = float(m.get("fade_out", 1.5))
        parts.append(f"[{len(parts)}:a]atrim=0:{dur},asetpts=N/SR/TB,afade=t=out:st={dur - fo}:d={fo},volume={m.get('gain_db', 0)}dB[a{len(parts)}]")
    for c in conf.get("sfx", []):
        f = pathlib.Path(c["file"]) if "/" in c["file"] else SKILL / "assets" / "sfx" / (c["file"] + ".ogg")
        if not f.is_absolute():
            f = d / f
        if not f.exists():
            die(f"sound effect not found: {f}", "use a name from assets/sfx/README.md or a path to your own file")
        k = len(parts)
        ms = int(float(c["t"]) * 1000)
        ins += ["-i", str(f)]
        parts.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms},volume={c.get('gain_db', -10)}dB[a{k}]")
    out = d / f"promo{suf}.mp4"
    poster_t = float(conf.get("poster", dur - 1.5))
    poster = d / f"promo{suf}.jpg"
    sh(["ffmpeg", "-v", "error", "-y", "-ss", str(poster_t), "-i", str(silent), "-frames:v", "1", "-q:v", "2", str(poster)], check=True)
    vf = "[0:v][1:v]overlay=enable='eq(n,0)'[v]"   # poster as frame 0 (the thumbnail), same length
    if parts:
        n = len(parts)
        mix = ";".join(p_.replace(f"[{i}:a]", f"[{i + 2}:a]") for i, p_ in enumerate(parts))
        mix += ";" + "".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:duration=longest:normalize=0,atrim=0:{dur},alimiter=limit=0.9," \
               "loudnorm=I=-14:TP=-1.5:LRA=9[a]"
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(poster)] + ins +
           ["-filter_complex", vf + ";" + mix, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", str(dur), str(out)], check=True)
    else:
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(poster), "-filter_complex", vf, "-map", "[v]",
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)
    print(f"{out.name}: {dur:.1f}s, {out.stat().st_size / 1e6:.1f} MB; poster {poster.name} (t={poster_t}s)")


def cmd_build(a):
    if voice_mode(a) == "none":
        cmd_render(a, dry=True)
    cmd_durations(a)
    cmd_render(a)
    cmd_assemble(a)
    cmd_qc(a)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check"); sub.add_parser("fonts"); sub.add_parser("selftest")
    p = sub.add_parser("status"); p.add_argument("lang", nargs="?")
    p = sub.add_parser("request"); p.add_argument("wanted"); p.add_argument("--missing", required=True)
    p.add_argument("--proposal", required=True); p.add_argument("--example", default="")
    p = sub.add_parser("new"); p.add_argument("dir"); p.add_argument("--title"); p.add_argument("--langs", default="en")
    p.add_argument("--voice", default="none", choices=["none", "piper", "manual", "openai"])
    sub.add_parser("claims"); sub.add_parser("assets")
    p = sub.add_parser("promo"); p.add_argument("dir", nargs="?", default="promo"); p.add_argument("--stills", default="")
    p.add_argument("--lang", default="", help="passed to the page as ?lang=..; outputs promo_<lang>.mp4")
    p.add_argument("--no-music", action="store_true")
    p = sub.add_parser("asset-add"); p.add_argument("file"); p.add_argument("--kind", required=True, choices=["measured", "reported", "illustration", "generated"])
    p.add_argument("--by", required=True); p.add_argument("--note", default="")
    for name in ("strings", "voice-script", "durations", "render", "assemble", "qc", "build"):
        p = sub.add_parser(name); p.add_argument("lang")
        p.add_argument("--voice", choices=["none", "piper", "manual", "openai"])
        p.add_argument("--quality", default="m", choices=list(QUAL))
        p.add_argument("--scenes", nargs="*"); p.add_argument("--dry", action="store_true"); p.add_argument("--no-music", action="store_true")
        p.add_argument("--only", nargs="*", help="durations: force these beats (scene:i) to be voiced again")
        p.add_argument("--frames", type=int, default=9)
    a = ap.parse_args()
    fn = {"check": cmd_check, "fonts": cmd_fonts, "status": cmd_status, "request": cmd_request, "selftest": cmd_selftest, "new": cmd_new, "claims": cmd_claims, "promo": cmd_promo, "assets": cmd_assets, "asset-add": cmd_asset_add,
          "strings": cmd_strings, "voice-script": cmd_voice_script, "durations": cmd_durations, "assemble": cmd_assemble,
          "qc": cmd_qc, "build": cmd_build}.get(a.cmd)
    if a.cmd == "render":
        return cmd_render(a, dry=a.dry)
    return fn(a)


if __name__ == "__main__":
    sys.exit(main() or 0)
