#!/usr/bin/env bash
# Estado de una ejecucion del harness: contenedores vivos e instancias con informe.
# Uso: status_run.sh <run_id> <modelo>
RUN="$1"; MODEL="$2"
docker ps --format '{{.Names}} {{.Status}}'
D=~/apr/logs/run_evaluation/"$RUN"/"$MODEL"
echo "Con report.json: $(ls "$D"/*/report.json 2>/dev/null | wc -l)"
for r in "$D"/*/report.json; do
  iid=$(basename "$(dirname "$r")")
  grep -q '"resolved": true' "$r" && echo "OK   $iid" || echo "FAIL $iid"
done
