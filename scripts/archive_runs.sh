#!/usr/bin/env bash
# Archiva resultados y logs del harness de los stems dados con un sufijo (p. ej. v1),
# para poder reevaluar con el mismo run_id sin perder la version anterior.
# Uso: archive_runs.sh <sufijo> <stem> [<stem> ...]
SUF="$1"; shift
cd ~/apr || exit 1
for stem in "$@"; do
  for d in "$stem" "${stem}_rerun"; do
    [ -d "logs/run_evaluation/$d" ] && mv "logs/run_evaluation/$d" "logs/run_evaluation/${d}_$SUF"
  done
  for f in work/"${stem}"_{stages.jsonl,preds.jsonl,results.csv}; do
    [ -f "$f" ] && mv "$f" "${f%.*}_$SUF.${f##*.}"
  done
  echo "archivado $stem -> _$SUF"
done
