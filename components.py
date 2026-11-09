"""Componentes visuales reutilizables (base tomada del Proyecto 1: listas enlazadas).

Por ahora: paleta, helper de texto, `Link` (flecha que sigue a sus extremos) y `Tag`
(etiqueta-puntero). Los componentes propios del DSU (nodo del bosque, arreglos
parent/size y pila de historia) se agregan en la siguiente etapa.
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
