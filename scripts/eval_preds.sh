#!/usr/bin/env bash
# Valida con el harness las predicciones preparadas (work/<stem>_preds.jsonl).
# Uso: eval_preds.sh <stem> [<stem> ...]    p. ej.: eval_preds.sh qwen7_dev llama8_dev
# El split se deduce del sufijo (_dev -> dev; _test50 -> test). run_id = stem.
cd ~/apr || exit 1
for stem in "$@"; do
  case "$stem" in *_dev) split=dev ;; *) split=test ;; esac
  preds="work/${stem}_preds.jsonl"
  n=$(wc -l < "$preds")
  echo "=== $stem ($n predicciones, split $split)"
  if [ "$n" -eq 0 ]; then continue; fi
  .venv/bin/python -m swebench.harness.run_evaluation -d SWE-bench/SWE-bench_Lite \
    -s "$split" -p "$preds" -id "$stem" --max_workers 3 2>&1 | grep -E "^(Total|Instances|Unremoved|Report)"
done
docker ps -q | wc -l
docker system df | head -2
