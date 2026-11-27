#!/usr/bin/env bash
# Diagnostico: ejecuta la verificacion gold de una instancia y muestra la salida completa.
# Uso: debug_gold.sh <instance_id>
cd ~/apr || exit 1
ls logs/run_evaluation/gold_test50/gold/ | grep -c .
ls -d logs/run_evaluation/gold_test50/gold/"$1" 2>&1
.venv/bin/python -m swebench.harness.run_evaluation -d SWE-bench/SWE-bench_Lite -s test \
  -p gold -id gold_test50 --max_workers 1 -i "$1" 2>&1 | grep -v "examples/s" | tail -25
