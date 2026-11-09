// escenarios.cpp — ejecuta el DSU con rollback sobre los escenarios del video y
// guarda cada traza en JSON. Uso:  escenarios [carpeta_salida]   (por defecto: trace)
//
// La animación lee estos archivos: todo lo que se ve en pantalla (padres, tamaños,
// pila de historia, pasos de find) sale de esta ejecución real.
#include <cstdio>
#include <filesystem>
#include <functional>
#include <string>
#include <vector>

#include "dsu_rollback.hpp"
#include "tracer.hpp"

namespace fs = std::filesystem;

// Motivación: ciudades conectadas por cables; probamos un escenario y lo deshacemos.
static void motivacion(Tracer& t) {
    t.meta(Fields().add("labels", std::vector<std::string>{"Lima", "Cusco", "Arequipa", "Piura", "Trujillo", "Puno"}));
    DSURollback d(6, &t);
    d.mark("Una red de ciudades, cada una aislada");
    d.unite(0, 4);  // Lima - Trujillo
    d.unite(1, 5);  // Cusco - Puno
    d.unite(1, 2);  // Cusco - Arequipa
    d.same(0, 1);
    const auto t0 = d.snapshot();
    d.mark("¿Y si agregamos un cable Trujillo - Puno?");
    d.unite(4, 5);
    d.same(0, 1);
    d.mark("Ctrl+Z: volvemos al estado anterior");
    d.rollback_to(t0);
    d.same(0, 1);
}

// Operaciones básicas y unión por tamaño (el árbol chico se cuelga del grande).
static void union_por_tamano(Tracer& t) {
    DSURollback d(8, &t);
    d.mark("Cada elemento empieza en su propio conjunto");
    d.unite(0, 1);
    d.unite(2, 3);
    d.unite(0, 2);  // empate 2 vs 2: queda la raíz de a
    d.unite(4, 5);
    d.unite(6, 4);  // 6 está solo: se cuelga del conjunto {4,5}
    d.mark("Unión por tamaño: el árbol más chico se cuelga del más grande");
    d.unite(3, 6);  // {0..3} (4) recibe a {4,5,6} (3)
    d.same(1, 7);
    d.same(5, 1);
}

// La operación nueva: snapshot, más uniones y vuelta atrás.
static void rollback_basico(Tracer& t) {
    DSURollback d(8, &t);
    d.unite(0, 1);
    d.unite(2, 3);
    d.unite(1, 3);
    d.mark("Guardamos el momento actual");
    const auto t0 = d.snapshot();
    d.unite(4, 5);
    d.unite(6, 7);
    d.unite(3, 5);
    d.same(0, 4);
    d.mark("Volvemos al momento guardado");
    d.rollback_to(t0);
    d.same(0, 4);
    d.mark("Un rollback más deshace unite(1, 3)");
    d.rollback();
    d.same(0, 2);
}

// Caso borde: unión redundante con marcador (implementación correcta).
static void borde_redundante(Tracer& t) {
    DSURollback d(5, &t);
    d.unite(0, 1);
    d.unite(1, 2);
    d.mark("0 y 2 ya están en el mismo conjunto");
    d.unite(2, 0);
    d.mark("Rollback deshace la unión redundante: no cambia nada");
    d.rollback();
    d.same(0, 2);
}

// Caso borde: el mismo escenario SIN marcador (error típico).
static void borde_sin_marcador(Tracer& t) {
    t.meta(Fields().add("bug", true));
    DSURollback d(5, &t, /*record_noops=*/false);
    d.unite(0, 1);
    d.unite(1, 2);
    d.mark("0 y 2 ya están en el mismo conjunto");
    d.unite(2, 0);
    d.mark("Sin marcador, rollback deshace unite(1, 2) por error");
    d.rollback();
    d.same(0, 2);
}

// Caso borde: rollback sin historia.
static void borde_pila_vacia(Tracer& t) {
    DSURollback d(3, &t);
    d.mark("Pila vacía: no hay nada que deshacer");
    d.rollback();
    d.unite(0, 1);
    d.rollback();
    d.mark("Otra vez vacía");
    d.rollback();
}

// Peor caso de find: uniones balanceadas, altura exactamente log2(16) = 4.
static void peor_caso_altura(Tracer& t) {
    const int n = 16;
    DSURollback d(n, &t);
    for (int step = 1; step < n; step <<= 1) {
        d.mark("Uniones de conjuntos de tamaño " + std::to_string(step));
        for (int i = 0; i + step < n; i += 2 * step) d.unite(i, i + step);
    }
    int deepest = 0, best = -1;
    for (int i = 0; i < n; ++i) {
        int k = 0;
        for (int x = i; d.parent()[x] != x; x = d.parent()[x]) ++k;
        if (k > best) best = k, deepest = i;
    }
    d.mark("El nodo más profundo está a log2(16) = 4 pasos de la raíz");
    d.find(deepest);
}

int main(int argc, char** argv) {
    const fs::path out = argc > 1 ? fs::path(argv[1]) : fs::path("trace");
    fs::create_directories(out);

    struct Scenario {
        const char* file;
        const char* description;
        std::function<void(Tracer&)> run;
    };
    const std::vector<Scenario> scenarios{
        {"00_motivacion", "Red de ciudades: probar un cable y deshacerlo", motivacion},
        {"01_union_por_tamano", "find, unite y same con unión por tamaño", union_por_tamano},
        {"02_rollback", "snapshot, rollback_to y rollback", rollback_basico},
        {"03_borde_redundante", "Unión redundante: se apila un marcador", borde_redundante},
        {"04_borde_sin_marcador", "Error típico: no apilar la unión redundante", borde_sin_marcador},
        {"05_borde_pila_vacia", "rollback() con la historia vacía", borde_pila_vacia},
        {"06_peor_caso_altura", "Uniones balanceadas: altura log2(n)", peor_caso_altura},
    };

    int failures = 0;
    for (const auto& s : scenarios) {
        Tracer t(s.file, s.description);
        s.run(t);
        const fs::path path = out / (std::string(s.file) + ".json");
        if (t.write(path.string())) {
            std::printf("%-26s %4zu eventos -> %s\n", s.file, t.size(), path.generic_string().c_str());
        } else {
            std::printf("ERROR: no se pudo escribir %s\n", path.generic_string().c_str());
            ++failures;
        }
    }
    return failures == 0 ? 0 : 1;
}
