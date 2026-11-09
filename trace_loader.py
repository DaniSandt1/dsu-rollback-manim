"""Lectura y validación de las trazas JSON que genera el programa C++ (`escenarios`).

La animación NO reimplementa el DSU: solo lee los eventos y el estado que registró
la implementación real. Este módulo verifica que cada traza sea coherente antes de
animarla (invariantes del bosque y efecto de cada evento sobre el estado).

Uso:  python trace_loader.py trace/*.json
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

FORMAT = "dsu-rollback-trace/1"


@dataclass(frozen=True)
class State:
    parent: tuple[int, ...]
    size: tuple[int, ...]
    history: tuple[tuple[int, int], ...]
    components: int

    @property
    def n(self) -> int:
        return len(self.parent)

    def roots(self) -> list[int]:
        return [i for i, p in enumerate(self.parent) if p == i]

    def children(self, x: int) -> list[int]:
        return [i for i, p in enumerate(self.parent) if p == x and i != x]

    def root_of(self, x: int) -> int:
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def depth(self, x: int) -> int:
        k = 0
        while self.parent[x] != x:
            x, k = self.parent[x], k + 1
        return k


@dataclass(frozen=True)
class Event:
    id: int
    op: str
    data: dict
    state: State

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)


@dataclass
class Trace:
    scenario: str
    description: str
    meta: dict
    events: list[Event] = field(default_factory=list)

    @property
    def n(self) -> int:
        return self.events[0].state.n if self.events else 0

    @property
    def initial(self) -> State:
        return self.events[0].state

    @property
    def final(self) -> State:
        return self.events[-1].state

    def labels(self) -> list[str]:
        return self.meta.get("labels") or [str(i) for i in range(self.n)]


def _state(d: dict) -> State:
    return State(
        parent=tuple(d["parent"]),
        size=tuple(d["size"]),
        history=tuple(tuple(h) for h in d["history"]),
        components=d["components"],
    )


def load_trace(path: str | Path) -> Trace:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("format") != FORMAT:
        raise ValueError(f"{path}: formato desconocido {raw.get('format')!r}")
    trace = Trace(raw["scenario"], raw.get("description", ""), raw.get("meta", {}))
    for e in raw["events"]:
        data = {k: v for k, v in e.items() if k not in ("id", "op", "state")}
        trace.events.append(Event(e["id"], e["op"], data, _state(e["state"])))
    validate(trace)
    return trace


class TraceError(ValueError):
    pass


def _check(cond: bool, ev: Event, msg: str):
    if not cond:
        raise TraceError(f"evento {ev.id} ({ev.op}): {msg}")


def _check_forest(s: State, ev: Event):
    n = s.n
    _check(len(s.size) == n, ev, "parent y size de distinto largo")
    roots = s.roots()
    _check(s.components == len(roots), ev, "components no coincide con el número de raíces")
    for x in range(n):
        _check(0 <= s.parent[x] < n, ev, f"parent[{x}] fuera de rango")
        _check(s.depth(x) < n, ev, "hay un ciclo en parent")  # depth termina solo si no hay ciclos
    for r in roots:
        members = sum(1 for x in range(n) if s.root_of(x) == r)
        _check(s.size[r] == members, ev, f"size[{r}] = {s.size[r]} pero el conjunto tiene {members}")


def validate(trace: Trace) -> None:
    """Revisa invariantes y que cada evento produzca el cambio de estado esperado."""
    _check(bool(trace.events) and trace.events[0].op == "init", trace.events[0], "la traza debe empezar con init")
    prev = None
    for ev in trace.events:
        s = ev.state
        if s.n:
            _check_forest(s, ev)
        if prev is not None:
            _check(s.n == prev.n, ev, "cambió la cantidad de elementos")
            changed = s.parent != prev.parent or s.size != prev.size
            if ev.op == "link":
                c, r = ev["child"], ev["root"]
                _check(prev.parent[c] == c and prev.parent[r] == r, ev, "link entre nodos que no eran raíces")
                _check(s.parent[c] == r and s.size[r] == prev.size[r] + prev.size[c], ev, "link mal aplicado")
                _check(prev.size[r] >= prev.size[c], ev, "no se respetó la unión por tamaño")
            elif ev.op == "unlink":
                c, r = ev["child"], ev["root"]
                _check(prev.parent[c] == r and s.parent[c] == c, ev, "unlink mal aplicado")
                _check(s.size[r] == prev.size[r] - s.size[c], ev, "size no se restauró")
            elif ev.op == "push":
                _check(len(s.history) == len(prev.history) + 1, ev, "push no agregó a la historia")
                _check(list(s.history[-1]) == [ev["child"], ev["root"]], ev, "push registró otro cambio")
            elif ev.op == "pop":
                _check(len(s.history) == len(prev.history) - 1, ev, "pop no quitó de la historia")
                _check(list(prev.history[-1]) == [ev["child"], ev["root"]], ev, "pop sacó otro cambio")
            else:
                _check(not changed and s.history == prev.history, ev, "este evento no debería cambiar el estado")
            if ev.op == "find_step":
                _check(s.parent[ev["from"]] == ev["to"], ev, "find_step no sigue a parent")
        prev = s


def summary(trace: Trace) -> str:
    ops: dict[str, int] = {}
    for ev in trace.events:
        ops[ev.op] = ops.get(ev.op, 0) + 1
    f = trace.final
    lines = [
        f"{trace.scenario}: {trace.description}",
        f"  n={trace.n}  eventos={len(trace.events)}  componentes finales={f.components}  "
        f"historia final={len(f.history)}  altura máx={max((f.depth(x) for x in range(f.n)), default=0)}",
        "  " + "  ".join(f"{k}×{v}" for k, v in sorted(ops.items())),
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    paths = argv or sorted(str(p) for p in (Path(__file__).parent / "trace").glob("*.json"))
    if not paths:
        print("No hay trazas. Generarlas con:  build/Release/escenarios trace")
        return 1
    bad = 0
    for p in paths:
        try:
            print(summary(load_trace(p)))
            print("  OK\n")
        except (TraceError, ValueError, KeyError) as e:
            print(f"{p}: ERROR {e}\n")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
