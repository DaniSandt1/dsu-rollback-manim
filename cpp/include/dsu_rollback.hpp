// dsu_rollback.hpp — Disjoint Set Union con rollback.
//
// · Unión por tamaño (la raíz del conjunto más chico se cuelga de la del más grande):
//   la altura de cada árbol es <= log2(n), así que find() es O(log n).
// · SIN compresión de caminos: find() no modifica nada, por eso cada unión cambia
//   exactamente un puntero (parent[child]) y un tamaño (size[root]), y deshacerla es O(1).
// · history es una pila con un registro por cada llamada a unite(). Si la unión es
//   redundante (a y b ya estaban juntos) se apila un MARCADOR vacío, para que
//   "rollback() deshace el último unite()" siga siendo cierto.
//
// Si se pasa un Tracer, cada paso se registra para la animación (ver tracer.hpp).
#pragma once

#include <cstddef>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "tracer.hpp"

class DSURollback {
public:
    struct Change {
        int child;  // raíz que se colgó; -1 si fue una unión redundante (marcador)
        int root;   // raíz que la recibió;  -1 en el marcador
        bool is_marker() const { return child < 0; }
    };

    // record_noops = false reproduce un error típico (no apilar las uniones redundantes);
    // existe solo para mostrar el caso borde en el video.
    explicit DSURollback(int n, Tracer* tracer = nullptr, bool record_noops = true)
        : parent_(checked_n(n)), size_(n, 1), components_(n), tracer_(tracer),
          record_noops_(record_noops) {
        for (int i = 0; i < n; ++i) parent_[i] = i;
        if (tracing()) emit("init", Fields().add("n", n).add("record_noops", record_noops));
    }

    // Sube por los padres hasta la raíz. O(altura) = O(log n). No modifica la estructura.
    int find(int x) const {
        check(x);
        const int start = x;
        int steps = 0;
        while (parent_[x] != x) {
            if (tracing()) emit("find_step", Fields().add("x", start).add("from", x).add("to", parent_[x]));
            x = parent_[x];
            ++steps;
        }
        if (tracing()) emit("find_root", Fields().add("x", start).add("root", x).add("steps", steps));
        return x;
    }

    // Une los conjuntos de a y b. Devuelve false si ya estaban juntos.
    bool unite(int a, int b) {
        check(a);
        check(b);
        if (tracing()) emit("unite_call", Fields().add("a", a).add("b", b));
        int ra = find(a);
        int rb = find(b);
        if (ra == rb) {
            if (tracing()) emit("unite_redundant", Fields().add("a", a).add("b", b).add("root", ra));
            if (record_noops_) {
                history_.push_back({-1, -1});
                if (tracing()) emit("push", Fields().add("child", -1).add("root", -1).add("marker", true));
            }
            return false;
        }
        if (size_[ra] < size_[rb]) std::swap(ra, rb);  // ra = raíz del conjunto más grande
        history_.push_back({rb, ra});
        if (tracing()) emit("push", Fields().add("child", rb).add("root", ra).add("marker", false));
        parent_[rb] = ra;
        size_[ra] += size_[rb];
        --components_;
        if (tracing()) emit("link", Fields().add("child", rb).add("root", ra).add("size_root", size_[ra]));
        return true;
    }

    bool same(int a, int b) const {
        if (tracing()) emit("same_call", Fields().add("a", a).add("b", b));
        const bool result = find(a) == find(b);
        if (tracing()) emit("same_result", Fields().add("a", a).add("b", b).add("result", result));
        return result;
    }

    // Deshace el último unite(). O(1). Devuelve false si no hay nada que deshacer.
    bool rollback() {
        if (tracing()) emit("rollback_call", Fields().add("depth", history_.size()));
        if (history_.empty()) {
            if (tracing()) emit("rollback_empty", Fields());
            return false;
        }
        const Change c = history_.back();
        history_.pop_back();
        if (tracing()) {
            emit("pop", Fields().add("child", c.child).add("root", c.root).add("marker", c.is_marker()));
        }
        if (!c.is_marker()) {
            parent_[c.child] = c.child;
            size_[c.root] -= size_[c.child];
            ++components_;
            if (tracing()) {
                emit("unlink", Fields().add("child", c.child).add("root", c.root).add("size_root", size_[c.root]));
            }
        }
        return true;
    }

    // Momento actual de la historia, para volver a él con rollback_to().
    std::size_t snapshot() const {
        if (tracing()) emit("snapshot", Fields().add("t", history_.size()));
        return history_.size();
    }

    // Deshace uniones hasta que la historia vuelva a tener tamaño t.
    void rollback_to(std::size_t t) {
        if (t > history_.size()) throw std::invalid_argument("rollback_to: momento futuro");
        if (tracing()) emit("rollback_to_call", Fields().add("t", t).add("from", history_.size()));
        while (history_.size() > t) rollback();
        if (tracing()) emit("rollback_to_done", Fields().add("t", t));
    }

    // Marca narrativa para sincronizar la animación (no cambia el estado).
    void mark(const std::string& text) const {
        if (tracing()) emit("mark", Fields().add("text", text));
    }

    int n() const { return static_cast<int>(parent_.size()); }
    int components() const { return components_; }
    int set_size(int x) const { return size_[find(x)]; }
    const std::vector<int>& parent() const { return parent_; }
    const std::vector<int>& sizes() const { return size_; }
    const std::vector<Change>& history() const { return history_; }

private:
    static std::size_t checked_n(int n) {
        if (n < 0) throw std::invalid_argument("n no puede ser negativo");
        return static_cast<std::size_t>(n);
    }

    void check(int x) const {
        if (x < 0 || x >= n()) throw std::out_of_range("elemento fuera de rango: " + std::to_string(x));
    }

    bool tracing() const { return tracer_ != nullptr; }

    std::string state_json() const {
        std::string h = "[";
        for (std::size_t i = 0; i < history_.size(); ++i) {
            if (i) h += ',';
            h += "[" + std::to_string(history_[i].child) + "," + std::to_string(history_[i].root) + "]";
        }
        h += "]";
        return "{\"parent\":" + json::array(parent_) + ",\"size\":" + json::array(size_) +
               ",\"history\":" + h + ",\"components\":" + std::to_string(components_) + "}";
    }

    void emit(const std::string& op, const Fields& f) const { tracer_->record(op, f, state_json()); }

    std::vector<int> parent_;
    std::vector<int> size_;
    std::vector<Change> history_;
    int components_;
    Tracer* tracer_;
    bool record_noops_;
};
