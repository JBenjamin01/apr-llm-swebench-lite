"""Conversor determinista SEARCH/REPLACE -> diff unificado (Seccion IV-C3).

Etapas:
  E1 (formato)   : la salida contiene al menos un bloque completo.
  E2 (aplicable) : ruta existente, cada SEARCH aparece una sola vez (exacto o,
                   en su defecto, tolerante a espacios), bloques sin solape,
                   diff no vacio y `git apply --check` sin errores.

Ajuste congelado tras la prueba de viabilidad: los marcadores <<<<<<< y >>>>>>>
se aceptan sin las palabras SEARCH/REPLACE (Llama-3.1-8B las omitia); el
separador ======= sigue siendo obligatorio.

Causas de fallo registradas (para la clasificacion de la Seccion IV-F):
  E1: no_blocks, truncated_output
  E2: wrong_path, search_not_found, search_ambiguous, overlap, empty_diff,
      git_apply_failed
"""
import difflib
import os
import re
import subprocess
import tempfile

BLOCK_RE = re.compile(
    r"^[ \t]*(?:```[^\n]*\n)?"          # bandera de codigo opcional
    r"(?:(?P<path>[^\n<>=`]*?)[ \t]*\n)?"  # linea con la ruta (opcional)
    r"(?:```[^\n]*\n)?"
    r"<{5,9} ?(?:SEARCH)?[ \t]*\n"       # SEARCH opcional (ajuste tras el piloto)
    r"(?P<search>.*?)"
    r"^={5,9}[ \t]*\n"                   # el separador sigue siendo obligatorio
    r"(?P<replace>.*?)"
    r"^>{5,9} ?(?:REPLACE)?[ \t]*$",
    re.S | re.M,
)


def parse_blocks(text, default_path):
    """Devuelve lista de (ruta, search, replace). Ruta vacia -> default_path."""
    blocks = []
    for m in BLOCK_RE.finditer(text):
        path = (m.group("path") or "").strip().strip("`*").strip()
        if path.lower().startswith(("file:", "path:")):
            path = path.split(":", 1)[1].strip()
        blocks.append((path or default_path, m.group("search"), m.group("replace")))
    return blocks


def _norm(line):
    return " ".join(line.split())


def locate(content, search):
    """Devuelve (inicio, fin) en caracteres o una causa de fallo."""
    if not search.strip():
        return "search_not_found"
    n = content.count(search)
    if n == 1:
        i = content.index(search)
        return i, i + len(search)
    if n > 1:
        return "search_ambiguous"
    # tolerante a espacios: compara linea a linea normalizando blancos
    c_lines = content.splitlines(keepends=True)
    s_lines = [l for l in search.splitlines()]
    while s_lines and not s_lines[-1].strip():
        s_lines.pop()
    while s_lines and not s_lines[0].strip():
        s_lines.pop(0)
    if not s_lines:
        return "search_not_found"
    target = [_norm(l) for l in s_lines]
    k = len(target)
    hits = [i for i in range(len(c_lines) - k + 1)
            if [_norm(l) for l in c_lines[i:i + k]] == target]
    if not hits:
        return "search_not_found"
    if len(hits) > 1:
        return "search_ambiguous"
    start = sum(len(l) for l in c_lines[:hits[0]])
    end = start + sum(len(l) for l in c_lines[hits[0]:hits[0] + k])
    return start, end


def _fix_eol(replace, original_chunk):
    """Conserva el salto de linea final del fragmento original."""
    if replace and not replace.endswith("\n") and original_chunk.endswith("\n"):
        replace += "\n"
    return replace


def to_diff(raw_output, path, content, repo_dir=None, finish_reason=None):
    """Aplica los bloques y devuelve un dict con e1, e2, cause, diff, n_blocks."""
    res = {"e1": False, "e2": False, "cause": None, "diff": "", "n_blocks": 0}
    blocks = parse_blocks(raw_output or "", path)
    res["n_blocks"] = len(blocks)
    if not blocks:
        res["cause"] = "truncated_output" if finish_reason == "length" else "no_blocks"
        return res
    res["e1"] = True

    spans = []
    for bpath, search, replace in blocks:
        if bpath != path:
            # tolerar prefijos tipo "./" o "a/"
            cand = re.sub(r"^(?:\./|a/|b/)", "", bpath)
            if cand != path:
                res["cause"] = "wrong_path"
                return res
        loc = locate(content, search)
        if isinstance(loc, str):
            res["cause"] = loc
            return res
        spans.append((loc[0], loc[1], replace))

    spans.sort()
    for (a0, a1, _), (b0, b1, _) in zip(spans, spans[1:]):
        if b0 < a1:
            res["cause"] = "overlap"
            return res

    new, last = [], 0
    for s0, s1, rep in spans:
        new.append(content[last:s0])
        new.append(_fix_eol(rep, content[s0:s1]))
        last = s1
    new.append(content[last:])
    new_content = "".join(new)

    diff = "".join(difflib.unified_diff(
        content.splitlines(keepends=True), new_content.splitlines(keepends=True),
        fromfile=f"a/{path}", tofile=f"b/{path}"))
    if not diff.strip():
        res["cause"] = "empty_diff"
        return res
    # difflib no emite la marca "\ No newline..." -> asegurar salto final
    if not diff.endswith("\n"):
        diff += "\n"
    diff = f"diff --git a/{path} b/{path}\n" + diff
    res["diff"] = diff

    if repo_dir is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False) as f:
            f.write(diff)
            tmp = f.name
        try:
            p = subprocess.run(["git", "apply", "--check", tmp], cwd=repo_dir,
                               capture_output=True, text=True)
        finally:
            os.unlink(tmp)
        if p.returncode != 0:
            res["cause"] = "git_apply_failed"
            res["git_error"] = p.stderr.strip()[:500]
            return res
    res["e2"] = True
    return res
