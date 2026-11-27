#!/usr/bin/env bash
# Exporta los informes del harness de los modelos (incluidas reejecuciones) al repositorio.
# Uso: export_model_runs.sh <stem> [<stem> ...]
REPO="$(cd "$(dirname "$0")/.." && pwd)"
for stem in "$@"; do
  model="${stem%%_*}"
  for run in "$stem" "${stem}_rerun"; do
    src=~/apr/logs/run_evaluation/"$run"/"$model"
    [ -d "$src" ] || continue
    for d in "$src"/*/; do
      iid="$(basename "$d")"; dest="$REPO/resultados/harness/$run/$iid"; mkdir -p "$dest"
      for f in report.json patch.diff test_output.txt; do [ -f "$d/$f" ] && cp "$d/$f" "$dest/"; done
    done
    echo "exportado $run"
  done
done
