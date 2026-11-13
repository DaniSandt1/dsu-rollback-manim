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
