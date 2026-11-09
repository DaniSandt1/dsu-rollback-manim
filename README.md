# DSU con rollback, animado con Manim

Proyecto 2 del curso **CS2023 – Algoritmos y Estructuras de Datos** (UTEC, 2026-2): un video
educativo sobre la **Disjoint Set Union con rollback** (Union-Find que puede deshacer uniones).
La estructura está implementada en **C++** y la animación (Python + [Manim Community](https://docs.manim.community/))
se genera a partir de la **traza real** de esa implementación.

**Integrantes:** Daniel Sandoval · Percy Castro

> Estado: en desarrollo. Ya están la implementación en C++, los tests y la exportación de trazas.
> La animación se está construyendo (ver [Hoja de ruta](#hoja-de-ruta)).

## La estructura de datos

**ADT: conjuntos disjuntos (Union-Find)** con una operación extra para volver atrás en el tiempo.

| Operación          | Qué hace                                                     | Costo     |
|--------------------|--------------------------------------------------------------|-----------|
| `find(x)`          | representante (raíz) del conjunto de `x`                     | O(log n)  |
| `unite(a, b)`      | une los conjuntos de `a` y `b`; apila el cambio en la historia | O(log n) (el enlace en sí es O(1)) |
| `same(a, b)`       | ¿`a` y `b` están en el mismo conjunto?                       | O(log n)  |
| `rollback()`       | deshace el último `unite`                                    | O(1)      |
| `snapshot()` / `rollback_to(t)` | guarda el momento actual / vuelve a él          | O(1) / O(k) para k uniones deshechas |

Decisiones clave:

- **Unión por tamaño:** el árbol más chico se cuelga del más grande, así la altura es ≤ log₂ n.
- **Sin compresión de caminos:** `find` no modifica nada. Cada unión cambia exactamente un
  `parent` y un `size`, por eso deshacerla cuesta O(1).
- **Uniones redundantes:** si `a` y `b` ya estaban juntos, igual se apila un *marcador* vacío.
  Si no, `rollback()` desharía una unión anterior por error (ver el escenario `04_borde_sin_marcador`).

## Cómo funciona el proyecto

```
C++ (DSURollback + Tracer)  ──►  trace/*.json  ──►  Python/Manim (lee la traza y anima)
```

Cada operación del DSU emite eventos (`find_step`, `push`, `link`, `pop`, `unlink`, …) con una foto
completa del estado (`parent`, `size`, `history`). La animación no recalcula nada: solo dibuja lo que
registró la implementación en C++.

## Estructura del repositorio

```
CMakeLists.txt
cpp/include/dsu_rollback.hpp   la estructura (header-only)
cpp/include/tracer.hpp         registro de eventos y exportación a JSON
cpp/src/escenarios.cpp         escenarios del video → trace/*.json
cpp/tests/tests.cpp            tests unitarios + prueba aleatoria contra fuerza bruta (BFS)
trace/                         trazas generadas (versionadas, para renderizar sin compilar)
trace_loader.py                lee y valida las trazas
components.py                  componentes visuales de Manim
```

## Software requerido

- Compilador C++17 y **CMake ≥ 3.16** (probado con MSVC / Visual Studio 2026; también sirve g++ o clang++).
- Python 3.10 o superior y Manim Community v0.21 (`pip install -r requirements.txt`).
- No hace falta LaTeX.

## Compilar, probar y generar las trazas

```bash
cmake -S . -B build
cmake --build build --config Release

# tests
ctest --test-dir build -C Release --output-on-failure
#   o directamente: build/Release/dsu_tests     (en Linux: build/dsu_tests)

# trazas para la animación
build/Release/escenarios trace                  # (en Linux: build/escenarios trace)

# validar las trazas desde Python
python trace_loader.py
```

### Escenarios

| Archivo | Qué muestra |
|---|---|
| `00_motivacion` | red de ciudades: probar un cable y deshacerlo |
| `01_union_por_tamano` | `find`, `unite`, `same`, unión por tamaño |
| `02_rollback` | `snapshot`, `rollback_to`, `rollback` |
| `03_borde_redundante` | unión redundante → marcador en la pila |
| `04_borde_sin_marcador` | el error típico de no apilarla |
| `05_borde_pila_vacia` | `rollback()` sin historia |
| `06_peor_caso_altura` | uniones balanceadas: altura exactamente log₂ 16 = 4 |

## Hoja de ruta

- [x] DSU con rollback en C++, tests y exportación de trazas a JSON
- [ ] Componentes de Manim: bosque, arreglos `parent`/`size`, pila de historia
- [ ] Escenas: motivación, concepto/ADT, por qué no compresión, rollback, casos borde, complejidad, créditos
- [ ] Guion de narración y render final (1080p60, ≤ 5 min)
- [ ] Informe (PDF, ≤ 4 páginas)

## Referencias

- [cp-algorithms: Disjoint Set Union](https://cp-algorithms.com/data_structures/disjoint_set_union.html)
- [3Blue1Brown](https://www.3blue1brown.com/) · [ManimCommunity/manim](https://github.com/ManimCommunity/manim)
