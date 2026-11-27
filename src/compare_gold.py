"""Compara cada parche resuelto con el parche del desarrollador (gold).

Para cada instancia resuelta reporta: identidad literal, solapamiento de las lineas
modificadas del archivo original y similitud textual de las lineas anadidas.
Uso (venv de swebench): python compare_gold.py work/*_results.csv > comparacion.md
"""
import csv
import difflib
import glob
import json
import re
import sys


def changed(patch):
    """Lineas del archivo original tocadas (por numero) y lineas anadidas (texto)."""
    old_lines, added = set(), []
    o = 0
    for ln in patch.splitlines():
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@", ln)
        if m:
            o = int(m.group(1))
            continue
        if ln.startswith(("---", "+++", "diff ")):
            continue
        if ln.startswith("-"):
            old_lines.add(o)
            o += 1
        elif ln.startswith("+"):
            added.append(ln[1:].strip())
            old_lines.add(o)  # insercion: se ancla en la linea siguiente
        else:
            o += 1
    return old_lines, [a for a in added if a]


def main():
    from swebench.harness.utils import load_swebench_dataset

    gold = {}
    for split in ("dev", "test"):
        for x in load_swebench_dataset("SWE-bench/SWE-bench_Lite", split):
            gold[x["instance_id"]] = x["patch"]
    print("| Modelo | Instancia | Idéntico | Líneas originales compartidas | Similitud de líneas añadidas |")
    print("|---|---|---|---|---|")
    for pat in sys.argv[1:]:
        for f in sorted(glob.glob(pat)):
            stem = f.split("/")[-1].replace("_results.csv", "")
            preds = {}
            for l in open(f"work/{stem}_preds.jsonl"):
                p = json.loads(l)
                preds[p["instance_id"]] = p["model_patch"]
            for r in csv.DictReader(open(f)):
                if r["resolved"] != "True":
                    continue
                iid = r["instance_id"]
                mp, gp = preds[iid], gold[iid]
                mo, ma = changed(mp)
                go, ga = changed(gp)
                inter = len(mo & go) / len(go | mo) if (go | mo) else 0
                sim = difflib.SequenceMatcher(None, "\n".join(ma), "\n".join(ga)).ratio()
                same = "sí" if ma == ga and mo == go else "no"
                print(f"| {stem} | {iid} | {same} | {inter:.2f} | {sim:.2f} |")


if __name__ == "__main__":
    main()
