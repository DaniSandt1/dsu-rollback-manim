# Guion de narración — DSU con rollback (≈ 4:37)

**Narradores:** **Daniel Sandoval** (secciones 00–02, de 0:00 a 2:08) ·
**Percy Castro** (secciones 02–05, de 2:08 a 4:37). Daniel narra ≈ 2 min 08 s y Percy ≈ 2 min 29 s
(≈ 540 palabras en total).

**Usos en la práctica** (lo pide el enunciado): la narración los menciona en 1:52 (backtracking y
grafos bipartitos), 2:21 (operaciones de «deshacer» en juegos o editores) y 2:32 (conectividad
dinámica offline).

Los tiempos corresponden al video completo a 1080p60 (`DSU_con_rollback_1080p60.mp4`, 4:36.6), que une
las escenas en este orden: `S00Motivacion`, `S01Operaciones`, `S02Rollback`, `S03SinCompresion`,
`S04CasoBorde` y `S05Complejidad`. Cada bloque empieza cuando aparece en pantalla el texto indicado
entre corchetes. El ritmo previsto es tranquilo (≈ 2,5 palabras por segundo); si alguien habla más
rápido, basta con dejar pausas: la animación ya tiene el tiempo reservado.

---

# DANIEL SANDOVAL (0:00 – 2:08)

## 00 · Título y motivación — 0:00

**0:00** [DSU con Rollback · Daniel Sandoval · Percy Castro]
> Esto es el DSU con rollback.

**0:03** [Una red de computadoras · Cada equipo comienza aislado]
> Imaginemos seis computadoras, todas aisladas.

**0:05** [Conectamos A y B]
> Conectamos A con B…

**0:07** [Conectamos C y D]
> …y C con D.

**0:09** [Guardamos este estado]
> Guardamos este estado…

**0:11** [Conectamos B y C]
> …y probamos B con C.

**0:13** [Rollback: volvemos al estado guardado]
> Si no nos sirve, lo deshacemos.

**0:16** [¿Cómo combinar grupos y volver a un estado anterior?]
> ¿Cómo unir grupos y volver atrás sin rehacer todo?

## 01 · Conjuntos disjuntos y operaciones — 0:20

**0:20** [Conjuntos disjuntos · Cada elemento pertenece a un único conjunto]
> La base es el DSU: conjuntos disjuntos.

**0:22** [En una red, cada conjunto representa una componente conectada]
> Cada conjunto es una componente de la red.

**0:25** [find(x) · unite(a, b) · same(a, b)]
> Sus operaciones: `find`, `unite` y `same`.

**0:30** [Operaciones y unión por tamaño]
> Cada conjunto es un árbol cuya raíz lo representa.

**0:34** [unite(0, 1)]
> `unite` busca ambas raíces y cuelga una de la otra.

**0:38** [Aparece 1 → 0 en la pila history]
> 1 apunta a 0, el tamaño sube a 2 y la pila lo anota.

**0:43** [unite(2, 3)]
> Lo mismo con 2 y 3…

**0:46** [unite(0, 2)]
> …y unimos los dos grupos.

**0:50** [unite(4, 5)]
> Del otro lado, 4, 5 y 6.

**0:57** [Unión por tamaño: el árbol más chico se cuelga del más grande]
> Al unir, el árbol más chico se cuelga del más grande.

**1:02** [Aparece 4 → 0 en la pila]
> 4, con tres elementos, se cuelga de 0, que tiene cuatro: así los árboles quedan bajos.

**1:09** [same(1, 7) → false]
> 1 y 7 tienen raíces distintas: no están conectados.

**1:15** [same(5, 1) → true]
> 5 y 1 comparten la raíz 0: están conectados.

## 02 · Snapshot y rollback — 1:20

**1:20** [Guardar y recuperar un estado]
> Ahora, lo nuevo.

**1:21** [Cada unión registra un cambio en la pila]
> Cada unión deja un registro en una pila…

**1:23** [snapshot() guarda la posición actual]
> …`snapshot` recuerda su altura…

**1:25** [rollback() deshace el cambio más reciente]
> …y `rollback` deshace el último cambio.

**1:31** [Aparece 1 → 0 en la pila]
> Unimos 0 y 1: la pila guarda qué raíz se colgó de cuál.

**1:37** [unite(2, 3)]
> Luego 2 con 3, y ambos grupos.

**1:45** [Guardamos el momento actual]
> Tomamos un snapshot: es solo el tamaño de la pila, 3.

**1:52** [unite(4, 5)]
> Hacemos tres uniones temporales, como en un backtracking: probar y, si no sirve, deshacer. También
> sirve para revisar si un grafo sigue siendo bipartito al probar aristas.

**2:05** [same(0, 4) → true]
> Ahora 0 y 4 están conectados.

---

# PERCY CASTRO (2:08 – 4:37)

## 02 · Snapshot y rollback (continuación) — 2:08

**2:08** [Volvemos al momento guardado]
> Volvemos con `rollback_to` de 3.

**2:12** [El registro 4 → 0 sale de la pila]
> Cada registro dice qué deshacer: 4 vuelve a ser raíz.

**2:17** [Sale 7 → 6]
> Después sale 7…

**2:21** [Sale 5 → 4]
> …y 5. Cada paso cambia solo dos valores: O(1). Por eso sirve en juegos o editores con «deshacer».

**2:29** [same(0, 4) → false]
> Volvimos al snapshot: 0 y 4 ya no están conectados.

**2:32** [Un rollback más deshace unite(1, 3)]
> Y un rollback más deshace la unión anterior: 0 y 2 vuelven a separarse. Así se resuelve la
> conectividad dinámica offline, con aristas que aparecen y desaparecen.

## 03 · ¿Por qué sin compresión de caminos? — 2:43

**2:43** [¿Y la compresión de caminos? · En un DSU normal, find() cuelga todo el camino de la raíz]
> ¿Y la compresión? En un DSU normal, `find` cuelga todo el camino de la raíz…

**2:47** […pero cambia punteros que la pila de rollback no registra]
> …pero cambia punteros que la pila no registra.

**2:58** [Unimos los dos árboles]
> Unimos los dos árboles: 7 queda a tres pasos de la raíz.

**3:02** [find(7) CON compresión: todo el camino pasa a apuntar a la raíz]
> `find` de 7 con compresión: 7 y 6 pasan a apuntar a 0, sin que la pila lo registre.

**3:10** [Ahora deshacemos la última unión]
> Deshacemos la última unión.

**3:13** [6 y 7 siguen colgados de 0: la pila no registró esos cambios]
> 4 vuelve a ser raíz, pero 6 y 7 siguen en 0.

**3:15** [same(7, 4) → false ✗ correcto: true]
> Las respuestas salen mal…

**3:20** [same(7, 1) → true ✗ correcto: false]
> 7 debería estar con 4, y no con 1.

**3:23** [Por eso: sin compresión]
> Por eso no comprimimos: `find` solo lee, y deshacer una unión cuesta O(1).

## 04 · Casos borde — 3:30

**3:30** [Casos borde]
> Dos casos borde:

**3:31** [1. Unir dos elementos que ya están en el mismo conjunto]
> unir elementos ya juntos…

**3:32** [2. Hacer rollback() sin nada que deshacer]
> …y hacer rollback con la pila vacía.

**3:35** [Error: no apilar la unión redundante]
> Si la unión redundante no apila nada…

**3:39** [0 y 2 ya están en el mismo conjunto]
> …`unite` de 2 y 0 no cambia nada…

**3:42** [Sin marcador, rollback deshace unite(1, 2) por error]
> …pero el rollback deshace la unión anterior: `same` da falso.

**3:48** [Correcto: apilar un marcador vacío]
> La solución: apilar un marcador vacío.

**3:55** [Aparece «marcador» en la pila]
> Así cada `unite` apila un registro…

**3:56** [Rollback deshace la unión redundante: no cambia nada]
> …y el rollback solo saca el marcador.

**4:02** [Pila vacía: no hay nada que deshacer]
> Con la pila vacía, `rollback` no hace nada: solo avisa.

**4:10** [Regla]
> La regla: cada `unite` apila un registro, y `rollback` deshace siempre el último.

## 05 · Complejidad y cierre — 4:16

**4:16** [Complejidad]
> La altura no pasa de log n: `find`, `unite` y `same` son O(log n); `rollback` es O(1).

**4:23** [Altura máxima medida en el peor caso (C++)]
> Medido en C++: con 1024 elementos, la altura es 10; sin unión por tamaño, 1023.

**4:29** [DSU con compresión · DSU con rollback]
> Comprimir es más rápido, pero no se puede deshacer.

**4:32** [Pagamos log n en find a cambio de poder deshacer en O(1)]
> Pagamos log n por deshacer en O(1). ¡Gracias!

---

### Cómo grabar y unir la voz

1. Cada uno graba su parte por separado (Audacity, OBS o el grabador del celular), siguiendo las
   marcas de tiempo. Percy empieza su pista en **2:08**.
2. Unan las dos pistas y el video en un editor (DaVinci Resolve, CapCut, Clipchamp), o con ffmpeg
   si ya juntaron la narración en un solo archivo:
   `ffmpeg -i DSU_con_rollback_1080p60.mp4 -i narracion.wav -c:v copy -c:a aac -shortest video_final.mp4`
3. El video dura 4:36.6 y el límite es 5:00. Si una frase no entra, es mejor alargar el
   `self.wait(...)` de esa parte en `dsu_video.py` (o bajar el `speed=` de esa escena) que acelerar
   la voz. Después hay que volver a renderizar, y los tiempos de este guion cambian desde ese punto.
4. El tramo más justo es el final (4:29–4:37): leyendo a ≈ 2,5 palabras por segundo la voz termina
   justo antes que el video, pero leyendo más lento se pasa. Si hace falta, se puede alargar el último
   `self.wait(3.0)` de `S05Complejidad`.
5. Los otros puntos donde la voz va un par de segundos detrás de la pantalla son 2:43 (tarjeta de
   compresión) y 3:13 (después del rollback). No es un problema: la animación sigue en pausa ahí.
