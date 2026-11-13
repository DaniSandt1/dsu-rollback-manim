"""Reproduce una traza del DSU (generada en C++) como animación de Manim.

`TraceAnimator` recorre los eventos en orden y, para cada uno, anima el cambio que la
implementación real registró. No calcula nada del DSU: las flechas, las posiciones de
los árboles, los arreglos y la pila salen del `state` de cada evento. Después de cada
evento se verifica que lo dibujado coincida con ese estado.
"""
from __future__ import annotations

from manim import *

from components import *
from trace_loader import State, Trace

# Zonas de la pantalla
FOREST_X = (-6.4, 3.6)
FOREST_TOP = 1.75
FOREST_BOTTOM = -0.95
ARRAY_PARENT_Y = -2.05
ARRAY_SIZE_Y = -2.75
STACK_X = 5.45
STACK_BOTTOM = -3.3
STACK_HEIGHT = 4.9


class TraceAnimator:
    def __init__(self, scene: Scene, trace: Trace, title: str, speed: float = 1.0):
        self.s, self.trace, self.title, self.speed = scene, trace, title, speed
        self.labels = trace.labels()
        self.n = trace.n
        states = [ev.state for ev in trace.events]
        self.max_depth = max(st.depth(x) for st in states for x in range(self.n))
        self.capacity = max(len(st.history) for st in states)

        width = FOREST_X[1] - FOREST_X[0]
        self.unit = min(1.0, width / (self.n + 0.6 * max(self.n - 1, 0)))
        self.level_h = min(1.05, (FOREST_TOP - FOREST_BOTTOM) / max(self.max_depth, 1))
        self.radius = min(0.3, self.unit * 0.4)

        self.state: State = trace.initial
        self.arrows: dict[int, Link] = {}   # hijo -> flecha hacia su padre
        self.parent_of: dict[int, int] = {}
        self.lit: set[int] = set()          # flechas resaltadas por un find
        self.rings: list[Mobject] = []
        self.ring = None                    # anillo del find en curso
        self.caption = None
        self.op_text = None
        self.result_text = None
        self.snapshots: dict[int, VGroup] = {}
        self.in_rollback_to = False

    # ------------------------------------------------------------- utilidades

    def play(self, *anims, rt=0.6):
        anims = [a for a in anims if a is not None]
        if anims:
            self.s.play(*anims, run_time=rt / self.speed)

    def wait(self, t):
        self.s.wait(t / self.speed)

    def lab(self, i):
        return self.labels[i]

    def positions(self, state):
        cx = (FOREST_X[0] + FOREST_X[1]) / 2
        return forest_layout(state.parent, cx, FOREST_TOP, self.unit, self.level_h)

    def make_link(self, child, parent):
        a, b = self.nodes[child], self.nodes[parent]
        return Link(lambda: edge_points(a, b)[0], lambda: edge_points(a, b)[1], width=3.5)

    def relayout(self, state, extra=(), rt=0.9):
        """Mueve los nodos a la posición que les corresponde en `state`."""
        pos = self.positions(state)
        anims = list(extra)
        for v, node in enumerate(self.nodes):
            node.generate_target()
            node.target.move_to(pos[v])
            node.target.style_root(state.parent[v] == v)
            anims.append(MoveToTarget(node))
        self.play(*anims, rt=rt)

    def set_op(self, text, color=C_TEXT):
        new = txt(text, 30, color, mono=True)
        new.move_to([FOREST_X[0] + new.width / 2, 2.6, 0])
        anims = [FadeIn(new, shift=UP * 0.15)]
        if self.op_text is not None:
            anims.append(FadeOut(self.op_text, shift=UP * 0.15))
        if self.result_text is not None:
            anims.append(FadeOut(self.result_text))
            self.result_text = None
        self.op_text = new
        self.play(*anims, rt=0.35)

    def set_result(self, text, color):
        new = txt(text, 30, color, mono=True).next_to(self.op_text, RIGHT, buff=0.35)
        anims = [FadeIn(new, scale=1.2)]
        if self.result_text is not None:
            anims.append(FadeOut(self.result_text))
        self.result_text = new
        self.play(*anims, rt=0.4)

    def clear_find(self):
        anims = [FadeOut(r) for r in self.rings]
        if self.ring is not None:
            anims.append(FadeOut(self.ring))
        anims += [self.arrows[c].animate.set_color(C_LINK) for c in self.lit if c in self.arrows]
        self.rings, self.ring, self.lit = [], None, set()
        self.play(*anims, rt=0.3)

    def check(self, state: State):
        """Lo dibujado debe ser exactamente el estado registrado por C++."""
        expected = {v: p for v, p in enumerate(state.parent) if p != v}
        assert self.parent_of == expected, f"flechas {self.parent_of} != parent {expected}"
        assert set(self.arrows) == set(expected), "flechas desfasadas"
        assert self.parent_arr.shown_values() == list(state.parent), "arreglo parent desfasado"
        assert self.size_arr.shown_values() == list(state.size), "arreglo size desfasado"
        assert len(self.stack.entries) == len(state.history), "pila desfasada"

    # ------------------------------------------------------------- armado

    def build(self):
        st = self.trace.initial
        self.header = txt(self.title, 34).to_edge(UP, buff=0.3)
        source = txt(f"traza: trace/{self.trace.scenario}.json  ·  generada por escenarios.cpp",
                     16, C_MUTED, mono=True).to_corner(DL, buff=0.25)

        pos = self.positions(st)
        self.nodes = [ForestNode(self.lab(v), self.radius).move_to(pos[v]).style_root(True)
                      for v in range(self.n)]

        cell = min(0.55, 7.2 / max(self.n, 1))
        self.parent_arr = ArrayView("parent", st.parent, cell=cell, show_index=True)
        self.size_arr = ArrayView("size", st.size, cell=cell)
        cx = (FOREST_X[0] + FOREST_X[1]) / 2 + 0.4
        for arr, y in ((self.parent_arr, ARRAY_PARENT_Y), (self.size_arr, ARRAY_SIZE_Y)):
            c = arr.cells.get_center()
            arr.shift([cx - c[0], y - c[1], 0])

        self.stack = HistoryStack(self.capacity, height=STACK_HEIGHT)
        self.stack.shift(np.array([STACK_X, STACK_BOTTOM, 0]) - self.stack.bottom)

        self.play(FadeIn(self.header, shift=DOWN * 0.2), FadeIn(source), rt=0.8)
        self.play(LaggedStart(*[GrowFromCenter(nd) for nd in self.nodes], lag_ratio=0.08), rt=1.0)
        self.play(FadeIn(self.parent_arr), FadeIn(self.size_arr), FadeIn(self.stack), rt=0.8)
        self.check(st)

    # ------------------------------------------------------------- eventos

    def run(self, tail_wait=1.5):
        self.build()
        for ev in self.trace.events[1:]:
            handler = getattr(self, "on_" + ev.op, None)
            if handler is None:
                raise ValueError(f"evento sin animación: {ev.op}")
            handler(ev)
            self.state = ev.state
            self.check(ev.state)
        self.wait(tail_wait)

    def on_mark(self, ev):
        new = txt(ev["text"], 26, C_MUTED).next_to(self.header, DOWN, buff=0.12)
        anims = [FadeIn(new)]
        if self.caption is not None:
            anims.append(FadeOut(self.caption))
        self.caption = new
        self.play(*anims, rt=0.5)
        self.wait(1.0)

    def on_unite_call(self, ev):
        self.set_op(f"unite({self.lab(ev['a'])}, {self.lab(ev['b'])})")

    def on_same_call(self, ev):
        self.set_op(f"same({self.lab(ev['a'])}, {self.lab(ev['b'])})")

    def on_snapshot(self, ev):
        t = ev["t"]
        self.set_op("t = snapshot()")
        self.set_result(f"→ {t}", C_ROOT)
        line = self.stack.snapshot_line(t)
        self.snapshots[t] = line
        self.play(Create(line), rt=0.6)
        self.wait(0.5)

    def on_find_step(self, ev):
        a, b = self.nodes[ev["from"]], self.nodes[ev["to"]]
        if self.ring is None:
            self.ring = Circle(radius=self.radius + 0.09).set_stroke(C_FIND, 5).move_to(a)
            self.play(Create(self.ring), rt=0.3)
        self.lit.add(ev["from"])
        self.play(self.ring.animate.move_to(b), self.arrows[ev["from"]].animate.set_color(C_FIND), rt=0.45)

    def on_find_root(self, ev):
        node = self.nodes[ev["root"]]
        if self.ring is None:
            self.ring = Circle(radius=self.radius + 0.09).set_stroke(C_ROOT, 5).move_to(node)
            self.play(Create(self.ring), rt=0.3)
        else:
            self.play(self.ring.animate.set_stroke(C_ROOT), rt=0.25)
        self.rings.append(self.ring)
        self.ring = None

    def on_push(self, ev):
        entry = self.stack.make_entry(ev["child"], ev["root"], self.labels)
        self.stack.entries.append(entry)
        self.play(FadeIn(entry, shift=DOWN * 0.4), rt=0.5)

    def on_link(self, ev):
        child, root = ev["child"], ev["root"]
        self.clear_find()
        link = self.make_link(child, root)
        self.arrows[child], self.parent_of[child] = link, root
        self.s.add(link)
        self.play(Create(link), rt=0.5)
        st = ev.state
        self.relayout(st, extra=self.parent_arr.update_to(st.parent, C_NEW) + self.size_arr.update_to(st.size, C_NEW))

    def on_unite_redundant(self, ev):
        self.set_result("ya están juntos", C_MARK)
        self.clear_find()

    def on_same_result(self, ev):
        ok = ev["result"]
        self.set_result("→ true" if ok else "→ false", C_NEW if ok else C_DEL)
        self.wait(0.6)
        self.clear_find()

    def on_rollback_call(self, ev):
        if not self.in_rollback_to:
            self.set_op("rollback()", C_DEL)

    def on_rollback_to_call(self, ev):
        self.in_rollback_to = True
        self.set_op(f"rollback_to({ev['t']})", C_DEL)

    def on_rollback_to_done(self, ev):
        self.in_rollback_to = False
        self.wait(0.4)
        line = self.snapshots.pop(ev["t"], None)
        if line is not None:
            self.play(FadeOut(line), rt=0.4)

    def on_rollback_empty(self, ev):
        msg = txt("nada que deshacer", 22, C_DEL).next_to(self.stack.frame, UP, buff=0.6)
        self.play(FadeIn(msg), Wiggle(self.stack.frame), rt=0.8)
        self.play(FadeOut(msg), rt=0.4)

    def on_pop(self, ev):
        entry = self.stack.entries.pop()
        self.play(entry[0].animate.set_stroke(C_DEL), entry[1].animate.set_color(C_DEL), rt=0.3)
        self.play(FadeOut(entry, shift=RIGHT * 0.6), rt=0.45)

    def on_unlink(self, ev):
        child = ev["child"]
        link = self.arrows.pop(child)
        self.parent_of.pop(child)
        self.lit.discard(child)
        link.clear_updaters()
        self.play(FadeOut(link), rt=0.45)
        st = ev.state
        self.relayout(st, extra=self.parent_arr.update_to(st.parent, C_DEL) + self.size_arr.update_to(st.size, C_DEL))
