"""Demo scenes. Every number on screen comes from assets/data.json (written by experiments/averaging.py)."""
from explainer.base import *

D = data()
NS = D["ns"]


def fmt(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") if v < 0.1 else f"{v:.3f}".rstrip("0").rstrip(".")


class S00Title(Beat):
    SCENE_ID = "s00_title"

    def construct(self):
        def show():
            t = T("Why averaging removes noise", 56, TEXT, weight=BOLD)
            s = T("a demo of the research-explainer skill", 26, DIM).next_to(t, DOWN, buff=0.4)
            self.play(FadeIn(t, shift=UP * 0.2), run_time=1.0)
            self.play(FadeIn(s), run_time=0.6)
        self.beat(0, show)
        self.outro()


class S01Noise(Beat):
    SCENE_ID = "s01_noise"

    def construct(self):
        clean = framed("clean", 3.6, nearest=True)
        noisy = framed("avg_01", 3.6, nearest=True)
        row = Group(clean, noisy).arrange(RIGHT if not RTL else LEFT, buff=1.2).shift(UP * 0.3)
        lc = T("clean", 24, GREY_).next_to(clean, DOWN)
        ln = T("one noisy copy", 24, GREY_).next_to(noisy, DOWN)

        def a0():
            self.play(FadeIn(clean), FadeIn(lc), run_time=0.8)
            self.play(FadeIn(noisy), FadeIn(ln), run_time=0.8)
        self.beat(0, a0)
        sig = pill(f"noise σ = {D['sigma']}", RED_, 24).next_to(noisy, UP, buff=0.3)
        self.beat(1, lambda: self.play(FadeIn(sig, shift=DOWN * 0.1), run_time=0.6))
        q = T("?", 90, ACCENT, weight=BOLD).move_to(row)
        self.beat(2, lambda: self.play(FadeIn(q, scale=0.6), run_time=0.6))
        self.outro()


class S02Average(Beat):
    SCENE_ID = "s02_average"

    def construct(self):
        tops, bots, labs = [], [], []
        for n in NS:
            tops.append(framed(f"avg_{n:02d}", 2.3, nearest=True))
            bots.append(framed(f"resid_{n:02d}", 2.3, nearest=True))
        top = Group(*tops).arrange(RIGHT if not RTL else LEFT, buff=0.5).shift(UP * 1.55)
        for t, b, n in zip(tops, bots, NS):
            b.next_to(t, DOWN, buff=0.75)
            labs.append(T(f"n = {n}", 22, GREY_).next_to(t, UP, buff=0.15))
        er = T("error (gain ×1)", 20, DIM).next_to(Group(*bots), DOWN, buff=0.2)

        def a0():
            for k in range(len(NS)):
                self.play(FadeIn(tops[k]), FadeIn(labs[k]), run_time=0.55)
        self.beat(0, a0)

        def a1():
            self.play(LaggedStart(*[FadeIn(b) for b in bots], lag_ratio=0.3), FadeIn(er), run_time=1.6)
        self.beat(1, a1)
        self.outro()


def chart(ymax=0.3):
    ax = Axes(x_range=[0, len(NS) + 1, 1], y_range=[0, ymax, 0.05], x_length=8.5, y_length=4.6,
              axis_config={"color": DIM, "include_ticks": False, "include_tip": False}).shift(DOWN * 0.1 + LEFT * 1.4)
    xl = VGroup(*[T(f"n = {n}", 20, GREY_).next_to(ax.c2p(k + 1, 0), DOWN, buff=0.2) for k, n in enumerate(NS)])
    yl = VGroup(*[T(f"{y:.2f}", 18, DIM).next_to(ax.c2p(0, y), LEFT, buff=0.15) for y in (0.0, 0.1, 0.2, 0.3) if y <= ymax])
    title = T("error (RMSE) after averaging", 26, TEXT, weight=BOLD).next_to(ax, UP, buff=0.35)
    return ax, VGroup(xl, yl, title)


def series(ax, key, color, dashed=False):
    ys = [D[key][str(n)] for n in NS]
    pts = [ax.c2p(k + 1, y) for k, y in enumerate(ys)]
    line = VMobject(stroke_color=color, stroke_width=3).set_points_as_corners(pts)
    if dashed:
        line = DashedVMobject(line, num_dashes=30)
    dots = VGroup(*[Dot(p, radius=0.07, color=color) for p in pts])
    return line, dots, ys


class S03Chart(Beat):
    SCENE_ID = "s03_chart"

    def construct(self):
        ax, deco = chart()
        line, dots, ys = series(ax, "independent", BLUE_)
        vals = VGroup(*[T(fmt(y), 18, BLUE_).next_to(d, UR, buff=0.08) for d, y in zip(dots, ys)])
        st = tag("final · our run, seed 0, 20 trials").to_corner(UR, buff=0.35)
        src = source_note("source: experiments/averaging.py → assets/data.json")
        key = VGroup(T("measured", 20, BLUE_), T("theory σ/√n", 20, GREY_)).arrange(DOWN, aligned_edge=START).next_to(ax, RIGHT, buff=0.6)

        def a0():
            self.play(Create(ax), FadeIn(deco), FadeIn(st), FadeIn(src), run_time=1.0)
            self.play(Create(line), LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.3), run_time=1.6)
            self.play(FadeIn(vals), FadeIn(key[0]), run_time=0.6)
        self.beat(0, a0)
        tl, td, _ = series(ax, "theory", GREY_, dashed=True)
        self.beat(1, lambda: self.play(Create(tl), FadeIn(td), FadeIn(key[1]), run_time=1.2))
        self.outro()


class S04Limit(Beat):
    SCENE_ID = "s04_limit"

    def construct(self):
        ax, deco = chart()
        line, dots, _ = series(ax, "independent", BLUE_)
        k1 = T("independent noise", 20, BLUE_)
        st = tag("final · our run, seed 0, 20 trials").to_corner(UR, buff=0.35)
        self.add(ax, deco, line, dots, st)

        def a0():
            k1.next_to(ax, RIGHT, buff=0.6).shift(DOWN * 1.2)
            self.play(FadeIn(k1), Indicate(line, color=BLUE_), run_time=1.0)
        self.beat(0, a0)
        cl, cd, cy = series(ax, "correlated", RED_)
        k2 = T("shared noise (correlation 0.5)", 20, RED_).next_to(ax, RIGHT, buff=0.6).shift(UP * 0.9)
        v = T(fmt(cy[-1]), 18, RED_).next_to(cd[-1], UR, buff=0.08)

        def a1():
            self.play(Create(cl), LaggedStart(*[FadeIn(d) for d in cd], lag_ratio=0.3), FadeIn(k2), run_time=1.6)
            self.play(FadeIn(v), run_time=0.4)
        self.beat(1, a1)
        fy = D["correlated_floor"]
        floor = DashedLine(ax.c2p(0.3, fy), ax.c2p(len(NS) + 0.7, fy), color=ACCENT, stroke_width=2.5)
        fl = T(f"floor {fmt(fy)}", 20, ACCENT).next_to(floor, DOWN, buff=0.1).align_to(floor, RIGHT)
        self.beat(2, lambda: self.play(Create(floor), FadeIn(fl), run_time=1.0))
        self.outro()
