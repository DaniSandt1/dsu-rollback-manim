// tracer.hpp — registro de eventos de la estructura, exportable a JSON.
//
// Cada operación del DSU emite uno o más eventos. Cada evento guarda su tipo ("op"),
// sus datos propios y una foto completa del estado (parent, size, history) DESPUÉS
// del evento. La animación (Python/Manim) solo lee este archivo: no recalcula nada.
#pragma once

#include <cstdio>
#include <fstream>
#include <string>
#include <utility>
#include <vector>

namespace json {

inline std::string escape(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 2);
    out += '"';
    for (unsigned char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\t': out += "\\t"; break;
            case '\r': out += "\\r"; break;
            default:
                if (c < 0x20) {
                    char buf[8];
                    std::snprintf(buf, sizeof buf, "\\u%04x", c);
                    out += buf;
                } else {
                    out += static_cast<char>(c);  // UTF-8 pasa tal cual
                }
        }
    }
    out += '"';
    return out;
}

inline std::string array(const std::vector<int>& v) {
    std::string out = "[";
    for (std::size_t i = 0; i < v.size(); ++i) {
        if (i) out += ',';
        out += std::to_string(v[i]);
    }
    return out + "]";
}

inline std::string array(const std::vector<std::string>& v) {
    std::string out = "[";
    for (std::size_t i = 0; i < v.size(); ++i) {
        if (i) out += ',';
        out += escape(v[i]);
    }
    return out + "]";
}

}  // namespace json

// Lista ordenada de pares clave → valor JSON ya serializado.
class Fields {
public:
    Fields& add(const std::string& key, int v) { return raw(key, std::to_string(v)); }
    Fields& add(const std::string& key, std::size_t v) { return raw(key, std::to_string(v)); }
    Fields& add(const std::string& key, bool v) { return raw(key, v ? "true" : "false"); }
    Fields& add(const std::string& key, const char* v) { return raw(key, json::escape(v)); }
    Fields& add(const std::string& key, const std::string& v) { return raw(key, json::escape(v)); }
    Fields& add(const std::string& key, const std::vector<int>& v) { return raw(key, json::array(v)); }
    Fields& add(const std::string& key, const std::vector<std::string>& v) { return raw(key, json::array(v)); }
    Fields& raw(const std::string& key, const std::string& json_value) {
        items_.emplace_back(key, json_value);
        return *this;
    }
    const std::vector<std::pair<std::string, std::string>>& items() const { return items_; }

private:
    std::vector<std::pair<std::string, std::string>> items_;
};

class Tracer {
public:
    explicit Tracer(std::string scenario, std::string description = "")
        : scenario_(std::move(scenario)), description_(std::move(description)) {}

    // Metadatos libres del escenario (p. ej. etiquetas de los nodos).
    Tracer& meta(const Fields& f) {
        for (const auto& kv : f.items()) meta_.raw(kv.first, kv.second);
        return *this;
    }

    void record(const std::string& op, const Fields& fields, const std::string& state_json) {
        std::string ev = "{\"id\":" + std::to_string(events_.size()) + ",\"op\":" + json::escape(op);
        for (const auto& kv : fields.items()) ev += "," + json::escape(kv.first) + ":" + kv.second;
        ev += ",\"state\":" + state_json + "}";
        events_.push_back(std::move(ev));
        ops_.push_back(op);
    }

    std::size_t size() const { return events_.size(); }
    const std::vector<std::string>& ops() const { return ops_; }
    const std::string& event_json(std::size_t i) const { return events_.at(i); }

    std::string to_json() const {
        std::string out = "{\n  \"format\": \"dsu-rollback-trace/1\",\n";
        out += "  \"scenario\": " + json::escape(scenario_) + ",\n";
        out += "  \"description\": " + json::escape(description_) + ",\n";
        out += "  \"meta\": {";
        bool first = true;
        for (const auto& kv : meta_.items()) {
            out += (first ? "" : ", ") + json::escape(kv.first) + ": " + kv.second;
            first = false;
        }
        out += "},\n  \"events\": [\n";
        for (std::size_t i = 0; i < events_.size(); ++i) {
            out += "    " + events_[i] + (i + 1 < events_.size() ? ",\n" : "\n");
        }
        return out + "  ]\n}\n";
    }

    bool write(const std::string& path) const {
        std::ofstream f(path, std::ios::binary);
        if (!f) return false;
        f << to_json();
        return static_cast<bool>(f);
    }

private:
    std::string scenario_, description_;
    Fields meta_;
    std::vector<std::string> events_;
    std::vector<std::string> ops_;
};
