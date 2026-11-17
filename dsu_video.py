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
        self.wait(1.5)
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


class OperationsAnimator(TraceAnimator):
    """Deja espacio para explicar las operaciones en puntos concretos de la traza."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unions_shown = 0
        self.queries_shown = 0

    def on_unite_call(self, ev):
        self.unions_shown += 1
        super().on_unite_call(ev)
        if self.unions_shown == 1:
            self.wait(2.5)  # Presentar unite y la búsqueda de ambas raíces.

    def on_link(self, ev):
        super().on_link(ev)
        if self.unions_shown == 1:
            self.wait(3)  # Explicar parent, size y el representante.
        elif self.unions_shown == 6:
            self.wait(3)  # Comparar los tamaños de los conjuntos unidos.
        else:
            self.wait(0.5)

    def on_same_result(self, ev):
        super().on_same_result(ev)
        self.queries_shown += 1
        self.wait(2 if self.queries_shown == 1 else 2.5)


class S01Operaciones(TraceScene):
    """Introduce el ADT y reproduce las operaciones de la traza C++."""

    def construct(self):
        heading = Text("Conjuntos disjuntos", font_size=42).to_edge(UP, buff=0.5)
        definition = Text("Cada elemento pertenece a un único conjunto", font_size=29)
        definition.next_to(heading, DOWN, buff=0.6)
        example = Text("En una red, cada conjunto representa\nuna componente conectada",
                       font_size=27, line_spacing=1.2).next_to(definition, DOWN, buff=0.55)
        operations = VGroup(
            Text("find(x)  →  representante de x", font_size=26, color=YELLOW),
            Text("unite(a, b)  →  une dos conjuntos", font_size=26, color=GREEN),
            Text("same(a, b)  →  ¿están conectados?", font_size=26, color=BLUE_B),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(example, DOWN, buff=0.55)
        self.play(FadeIn(heading), FadeIn(definition))
        self.wait(1.2)
        self.play(FadeIn(example))
        self.wait(1.2)
        self.play(LaggedStart(*[FadeIn(op, shift=RIGHT * 0.2) for op in operations], lag_ratio=0.3))
        self.wait(3)
        self.play(FadeOut(heading), FadeOut(definition), FadeOut(example), FadeOut(operations))

        trace = load_trace(TRACE_DIR / "01_union_por_tamano.json")
        OperationsAnimator(self, trace, "Operaciones y unión por tamaño").run()


class RollbackAnimator(TraceAnimator):
    """Enfatiza la historia y deja tiempo para narrar cada reversión."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.saved_state = None
        self.undo_count = 0

    def on_push(self, ev):
        super().on_push(ev)
        if len(ev.state.history) == 1:
            self.play(Indicate(self.stack.entries[-1], color=YELLOW), rt=0.7)
            self.wait(2.5)

    def on_snapshot(self, ev):
        self.saved_state = ev.state
        super().on_snapshot(ev)
        self.wait(4)  # El snapshot guarda la profundidad, no una copia del bosque.

    def on_rollback_to_call(self, ev):
        super().on_rollback_to_call(ev)
        self.wait(2)

    def on_pop(self, ev):
        self.undo_count += 1
        self.play(Indicate(self.stack.entries[-1], color=RED), rt=0.7)
        super().on_pop(ev)

    def on_unlink(self, ev):
        super().on_unlink(ev)
        self.wait(2.5 if self.undo_count == 1 else 1.2)

    def on_rollback_to_done(self, ev):
        # El estado recuperado debe coincidir exactamente con el snapshot de C++.
        assert ev.state == self.saved_state
        self.wait(2.5)
        super().on_rollback_to_done(ev)

    def on_same_result(self, ev):
        super().on_same_result(ev)
        self.wait(1.5)


class S02Rollback(TraceScene):
    """Snapshot, uniones temporales y recuperación desde la traza real."""

    def construct(self):
        heading = Text("Guardar y recuperar un estado", font_size=40).to_edge(UP, buff=0.6)
        explanation = VGroup(
            Text("Cada unión registra un cambio en la pila", font_size=28),
            Text("snapshot() guarda la posición actual", font_size=28, color=YELLOW),
            Text("rollback() deshace el cambio más reciente", font_size=28, color=RED_B),
        ).arrange(DOWN, buff=0.45).move_to(ORIGIN)
        self.play(FadeIn(heading))
        for line in explanation:
            self.play(FadeIn(line, shift=UP * 0.1), run_time=0.7)
            self.wait(1.3)
        self.play(FadeOut(heading), FadeOut(explanation))
        trace = load_trace(TRACE_DIR / "02_rollback.json")
        RollbackAnimator(self, trace, "Snapshot y rollback").run()


class TraceDemo(TraceScene):
    """Anima la traza indicada en la variable de entorno TRACE."""

    def construct(self):
        path = Path(os.environ.get("TRACE", TRACE_DIR / "02_rollback.json"))
        trace = load_trace(path)
        TraceAnimator(self, trace, trace.description).run()
