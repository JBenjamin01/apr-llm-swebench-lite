"""Pipeline de validacion (Seccion IV-D). Se ejecuta en WSL con el venv de swebench.

  prepare : salidas de Kaggle -> E1/E2 + predicciones para el harness
  collect : informes del harness -> E3/E4/E5 por instancia (CSV)
  flaky   : lista de instancias con P2P fallidas para reejecutar

Ejemplo:
  python pipeline.py prepare --gen out/qwen7_dev.jsonl --work work/
  python -m swebench.harness.run_evaluation -d SWE-bench/SWE-bench_Lite -s dev \
      -p work/qwen7_dev_preds.jsonl -id qwen7_dev --max_workers 3
  python pipeline.py collect --gen out/qwen7_dev.jsonl --work work/ \
      --run-id qwen7_dev [--rerun-id qwen7_dev_rerun]
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from convert import to_diff  # noqa: E402

DATASET = "SWE-bench/SWE-bench_Lite"


def load_jsonl(p):
    with open(p) as f:
        return [json.loads(l) for l in f if l.strip()]


def fetch_file(repo, commit, path, cache):
    import requests

    fp = cache / repo.replace("/", "__") / commit / path
    if fp.exists():
        return fp.read_text()
    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    for attempt in range(5):
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(r.text)
            return r.text
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{url}: {r.status_code}")


def git_check(path, content, diff):
    """`git apply --check` en un arbol temporal con el archivo en el commit base.
    El parche toca un solo archivo, por lo que equivale a hacerlo en el repo."""
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        p = subprocess.run(["git", "apply", "--check", "-"], cwd=d, input=diff,
                           capture_output=True, text=True)
        return p.returncode == 0, p.stderr.strip()[:500]


def cmd_prepare(a):
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    cache = work / "files"
    gens = load_jsonl(a.gen)
    if a.valid:
        valid = set(Path(a.valid).read_text().split())
        excl = [g["instance_id"] for g in gens if g["instance_id"] not in valid]
        gens = [g for g in gens if g["instance_id"] in valid]
        print(f"excluidas por verificacion gold: {len(excl)}")
    model = gens[0]["model"]
    stem = Path(a.gen).stem
    stages, preds = [], []
    for g in gens:
        st = {"instance_id": g["instance_id"], "model": model,
              "gen_error": g.get("error")}
        if g.get("error"):
            st.update(e1=False, e2=False, cause="generation_error", diff="")
        else:
            content = fetch_file(g["repo"], g["base_commit"], g["path"], cache)
            r = to_diff(g["raw_output"], g["path"], content,
                        finish_reason=g.get("finish_reason"))
            if r["e2"]:
                ok, err = git_check(g["path"], content, r["diff"])
                if not ok:
                    r.update(e2=False, cause="git_apply_failed", git_error=err)
            st.update(e1=r["e1"], e2=r["e2"], cause=r["cause"], diff=r["diff"],
                      n_blocks=r["n_blocks"], git_error=r.get("git_error"))
            if r["e2"]:
                preds.append({"instance_id": g["instance_id"],
                              "model_name_or_path": model,
                              "model_patch": r["diff"]})
        stages.append(st)
    with open(work / f"{stem}_stages.jsonl", "w") as f:
        for s in stages:
            f.write(json.dumps(s) + "\n")
    with open(work / f"{stem}_preds.jsonl", "w") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")
    n = len(stages)
    print(f"{stem}: n={n} E1={sum(s['e1'] for s in stages)} "
          f"E2={sum(s['e2'] for s in stages)} -> {len(preds)} predicciones")


def harness_result(run_id, model, iid, logs_root):
    """Lee report.json y test_output.txt del harness para una instancia."""
    d = Path(logs_root) / "run_evaluation" / run_id / model / iid
    rep = d / "report.json"
    if not rep.exists():
        return None
    r = json.loads(rep.read_text())[iid]
    ts = r.get("tests_status", {})
    status_map = {}
    try:
        from swebench.harness.grading import get_logs_eval
        from swebench.harness.utils import load_swebench_dataset, make_test_spec

        global _DS
        if "_DS" not in globals():
            _DS = {x["instance_id"]: x for x in load_swebench_dataset(DATASET, _SPLIT)}
        spec = make_test_spec(_DS[iid])
        status_map, _found = get_logs_eval(spec, str(d / "test_output.txt"))
    except Exception as e:  # noqa: BLE001
        print("aviso: no se pudo leer el log de", iid, e)
    f2p, p2p = ts.get("FAIL_TO_PASS", {}), ts.get("PASS_TO_PASS", {})
    return {
        "applied": r.get("patch_successfully_applied", False),
        "parsed_tests": len(status_map),
        "f2p_ok": len(f2p.get("success", [])), "f2p_fail": f2p.get("failure", []),
        "p2p_ok": len(p2p.get("success", [])), "p2p_fail": p2p.get("failure", []),
        "resolved_harness": r.get("resolved", False),
    }


def cmd_collect(a):
    global _SPLIT
    _SPLIT = a.split
    work = Path(a.work)
    stem = Path(a.gen).stem
    gens = {g["instance_id"]: g for g in load_jsonl(a.gen)}
    stages = load_jsonl(work / f"{stem}_stages.jsonl")
    rows = []
    for s in stages:
        g = gens[s["instance_id"]]
        row = {k: s.get(k) for k in ("instance_id", "model", "e1", "e2", "cause")}
        row.update({k: g.get(k) for k in (
            "repo", "prompt_tokens", "output_tokens", "file_tokens", "file_lines",
            "truncated", "gen_time_s", "energy_wh", "mean_power_w", "peak_mem_gb",
            "finish_reason")})
        row.update(e3=False, e4=False, e5=False, resolved=False,
                   n_f2p_fail=None, n_p2p_fail=None, n_p2p_fail_rerun=None,
                   resolved_harness=None)
        if s["e2"]:
            h = harness_result(a.run_id, s["model"], s["instance_id"], a.logs)
            if h is None:
                row["cause"] = "harness_no_report"
            else:
                row["e3"] = bool(h["applied"] and h["parsed_tests"] > 0)
                if not row["e3"]:
                    row["cause"] = "not_executable" if h["applied"] else "harness_apply_failed"
                else:
                    p2p_fail = set(h["p2p_fail"])
                    if p2p_fail and a.rerun_id:
                        h2 = harness_result(a.rerun_id, s["model"], s["instance_id"], a.logs)
                        if h2 is not None:
                            p2p_fail &= set(h2["p2p_fail"])  # falla en ambas ejecuciones
                            row["n_p2p_fail_rerun"] = len(h2["p2p_fail"])
                    row["e4"] = len(h["f2p_fail"]) == 0 and h["f2p_ok"] > 0
                    row["e5"] = len(p2p_fail) > 0
                    row["resolved"] = row["e4"] and not row["e5"]
                    row["n_f2p_fail"] = len(h["f2p_fail"])
                    row["n_p2p_fail"] = len(p2p_fail)
                    row["resolved_harness"] = h["resolved_harness"]
        rows.append(row)
    out = work / f"{stem}_results.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    print(f"{stem}: n={n} " + " ".join(
        f"{k.upper()}={sum(bool(r[k]) for r in rows)}"
        for k in ("e1", "e2", "e3", "e4", "e5", "resolved")))
    print("->", out)


def cmd_flaky(a):
    """Instancias con alguna P2P fallida: candidatas a reejecucion."""
    global _SPLIT
    _SPLIT = a.split
    work = Path(a.work)
    stem = Path(a.gen).stem
    ids = []
    for s in load_jsonl(work / f"{stem}_stages.jsonl"):
        if s["e2"]:
            h = harness_result(a.run_id, s["model"], s["instance_id"], a.logs)
            if h and h["p2p_fail"]:
                ids.append(s["instance_id"])
    print(" ".join(ids))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "collect", "flaky"):
        p = sub.add_parser(name)
        p.add_argument("--gen", required=True)
        p.add_argument("--work", required=True)
        p.add_argument("--split", default="dev")
        p.add_argument("--logs", default="logs")
        p.add_argument("--run-id")
        p.add_argument("--rerun-id")
        p.add_argument("--valid", help="archivo con los instance_id validos (gold resuelto)")
    a = ap.parse_args()
    {"prepare": cmd_prepare, "collect": cmd_collect, "flaky": cmd_flaky}[a.cmd](a)


if __name__ == "__main__":
    main()
