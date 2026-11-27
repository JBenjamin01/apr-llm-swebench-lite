#!/usr/bin/env bash
# Inspecciona las instancias cuyo parche de referencia (gold) no se resuelve.
cd ~/apr/logs/run_evaluation/gold_dev/gold || exit 1
for i in pydicom__pydicom-1139 pydicom__pydicom-1413; do
  echo "== $i"
  grep -E "^E  " "$i/test_output.txt" | sort | uniq -c | head -6
done
