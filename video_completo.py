"""Genera el video completo: renderiza las escenas en orden y las une en un solo MP4.

    python video_completo.py                 # 1080p60 (por defecto)
    python video_completo.py --calidad k     # 4K
    python video_completo.py --calidad l     # vista previa 480p
    python video_completo.py --solo-unir     # no renderiza: une las escenas ya renderizadas

Resultado: media/videos/DSU_con_rollback_<resolución>.mp4

Las escenas se renderizan una por una (en paralelo, Manim puede chocar con sus archivos temporales de
texto) y se unen sin recodificar, con el mismo método que usa Manim para unir sus clips parciales.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import av

ESCENAS = [
    "S00Motivacion",
    "S01Operaciones",
    "S02Rollback",
    "S03SinCompresion",
    "S04CasoBorde",
    "S05Complejidad",
]
# Carpeta donde Manim deja cada calidad.
CARPETAS = {"l": "480p15", "m": "720p30", "h": "1080p60", "p": "1440p60", "k": "2160p60"}

RAIZ = Path(__file__).parent
SALIDA_ESCENAS = RAIZ / "media" / "videos" / "dsu_video"


def renderizar(calidad: str) -> None:
    for i, escena in enumerate(ESCENAS, 1):
        print(f"[{i}/{len(ESCENAS)}] renderizando {escena} ...", flush=True)
        cmd = [sys.executable, "-m", "manim", f"-q{calidad}", "--progress_bar", "none",
               "-v", "WARNING", "dsu_video.py", escena]
        if subprocess.run(cmd, cwd=RAIZ).returncode != 0:
            sys.exit(f"Falló el render de {escena}")


def datos(path: Path):
    with av.open(str(path)) as c:
        s = c.streams.video[0]
        clave = (s.codec_context.name, s.width, s.height, round(float(s.average_rate)), s.format.name)
        return clave, float(c.duration) / av.time_base


def unir(archivos: list[Path], salida: Path) -> float:
    claves = {datos(a)[0] for a in archivos}
    if len(claves) != 1:
        sys.exit(f"Las escenas tienen formatos distintos y no se pueden unir sin recodificar: {claves}")

    lista = salida.with_suffix(".txt")
    lista.write_text("".join(f"file 'file:{a.resolve().as_posix()}'\n" for a in archivos), encoding="utf-8")
    try:
        entrada = av.open(str(lista), options={"safe": "0", "an": "1"}, format="concat")
        origen = entrada.streams.video[0]
        destino = av.open(str(salida), mode="w")
        destino.metadata["title"] = "DSU con rollback"
        stream = destino.add_stream_from_template(template=origen)
        for paquete in entrada.demux(origen):
            if paquete.dts is None:  # paquetes de "flush" que genera demux
                continue
            paquete.dts = None  # que libav recalcule el dts al pasar de un archivo a otro
            paquete.stream = stream
            destino.mux(paquete)
        entrada.close()
        destino.close()
    finally:
        lista.unlink(missing_ok=True)

    suma = sum(datos(a)[1] for a in archivos)
    total = datos(salida)[1]
    if abs(total - suma) > 1.0:
        sys.exit(f"El video unido dura {total:.1f} s pero las escenas suman {suma:.1f} s")
    return total


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--calidad", choices=sorted(CARPETAS), default="h", help="calidad de Manim (por defecto h)")
    p.add_argument("--solo-unir", action="store_true", help="no renderizar; unir lo ya renderizado")
    args = p.parse_args()

    if not args.solo_unir:
        renderizar(args.calidad)

    carpeta = SALIDA_ESCENAS / CARPETAS[args.calidad]
    archivos = [carpeta / f"{e}.mp4" for e in ESCENAS]
    faltan = [a.name for a in archivos if not a.exists()]
    if faltan:
        sys.exit(f"Faltan escenas renderizadas en {carpeta}: {', '.join(faltan)}")

    salida = RAIZ / "media" / "videos" / f"DSU_con_rollback_{CARPETAS[args.calidad]}.mp4"
    total = unir(archivos, salida)
    for a in archivos:
        print(f"  {a.stem:18s} {datos(a)[1]:6.1f} s")
    print(f"\nVideo completo: {salida.relative_to(RAIZ).as_posix()}  "
          f"({int(total // 60)}:{total % 60:04.1f}, {salida.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
