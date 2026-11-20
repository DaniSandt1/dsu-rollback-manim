# DSU con rollback, animado con Manim

Proyecto 2 del curso **CS2023 – Algoritmos y Estructuras de Datos** (UTEC, 2026-2): un video
educativo sobre la **Disjoint Set Union con rollback** (Union-Find que puede deshacer uniones).
La estructura está implementada en **C++** y la animación (Python + [Manim Community](https://docs.manim.community/))
se genera a partir de la **traza real** de esa implementación.

**Integrantes:** Daniel Sandoval · Percy Castro

| | |
|---|---|
| **Video final e informe** | [Carpeta en Google Drive](https://drive.google.com/drive/u/0/folders/1CFkgbC1qCD-Gbf3nazMhq7Ty5xOcuhxU) |

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

**Usos en la práctica:** algoritmos de *backtracking* que prueban uniones y las deshacen,
**conectividad dinámica offline** (aristas que aparecen y desaparecen, resuelta con un árbol de
segmentos sobre el tiempo + DSU con rollback), verificar si un grafo sigue siendo **bipartito**
mientras se prueban aristas, y en general cualquier operación de «deshacer» sobre grupos.

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
components.py                  componentes visuales: nodo, bosque, arreglos parent/size, pila de historia
animator.py                    TraceAnimator: convierte cada evento de la traza en animaciones
dsu_video.py                   escenas del video
video_completo.py              renderiza las seis escenas en orden y las une en un solo MP4
guion.md                       guion de narración con marcas de tiempo
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

## Generar el video completo

```bash
python video_completo.py                 # renderiza las 6 escenas a 1080p60 y las une
python video_completo.py --calidad l     # vista previa rápida (480p)
python video_completo.py --solo-unir     # solo une escenas ya renderizadas
```

El resultado queda en `media/videos/DSU_con_rollback_1080p60.mp4` (MP4, H.264, 1920×1080, 60 fps,
≈ 4:37). Las escenas se renderizan una por una y se unen sin recodificar; el script verifica que la
duración final coincida con la suma de las escenas. Los tiempos de `guion.md` corresponden a este video
(la vista previa a 480p dura un poco más, ≈ 4:45, porque a 15 fps cada animación se redondea a
cuadros enteros).

## Renderizar una escena

| Escena | Contenido | Traza | Duración aprox. |
|---|---|---|---|
| `S00Motivacion` | título, autores y red de computadoras | `00_motivacion` | 0:20 |
| `S01Operaciones` | ADT, `find` / `unite` / `same`, unión por tamaño | `01_union_por_tamano` | 1:00 |
| `S02Rollback` | `snapshot`, `rollback_to`, `rollback` | `02_rollback` | 1:23 |
| `S03SinCompresion` | por qué no se comprimen caminos | `07_sin_compresion` | 0:47 |
| `S04CasoBorde` | unión redundante (con y sin marcador) y pila vacía | `04`, `03`, `05` | 0:46 |
| `S05Complejidad` | tabla de costos y alturas medidas en C++ | `medidas/alturas.json` | 0:20 |

```bash
# Una escena: vista previa (480p) o alta resolución (1080p60)
manim -pql dsu_video.py S03SinCompresion
manim -qh  dsu_video.py S03SinCompresion

# Cualquier otra traza con el mismo animador (PowerShell: $env:TRACE="trace/...json"; manim ...)
TRACE=trace/06_peor_caso_altura.json manim -pql dsu_video.py TraceDemo
```

El animador no calcula nada del DSU: después de cada evento verifica que las flechas, los
arreglos y la pila dibujados coincidan exactamente con el estado que registró el programa C++.

### Escenarios

| Archivo | Qué muestra |
|---|---|
| `00_motivacion` | red de computadoras: probar una conexión y deshacerla |
| `01_union_por_tamano` | `find`, `unite`, `same`, unión por tamaño |
| `02_rollback` | `snapshot`, `rollback_to`, `rollback` |
| `03_borde_redundante` | unión redundante → marcador en la pila |
| `04_borde_sin_marcador` | el error típico de no apilarla |
| `05_borde_pila_vacia` | `rollback()` sin historia |
| `06_peor_caso_altura` | uniones balanceadas: altura exactamente log₂ 16 = 4 |
| `07_sin_compresion` | `find` con compresión + `rollback`: la estructura queda inconsistente |
| `medidas/alturas.json` | altura máxima medida en el peor caso, con y sin unión por tamaño (n = 2 … 1024) |

En las trazas de error (`04`, `07`) el programa C++ ejecuta en paralelo la versión correcta y
guarda sus respuestas en `meta.expected_same`; el video las usa para marcar "✗ correcto: …".
`find_with_compression` existe solo para esa demostración: la estructura real nunca comprime.

## Referencias

- [cp-algorithms: Disjoint Set Union](https://cp-algorithms.com/data_structures/disjoint_set_union.html)
- [3Blue1Brown](https://www.3blue1brown.com/) · [ManimCommunity/manim](https://github.com/ManimCommunity/manim)
