"""Componentes visuales.

Base tomada del Proyecto 1 (paleta, `txt`, `Link`, `Tag`) más los componentes del DSU:
`ForestNode`, `forest_layout`, `ArrayView` (parent/size) y `HistoryStack`.
Ninguno conoce la lógica del DSU: solo dibujan el estado que reciben de la traza.
"""
from __future__ import annotations

import numpy as np
from manim import *

# Si alguna fuente no está instalada, Pango usa una de reemplazo automáticamente.
FONT_SANS = "Segoe UI"
FONT_MONO = "Consolas"

BG = "#0F1117"
C_TEXT = "#ECECEC"
C_MUTED = "#6B7280"
C_GRID = "#2E3440"
C_NODE = "#58C4DD"
C_NODE_BG = "#1A2130"
C_LINK = "#DDDDDD"
C_NEW = "#83C167"     # unión nueva / resultado verdadero
C_DEL = "#FC6255"     # rollback / resultado falso / error
C_ROOT = "#FFD166"    # raíces (representantes)
C_FIND = "#4ECDC4"    # camino que recorre find
C_MARK = "#E07BE0"    # marcador de unión redundante
C_STACK = "#F4A261"   # pila de historia


def txt(s, size=32, color=C_TEXT, mono=False, **kw):
    return Text(s, font=FONT_MONO if mono else FONT_SANS, font_size=size, color=color, **kw)


class Link(VGroup):
    """Flecha que se redibuja cada frame siguiendo a sus extremos (p. ej. hijo → padre)."""

    def __init__(self, start_fn, end_fn, arc=0.0, color=C_LINK, width=4):
        super().__init__()
        self.start_fn, self.end_fn, self.arc = start_fn, end_fn, arc
        self.link_color, self.stroke_w = color, width
        self._old = None
        self.alpha = ValueTracker(1.0)
        self.arrow = self._make(*self._geometry())
        self.add(self.arrow)
        self.add_updater(lambda m: m._refresh())

    def _geometry(self):
        s, e, a = self.start_fn(), self.end_fn(), self.arc
        if self._old is not None:
            t = self.alpha.get_value()
            old_s, old_e, old_a = self._old
            s, e, a = interpolate(old_s(), s, t), interpolate(old_e(), e, t), interpolate(old_a, a, t)
        return s, e, a

    def _make(self, s, e, a):
        s, e = np.array(s, dtype=float), np.array(e, dtype=float)
        if np.linalg.norm(e - s) < 0.02:
            e = s + RIGHT * 0.02
        if abs(a) < 0.02:
            a = 0
        return Arrow(
            s, e, buff=0, path_arc=a, color=self.link_color, stroke_width=self.stroke_w,
            tip_length=0.18, max_tip_length_to_length_ratio=0.4,
            max_stroke_width_to_length_ratio=20,
        )

    def _refresh(self):
        new = self._make(*self._geometry())
        for old, fresh in zip(self.arrow.family_members_with_points(), new.family_members_with_points()):
            fresh.set_style(**old.get_style(), family=False)
        self.arrow.become(new)

    def retarget(self, end_fn=None, start_fn=None, arc=None):
        self._old = (self.start_fn, self.end_fn, self.arc)
        if end_fn is not None:
            self.end_fn = end_fn
        if start_fn is not None:
            self.start_fn = start_fn
        if arc is not None:
            self.arc = arc
        self.alpha.set_value(0)
        return self.alpha.animate.set_value(1)


class Tag(VGroup):
    """Etiqueta-puntero (x, root, ...) que sigue a su objetivo."""

    def __init__(self, name, color, target=None, below=True, dx=0.0, length=0.45):
        super().__init__()
        self.below, self.dx = below, dx
        direction = DOWN if below else UP
        self.arrow = Arrow(direction * length, ORIGIN, buff=0, color=color, stroke_width=4,
                           tip_length=0.15, max_tip_length_to_length_ratio=0.5)
        self.label = txt(name, 24, color, mono=True).next_to(self.arrow, direction, buff=0.06)
        self.pin = VectorizedPoint(ORIGIN)
        self.add(self.arrow, self.label, self.pin)
        self.target, self._old = target, None
        self.alpha = ValueTracker(1.0)
        self.add_updater(lambda m: m._refresh())
        self._refresh()

    def anchor(self, mob):
        p = mob.get_bottom() + DOWN * 0.08 if self.below else mob.get_top() + UP * 0.08
        return p + RIGHT * self.dx

    def _refresh(self):
        if self.target is None:
            return
        p = self.anchor(self.target)
        if self._old is not None:
            p = interpolate(self.anchor(self._old), p, self.alpha.get_value())
        self.shift(p - self.pin.get_center())

    def retarget(self, mob):
        self._old, self.target = self.target, mob
        self.alpha.set_value(0)
        return self.alpha.animate.set_value(1)


# --------------------------------------------------------------------------- DSU


def edge_points(child, parent):
    """Extremos de la flecha hijo → padre, sobre el borde de cada círculo."""
    c, p = child.get_center(), parent.get_center()
    d = p - c
    length = np.linalg.norm(d)
    u = d / length if length > 1e-6 else UP
    return c + u * child.radius, p - u * parent.radius


class ForestNode(VGroup):
    """Un elemento del DSU: círculo con su etiqueta. Las raíces llevan borde dorado."""

    def __init__(self, label, radius=0.3):
        super().__init__()
        self.radius = radius
        self.circle = Circle(radius=radius).set_fill(C_NODE_BG, 1).set_stroke(C_NODE, 3)
        self.label = txt(str(label), max(14, int(radius * 85)), mono=True).move_to(self.circle)
        if self.label.width > radius * 1.5:
            self.label.scale_to_fit_width(radius * 1.5)
        self.add(self.circle, self.label)

    def style_root(self, is_root):
        self.circle.set_stroke(C_ROOT if is_root else C_NODE, 4 if is_root else 3)
        return self


def forest_layout(parent, center_x, top_y, unit, level_h, gap=0.6):
    """Posición de cada nodo para dibujar el bosque descrito por `parent`.

    Cada árbol se dibuja con la raíz arriba; un nodo queda centrado sobre sus hijos
    (ordenados por índice) y los árboles van de izquierda a derecha según su raíz.
    """
    n = len(parent)
    children = [[] for _ in range(n)]
    roots = []
    for v, p in enumerate(parent):
        if p == v:
            roots.append(v)
        else:
            children[p].append(v)

    width = [0.0] * n

    def measure(v):
        width[v] = max(1.0, sum(measure(c) for c in children[v]))
        return width[v]

    for r in roots:
        measure(r)

    slot, depth = [0.0] * n, [0] * n

    def place(v, left, d):
        depth[v] = d
        if not children[v]:
            slot[v] = left + 0.5
            return
        cur = left
        for c in children[v]:
            place(c, cur, d + 1)
            cur += width[c]
        slot[v] = (slot[children[v][0]] + slot[children[v][-1]]) / 2

    cur = 0.0
    for r in roots:
        place(r, cur, 0)
        cur += width[r] + gap
    total = cur - gap if roots else 0.0
    x0 = center_x - total * unit / 2
    return {v: np.array([x0 + slot[v] * unit, top_y - depth[v] * level_h, 0.0]) for v in range(n)}


class ArrayView(VGroup):
    """Fila de celdas con el contenido de un arreglo (parent o size)."""

    def __init__(self, name, values, cell=0.55, show_index=False):
        super().__init__()
        self.values = list(values)
        self.font = max(14, int(cell * 46))
        self.cells = VGroup(*[
            Square(cell).set_stroke(C_GRID, 2).set_fill(C_NODE_BG, 1) for _ in values
        ]).arrange(RIGHT, buff=0)
        self.vals = VGroup(*[
            txt(str(v), self.font, mono=True).move_to(c) for v, c in zip(values, self.cells)
        ])
        self.name = txt(name, 24, C_MUTED, mono=True).next_to(self.cells, LEFT, buff=0.25)
        self.index = VGroup(*[
            txt(str(i), 16, C_MUTED, mono=True).next_to(c, UP, buff=0.08) for i, c in enumerate(self.cells)
        ]) if show_index else VGroup()
        self.colored = set()
        self.add(self.cells, self.vals, self.name, self.index)

    def update_to(self, values, color):
        """Animaciones para pasar a `values`; las celdas que cambian quedan resaltadas."""
        anims = []
        for i, (old, new) in enumerate(zip(self.values, values)):
            if old != new:
                fresh = txt(str(new), self.font, color, mono=True).move_to(self.cells[i])
                anims += [Transform(self.vals[i], fresh), Indicate(self.cells[i], color=color, scale_factor=1.12)]
                self.colored.add(i)
            elif i in self.colored:
                anims.append(self.vals[i].animate.set_color(C_TEXT))
                self.colored.discard(i)
        self.values = list(values)
        return anims

    def shown_values(self):
        return list(self.values)


class HistoryStack(VGroup):
    """Pila de cambios: cada unite apila (hijo → raíz) o un marcador vacío."""

    def __init__(self, capacity, height=5.0, width=1.9):
        super().__init__()
        self.w = width
        self.entry_h = min(0.5, (height - 0.2) / max(capacity, 1))
        h = height
        self.frame = VGroup(
            Line([-width / 2, h, 0], [-width / 2, 0, 0]),
            Line([-width / 2, 0, 0], [width / 2, 0, 0]),
            Line([width / 2, 0, 0], [width / 2, h, 0]),
        ).set_stroke(C_MUTED, 3)
        self.title = txt("history", 24, C_STACK, mono=True).next_to(self.frame, UP, buff=0.15)
        self.entries = []
        self.add(self.frame, self.title)

    @property
    def bottom(self):
        return self.frame[1].get_center()

    def level_y(self, k):
        """Altura del borde inferior de la entrada número k (0 = fondo)."""
        return self.bottom[1] + 0.1 + self.entry_h * k

    def make_entry(self, child, root, labels):
        marker = child < 0
        color = C_MARK if marker else C_STACK
        box = RoundedRectangle(corner_radius=0.06, width=self.w - 0.24, height=self.entry_h - 0.07)
        box.set_fill(C_NODE_BG, 1).set_stroke(color, 2.5)
        text = "∅ redundante" if marker else f"{labels[child]} → {labels[root]}"
        label = txt(text, max(14, int(self.entry_h * 48)), color, mono=True)
        if label.width > box.width - 0.15:
            label.scale_to_fit_width(box.width - 0.15)
        entry = VGroup(box, label.move_to(box))
        k = len(self.entries)
        entry.move_to([self.bottom[0], self.level_y(k) + self.entry_h / 2, 0])
        return entry

    def snapshot_line(self, t):
        y = self.level_y(t) - 0.035
        x = self.bottom[0]
        line = DashedLine([x - self.w / 2 - 0.15, y, 0], [x + self.w / 2 + 0.15, y, 0], dash_length=0.1)
        line.set_stroke(C_ROOT, 3)
        tag = txt(f"t={t}", 20, C_ROOT, mono=True).next_to(line, LEFT, buff=0.1)
        return VGroup(line, tag)
