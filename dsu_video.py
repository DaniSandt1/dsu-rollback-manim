"""Escenas del video. Cada escena reproduce una traza generada por el programa C++.

    manim -pql dsu_video.py S02Rollback           # vista previa rápida (480p)
    manim -qh  dsu_video.py S02Rollback           # 1080p60

Para revisar cualquier otra traza con el mismo animador:
    TRACE=trace/01_union_por_tamano.json manim -pql dsu_video.py TraceDemo
"""
from __future__ import annotations

import os
from pathlib import Path

from manim import *

from animator import TraceAnimator
from components import BG
from trace_loader import load_trace

TRACE_DIR = Path(__file__).parent / "trace"


class S00Motivacion(Scene):
    """Red de computadoras: los cables siguen las operaciones de la traza real."""

    def construct(self):
        self.camera.background_color = BG
        trace = load_trace(TRACE_DIR / "00_motivacion.json")
        title = Text("DSU con Rollback", font_size=46, color=WHITE)
        subtitle = Text("Conectividad dinámica", font_size=26, color=BLUE_B).next_to(title, DOWN)
        authors = Text("Daniel Sandoval · Percy Castro", font_size=20).next_to(subtitle, DOWN, buff=0.45)
        self.play(FadeIn(title), FadeIn(subtitle), FadeIn(authors))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle), FadeOut(authors))

        heading = Text("Una red de computadoras", font_size=32).to_edge(UP)
        positions = [LEFT * 4 + UP, LEFT * 2 + UP, RIGHT * 2 + UP, RIGHT * 4 + UP,
                     LEFT * 2 + DOWN * 1.2, RIGHT * 2 + DOWN * 1.2]
        nodes = []
        for label, pos in zip(trace.labels(), positions):
            screen = RoundedRectangle(width=1.0, height=0.65, corner_radius=0.08, color=BLUE_B)
            stand = Line(DOWN * 0.32, DOWN * 0.48, color=BLUE_B)
            base = Line(LEFT * 0.25 + DOWN * 0.48, RIGHT * 0.25 + DOWN * 0.48, color=BLUE_B)
            node = VGroup(screen, stand, base, Text(label, font_size=22).move_to(screen)).move_to(pos)
            nodes.append(node)
        caption = Text("Cada equipo comienza aislado", font_size=25).to_edge(DOWN)
        self.play(FadeIn(heading), *[FadeIn(n) for n in nodes], FadeIn(caption))
        self.wait(1)
        cables = []
        pending = None
        for event in trace.events:
            if event.op == "unite_call":
                pending = (event["a"], event["b"])
            elif event.op == "snapshot":
                new = Text("Guardamos este estado", font_size=25, color=YELLOW).to_edge(DOWN)
                self.play(Transform(caption, new))
                self.wait(1)
            elif event.op == "link":
                a, b = pending
                cable = Line(nodes[a].get_center(), nodes[b].get_center(), color=GREEN, stroke_width=5)
                cables.append(cable)
                new = Text(f"Conectamos {trace.labels()[a]} y {trace.labels()[b]}", font_size=25).to_edge(DOWN)
                self.play(Create(cable), Transform(caption, new))
                self.wait(1)
            elif event.op == "unlink":
                new = Text("Rollback: volvemos al estado guardado", font_size=25, color=YELLOW).to_edge(DOWN)
                self.play(FadeOut(cables.pop()), Transform(caption, new))
                self.wait(1)
        question = Text("¿Cómo combinar grupos y volver\na un estado anterior?", font_size=30, line_spacing=1.2)
        self.play(FadeOut(heading), FadeOut(caption), *[FadeOut(n) for n in nodes],
                  *[FadeOut(c) for c in cables])
        self.play(Write(question))
        self.wait(2)


class TraceScene(Scene):
    trace_file = ""
    title = ""
    speed = 1.0

    def setup(self):
        self.camera.background_color = BG

    def construct(self):
        trace = load_trace(TRACE_DIR / self.trace_file)  # valida la traza antes de animarla
        TraceAnimator(self, trace, self.title, self.speed).run()


class S02Rollback(TraceScene):
    trace_file = "02_rollback.json"
    title = "Rollback: volver atrás en el tiempo"


class TraceDemo(TraceScene):
    """Anima la traza indicada en la variable de entorno TRACE."""

    def construct(self):
        path = Path(os.environ.get("TRACE", TRACE_DIR / "02_rollback.json"))
        trace = load_trace(path)
        TraceAnimator(self, trace, trace.description).run()
