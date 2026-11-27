"""Generacion de parches (protocolo de la Seccion IV-C del articulo).

Uso (en Kaggle, acelerador GPU T4 x2, Internet activado):
    python gen.py --model qwen7 --split dev
    python gen.py --model qwen14 --split dev --limit 2   # prueba rapida

Un proceso por modelo: vLLM no libera bien la GPU entre modelos.
Salida en /kaggle/working/out/<modelo>_<split>.jsonl (una linea por instancia)
y <modelo>_<split>_meta.json. Si la sesion se corta, al relanzar se omiten
las instancias ya generadas.
"""
import argparse
import ast
import json
import os
import platform
import re
import shutil
import sys
import threading
import time
import traceback

os.environ.setdefault("HF_HOME", "/tmp/hf")  # /kaggle/working tiene solo 20 GB

MODELS = {
    # clave: (repositorio HF, tensor_parallel, kv_cache_dtype)
    "qwen7": ("Qwen/Qwen2.5-Coder-7B-Instruct-AWQ", 1, "auto"),
    "qwen14": ("Qwen/Qwen2.5-Coder-14B-Instruct-AWQ", 2, "auto"),
    "qwen32": ("Qwen/Qwen2.5-Coder-32B-Instruct-AWQ", 2, "fp8"),
    "llama8": ("hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4", 1, "auto"),
}

MAX_CTX = 32768
MAX_OUT = 2048
MARGIN = 64
SEED = 0
OUT_DIR = "/kaggle/working/out"

SYSTEM = (
    "You are an expert software engineer working on a Python repository. "
    "You will receive a GitHub issue and the content of the source file that "
    "must be changed to resolve it. Make the minimal correct change that "
    "resolves the issue."
)

FORMAT_SPEC = """Return your change ONLY as one or more SEARCH/REPLACE blocks, using exactly this format:

{path}
<<<<<<< SEARCH
lines copied exactly from the current file
=======
lines that replace them
>>>>>>> REPLACE

Rules:
- The first line of every block is the file path, exactly as shown above.
- The SEARCH part must match the current file character by character, including indentation and comments, and must appear only once in the file.
- Keep each SEARCH part short: the lines to change plus just enough surrounding lines to make it unique.
- To insert code, put the neighbouring existing lines in SEARCH and repeat them in REPLACE together with the new code.
- Do not edit test files. Do not write explanations; output only the blocks."""

USER_TMPL = """<issue>
{issue}
</issue>

<file path="{path}">
{content}</file>

{fmt}"""


# --------------------------------------------------------------------------
# Contexto: archivo oraculo y recorte
# --------------------------------------------------------------------------
def gold_path(patch):
    paths = re.findall(r"^diff --git a/(\S+) b/", patch, flags=re.M)
    return paths[0]


def fetch_file(repo, commit, path):
    import requests

    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    for attempt in range(5):
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            return r.text
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"No se pudo descargar {url}: {r.status_code}")


def _span(node):
    start = node.lineno
    if getattr(node, "decorator_list", None):
        start = min(d.lineno for d in node.decorator_list)
    return start, node.end_lineno  # 1-based, inclusivo


def truncate(src, issue, budget, ntok):
    """Seccion IV-C1: cabecera + definiciones nombradas en el issue."""
    if ntok(src) <= budget:
        return src, False
    lines = src.splitlines(keepends=True)
    keep = [False] * (len(lines) + 2)

    def mark(a, b):
        for i in range(a, b + 1):
            keep[i] = True

    words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", issue))
    defs = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        tree = None

    if tree is not None:
        for node in tree.body:
            a, b = _span(node)
            if not isinstance(node, defs):
                mark(a, b)  # importaciones, constantes, etc.
            elif isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, defs)]
                named = [m for m in methods if m.name in words]
                if node.name in words and not named:
                    mark(a, b)
                elif named or node.name in words:
                    first = min((_span(m)[0] for m in methods), default=b + 1)
                    mark(a, first - 1)  # firma, docstring y atributos de clase
                    for m in named:
                        mark(*_span(m))
            elif node.name in words:
                mark(a, b)

    out, i = [], 1
    while i <= len(lines):
        if keep[i]:
            out.append(lines[i - 1])
            i += 1
        else:
            j = i
            while j <= len(lines) and not keep[j]:
                j += 1
            gap = lines[i - 1:j - 1]
            if all(not g.strip() for g in gap):
                out.extend(gap)  # solo lineas en blanco: se conservan
            else:
                out.append(f"# ... (lines {i}-{j - 1} omitted) ...\n")
            i = j
    text = "".join(out)

    if ntok(text) > budget:  # ultimo recurso: corte por el final
        acc = []
        for ln in out:
            acc.append(ln)
            if ntok("".join(acc)) > budget - 20:
                acc.pop()
                break
        acc.append("# ... (rest of file omitted) ...\n")
        text = "".join(acc)
    return text, True


# --------------------------------------------------------------------------
# Medicion de GPU (potencia y memoria) con NVML a 1 Hz
# --------------------------------------------------------------------------
class GpuMonitor:
    def __init__(self, period=1.0):
        import pynvml

        pynvml.nvmlInit()
        self.nvml = pynvml
        self.handles = [pynvml.nvmlDeviceGetHandleByIndex(i)
                        for i in range(pynvml.nvmlDeviceGetCount())]
        self.period = period
        self.samples = []  # (t, watts_total, mem_gb_total)
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def read(self):
        w = sum(self.nvml.nvmlDeviceGetPowerUsage(h) for h in self.handles) / 1000
        m = sum(self.nvml.nvmlDeviceGetMemoryInfo(h).used for h in self.handles) / 1e9
        return w, m

    def _run(self):
        while not self._stop.is_set():
            w, m = self.read()
            self.samples.append((time.time(), w, m))
            time.sleep(self.period)

    def window(self, t0, t1):
        pts = [s for s in self.samples if t0 <= s[0] <= t1]
        if len(pts) < 2:
            w, m = self.read()
            return w * (t1 - t0) / 3600, m, w
        wh = sum((b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in zip(pts, pts[1:])) / 3600
        return wh, max(p[2] for p in pts), sum(p[1] for p in pts) / len(pts)

    def gpu_names(self):
        n = self.nvml.nvmlDeviceGetName
        return [x.decode() if isinstance(x, bytes) else x for x in map(n, self.handles)]

    def stop(self):
        self._stop.set()


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--split", default="dev", choices=["dev", "test"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ids", default="", help="lista de instance_id separada por comas")
    ap.add_argument("--gpu-util", type=float, default=0.92)
    ap.add_argument("--kv", default=None, help="sobrescribe kv_cache_dtype")
    args = ap.parse_args()

    from datasets import load_dataset

    hf_id, tp, kv = MODELS[args.model]
    kv = args.kv or kv
    os.makedirs(OUT_DIR, exist_ok=True)
    stem = f"{OUT_DIR}/{args.model}_{args.split}"
    out_path, meta_path = stem + ".jsonl", stem + "_meta.json"

    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split=args.split)
    rows = list(ds)
    if args.ids:
        wanted = set(args.ids.split(","))
        rows = [r for r in rows if r["instance_id"] in wanted]
    if args.limit:
        rows = rows[: args.limit]

    done = set()
    if os.path.exists(out_path):
        with open(out_path) as f:
            done = {json.loads(l)["instance_id"] for l in f if l.strip()}
    rows = [r for r in rows if r["instance_id"] not in done]
    print(f"[{args.model}] {len(rows)} instancias por generar ({len(done)} ya hechas)")
    if not rows:
        return

    mon = GpuMonitor()
    mem_idle = mon.read()[1]

    import torch
    import vllm
    from huggingface_hub import model_info
    from vllm import LLM, SamplingParams

    meta = {
        "model_key": args.model, "hf_id": hf_id, "split": args.split,
        "tensor_parallel": tp, "kv_cache_dtype": kv, "quantization": "awq",
        "dtype": "float16", "max_model_len": MAX_CTX, "max_tokens": MAX_OUT,
        "temperature": 0.0, "seed": SEED, "gpu_memory_utilization": args.gpu_util,
        "gpus": mon.gpu_names(), "vllm": vllm.__version__, "torch": torch.__version__,
        "python": platform.python_version(),
    }
    try:
        meta["hf_revision"] = model_info(hf_id).sha
    except Exception as e:  # noqa: BLE001
        meta["hf_revision"] = f"error: {e}"

    t_load = time.time()
    try:
        llm = LLM(
            model=hf_id, quantization="awq", dtype="half",
            tensor_parallel_size=tp, max_model_len=MAX_CTX,
            gpu_memory_utilization=args.gpu_util, kv_cache_dtype=kv,
            seed=SEED, enforce_eager=True, trust_remote_code=False,
        )
    except Exception as e:  # noqa: BLE001
        meta["load_error"] = f"{type(e).__name__}: {e}"
        meta["load_traceback"] = traceback.format_exc()
        json.dump(meta, open(meta_path, "w"), indent=2)
        print("ERROR AL CARGAR EL MODELO:", meta["load_error"])
        sys.exit(1)
    meta["load_time_s"] = round(time.time() - t_load, 1)
    meta["mem_after_load_gb"] = round(mon.read()[1] - mem_idle, 2)
    json.dump(meta, open(meta_path, "w"), indent=2)

    tok = llm.get_tokenizer()
    ntok = lambda s: len(tok.encode(s, add_special_tokens=False))  # noqa: E731
    sp = SamplingParams(temperature=0.0, max_tokens=MAX_OUT, seed=SEED)

    def build(issue, path, content):
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": USER_TMPL.format(
                    issue=issue, path=path, content=content,
                    fmt=FORMAT_SPEC.format(path=path))}]
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    for k, r in enumerate(rows, 1):
        iid = r["instance_id"]
        rec = {"instance_id": iid, "model": args.model, "repo": r["repo"],
               "base_commit": r["base_commit"]}
        try:
            path = gold_path(r["patch"])
            src = fetch_file(r["repo"], r["base_commit"], path)
            issue = r["problem_statement"]
            overhead = ntok(build(issue, path, ""))
            budget = MAX_CTX - MAX_OUT - MARGIN - overhead
            content, cut = truncate(src, issue, budget, ntok)
            prompt = build(issue, path, content)

            t0 = time.time()
            out = llm.generate([prompt], sp, use_tqdm=False)[0]
            t1 = time.time()
            time.sleep(0.05)
            wh, peak, watts = mon.window(t0 - 1, t1 + 1)
            o = out.outputs[0]
            rec.update({
                "path": path, "raw_output": o.text, "finish_reason": o.finish_reason,
                "prompt_tokens": len(out.prompt_token_ids),
                "output_tokens": len(o.token_ids),
                "file_tokens": ntok(src), "file_lines": src.count("\n") + 1,
                "truncated": cut, "gen_time_s": round(t1 - t0, 3),
                "energy_wh": round(wh, 4), "mean_power_w": round(watts, 1),
                "peak_mem_gb": round(peak, 2), "prompt": prompt, "error": None,
            })
        except Exception as e:  # noqa: BLE001
            rec.update({"error": f"{type(e).__name__}: {e}",
                        "traceback": traceback.format_exc()})
        with open(out_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"[{args.model}] {k}/{len(rows)} {iid} "
              f"t={rec.get('gen_time_s')}s out={rec.get('output_tokens')} "
              f"cut={rec.get('truncated')} err={rec['error']}", flush=True)

    mon.stop()
    meta["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(meta, open(meta_path, "w"), indent=2)
    shutil.rmtree(os.path.join(os.environ["HF_HOME"], "hub"), ignore_errors=True)


if __name__ == "__main__":
    main()
