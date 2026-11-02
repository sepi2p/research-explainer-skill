"""How a neural network sees, and how to fool it. Visual first: every beat is a motion; words are labels.
Every image and number comes from assets/ (experiments/network.py on CC0 photos), read here, never typed."""
from PIL import Image
from explainer.base import *

D = data()
A = D["attack"]
MONO = "DejaVu Sans Mono"
CLS_FA = {"golden retriever": "گلدن رتریور", "Great Pyrenees": "سگ پیرنه", "kuvasz": "کوواس", "Labrador retriever": "لابرادور",
          "clumber": "کلامبر", "goldfish": "ماهی قرمز", "Egyptian cat": "گربهٔ مصری", "mousetrap": "تلهٔ موش",
          "flamingo": "فلامینگو", "greenhouse": "گلخانه", "tench": "ماهی تنچ"}


def cls(name):
    return L(name, fa=CLS_FA.get(name, name))


def pct(p):
    return ">99.99%" if p >= 0.99995 else f"{p * 100:.1f}%"


def mono(s, size=22, color=TEXT):
    return Text(s, font=MONO, font_size=size, color=color)


def arr(name):
    return np.asarray(Image.open(asset(name)).convert("RGB"))


def px_point(m, x, y, n=224):
    """Point of pixel (x, y) of an n-pixel-wide square image mobject."""
    s = m.width / n
    return m.get_corner(UL) + np.array([x * s, -y * s, 0])


NAME, VAL = (2, 0) if RTL else (0, 2)     # bar_chart rows: [name, bar, value], reversed in RTL


def top_bars(items, w=5.6, hi=0, color=BLUE_):
    return bar_chart([cls(i["label"]) for i in items], [i["p"] * 100 for i in items], w=w, row=0.62, color=color, hi=hi,
                     hi_color=ACCENT, size=24, vmax=100, fmt="{:.1f}", suffix="%")


class S00Title(Beat):
    SCENE_ID = "s00_title"

    def construct(self):
        a = np.asarray(Image.open(asset("photo.png")).resize((16, 16), Image.BILINEAR))
        photo = img("photo.png", h=5.6, nearest=False).move_to(LEFT * 3.6)
        cell = photo.width / 16
        g = np.random.default_rng(0)
        tiles = VGroup()
        for r in range(16):
            for c in range(16):
                sq = Square(cell * 0.94, stroke_width=0, fill_color=rgb_to_color(a[r, c] / 255), fill_opacity=1)
                sq.target_pos = photo.get_corner(UL) + np.array([(c + 0.5) * cell, -(r + 0.5) * cell, 0])
                sq.rot0 = g.uniform(-1, 1)
                sq.move_to([g.uniform(-7, 7), g.uniform(-4, 4), 0]).rotate(sq.rot0).scale(g.uniform(0.3, 1.2))
                tiles.add(sq)
        t1 = T(L("How a neural network sees", fa="یک شبکهٔ عصبی چطور می‌بیند"), 46, TEXT, weight=BOLD)
        t2 = T(L("and how to fool it", fa="و چطور می‌شود فریبش داد"), 34, ACCENT)
        title = VGroup(t1, t2).arrange(DOWN, buff=0.3, aligned_edge=START)
        if title.width > 6.6:
            title.scale_to_fit_width(6.6)
        title.next_to(photo, RIGHT if not RTL else LEFT, buff=0.6)
        if RTL:
            Group(photo, title).arrange(LEFT, buff=0.6).move_to(ORIGIN)
            for r in range(16):
                for c in range(16):
                    tiles[r * 16 + c].target_pos = photo.get_corner(UL) + np.array([(c + 0.5) * cell, -(r + 0.5) * cell, 0])

        def show():
            self.play(LaggedStart(*[FadeIn(s, scale=0.5) for s in tiles], lag_ratio=0.002), run_time=0.8)
            self.play(LaggedStart(*[s.animate.move_to(s.target_pos).rotate(-s.rot0).set(width=cell * 0.94)
                                    for s in tiles], lag_ratio=0.004), run_time=2.0)
            self.play(FadeIn(photo), tiles.animate.set_opacity(0), run_time=0.8)
            self.remove(tiles)
            self.play(FadeIn(t1, shift=UP * 0.2), run_time=0.6)
            self.play(FadeIn(t2, shift=UP * 0.2), run_time=0.5)
        self.beat(0, show)
        self.outro()


class S01Pixels(Beat):
    SCENE_ID = "s01_pixels"

    def construct(self):
        photo = img("photo.png", h=6.6).move_to(LEFT * 3.2 if not RTL else RIGHT * 3.2)
        P = D["patch"]
        x0, y0, n = P["x"], P["y"], P["size"]
        rgb = np.array(P["rgb"], dtype=np.uint8)
        small = Rectangle(width=photo.width / 224 * n, height=photo.width / 224 * n, stroke_color=ACCENT, stroke_width=3)
        small.move_to((px_point(photo, x0, y0) + px_point(photo, x0 + n, y0 + n)) / 2)
        big = array_img(rgb, h=5.6).move_to(RIGHT * 3.6 if not RTL else LEFT * 3.6)
        frame = SurroundingRectangle(big, buff=0, color=ACCENT, stroke_width=3)
        lines = VGroup(*[DashedLine(small.get_corner(c), frame.get_corner(c), stroke_color=ACCENT, stroke_width=1.5, dash_length=0.08)
                         for c in (UL, DL, UR, DR)])
        cs = big.width / n
        nums = VGroup()
        for r in range(n):
            for c in range(n):
                v = rgb[r, c]
                lum = 0.299 * v[0] + 0.587 * v[1] + 0.114 * v[2]
                col = BG if lum > 140 else TEXT
                cellnums = VGroup(*[Text(str(int(x)), font=MONO, font_size=15, color=col) for x in v]).arrange(DOWN, buff=0.04)
                cellnums.move_to(big.get_corner(UL) + np.array([(c + 0.5) * cs, -(r + 0.5) * cs, 0]))
                nums.add(cellnums)

        def a0():
            self.play(FadeIn(photo, scale=1.03), run_time=0.8)
            self.play(Create(small), run_time=0.5)
            self.play(Create(lines), TransformFromCopy(small, frame), FadeIn(big, target_position=small.get_center(), scale=0.05), run_time=1.3)
            self.play(LaggedStart(*[FadeIn(cn, scale=0.6) for cn in nums], lag_ratio=0.03), run_time=1.8)
        self.beat(0, a0)

        rgbimg = arr("photo.png")
        planes = []
        for k, colr in enumerate((RED_, GREEN_, BLUE_)):
            ch = np.zeros_like(rgbimg)
            ch[..., k] = rgbimg[..., k]
            planes.append(array_img(ch, h=4.2, nearest=False))
        labels = [T(s, 30, c, weight=BOLD) for s, c in (("R", RED_), ("G", GREEN_), ("B", BLUE_))]
        tr_ = ValueTracker(0)
        count = ticker(tr_, "{:,.0f}", 60, ACCENT, place=lambda m: m.move_to(DOWN * 3.15), weight=BOLD)
        eq = T("224 × 224 × 3 =", 36, GREY_).move_to(DOWN * 2.35)

        def a1():
            self.play(FadeOut(VGroup(nums, lines, frame, small)), FadeOut(big), photo.animate.set(height=4.2).move_to(ORIGIN + UP * 0.6), run_time=0.9)
            for p in planes:
                p.move_to(photo)
            self.add(*planes[::-1])
            self.remove(photo)
            offs = [np.array([-2.6, 0.7, 0]), np.array([0, 0.35, 0]), np.array([2.6, 0, 0])]
            self.play(*[p.animate.shift(o) for p, o in zip(planes, offs)], run_time=1.2)
            for p, l in zip(planes, labels):
                l.next_to(p, UP, buff=0.15)
            self.play(LaggedStart(*[FadeIn(l, shift=DOWN * 0.1) for l in labels], lag_ratio=0.2), FadeIn(eq), run_time=0.7)
            self.add(count)
            self.play(tr_.animate.set_value(224 * 224 * 3), run_time=1.6, rate_func=rate_functions.ease_out_cubic)
        self.beat(1, a1)
        self.outro()


class S02Filters(Beat):
    SCENE_ID = "s02_filters"

    def construct(self):
        F = arr("filters.png")
        tiles = Group()
        for k in range(64):
            r, c = divmod(k, 8)
            t = array_img(F[1 + r * 9:1 + r * 9 + 7, 1 + c * 9:1 + c * 9 + 7], h=0.6)
            tiles.add(t)
        tiles.arrange_in_grid(8, 8, buff=0.08).move_to(ORIGIN)
        best = D["conv1_best"]

        def a0():
            self.play(LaggedStart(*[FadeIn(t, scale=0.3) for t in tiles], lag_ratio=0.03), run_time=2.0)
            others = [tiles[k] for k in range(64) if k not in best]
            self.play(*[t.animate.set_opacity(0.18) for t in others], *[tiles[k].animate.scale(1.5) for k in best], run_time=0.8)
            self.play(*[Circumscribe(tiles[k], color=ACCENT, buff=0.04) for k in best], run_time=0.8)
        self.beat(0, a0)

        k0 = best[0]
        photo = img("photo.png", h=4.6).move_to(LEFT * 3.4 if not RTL else RIGHT * 3.4).shift(DOWN * 0.2)
        fmap = img(f"fmap_conv1_{k0}.png", h=4.6, nearest=True).move_to(RIGHT * 3.4 if not RTL else LEFT * 3.4).shift(DOWN * 0.2)
        cover = Rectangle(width=fmap.width + 0.02, height=fmap.height + 0.02, fill_color=BG, fill_opacity=1, stroke_width=0).move_to(fmap)
        edge = SurroundingRectangle(fmap, buff=0, color=DIM, stroke_width=1.5)
        probe = Square(0.42, stroke_color=ACCENT, stroke_width=3, fill_color=ACCENT, fill_opacity=0.15)
        ftile = array_img(F[1 + (k0 // 8) * 9:1 + (k0 // 8) * 9 + 7, 1 + (k0 % 8) * 9:1 + (k0 % 8) * 9 + 7], h=0.42)
        prog = ValueTracker(0)
        ROWS = 5

        def place_probe(m):
            p = prog.get_value()
            row = min(int(p * ROWS), ROWS - 1)
            fr = p * ROWS - row
            x = photo.get_left()[0] + 0.21 + fr * (photo.width - 0.42)
            y = photo.get_top()[1] - 0.21 - (row + 0.5) / ROWS * (photo.height - 0.42)
            m.move_to([x, y, 0])
        probe.add_updater(place_probe)
        ftile.add_updater(place_probe)

        def shrink(m):
            p = prog.get_value()
            h = max(fmap.height * (1 - p), 0.001)
            m.stretch_to_fit_height(h).align_to(fmap, DOWN)
        cover.add_updater(shrink)
        link = always_redraw(lambda: DashedLine(probe.get_center(), [fmap.get_left()[0] if not RTL else fmap.get_right()[0], cover.get_bottom()[1], 0],
                                                stroke_color=ACCENT, stroke_width=1.5, dash_length=0.08))

        def a1():
            self.play(FadeOut(Group(*[tiles[k] for k in range(64) if k != k0])), tiles[k0].animate.move_to(photo.get_corner(UL)).set(height=0.42), run_time=0.8)
            self.remove(tiles[k0])
            self.play(FadeIn(photo), FadeIn(fmap), FadeIn(cover), Create(edge), FadeIn(probe), FadeIn(ftile), run_time=0.6)
            self.add(link)
            self.play(prog.animate.set_value(1), run_time=3.6, rate_func=linear)
            for m in (probe, ftile, cover):
                m.clear_updaters()
            self.remove(link, cover)
            self.play(FadeOut(probe), FadeOut(ftile), run_time=0.3)
        self.beat(1, a1)

        pairs = Group()
        for k in best:
            f = array_img(F[1 + (k // 8) * 9:1 + (k // 8) * 9 + 7, 1 + (k % 8) * 9:1 + (k % 8) * 9 + 7], h=0.8)
            m = img(f"fmap_conv1_{k}.png", h=3.4, nearest=True)
            pairs.add(Group(f, m).arrange(DOWN, buff=0.3))
        pairs.arrange(RIGHT if not RTL else LEFT, buff=0.6).move_to(DOWN * 0.1)

        def a2():
            self.play(FadeOut(photo), FadeOut(edge), ReplacementTransform(fmap, pairs[0][1]), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.3) for p in [pairs[0][0], pairs[1], pairs[2]]], lag_ratio=0.3), run_time=1.2)
        self.beat(2, a2)
        self.outro()


STAGE_H = [2.3, 1.95, 1.65, 1.38, 1.15]


def stage_stack(i, s):
    maps = [img(f"stage_{s['name']}_{k}.png", h=STAGE_H[i], nearest=True) for k in range(6)]
    st = fan(maps[::-1], dx=0.11, dy=0.09)
    return st


class S03Layers(Beat):
    SCENE_ID = "s03_layers"

    def construct(self):
        st = D["stages"]
        stacks, labs = [], []
        for i, s in enumerate(st):
            stacks.append(stage_stack(i, s))
        Group(*stacks).arrange(RIGHT if not RTL else LEFT, buff=0.45).move_to(UP * 0.4)
        xs = [g.get_center()[0] for g in stacks]
        for i, s in enumerate(st):
            g = stacks[i]
            lab = VGroup(T(f"{s['channels']}", 30, ACCENT, weight=BOLD), T(f"{s['h']}×{s['w']}", 24, GREY_)).arrange(DOWN, buff=0.1)
            lab.next_to(g, DOWN, buff=0.35)
            labs.append(lab)
        names = [T(s["name"], 20, DIM).next_to(stacks[i], UP, buff=0.25) for i, s in enumerate(st)]
        path = VMobject().set_points_smoothly([np.array([xs[0] - 1.8 * (1 if not RTL else -1), 0.4, 0])] +
                                              [np.array([x, 0.4 + 0.25 * (-1) ** k, 0]) for k, x in enumerate(xs)] +
                                              [np.array([xs[-1] + 1.6 * (1 if not RTL else -1), 0.4, 0])])

        def a0():
            for i in range(5):
                self.play(FadeIn(stacks[i], shift=RIGHT * 0.4 * (1 if not RTL else -1), scale=0.9), FadeIn(labs[i], shift=UP * 0.15),
                          FadeIn(names[i]), run_time=0.75)
            dots = [Dot(radius=0.06, color=ACCENT).set_z_index(30) for _ in range(14)]
            self.play(LaggedStart(*[MoveAlongPath(d, path, rate_func=linear) for d in dots], lag_ratio=0.12), run_time=2.6)
            self.remove(*dots)
            self.play(Circumscribe(labs[0], color=ACCENT), Circumscribe(labs[-1], color=ACCENT), run_time=1.0)
        self.beat(0, a0)
        self.outro()


class S04Decision(Beat):
    SCENE_ID = "s04_decision"

    def construct(self):
        s = D["stages"][-1]
        stack = stage_stack(4, s).move_to(LEFT * 5.0 if not RTL else RIGHT * 5.0)
        pooled = np.array(D["pooled"])
        n = len(pooled)
        bw = 9.6 / n
        x0 = -3.4 if not RTL else 3.4 - 9.6
        code = VGroup(*[Rectangle(width=bw * 0.8, height=max(0.02, v / pooled.max() * 2.4), stroke_width=0,
                                  fill_color=interpolate_color(ManimColor(BLUE_), ManimColor(ACCENT), v / pooled.max()), fill_opacity=1)
                        .move_to([x0 + (k + 0.5) * bw, 0, 0], aligned_edge=DOWN) for k, v in enumerate(pooled)])
        code.shift(DOWN * 0.8)
        n_lab = T(f"{n}", 34, ACCENT, weight=BOLD).next_to(code, DOWN, buff=0.3)

        def a0():
            self.play(FadeIn(stack, shift=RIGHT * 0.3), run_time=0.6)
            self.play(FadeOut(stack, target_position=code.get_left() if not RTL else code.get_right(), scale=0.1), run_time=0.7)
            self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in code], lag_ratio=0.004), FadeIn(n_lab), run_time=1.8)
        self.beat(0, a0)

        bars = top_bars(D["top5"]).move_to(RIGHT * 2.2 if not RTL else LEFT * 2.2)
        cnt = T(L("1,000 classes", fa="۱٬۰۰۰ دسته"), 24, DIM).next_to(bars, UP, buff=0.4)

        def a1():
            self.play(code.animate.scale(0.36).move_to(LEFT * 5.4 if not RTL else RIGHT * 5.4), FadeOut(n_lab), run_time=0.8)
            streams = [Line(code.get_right() if not RTL else code.get_left(), r[1].get_left() if not RTL else r[1].get_right(),
                            stroke_color=ACCENT, stroke_width=2).set_opacity(0.5) for r in bars]
            self.play(LaggedStart(*[ShowPassingFlash(l, time_width=0.5) for l in streams], lag_ratio=0.1), FadeIn(cnt), run_time=0.9)
            for r in bars:
                r[1][1].set_z_index(2)
            self.play(LaggedStart(*[AnimationGroup(FadeIn(r[NAME]), FadeIn(r[1][0]), GrowFromEdge(r[1][1], LEFT if not RTL else RIGHT))
                                    for r in bars], lag_ratio=0.15), run_time=1.4)
            self.play(LaggedStart(*[FadeIn(r[VAL], scale=1.3) for r in bars], lag_ratio=0.1), run_time=0.8)
            self.play(Circumscribe(bars[0], color=ACCENT), run_time=0.8)
        self.beat(1, a1)
        self.outro()


class S05Saliency(Beat):
    SCENE_ID = "s05_saliency"

    def construct(self):
        photo = img("photo.png", h=6.8)
        sal = img("saliency.png", h=6.8)
        tr_ = ValueTracker(0)
        scan = always_redraw(lambda: Line([photo.get_left()[0] + tr_.get_value() * photo.width, photo.get_top()[1], 0],
                                          [photo.get_left()[0] + tr_.get_value() * photo.width, photo.get_bottom()[1], 0],
                                          stroke_color=ACCENT, stroke_width=4))
        sal.add_updater(lambda m: m.set_opacity(tr_.get_value()))

        def a0():
            self.play(FadeIn(photo, scale=1.02), run_time=0.6)
            sal.set_opacity(0)
            self.add(sal, scan)
            self.play(tr_.animate.set_value(1), run_time=2.0, rate_func=smooth)
            sal.clear_updaters()
            self.remove(scan)
            self.wait(0.6)
        self.beat(0, a0)
        self.outro()


class S06Gallery(Beat):
    SCENE_ID = "s06_gallery"

    def construct(self):
        items = [{"img": "photo.png", "top1": D["top5"][0], "ok": True}] + \
                [{"img": f"gallery_{g['name']}.png", "top1": g["top1"], "ok": g["top1"]["label"] != "mousetrap"} for g in D["gallery"]]
        cards = []
        for it in items:
            im = img(it["img"], h=2.9)
            lab = VGroup(T(cls(it["top1"]["label"]), 24, TEXT, weight=BOLD), T(pct(it["top1"]["p"]), 22, GREY_)).arrange(DOWN, buff=0.08)
            box = RoundedRectangle(corner_radius=0.18, width=im.width + 0.3, height=im.height + lab.height + 0.65, fill_color=PANEL,
                                   fill_opacity=1, stroke_color=DIM, stroke_width=1.5)
            im.move_to(box.get_top() + DOWN * (0.15 + im.height / 2))
            lab.next_to(im, DOWN, buff=0.15)
            cards.append(Group(box, im, lab))
        row = Group(*cards).arrange(RIGHT if not RTL else LEFT, buff=0.35).move_to(UP * 0.2)

        def a0():
            self.play(FadeIn(cards[0], shift=UP * 0.4), run_time=0.6)
            for c in cards[1:3]:
                self.play(FadeIn(c, shift=UP * 1.2, scale=0.9), run_time=0.6)
                self.play(c[0].animate.set_stroke(GREEN_, 2.5), run_time=0.3)
        self.beat(0, a0)

        def a1():
            c = cards[3]
            self.play(FadeIn(c, shift=UP * 1.2, scale=0.9), run_time=0.6)
            strike = Line(c[2][0].get_left() + LEFT * 0.1, c[2][0].get_right() + RIGHT * 0.1, stroke_color=RED_, stroke_width=5)
            self.play(c[0].animate.set_stroke(RED_, 3), Create(strike), c[2][0].animate.set_color(RED_), run_time=0.6)
            self.play(Wiggle(c, scale_value=1.04, rotation_angle=0.02 * TAU), run_time=0.8)
        self.beat(1, a1)
        self.outro()


class S07Attack(Beat):
    SCENE_ID = "s07_attack"

    def construct(self):
        h = 3.9
        photo = img("photo.png", h=h)
        delta = img("delta.png", h=h, nearest=True)
        adv = img("adv.png", h=h)
        plus, eq = T("+", 70, GREY_), T("=", 70, GREY_)
        row = Group(photo, plus, delta, eq, adv).arrange(RIGHT if not RTL else LEFT, buff=0.35).move_to(UP * 0.5)
        dl = T(L(f"change ×{A['gain']:.0f}", fa=f"تغییر ×{A['gain']:.0f}"), 24, ACCENT).next_to(delta, DOWN, buff=0.25)
        dl2 = T(L(f"max {A['max_change_255']}/255 per value", fa=f"حداکثر {A['max_change_255']}/255 در هر مقدار"), 22, GREY_).next_to(dl, DOWN, buff=0.12)

        def a0():
            self.play(FadeIn(photo), run_time=0.5)
            self.play(FadeIn(plus), FadeIn(delta, shift=LEFT * 0.6 if not RTL else RIGHT * 0.6), run_time=0.7)
            self.play(FadeIn(dl), FadeIn(dl2), run_time=0.5)
            for _ in range(3):
                self.play(delta.animate.set_opacity(0.55), run_time=0.2)
                self.play(delta.animate.set_opacity(1), run_time=0.2)
            self.play(FadeIn(eq), FadeIn(adv, shift=LEFT * 0.4 if not RTL else RIGHT * 0.4), run_time=0.7)
        self.beat(0, a0)

        big1 = img("photo.png", h=5.6)
        big2 = img("adv.png", h=5.6)
        pair = Group(big1, big2).arrange(RIGHT if not RTL else LEFT, buff=0.5).move_to(UP * 0.3)
        l1 = T(L("before", fa="قبل"), 26, GREY_).next_to(big1, DOWN, buff=0.2)
        l2 = T(L("after", fa="بعد"), 26, GREY_).next_to(big2, DOWN, buff=0.2)
        ps = tag(f"PSNR {A['psnr_db']} dB", 20).next_to(pair, DOWN, buff=0.8)

        def a1():
            self.play(FadeOut(VGroup(plus, eq, dl, dl2)), FadeOut(delta), ReplacementTransform(photo, big1), ReplacementTransform(adv, big2), run_time=1.0)
            self.play(FadeIn(l1), FadeIn(l2), FadeIn(ps), run_time=0.5)
            self.play(Indicate(big1, scale_factor=1.02, color=WHITE), Indicate(big2, scale_factor=1.02, color=WHITE), run_time=1.0)
        self.beat(1, a1)

        b_clean = top_bars(D["top5"], w=5.0).move_to(RIGHT * 2.4 if not RTL else LEFT * 2.4)
        b_adv = top_bars(A["top5"], w=5.0, color=GREY_).move_to(b_clean)
        b_adv[0][VAL].become(T(pct(A["top5"][0]["p"]), 24, RED_).move_to(b_adv[0][VAL], aligned_edge=LEFT if not RTL else RIGHT))
        b_adv[0][1][1].set_fill(RED_)
        b_adv[0][NAME].set_color(RED_)
        for b in (b_clean, b_adv):
            for r in b:
                r[1][1].set_z_index(2)
        thumb = img("adv.png", h=3.6).move_to(LEFT * 4.3 if not RTL else RIGHT * 4.3)

        def a2():
            self.play(FadeOut(VGroup(l1, l2, ps)), FadeOut(big1), ReplacementTransform(big2, thumb), FadeIn(b_clean), run_time=0.9)
            self.wait(0.4)
            self.play(ReplacementTransform(b_clean, b_adv), run_time=1.4, rate_func=rate_functions.ease_in_out_cubic)
            self.play(Flash(b_adv[0][1][1].get_right(), color=RED_, line_length=0.3), Circumscribe(b_adv[0], color=RED_), run_time=0.8)
        self.beat(2, a2)

        cav = VGroup(tag(L("white-box: the attacker knows the weights", fa="جعبه‌سفید: مهاجم وزن‌ها را می‌داند"), 20),
                     tag(L("one model · one photo · digital", fa="یک مدل · یک عکس · دیجیتال"), 20)).arrange(DOWN, buff=0.18)
        cav.next_to(b_adv, DOWN, buff=0.5)
        self.beat(3, lambda: self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in cav], lag_ratio=0.3), run_time=0.8))
        self.outro()


class S08Close(Beat):
    SCENE_ID = "s08_close"

    def construct(self):
        script = VGroup(RoundedRectangle(corner_radius=0.18, width=4.6, height=1.1, fill_color=PANEL, fill_opacity=1, stroke_color=ACCENT, stroke_width=2),
                        mono("experiments/network.py", 24, ACCENT))
        script[1].move_to(script[0])
        script.move_to(LEFT * 3.9 if not RTL else RIGHT * 3.9)
        names = ["photo.png", "filters.png"] + [f"fmap_conv1_{k}.png" for k in D["conv1_best"]] + \
                [f"stage_{s['name']}_0.png" for s in D["stages"]] + ["saliency.png", "delta.png", "adv.png"] + \
                [f"gallery_{g['name']}.png" for g in D["gallery"]]
        thumbs = Group(*[img(n, h=1.05, nearest=("stage" in n or "fmap" in n or "filters" in n or "delta" in n)) for n in names])
        thumbs.arrange_in_grid(4, 4, buff=0.15).move_to(RIGHT * 2.6 if not RTL else LEFT * 2.6)
        src = T(L("ResNet-18 · ImageNet weights · CC0 photos", fa="ResNet-18 · وزن‌های ImageNet · عکس‌های CC0"), 22, DIM, max_w=5.4).next_to(script, DOWN, buff=0.35)

        def a0():
            self.play(FadeIn(script, scale=0.9), FadeIn(src), run_time=0.6)
            self.play(LaggedStart(*[FadeIn(t, target_position=script.get_center(), scale=0.2) for t in thumbs], lag_ratio=0.08), run_time=2.4)
            self.play(Circumscribe(script, color=ACCENT), run_time=0.8)
        self.beat(0, a0)
        self.outro()
