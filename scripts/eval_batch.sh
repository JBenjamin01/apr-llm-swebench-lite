#!/usr/bin/env bash
# Ejecuta el harness sobre un subconjunto de la muestra de test filtrado por patron.
# Uso: eval_batch.sh <predicciones|gold> <run_id> <patron> [split] [archivo_ids]
#   eval_batch.sh gold gold_test50 sympy
set -euo pipefail
PREDS="$1"; RUN="$2"; PAT="$3"; SPLIT="${4:-test}"; IDS_FILE="${5:-$HOME/apr/sample_test50_seed2026.txt}"
cd ~/apr
mapfile -t IDS < <(grep -- "$PAT" "$IDS_FILE")
echo "Instancias: ${#IDS[@]}"
.venv/bin/python -m swebench.harness.run_evaluation -d SWE-bench/SWE-bench_Lite -s "$SPLIT" \
  -p "$PREDS" -id "$RUN" --max_workers 3 -i "${IDS[@]}" 2>&1 | tail -14
docker system df | head -2
