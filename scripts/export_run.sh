#!/usr/bin/env bash
# Copia los informes de una ejecucion del harness (WSL ~/apr) al repositorio.
# Uso: export_run.sh <run_id> <modelo>    p. ej.: export_run.sh gold_dev gold
set -euo pipefail
RUN="$1"; MODEL="$2"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$REPO/resultados/harness/$RUN"
mkdir -p "$DEST"
cp ~/apr/"$MODEL.$RUN.json" "$DEST/summary.json"
for d in ~/apr/logs/run_evaluation/"$RUN"/"$MODEL"/*/; do
  iid="$(basename "$d")"
  mkdir -p "$DEST/$iid"
  for f in report.json patch.diff test_output.txt run_instance.log; do
    [ -f "$d/$f" ] && cp "$d/$f" "$DEST/$iid/"
  done
done
echo "Exportado en $DEST"
