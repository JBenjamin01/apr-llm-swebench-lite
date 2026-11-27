#!/usr/bin/env bash
# E3-E5 por instancia. Si hay P2P fallidas, las reejecuta (run_id <stem>_rerun)
# y vuelve a calcular con la interseccion de ambas ejecuciones.
# Uso: collect.sh <stem> [<stem> ...]
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd ~/apr || exit 1
for stem in "$@"; do
  case "$stem" in *_dev) split=dev ;; *) split=test ;; esac
  P=".venv/bin/python $REPO/src/pipeline.py"
  mapfile -t FL < <($P flaky --gen "out/$stem.jsonl" --work work --split "$split" --run-id "$stem" | tr ' ' '\n' | grep .)
  if [ "${#FL[@]}" -gt 0 ]; then
    echo "[$stem] reejecutando ${#FL[@]} instancias con P2P fallidas: ${FL[*]}"
    .venv/bin/python -m swebench.harness.run_evaluation -d SWE-bench/SWE-bench_Lite -s "$split" \
      -p "work/${stem}_preds.jsonl" -id "${stem}_rerun" --max_workers 3 -i "${FL[@]}" >/dev/null 2>&1
    $P collect --gen "out/$stem.jsonl" --work work --split "$split" --run-id "$stem" --rerun-id "${stem}_rerun"
  else
    $P collect --gen "out/$stem.jsonl" --work work --split "$split" --run-id "$stem"
  fi
done
