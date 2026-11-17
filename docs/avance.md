# Avance: DSU con rollback

## Plan del video

Duración prevista: aproximadamente 4:20, con un máximo de cinco minutos.

| Tiempo aproximado | Contenido |
| --- | --- |
| 0:00–0:20 | Título y motivación: red de computadoras. |
| 0:20–0:50 | Conjuntos disjuntos, conectividad y operaciones del ADT. |
| 0:50–1:40 | `find`, `unite`, `same` y unión por tamaño. |
| 1:40–2:35 | Snapshot y rollback con pila de cambios. |
| 2:35–3:15 | Por qué no usamos compresión de caminos. |
| 3:15–3:50 | Caso borde: unión redundante y marcador. |
| 3:50–4:20 | Complejidad y cierre. |

## Primera escena: título y motivación

Seis computadoras A–F empiezan aisladas. Se conectan A con B y C con D; se guarda un snapshot. Se prueba la conexión B–C y los cuatro equipos quedan en una componente. Luego se deshace esa conexión temporal para volver al estado guardado.

Narración propuesta: «Imaginemos seis computadoras, inicialmente aisladas. Agregamos conexiones: primero A con B, luego C con D, y después unimos los grupos de B y C. Ahora esos cuatro equipos pertenecen a una misma componente conectada. Si estamos explorando una configuración temporal, podemos guardar el estado, probar nuevas conexiones y deshacer las más recientes para volver a ese estado sin reconstruir todo desde cero».

Pregunta final: **¿Cómo podemos combinar grupos y volver eficientemente a un estado anterior?**

El rollback deshace modificaciones recientes en orden inverso; no elimina una conexión arbitraria. El DSU representa conectividad y no almacena los cables de la red.

## Implementación

La escena inicial consume `trace/00_motivacion.json`, generada por el escenario C++. Las escenas posteriores pueden reutilizar las trazas existentes; la escena de rollback podrá ajustarse durante el desarrollo.
