"""Building blocks for research explainer scenes (Manim Community Edition).

A scene subclasses Beat, sets SCENE_ID to a scene id in narration_<lang>.json, and calls self.beat(i, fn) once per narration
beat in order. Each beat plays its voice clip (if any), shows its caption in timed chunks in a strip under the picture, runs
fn (the animation), then waits until the beat's length is used up. Text goes through T(), which handles Persian: right-to-left
order, Persian digits, Vazirmatn, and Latin runs (names, formulas) kept in Inter.
"""
import json, os, re, textwrap
import numpy as np
from manim import *  # noqa: F401,F403

from .project import ROOT, CONF, BUILD, ASSETS, LANG, RTL, durations, load_json
from .captions import split_caption, chunk_times

# ---------- look ----------
_P = {"bg": "#0e0f12", "panel": "#1a1c22", "text": "#e9e9e9", "dim": "#6b7079", "grey": "#b8bcc4",
      "accent": "#ffd166", "a": "#58c4dd", "b": "#fc6255", "c": "#83c167", "d": "#d291ff", "e": "#4fd1c5"}
_P.update(CONF.get("palette", {}))
BG, PANEL, TEXT, DIM, GREY_ = _P["bg"], _P["panel"], _P["text"], _P["dim"], _P["grey"]
ACCENT, BLUE_, RED_, GREEN_, PURPLE, TEAL = _P["accent"], _P["a"], _P["b"], _P["c"], _P["d"], _P["e"]
AMBER = ACCENT
LATIN_FONT = CONF.get("latin_font", "Inter")
RTL_FONT = CONF.get("rtl_font", "Vazirmatn")
config.background_color = BG

CAPTIONS = CONF.get("captions", "srt")   # "srt": subtitles only as a separate .srt, the whole frame is picture (default)
                                         # "burn": a caption strip under the picture, captions burned into the video
CAP_STRIP = 1.25 if CAPTIONS == "burn" else 0.0   # caption strip height (frame units)
FRAME_H = 8 + CAP_STRIP
START = RIGHT if RTL else LEFT   # text groups align to the reading start

# ---------- language ----------
_STR = load_json(ROOT / f"strings_{LANG}.json", {"exact": {}, "patterns": []}) if LANG != "en" else {"exact": {}, "patterns": []}
_KEEP = set(CONF.get("keep_latin", []))
_SYMBOLS = re.compile(r"^[\s\d−\-+=×÷→←.,:;%()/·…<>≤≥≈±^_|*'\"\[\]{}]+$")
_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_MISSING = BUILD / f"missing_strings_{LANG}.txt"


def L(en, **other):
    """Inline translation: L("Queries", fa="پرسش‌ها"). Falls back to strings_<lang>.json, then to English (logged)."""
    return other.get(LANG, en)


def fa_digits(s):
    """Persian digits, decimal point, thousands separator and percent sign (only next to digits)."""
    s = re.sub(r"(?<=\d)\.(?=\d)", "٫", s)
    s = re.sub(r"(?<=\d),(?=\d{3})", "٬", s)
    s = re.sub(r"(?<=\d)%", "٪", s)
    return s.translate(_FA_DIGITS)


def tr(s):
    """The on-screen form of a string in the render language (English unchanged)."""
    if LANG == "en" or not s.strip() or re.search(r"[֐-ۿ]", s):
        return s
    if s in _STR.get("exact", {}):
        return _STR["exact"][s]
    for pat, rep in _STR.get("patterns", []):
        m = re.fullmatch(pat, s)
        if m:
            return rep.format(*[fa_digits(g) if (g is not None and LANG == "fa") else (g or "") for g in m.groups()])
    if not re.search(r"[A-Za-z]", s) or s in _KEEP or _SYMBOLS.match(s):
        return fa_digits(s) if LANG == "fa" else s
    _MISSING.parent.mkdir(parents=True, exist_ok=True)
    with open(_MISSING, "a") as f:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
    return s


# letters of right-to-left scripts (Hebrew, Arabic, Persian), not counting the Arabic-Indic digits and number signs
RTL_LETTERS = re.compile("[\u0590-\u05ff\u0620-\u065f\u066e-\u06ef\u06fa-\u06ff\ufb50-\ufdff\ufe70-\ufeff]")


_LAT = "A-Za-z\u0370-\u03ff∞√∑∏∫∂∇"            # Latin and Greek letters, math operators that start a run
_MID = _LAT + "0-9_+\\-./−×÷=·,()\\[\\]^<>≤≥≈±→←|' \u0303"
_OPS = "=<>≤≥≈±×÷+\\-−/·"
_FA_NUM = "\u06f0-\u06f9\u0660-\u0669\u066b\u066c"
# a Latin/math run, plus "= ۶۴"-style tails (operator, then Persian digits), so "n = ۶۴" stays one left-to-right run;
# Persian digits after a plain word ("ResNet ۱۸") stay on the Persian side
LATIN_RUN = re.compile(f"[{_LAT}](?:[{_MID}]*[{_LAT}0-9+)\\]\u0303])?(?:\\s*[{_OPS}]\\s*[0-9{_FA_NUM}]+)*")


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(s, size=30, color=TEXT, weight=NORMAL, max_w=15.4, **kw):
    """Text in the render language. Persian/Arabic goes through Pango markup with direction marks so mixed runs order right."""
    s = tr(str(s))
    if RTL_LETTERS.search(s):
        # each Latin/math run (names, formulas) is isolated (LRI ... PDI) and set in the Latin font, so it reads left to right
        # and nearby punctuation stays on the RTL side. Runs are found on the raw text, then each piece is escaped.
        parts, last = [], 0
        for m_ in LATIN_RUN.finditer(s):
            run, end = m_.group(0), m_.end()
            while run.endswith(")") and run.count(")") > run.count("("):   # "(RMSE)": the closing bracket belongs outside
                run, end = run[:-1], end - 1
            parts.append(_esc(s[last:m_.start()]))
            parts.append(f'\u2066<span font_family="{LATIN_FONT}">{_esc(run)}</span>\u2069')
            last = end
        parts.append(_esc(s[last:]))
        esc = "".join(parts)
        kw.pop("line_spacing", None)
        m = MarkupText("‏" + esc.replace("\n", "\n‏"), font=RTL_FONT, font_size=size * 0.95, color=color, weight=weight, **kw)
    else:   # English, or a formula/number with no RTL letters ("n = ۴"): left to right; Persian digits need the RTL font
        font = RTL_FONT if re.search("[\u0660-\u066c\u06f0-\u06f9]", s) else LATIN_FONT
        m = Text(s, font=font, font_size=size * (0.95 if font == RTL_FONT else 1), color=color, weight=weight, **kw)
    if max_w and m.width > max_w:
        m.scale_to_fit_width(max_w)
    return m


def wrap(s, width=84):
    return "\n".join(textwrap.wrap(s, width=width))


def tlines(lines, size=26, color=TEXT, buff=0.18, **kw):
    """Several lines aligned to the reading start (left for English, right for Persian)."""
    g = VGroup(*[T(l, size, color, **kw) if isinstance(l, str) else l for l in lines])
    return g.arrange(DOWN, buff=buff, aligned_edge=START)


# ---------- assets (real data only: see references/experiments.md) ----------
def asset(name):
    p = ASSETS / name
    if not p.suffix:
        p = p.with_suffix(".png")
    assert p.exists(), f"missing asset {p} (generate it with an experiment script and register it in assets/manifest.json)"
    return p


def img(name, h=None, w=None, nearest=False):
    """An image from assets/. nearest=True keeps pixels sharp (small images, perturbation maps)."""
    m = ImageMobject(str(asset(name)))
    if nearest:
        m.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
    if h: m.scale_to_fit_height(h)
    if w: m.scale_to_fit_width(w)
    return m


def framed(name, h=2.0, color=GREY_, sw=2, nearest=False):
    m = img(name, h, nearest=nearest)
    return Group(m, SurroundingRectangle(m, buff=0.0, color=color, stroke_width=sw))


def data(name="data.json"):
    """Numbers measured by the experiment scripts (assets/data.json by default). Scenes read numbers from here, never type them."""
    return json.loads(asset(name).read_text())


# ---------- widgets ----------
def pill(text, color, size=24, fg=BG):
    t = T(text, size, fg, weight=BOLD)
    bg = RoundedRectangle(corner_radius=min(0.25, (t.height + 0.3) / 2), width=t.width + 0.45, height=t.height + 0.3,
                          color=color, fill_opacity=1, stroke_width=0)
    return VGroup(bg, t.move_to(bg))


STATUS_COLORS = {"final": GREEN_, "reported": GREY_, "development": ACCENT, "in progress": ACCENT, "planned": GREY_,
                 "illustration": PURPLE, "preliminary": ACCENT}


def tag(status, size=17):
    """A status label on a number: final / development / in progress / planned / reported (from a paper) / illustration."""
    key = next((k for k in STATUS_COLORS if status.lower().startswith(k)), None)
    col = STATUS_COLORS.get(key, GREY_)
    t = T(status, size, col)
    box = RoundedRectangle(corner_radius=0.12, width=t.width + 0.3, height=t.height + 0.2, stroke_color=col, stroke_width=1.5, fill_opacity=0)
    return VGroup(box, t.move_to(box))


def note(s, size=18, color=DIM):
    return T(s, size, color)


def source_note(s, size=16):
    """Small source line, e.g. "Smith et al. 2024, Table 3" or "our run, experiments/noise.py, seed 0"."""
    return T(s, size, DIM).to_corner(DR if not RTL else DL, buff=0.25).shift(UP * 0.05)


def panel(w, h, color=GREY_, title=None, tsize=22):
    box = RoundedRectangle(corner_radius=0.18, width=w, height=h, stroke_color=color, stroke_width=2, fill_color=PANEL, fill_opacity=0.9)
    g = VGroup(box)
    if title:
        g.add(T(title, tsize, color, weight=BOLD).move_to(box.get_top() + DOWN * 0.35))
    return g


def bar_chart(labels, values, w=6.0, row=0.42, color=BLUE_, hi=None, hi_color=ACCENT, size=20, vmax=None, fmt="{:.1f}", suffix=""):
    """Horizontal bars with labels and printed values. Values come from data(); fmt controls the printed number."""
    vmax = vmax or max(values) or 1
    rows = VGroup()
    for k, (lab, v) in enumerate(zip(labels, values)):
        c = hi_color if k == hi else color
        bg = Rectangle(width=w, height=row * 0.7, stroke_width=0, fill_color="#26292f", fill_opacity=1)
        bar = Rectangle(width=max(w * v / vmax, 0.001), height=row * 0.7, stroke_width=0, fill_color=c, fill_opacity=1)
        bar.move_to(bg, aligned_edge=RIGHT if RTL else LEFT)
        val = T(fmt.format(v) + suffix, size, c)
        name = T(lab, size, GREY_ if k != hi else TEXT)
        parts = [name, VGroup(bg, bar), val]
        r = VGroup(*(reversed(parts) if RTL else parts)).arrange(RIGHT, buff=0.2)
        rows.add(r)
    rows.arrange(DOWN, buff=row * 0.3, aligned_edge=RIGHT if RTL else LEFT)
    # line the bars up in one column
    xs = [r[1].get_left()[0] if not RTL else r[1].get_right()[0] for r in rows]
    for r, x in zip(rows, xs):
        edge = r[1].get_left()[0] if not RTL else r[1].get_right()[0]
        r[1].shift(RIGHT * ((max(xs) if not RTL else min(xs)) - edge))   # bars start after the longest label
        (r[0] if RTL else r[2]).next_to(r[1], RIGHT if not RTL else LEFT, buff=0.2)   # the value sits at the bar's end
    return rows


def curve(ax, ys, color, sw=3, xs=None):
    xs = xs if xs is not None else np.arange(1, len(ys) + 1)
    return VMobject(stroke_color=color, stroke_width=sw).set_points_as_corners([ax.c2p(x, y) for x, y in zip(xs, ys)])


def amplified(diff, gain=None):
    """Make an invisible difference visible: a signed difference image (H, W[, 3], any scale) -> uint8 RGB with 0 at mid-grey.
    Returns (array, gain). Always print the gain on screen (e.g. "difference ×40")."""
    d = np.asarray(diff, dtype=float)
    if gain is None:
        gain = 0.5 / max(np.abs(d).max(), 1e-12)
    a = np.clip(0.5 + d * gain, 0, 1)
    if a.ndim == 2:
        a = np.stack([a] * 3, -1)
    return (a * 255).astype(np.uint8), gain


def array_img(a, h=2.0, nearest=True):
    """An ImageMobject from a numpy array (uint8 or 0-1 floats)."""
    a = np.asarray(a)
    if a.dtype != np.uint8:
        a = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    m = ImageMobject(a)
    if nearest:
        m.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
    return m.scale_to_fit_height(h)


def steps_tracker(names, active):
    """A row of numbered steps in the top corner; `active` (1-based) is highlighted."""
    items = VGroup()
    for k, n in enumerate(names, 1):
        col = ACCENT if k == active else (GREY_ if k < active else DIM)
        dot = Circle(radius=0.16, stroke_color=col, stroke_width=2, fill_color=col if k <= active else BG, fill_opacity=1)
        num = T(str(k), 17, BG if k <= active else DIM, weight=BOLD).move_to(dot)
        parts = [VGroup(dot, num), T(n, 21, col, weight=BOLD if k == active else NORMAL)]
        items.add(VGroup(*(reversed(parts) if RTL else parts)).arrange(RIGHT, buff=0.12))
    if RTL:
        items = VGroup(*reversed(items))
    return items.arrange(RIGHT, buff=0.35).to_corner(UL if RTL else UR, buff=0.3)


# ---------- motion vocabulary (visual storytelling: the motion is the explanation) ----------
def ticker(tracker, fmt="{:.3f}", size=36, color=TEXT, place=None, **kw):
    """A number that follows a ValueTracker while it animates (an error counting down, a count going up).
    place: function that positions the new text each frame, e.g. lambda m: m.next_to(dot, UP)."""
    def make():
        m = T(fmt.format(tracker.get_value()), size, color, **kw)
        return place(m) if place else m
    return always_redraw(make)


def fan(mobs, dx=0.16, dy=-0.12):
    """Lay objects as a fanned stack (each shifted a little), so the viewer sees there are many of them."""
    base = mobs[0].get_center()
    for k, m in enumerate(mobs):
        m.move_to(base + k * np.array([dx, dy, 0])).set_z_index(k)
    return Group(*mobs)


def gather(mobs, target, run_time=1.6, lag=0.06):
    """Many objects fly into one place and become `target` (n copies -> their average). Returns an animation."""
    c = target.get_center()
    flights = [FadeOut(m, target_position=c, scale=max(target.height / max(m.height, 1e-6), 0.2)) for m in mobs]
    return Succession(LaggedStart(*flights, lag_ratio=lag), FadeIn(target, scale=1.08), run_time=run_time)


def collapse_to(m, point, color=ACCENT, radius=0.09):
    """An image or group collapses into a data point (an averaged image becomes its error on a chart).
    Returns (dot, animation); add the dot to later groups."""
    d = Dot(point, radius=radius, color=color)
    return d, Succession(FadeOut(m, target_position=point, scale=0.04), GrowFromCenter(d))


def value_axis(x0, x1, lo, hi, y=0.0, color=DIM):
    """A plain horizontal value line. Returns (line, f) with f(value) -> point."""
    line = Line([x0, y, 0], [x1, y, 0], color=color, stroke_width=2)
    return line, (lambda v: np.array([x0 + (v - lo) / (hi - lo) * (x1 - x0), y, 0]))


def dot_plot(values, f, color=BLUE_, r=0.055, rise=0.0):
    """One dot per value on a value_axis mapping f; rise lifts dots that share a position into a little column."""
    dots = VGroup()
    for v in values:
        p = f(v)
        dots.add(Dot(p + UP * rise, radius=r, color=color))
    return dots


def particles(n, center=ORIGIN, spread=1.0, seed=0, color=GREY_, r=0.03, opacity=0.8):
    """Seeded cloud of dots (noise, samples, a population). Same seed, same cloud."""
    g = np.random.default_rng(seed)
    pts = g.normal(0, spread, (n, 2))
    return VGroup(*[Dot(np.array(center) + [x, y, 0], radius=r, color=color, fill_opacity=opacity) for x, y in pts])


def push_in(scene, target, zoom=2.0):
    """Camera moves in on a region (a pixel, a detail of a chart). Undo with pull_out. Returns an animation."""
    return scene.camera.frame.animate.move_to(target.get_center() if hasattr(target, "get_center") else target).set(height=FRAME_H / zoom)


def pull_out(scene):
    return scene.camera.frame.animate.move_to(DOWN * CAP_STRIP / 2).set(height=FRAME_H)


def spotlight(mob, others, dim=0.75, color=ACCENT):
    """Dim everything else and ring the thing that matters now. Returns an animation."""
    return AnimationGroup(*[o.animate.fade(dim) for o in others], Circumscribe(mob, color=color, buff=0.08))


# ---------- the beat-synced scene ----------
_DUR = None


class Beat(MovingCameraScene):
    SCENE_ID = None
    PAD = 0.25          # silence after each beat's clip
    STEPS = None        # (names, active) for a steps_tracker in the corner

    def setup(self):
        global _DUR
        _DUR = _DUR or durations()
        assert self.SCENE_ID in _DUR, f"{self.SCENE_ID} is not in the narration ({sorted(_DUR)})"
        self.spec = _DUR[self.SCENE_ID]["beats"]
        self.cap = None
        self.camera.frame.set(height=FRAME_H).move_to(DOWN * CAP_STRIP / 2)
        self.strip = (Rectangle(width=FRAME_H * 16 / 9 + 0.1, height=CAP_STRIP + 0.05, fill_color="#07080a", fill_opacity=1,
                                stroke_width=0).move_to(DOWN * (4 + CAP_STRIP / 2)).set_z_index(40) if CAP_STRIP else VGroup())
        self.add(self.strip)
        self.keep = [self.strip]
        if self.STEPS:
            self.tracker = steps_tracker(*self.STEPS)
            self.add(self.tracker)
            self.keep.append(self.tracker)

    def caption_mob(self, text):
        width = 84 if not RTL else 90
        lines = len(textwrap.wrap(text, width))
        if lines > 1:   # balance the lines, so no single word sits alone on the second line
            width = min(width, -(-len(text) // lines) + 8)
        t = T(wrap(text, width), 30, TEXT, line_spacing=0.85, max_w=None)
        if t.width > 14.2:
            t.scale_to_fit_width(14.2)
        if t.height > CAP_STRIP - 0.25:
            t.scale_to_fit_height(CAP_STRIP - 0.25)
        return t.move_to(DOWN * (4 + CAP_STRIP / 2))

    def beat(self, i, fn=None, pad=None):
        """Play beat i: its sound, its caption in timed chunks, and the animation fn (which may call self.play many times)."""
        b = self.spec[i]
        start = self.time
        self.__dict__.setdefault("timings", []).append({"beat": i, "start": start, "audio": b["dur"]})
        if b.get("wav"):
            self.add_sound(b["wav"])
        chunks = split_caption(b.get("caption", "")) if CAPTIONS == "burn" else [""]
        times = chunk_times(chunks, b["dur"])
        if self.cap is not None:
            self.remove(self.cap)
        self.cap = VGroup(self.caption_mob(chunks[0]) if chunks[0] else VMobject()).set_z_index(50)
        self.add(self.cap)
        if len(chunks) > 1:
            state = {"t": 0.0, "k": 0}

            def upd(m, dt):
                state["t"] += dt
                k = state["k"]
                while k + 1 < len(chunks) and state["t"] >= times[k + 1]:
                    k += 1
                if k != state["k"]:
                    state["k"] = k
                    m.become(VGroup(self.caption_mob(chunks[k])).set_z_index(50))
            self.cap.add_updater(upd)
        if fn:
            fn()
        rest = b["dur"] + (self.PAD if pad is None else pad) - (self.time - start)
        if rest > 0:
            self.wait(rest)
        self.cap.clear_updaters()

    def tear_down(self):
        """Check every beat was played once, in order, and record the start times (for the .srt and the reading-time plan)."""
        played = [t["beat"] for t in self.__dict__.get("timings", [])]
        assert played == list(range(len(self.spec))), f"{self.SCENE_ID}: beats played {played}, narration has {len(self.spec)}"
        d = BUILD / "timings" / os.environ.get("TIMINGS_TAG", "default")
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{self.SCENE_ID}.json").write_text(json.dumps({"beats": self.timings, "end": self.time, "pad": self.PAD}))

    def clear_stage(self, run_time=0.5, keep=()):
        ms = [m for m in self.mobjects if m not in self.keep and m is not self.cap and m not in keep]
        if ms:
            self.play(*[FadeOut(m) for m in ms], run_time=run_time)

    def outro(self):
        if self.cap is not None:
            self.remove(self.cap)
        ms = [m for m in self.mobjects if m is not self.strip]
        if ms:
            self.play(*[FadeOut(m) for m in ms], run_time=0.5)
        self.wait(0.15)
