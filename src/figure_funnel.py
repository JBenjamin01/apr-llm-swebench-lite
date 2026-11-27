"""Figura: instancias que alcanzan cada etapa (muestra de test, n = 50) por modelo.

Uso: python figure_funnel.py <results_7b.csv> <results_14b.csv> <salida.png>
Barras horizontales agrupadas; serie 2 con textura para impresion en blanco y negro.
"""
import csv
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

STAGES = [("e1", "E1 Formato"), ("e2", "E2 Aplicable"), ("e3", "E3 Ejecutable"),
          ("e4", "E4 Corrige"), ("resolved", "Resuelta"), ("e5", "E5 Regresión")]
SERIES = [("Qwen2.5-Coder-7B", "#257de0", None), ("Qwen2.5-Coder-14B (compl.)", "#f47230", "////")]
TEXT, TEXT2, GRID = "#191919", "#666666", "#e6e6e6"


def counts(path):
    rows = list(csv.DictReader(open(path)))
    return [sum(r[k] == "True" for r in rows) for k, _ in STAGES], len(rows)


def main(a, b, out):
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                         "font.size": 8, "hatch.linewidth": 0.6, "hatch.color": "white"})
    data = [counts(a), counts(b)]
    n = data[0][1]
    fig, ax = plt.subplots(figsize=(3.45, 2.55), dpi=300)
    h, gap = 0.36, 0.04
    ys = []
    for i in range(len(STAGES)):
        y = i + (0.45 if i == len(STAGES) - 1 else 0)  # separa E5: no es etapa del embudo
        ys.append(y)
        for j, ((label, color, hatch), (vals, _)) in enumerate(zip(SERIES, data)):
            yy = y - (h + gap) / 2 + j * (h + gap)
            ax.barh(yy, vals[i], height=h, color=color, hatch=hatch, edgecolor="white",
                    linewidth=0, label=label if i == 0 else None)
            ax.text(vals[i] + 0.8, yy, str(vals[i]), va="center", ha="left", fontsize=7, color=TEXT)
    ax.axhline(ys[-1] - 0.72, color=TEXT2, linewidth=0.5, linestyle=(0, (2, 2)))
    ax.set_yticks(ys, [s for _, s in STAGES])
    ax.invert_yaxis()
    ax.set_xlim(0, n)
    ax.set_xticks(range(0, n + 1, 10))
    ax.set_xlabel(f"Instancias (de {n})", color=TEXT2)
    ax.xaxis.grid(True, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="both", length=0, colors=TEXT)
    ax.legend(loc="lower right", frameon=False, fontsize=7, handlelength=1.4)
    fig.tight_layout(pad=0.3)
    fig.savefig(out, dpi=300)
    print("ok", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
