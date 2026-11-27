"""Prepara la revision manual de los parches resueltos y calcula el kappa de Cohen.

  python manual_review.py preparar <salida_dir>     (venv de swebench, en ~/apr)
  python manual_review.py kappa <revisor_A.csv> <revisor_B.csv>
"""
import csv
import glob
import html
import json
import sys
from pathlib import Path

CATS = "equivalente | plausible_distinto | incorrecto"


def preparar(out):
    from swebench.harness.utils import load_swebench_dataset

    ds = {}
    for split in ("dev", "test"):
        for x in load_swebench_dataset("SWE-bench/SWE-bench_Lite", split):
            ds[x["instance_id"]] = x
    items = []
    for f in sorted(glob.glob("work/*_results.csv")):
        stem = Path(f).name.replace("_results.csv", "")
        preds = {json.loads(l)["instance_id"]: json.loads(l)["model_patch"]
                 for l in open(f"work/{stem}_preds.jsonl")}
        for r in csv.DictReader(open(f)):
            if r["resolved"] == "True":
                items.append((stem, r["instance_id"], preds[r["instance_id"]]))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    css = ("body{font-family:sans-serif;max-width:1400px;margin:auto;padding:1em}"
           "pre{background:#f6f6f6;padding:.6em;overflow-x:auto;font-size:12px;white-space:pre-wrap}"
           ".g{display:grid;grid-template-columns:1fr 1fr;gap:1em}h2{border-top:2px solid #333;"
           "padding-top:.6em}details{margin:.4em 0}")
    parts = [f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>",
             "<h1>Revisión manual de parches resueltos</h1>",
             "<p>Para cada caso, compare el parche del modelo con el del desarrollador y anote en "
             f"<b>su propia</b> planilla una categoría: <code>{CATS}</code>.</p><ul>"
             "<li><b>equivalente</b>: hace lo mismo que el parche del desarrollador (aunque cambie la "
             "forma).</li><li><b>plausible_distinto</b>: corrige el issue de otra manera razonable."
             "</li><li><b>incorrecto</b>: pasa las pruebas pero no corrige realmente el issue o "
             "rompe otro comportamiento.</li></ul><p>No consultar al otro revisor hasta terminar."
             "</p>"]
    rows = []
    for k, (stem, iid, mp) in enumerate(items, 1):
        x = ds[iid]
        parts.append(f"<h2>Caso {k}: {html.escape(iid)} <small>({html.escape(stem)})</small></h2>")
        parts.append("<details><summary>Enunciado del issue</summary><pre>"
                     f"{html.escape(x['problem_statement'])}</pre></details>")
        parts.append("<div class='g'><div><h3>Parche del modelo</h3><pre>"
                     f"{html.escape(mp)}</pre></div><div><h3>Parche del desarrollador</h3><pre>"
                     f"{html.escape(x['patch'])}</pre></div></div>")
        rows.append({"caso": k, "instance_id": iid, "modelo": stem, "categoria": "", "comentario": ""})
    parts.append("</body></html>")
    (out / "parches_para_revisar.html").write_text("\n".join(parts), encoding="utf8")
    for who in ("A", "B"):
        with open(out / f"planilla_revisor_{who}.csv", "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print(f"{len(items)} casos -> {out}")


def kappa(fa, fb):
    a = {r["caso"]: r["categoria"].strip() for r in csv.DictReader(open(fa, encoding="utf-8-sig"))}
    b = {r["caso"]: r["categoria"].strip() for r in csv.DictReader(open(fb, encoding="utf-8-sig"))}
    keys = sorted(set(a) & set(b), key=int)
    n = len(keys)
    po = sum(a[k] == b[k] for k in keys) / n
    cats = set(a.values()) | set(b.values())
    pe = sum((sum(a[k] == c for k in keys) / n) * (sum(b[k] == c for k in keys) / n) for c in cats)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    print(f"n={n} acuerdo observado={po:.2f} kappa={k:.2f}")
    for k_ in keys:
        if a[k_] != b[k_]:
            print(f"  desacuerdo en caso {k_}: A={a[k_]} B={b[k_]}")


if __name__ == "__main__":
    {"preparar": lambda: preparar(sys.argv[2]),
     "kappa": lambda: kappa(sys.argv[2], sys.argv[3])}[sys.argv[1]]()
