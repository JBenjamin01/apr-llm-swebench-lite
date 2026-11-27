#!/usr/bin/env bash
# Corre el analisis sobre los resultados de un split y lo copia al repositorio.
# Uso: analyze.sh <dev|test50>
SPLIT="$1"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd ~/apr || exit 1
.venv/bin/python "$REPO/src/analysis.py" --results "work/*_${SPLIT}_results.csv" \
  --meta "out/*_${SPLIT}_meta.json" --out "analisis_${SPLIT}" > /dev/null
mkdir -p "$REPO/resultados/analisis_${SPLIT}"
cp analisis_${SPLIT}/* "$REPO/resultados/analisis_${SPLIT}/"
cp work/*_${SPLIT}_results.csv "$REPO/resultados/analisis_${SPLIT}/"
echo "ok $SPLIT"
