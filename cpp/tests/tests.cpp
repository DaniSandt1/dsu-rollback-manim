// tests.cpp — pruebas del DSU con rollback (sin dependencias externas).
//
// Además de casos puntuales, hay una prueba aleatoria que compara el DSU contra una
// solución de fuerza bruta (BFS sobre las aristas activas) en miles de operaciones.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <functional>
#include <queue>
#include <random>
#include <string>
#include <utility>
#include <vector>

#include "dsu_rollback.hpp"
#include "tracer.hpp"

static int g_checks = 0, g_failures = 0;

#define CHECK(cond)                                                              \
    do {                                                                         \
        ++g_checks;                                                              \
        if (!(cond)) {                                                           \
            ++g_failures;                                                        \
            std::printf("    FALLA %s:%d  %s\n", __FILE__, __LINE__, #cond);    \
        }                                                                        \
    } while (0)

template <class E, class F>
static bool throws(F f) {
    try {
        f();
    } catch (const E&) {
        return true;
    } catch (...) {
    }
    return false;
}

// ---------------------------------------------------------------- utilidades

static int depth(const DSURollback& d, int x) {
    int k = 0;
    while (d.parent()[x] != x) x = d.parent()[x], ++k;
    return k;
}

static int max_depth(const DSURollback& d) {
    int m = 0;
    for (int i = 0; i < d.n(); ++i) m = std::max(m, depth(d, i));
    return m;
}

// Conectividad por fuerza bruta: BFS sobre la lista de aristas activas.
struct BruteForce {
    int n;
    std::vector<std::pair<int, int>> edges;

    std::vector<int> labels() const {
        std::vector<std::vector<int>> adj(n);
        for (auto [a, b] : edges) adj[a].push_back(b), adj[b].push_back(a);
        std::vector<int> comp(n, -1);
        int c = 0;
        for (int s = 0; s < n; ++s) {
            if (comp[s] != -1) continue;
            std::queue<int> q;
            q.push(s);
            comp[s] = c;
            while (!q.empty()) {
                int u = q.front();
                q.pop();
                for (int v : adj[u]) if (comp[v] == -1) comp[v] = c, q.push(v);
            }
            ++c;
        }
        return comp;
    }
    int components() const {
        auto l = labels();
        int m = -1;
        for (int x : l) m = std::max(m, x);
        return m + 1;
    }
};

// ---------------------------------------------------------------- casos

static void test_estado_inicial() {
    DSURollback d(5);
    CHECK(d.components() == 5);
    CHECK(d.history().empty());
    for (int i = 0; i < 5; ++i) {
        CHECK(d.find(i) == i);
        CHECK(d.set_size(i) == 1);
    }
    CHECK(!d.same(0, 1));
}

static void test_union_basica() {
    DSURollback d(6);
    CHECK(d.unite(0, 1));
    CHECK(d.unite(2, 3));
    CHECK(d.same(0, 1));
    CHECK(!d.same(1, 2));
    CHECK(d.unite(1, 3));
    CHECK(d.same(0, 2));
    CHECK(d.set_size(3) == 4);
    CHECK(d.components() == 3);
    CHECK(d.history().size() == 3);
}

static void test_union_por_tamano() {
    DSURollback d(5);
    d.unite(0, 1);
    d.unite(0, 2);  // {0,1,2} con raíz 0
    // 3 está solo: aunque lo pasemos primero, debe colgarse de la raíz grande.
    d.unite(3, 2);
    CHECK(d.parent()[3] == 0);
    CHECK(d.find(3) == 0);
    CHECK(d.sizes()[0] == 4);
    // Empate: la raíz de a queda como raíz.
    DSURollback e(2);
    e.unite(1, 0);
    CHECK(e.parent()[0] == 1);
}

static void test_find_no_modifica() {
    DSURollback d(8);
    d.unite(0, 1), d.unite(2, 3), d.unite(0, 2), d.unite(4, 5), d.unite(6, 7), d.unite(4, 6), d.unite(0, 4);
    auto before = d.parent();
    for (int i = 0; i < 8; ++i) d.find(i);
    CHECK(d.parent() == before);  // sin compresión de caminos
}

static void test_rollback_restaura_exacto() {
    DSURollback d(7);
    std::vector<std::vector<int>> parents{d.parent()}, sizes{d.sizes()};
    const std::vector<std::pair<int, int>> ops{{0, 1}, {2, 3}, {1, 3}, {4, 5}, {6, 4}, {0, 6}};
    for (auto [a, b] : ops) {
        d.unite(a, b);
        parents.push_back(d.parent());
        sizes.push_back(d.sizes());
    }
    for (int k = static_cast<int>(ops.size()) - 1; k >= 0; --k) {
        CHECK(d.rollback());
        CHECK(d.parent() == parents[k]);
        CHECK(d.sizes() == sizes[k]);
    }
    CHECK(d.components() == 7);
}

static void test_rollback_to() {
    DSURollback d(6);
    d.unite(0, 1);
    d.unite(2, 3);
    const auto t = d.snapshot();
    const auto p = d.parent();
    d.unite(1, 2);
    d.unite(4, 5);
    d.unite(0, 4);
    CHECK(d.same(3, 5));
    d.rollback_to(t);
    CHECK(d.history().size() == t);
    CHECK(d.parent() == p);
    CHECK(!d.same(1, 2));
    CHECK(d.same(0, 1));
    CHECK(throws<std::invalid_argument>([&] { d.rollback_to(t + 1); }));
}

// Caso borde: unir dos elementos que ya están juntos.
static void test_union_redundante_apila_marcador() {
    DSURollback d(3);
    d.unite(0, 1);
    d.unite(1, 2);
    const auto p = d.parent();
    CHECK(!d.unite(2, 0));  // redundante
    CHECK(d.history().size() == 3);
    CHECK(d.history().back().is_marker());
    CHECK(d.parent() == p);
    CHECK(d.rollback());     // deshace el marcador...
    CHECK(d.parent() == p);  // ...y el estado no cambia
    CHECK(d.same(0, 2));
}

// El error que evita el marcador: sin él, rollback() deshace la unión equivocada.
static void test_sin_marcador_rompe_rollback() {
    DSURollback d(3, nullptr, /*record_noops=*/false);
    d.unite(0, 1);
    d.unite(1, 2);
    d.unite(2, 0);  // redundante, no se apila
    d.rollback();   // el usuario quiere deshacer unite(2,0)...
    CHECK(!d.same(0, 2));  // ...pero se deshizo unite(1,2)
}

// Caso borde: estructura sin historia.
static void test_rollback_pila_vacia() {
    DSURollback d(3);
    CHECK(!d.rollback());
    CHECK(d.components() == 3);
    d.unite(0, 1);
    CHECK(d.rollback());
    CHECK(!d.rollback());
    DSURollback vacio(0);
    CHECK(vacio.components() == 0);
    CHECK(!vacio.rollback());
}

static void test_rangos() {
    DSURollback d(3);
    CHECK(throws<std::out_of_range>([&] { d.find(3); }));
    CHECK(throws<std::out_of_range>([&] { d.unite(-1, 0); }));
    CHECK(throws<std::invalid_argument>([] { DSURollback x(-1); }));
}

// Con unión por tamaño, la altura nunca pasa de log2(n). Peor caso: uniones balanceadas.
static void test_altura_logaritmica() {
    const int n = 1 << 10;
    DSURollback d(n);
    for (int step = 1; step < n; step <<= 1)
        for (int i = 0; i + step < n; i += 2 * step) d.unite(i, i + step);
    CHECK(d.components() == 1);
    CHECK(max_depth(d) == 10);  // se alcanza exactamente log2(n)
}

static void test_tracer() {
    Tracer t("prueba");
    DSURollback d(3, &t);
    d.unite(0, 1);
    d.unite(1, 0);
    d.rollback();
    d.rollback();
    d.rollback();
    const auto& ops = t.ops();
    auto count = [&](const std::string& op) {
        int c = 0;
        for (const auto& o : ops) c += (o == op);
        return c;
    };
    CHECK(ops.front() == "init");
    CHECK(count("link") == 1);
    CHECK(count("unite_redundant") == 1);
    CHECK(count("push") == 2);
    CHECK(count("pop") == 2);
    CHECK(count("unlink") == 1);
    CHECK(count("rollback_empty") == 1);
    // El estado registrado en el último evento coincide con la estructura real.
    CHECK(t.event_json(t.size() - 1).find("\"parent\":[0,1,2]") != std::string::npos);
    CHECK(t.to_json().find("\"format\": \"dsu-rollback-trace/1\"") != std::string::npos);
}

// Prueba aleatoria contra fuerza bruta: unite / rollback / rollback_to / same.
static void test_aleatorio_vs_fuerza_bruta() {
    for (unsigned seed = 1; seed <= 8; ++seed) {
        std::mt19937 rng(seed);
        const int n = 2 + static_cast<int>(rng() % 40);
        DSURollback d(n);
        BruteForce bf{n, {}};
        std::vector<std::vector<int>> saved;  // parent[] antes de cada unite, para comparar al deshacer
        std::vector<std::size_t> marks;
        const int limit = static_cast<int>(std::floor(std::log2(n)));
        int bad_same = 0, bad_restore = 0, bad_height = 0, bad_comp = 0;

        for (int it = 0; it < 4000; ++it) {
            const unsigned r = rng() % 100;
            if (r < 45) {
                int a = rng() % n, b = rng() % n;
                saved.push_back(d.parent());
                d.unite(a, b);
                bf.edges.push_back({a, b});
            } else if (r < 70) {
                const bool had = !bf.edges.empty();
                if (d.rollback() != had) ++bad_restore;
                if (had) {
                    bf.edges.pop_back();
                    if (d.parent() != saved.back()) ++bad_restore;
                    saved.pop_back();
                }
            } else if (r < 75) {
                marks.push_back(d.history().size());
            } else if (r < 80 && !marks.empty()) {
                std::size_t t = marks.back();
                marks.pop_back();
                if (t > d.history().size()) continue;
                d.rollback_to(t);
                bf.edges.resize(t);
                saved.resize(t);
            } else {
                int a = rng() % n, b = rng() % n;
                auto l = bf.labels();
                if (d.same(a, b) != (l[a] == l[b])) ++bad_same;
            }
            if (d.history().size() != bf.edges.size()) ++bad_restore;
            if (max_depth(d) > limit) ++bad_height;
            if (it % 50 == 0 && d.components() != bf.components()) ++bad_comp;
        }
        CHECK(bad_same == 0);
        CHECK(bad_restore == 0);
        CHECK(bad_height == 0);
        CHECK(bad_comp == 0);
    }
}

int main() {
    const std::vector<std::pair<const char*, std::function<void()>>> tests{
        {"estado inicial", test_estado_inicial},
        {"union basica", test_union_basica},
        {"union por tamano", test_union_por_tamano},
        {"find no modifica (sin compresion)", test_find_no_modifica},
        {"rollback restaura el estado exacto", test_rollback_restaura_exacto},
        {"snapshot + rollback_to", test_rollback_to},
        {"borde: union redundante apila marcador", test_union_redundante_apila_marcador},
        {"borde: sin marcador el rollback falla", test_sin_marcador_rompe_rollback},
        {"borde: rollback con pila vacia", test_rollback_pila_vacia},
        {"rangos invalidos", test_rangos},
        {"altura <= log2(n)", test_altura_logaritmica},
        {"tracer registra los eventos", test_tracer},
        {"aleatorio vs fuerza bruta (BFS)", test_aleatorio_vs_fuerza_bruta},
    };
    for (const auto& [name, fn] : tests) {
        const int before = g_failures;
        fn();
        std::printf("[%s] %s\n", g_failures == before ? " OK " : "FAIL", name);
    }
    std::printf("\n%d verificaciones, %d fallas\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
