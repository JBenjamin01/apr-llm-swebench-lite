"""Analisis estadistico (Seccion IV-G). Uso:
  python analysis.py --results work/*_results.csv --meta out/*_meta.json --out analisis/
Genera: embudo por modelo (absoluto y condicional, IC de Wilson 95 %),
costos (RQ4), comparaciones apareadas (McNemar exacto, Wilcoxon, delta de
Cliff, Holm) y la figura costo-efectividad.
"""
import argparse
import csv
import glob
import itertools
import json
import math
import statistics as st
from pathlib import Path

STAGES = ["e1", "e2", "e3", "e4", "e5", "resolved"]


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"),) * 2
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar_exact(b, c):
    """p bilateral exacto (binomial) sobre los pares discordantes."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def cliffs_delta(x, y):
    gt = sum(1 for a in x for b in y if a > b)
    lt = sum(1 for a in x for b in y if a < b)
    return (gt - lt) / (len(x) * len(y))


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, running = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(pvals) - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def b(v):
    return str(v).strip().lower() in ("true", "1")


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", nargs="+", required=True)
    ap.add_argument("--meta", nargs="*", default=[])
    ap.add_argument("--out", default="analisis")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    data = {}
    for pat in a.results:
        for p in glob.glob(pat):
            rows = list(csv.DictReader(open(p)))
            if rows:
                data[rows[0]["model"]] = {r["instance_id"]: r for r in rows}
    metas = {}
    for pat in a.meta:
        for p in glob.glob(pat):
            m = json.load(open(p))
            metas[m["model_key"]] = m
    models = sorted(data)
    lines = ["# Resultados del analisis\n"]

    # ---- Embudo (RQ1-RQ3) ----
    lines.append("## Embudo por etapa (absoluto sobre n; IC Wilson 95 %)\n")
    lines.append("| Modelo | n | " + " | ".join(s.upper() for s in STAGES) + " |")
    lines.append("|---" * (len(STAGES) + 2) + "|")
    summary = {}
    for m in models:
        rows = list(data[m].values())
        n = len(rows)
        cells, summary[m] = [], {"n": n}
        for s in STAGES:
            k = sum(b(r[s]) for r in rows)
            lo, hi = wilson(k, n)
            summary[m][s] = k
            cells.append(f"{k} ({100*k/n:.1f} %; {100*lo:.1f}–{100*hi:.1f})")
        lines.append(f"| {m} | {n} | " + " | ".join(cells) + " |")

    lines.append("\n## Tasas condicionales\n")
    lines.append("| Modelo | E2/E1 | E3/E2 | E4/E3 | E5/E3 | E5/E4 |")
    lines.append("|---|---|---|---|---|---|")
    for m in models:
        s = summary[m]
        rows = list(data[m].values())
        e5_e4 = sum(b(r["e5"]) and b(r["e4"]) for r in rows)

        def r_(k, n):
            return f"{k}/{n} ({100*k/n:.0f} %)" if n else "—"
        lines.append(f"| {m} | {r_(s['e2'], s['e1'])} | {r_(s['e3'], s['e2'])} | "
                     f"{r_(s['e4'], s['e3'])} | {r_(s['e5'], s['e3'])} | {r_(e5_e4, s['e4'])} |")

    # ---- Causas de fallo ----
    lines.append("\n## Causas de fallo (primera etapa fallida)\n")
    causes = sorted({r["cause"] for m in models for r in data[m].values() if r["cause"]})
    lines.append("| Causa | " + " | ".join(models) + " |")
    lines.append("|---" * (len(models) + 1) + "|")
    for c in causes:
        lines.append(f"| {c} | " + " | ".join(
            str(sum(r["cause"] == c for r in data[m].values())) for m in models) + " |")

    # ---- Costo (RQ4) ----
    lines.append("\n## Costo (RQ4)\n")
    lines.append("| Modelo | t. gen. mediana [IQR] (s) | tokens salida mediana | "
                 "memoria GPU máx. (GB) | energía total (Wh) | Wh por instancia | "
                 "GPU-s por resuelta | prompts recortados | salidas truncadas |")
    lines.append("|---" * 9 + "|")
    cost = {}
    for m in models:
        rows = list(data[m].values())
        t = [f(r["gen_time_s"]) for r in rows if f(r["gen_time_s"]) is not None]
        to = [f(r["output_tokens"]) for r in rows if f(r["output_tokens"]) is not None]
        mem = [f(r["peak_mem_gb"]) for r in rows if f(r["peak_mem_gb"]) is not None]
        en = [f(r["energy_wh"]) for r in rows if f(r["energy_wh"]) is not None]
        res = summary[m]["resolved"]
        ngpu = len(metas.get(m, {}).get("gpus", [])) or 1
        tp = metas.get(m, {}).get("tensor_parallel", 1)
        gpu_s = sum(t) * tp
        cost[m] = {"t_med": st.median(t) if t else float("nan"), "gpu_s": gpu_s,
                   "res_rate": res / len(rows), "tp": tp, "ngpu": ngpu}
        lines.append(
            f"| {m} | {st.median(t):.1f} [{q(t,.25):.1f}–{q(t,.75):.1f}] | "
            f"{st.median(to):.0f} | {max(mem):.1f} | {sum(en):.1f} | "
            f"{sum(en)/len(en):.2f} | "
            f"{(gpu_s/res) if res else float('inf'):.0f} | "
            f"{sum(b(r['truncated']) for r in rows)} | "
            f"{sum(r['finish_reason']=='length' for r in rows)} |")

    # ---- Comparaciones apareadas ----
    if len(models) > 1:
        lines.append("\n## Comparaciones apareadas (McNemar exacto, Holm)\n")
        lines.append("| Métrica | Par | b (A sí, B no) | c (A no, B sí) | p | p Holm |")
        lines.append("|---|---|---|---|---|---|")
        for s in STAGES:
            pairs, ps = [], []
            for m1, m2 in itertools.combinations(models, 2):
                ids = set(data[m1]) & set(data[m2])
                bb = sum(b(data[m1][i][s]) and not b(data[m2][i][s]) for i in ids)
                cc = sum(not b(data[m1][i][s]) and b(data[m2][i][s]) for i in ids)
                pairs.append((m1, m2, bb, cc))
                ps.append(mcnemar_exact(bb, cc))
            for (m1, m2, bb, cc), p, pa in zip(pairs, ps, holm(ps)):
                lines.append(f"| {s.upper()} | {m1} vs {m2} | {bb} | {cc} | {p:.3f} | {pa:.3f} |")

        lines.append("\n## Tiempo de generación (Wilcoxon apareado, delta de Cliff, Holm)\n")
        lines.append("| Par | mediana A (s) | mediana B (s) | p | p Holm | δ de Cliff |")
        lines.append("|---|---|---|---|---|---|")
        try:
            from scipy.stats import wilcoxon
        except ImportError:
            wilcoxon = None
        pairs, ps = [], []
        for m1, m2 in itertools.combinations(models, 2):
            ids = sorted(set(data[m1]) & set(data[m2]))
            x = [f(data[m1][i]["gen_time_s"]) for i in ids]
            y = [f(data[m2][i]["gen_time_s"]) for i in ids]
            xy = [(u, v) for u, v in zip(x, y) if u is not None and v is not None]
            x, y = [u for u, _ in xy], [v for _, v in xy]
            p = wilcoxon(x, y).pvalue if wilcoxon and len(x) > 5 else float("nan")
            pairs.append((m1, m2, x, y))
            ps.append(p)
        valid = [p for p in ps if not math.isnan(p)]
        adj = iter(holm(valid)) if valid else iter([])
        for (m1, m2, x, y), p in zip(pairs, ps):
            pa = next(adj) if not math.isnan(p) else float("nan")
            lines.append(f"| {m1} vs {m2} | {st.median(x):.1f} | {st.median(y):.1f} | "
                         f"{p:.4f} | {pa:.4f} | {cliffs_delta(x, y):+.2f} |")

    # ---- Por repositorio (exploratorio) ----
    lines.append("\n## Resueltas por repositorio (exploratorio)\n")
    repos = sorted({r["repo"] for m in models for r in data[m].values()})
    lines.append("| Repositorio | n | " + " | ".join(models) + " |")
    lines.append("|---" * (len(models) + 2) + "|")
    for rp in repos:
        n = sum(r["repo"] == rp for r in data[models[0]].values())
        lines.append(f"| {rp} | {n} | " + " | ".join(
            str(sum(b(r["resolved"]) for r in data[m].values() if r["repo"] == rp))
            for m in models) + " |")

    (out / "resultados.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    json.dump({"summary": summary, "cost": cost}, open(out / "resumen.json", "w"), indent=2)
    print("\n".join(lines))

    # ---- Figura costo-efectividad ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(4.2, 3.0), dpi=200)
        for m in models:
            c = cost[m]
            ax.scatter(c["gpu_s"] / summary[m]["n"], 100 * c["res_rate"], s=36)
            ax.annotate(m, (c["gpu_s"] / summary[m]["n"], 100 * c["res_rate"]),
                        textcoords="offset points", xytext=(5, 4), fontsize=8)
        ax.set_xlabel("GPU-segundos por instancia")
        ax.set_ylabel("Instancias resueltas (%)")
        ax.grid(alpha=.3)
        fig.tight_layout()
        fig.savefig(out / "costo_efectividad.png")
    except ImportError:
        print("matplotlib no disponible: se omite la figura")


if __name__ == "__main__":
    main()
