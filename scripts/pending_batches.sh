#!/usr/bin/env bash
# Completa las instancias de test pendientes por tandas: verificacion gold, conversion,
# harness de los modelos, colecta, exportacion y borrado de imagenes. Se detiene si el
# disco de Windows baja de MIN_GB.
# Uso: pending_batches.sh <archivo_ids> <tamano_tanda>
set -uo pipefail
IDS_FILE="$1"; BATCH="${2:-5}"; MIN_GB=6
S="$(cd "$(dirname "$0")" && pwd)"
WIN="/mnt/c/Users/jhona/Documents/Projects/CS_Artículo/kaggle_out"
mapfile -t ALL < <(tr -d '' < "$IDS_FILE" | grep .)
cd ~/apr || exit 1
for ((i = 0; i < ${#ALL[@]}; i += BATCH)); do
  free=$(df --output=avail -BG /mnt/c | tail -1 | tr -dc 0-9)
  if [ "$free" -lt "$MIN_GB" ]; then echo "ALTO: solo ${free} GB libres en C:"; exit 2; fi
  B=("${ALL[@]:i:BATCH}")
  echo "=== tanda $((i / BATCH + 1)): ${B[*]} (libres: ${free} GB)"
  .venv/bin/python -m swebench.harness.run_evaluation -d SWE-bench/SWE-bench_Lite -s test \
    -p gold -id gold_test50 --max_workers 3 -i "${B[@]}" 2>&1 | grep -E "^Instances (resolved|unresolved)|Error|error|Traceback|rate" | head -8
  bash "$S/prepare_session.sh" "$WIN/A/out" 2>&1 | grep -E "^qwen7_test50"
  bash "$S/prepare_session.sh" "$WIN/B/out" 2>&1 | grep -E "^qwen14_test50"
  bash "$S/eval_preds.sh" qwen7_test50 qwen14_test50 2>&1 | grep -E "^(===|Instances resolved)"
  bash "$S/collect.sh" qwen7_test50 qwen14_test50 2>&1 | grep -E "n=|reejecutando"
  for id in "${B[@]}"; do
    docker images --format '{{.Repository}}:{{.Tag}}' | grep -- "${id//__/_1776_}" | xargs -r docker rmi -f >/dev/null
  done
done
bash "$S/export_run.sh" gold_test50 gold >/dev/null
bash "$S/export_model_runs.sh" qwen7_test50 qwen14_test50
echo "FIN"
