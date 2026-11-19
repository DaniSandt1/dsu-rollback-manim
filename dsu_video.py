"""Escenas del video. Cada escena reproduce una traza generada por el programa C++.

    manim -pql dsu_video.py S02Rollback           # vista previa rápida (480p)
    manim -qh  dsu_video.py S02Rollback           # 1080p60

Para revisar cualquier otra traza con el mismo animador:
    TRACE=trace/01_union_por_tamano.json manim -pql dsu_video.py TraceDemo
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from manim import *

from animator import TraceAnimator
from components import BG, C_DEL, C_MUTED, C_NEW, C_ROOT, C_TEXT, txt
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


def fade_all(scene, rt=0.6):
    """Saca todo de la pantalla (y detiene las flechas que siguen a los nodos)."""
    mobs = list(scene.mobjects)
    for m in mobs:
        m.clear_updaters()
    if mobs:
        scene.play(*[FadeOut(m) for m in mobs], run_time=rt)


def intro_card(scene, heading, lines, colors=None, wait_each=1.1, wait_end=1.2):
    """Tarjeta de texto en el estilo de las otras escenas."""
    title = Text(heading, font_size=40).to_edge(UP, buff=0.6)
    colors = colors or [WHITE] * len(lines)
    body = VGroup(*[Text(l, font_size=28, color=c) for l, c in zip(lines, colors)])
    body.arrange(DOWN, buff=0.45).move_to(ORIGIN)
    scene.play(FadeIn(title))
    for line in body:
        scene.play(FadeIn(line, shift=UP * 0.1), run_time=0.6)
        scene.wait(wait_each)
    scene.wait(wait_end)
    scene.play(FadeOut(title), FadeOut(body), run_time=0.6)


class S03SinCompresion(TraceScene):
    """Por qué la estructura no comprime caminos: traza real de compresión + rollback."""

    def construct(self):
        intro_card(self, "¿Y la compresión de caminos?", [
            "En un DSU normal, find() cuelga todo el camino de la raíz",
            "Eso acelera las búsquedas siguientes...",
            "...pero cambia punteros que la pila de rollback no registra",
        ], colors=[WHITE, WHITE, RED_B], wait_each=0.9, wait_end=0.8)
        trace = load_trace(TRACE_DIR / "07_sin_compresion.json")
        TraceAnimator(self, trace, "Compresión de caminos + rollback", speed=1.25).run(
            tail_wait=1.0, prelude_speed=3.0)
        fade_all(self)
        intro_card(self, "Por eso: sin compresión", [
            "find() solo lee: no modifica la estructura",
            "Cada unión cambia 1 parent y 1 size",
            "Deshacerla es restaurar esos 2 valores: O(1)",
        ], colors=[WHITE, WHITE, GREEN], wait_each=0.8, wait_end=0.8)


class S04CasoBorde(TraceScene):
    """Casos borde con trazas reales: unión redundante (con y sin marcador) y pila vacía."""

    def construct(self):
        intro_card(self, "Casos borde", [
            "1. Unir dos elementos que ya están en el mismo conjunto",
            "2. Hacer rollback() sin nada que deshacer",
        ], wait_each=0.8, wait_end=0.5)
        parts = [
            ("04_borde_sin_marcador.json", "Error: no apilar la unión redundante"),
            ("03_borde_redundante.json", "Correcto: apilar un marcador vacío"),
            ("05_borde_pila_vacia.json", "rollback() con la pila vacía"),
        ]
        for file, title in parts:
            trace = load_trace(TRACE_DIR / file)
            TraceAnimator(self, trace, title, speed=1.6).run(tail_wait=1.0, prelude_speed=2.5)
            fade_all(self)
        intro_card(self, "Regla", [
            "Cada unite() apila exactamente un registro",
            "→ rollback() siempre deshace el último unite()",
        ], colors=[WHITE, GREEN], wait_each=0.9, wait_end=0.8)


class S05Complejidad(Scene):
    """Tabla de costos y alturas MEDIDAS por el programa C++ (trace/medidas/alturas.json)."""

    def setup(self):
        self.camera.background_color = BG

    def construct(self):
        data = json.loads((TRACE_DIR / "medidas" / "alturas.json").read_text(encoding="utf-8"))
        assert data.get("format") == "dsu-alturas/1", "alturas.json con formato desconocido"
        rows = {r["n"]: r for r in data["rows"]}

        heading = Text("Complejidad", font_size=42).to_edge(UP, buff=0.4)
        self.play(FadeIn(heading))

        table = [
            ("find(x)", "O(log n)", "altura ≤ log₂ n por la unión por tamaño"),
            ("unite(a, b)", "O(log n)", "2 find + enlace O(1)"),
            ("same(a, b)", "O(log n)", "2 find"),
            ("rollback()", "O(1)", "restaura 1 parent y 1 size"),
            ("rollback_to(t)", "O(k)", "k = uniones que se deshacen"),
            ("memoria", "O(n + m)", "arreglos + pila de m uniones"),
        ]
        col_x = (-6.0, -2.2, -0.2)
        mobs = VGroup()
        for i, (op, cost, why) in enumerate(table):
            y = 1.6 - i * 0.7
            a = txt(op, 28, C_ROOT, mono=True)
            b = txt(cost, 28, GREEN if cost == "O(1)" else C_TEXT, mono=True)
            c = txt(why, 24, C_MUTED)
            for m, x in zip((a, b, c), col_x):
                m.move_to([x + m.width / 2, y, 0])
            mobs.add(VGroup(a, b, c))
        mobs.move_to([0, mobs.get_center()[1], 0])
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in mobs], lag_ratio=0.25), run_time=2.4)
        self.wait(3.0)
        self.play(FadeOut(mobs), run_time=0.6)

        # Alturas medidas en C++ (peor caso de cada estrategia).
        sub = Text("Altura máxima medida en el peor caso (C++)", font_size=30).next_to(heading, DOWN, buff=0.45)
        xs = (-4.2, -0.6, 3.6)
        header = VGroup(txt("n", 28, C_MUTED, mono=True), txt("con unión por tamaño", 26, C_NEW),
                        txt("sin unión por tamaño", 26, C_DEL))
        for m, x in zip(header, xs):
            m.move_to([x, 1.3, 0])
        body = VGroup()
        for i, n in enumerate((16, 128, 1024)):
            r = rows[n]
            cells = VGroup(txt(str(n), 30, mono=True),
                           txt(str(r["por_tamano"]), 30, C_NEW, mono=True),
                           txt(str(r["sin_tamano"]), 30, C_DEL, mono=True))
            for m, x in zip(cells, xs):
                m.move_to([x, 0.5 - i * 0.7, 0])
            body.add(cells)
        note = VGroup(txt("= log₂ n", 24, C_MUTED).move_to([xs[1], -1.75, 0]),
                      txt("= n − 1", 24, C_MUTED).move_to([xs[2], -1.75, 0]))
        self.play(FadeIn(sub), FadeIn(header), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.15) for r in body], lag_ratio=0.3), run_time=1.5)
        self.play(FadeIn(note), run_time=0.6)
        self.wait(3.0)
        self.play(FadeOut(sub), FadeOut(header), FadeOut(body), FadeOut(note), run_time=0.6)

        # Comparación final.
        left = VGroup(Text("DSU con compresión", font_size=30, color=YELLOW),
                      Text("find: α(n) amortizado", font_size=26),
                      Text("rollback: no se puede en O(1)", font_size=26, color=RED_B)).arrange(DOWN, buff=0.35)
        right = VGroup(Text("DSU con rollback", font_size=30, color=YELLOW),
                       Text("find: O(log n)", font_size=26),
                       Text("rollback: O(1)", font_size=26, color=GREEN)).arrange(DOWN, buff=0.35)
        VGroup(left, right).arrange(RIGHT, buff=2.0).move_to(DOWN * 0.1)
        mid_x = (left.get_right()[0] + right.get_left()[0]) / 2
        divider = Line(UP * 1.3, DOWN * 1.3, color=C_MUTED).move_to([mid_x, left.get_center()[1], 0])
        tradeoff = Text("Pagamos log n en find a cambio de poder deshacer en O(1)",
                        font_size=26, color=C_MUTED).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(left), FadeIn(right), Create(divider), run_time=1.0)
        self.wait(1.5)
        self.play(FadeIn(tradeoff), run_time=0.6)
        self.wait(3.0)
        self.play(*[FadeOut(m) for m in (heading, left, right, divider, tradeoff)], run_time=0.6)


class TraceDemo(TraceScene):
    """Anima la traza indicada en la variable de entorno TRACE."""

    def construct(self):
        path = Path(os.environ.get("TRACE", TRACE_DIR / "02_rollback.json"))
        trace = load_trace(path)
        TraceAnimator(self, trace, trace.description).run()
