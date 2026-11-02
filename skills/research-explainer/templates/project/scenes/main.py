"""Scenes. One class per scene, registered in project.json in playing order. Numbers come from data(), never typed here."""
from explainer.base import *


class S00Title(Beat):
    SCENE_ID = "s00_title"

    def construct(self):
        def show():
            t = T(CONF.get("title", "TITLE"), 54, TEXT, weight=BOLD)
            self.play(FadeIn(t, shift=UP * 0.2), run_time=1.0)
        self.beat(0, show)
        self.outro()


class S01Hook(Beat):
    SCENE_ID = "s01_hook"

    def construct(self):
        box = panel(6, 3.5, ACCENT, title="replace with a real image: framed('name')")
        self.beat(0, lambda: self.play(FadeIn(box), run_time=0.8))
        q = T("?", 90, ACCENT, weight=BOLD).next_to(box, RIGHT if not RTL else LEFT, buff=0.6)
        self.beat(1, lambda: self.play(FadeIn(q, scale=0.6), run_time=0.6))
        self.outro()
