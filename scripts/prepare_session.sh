#!/usr/bin/env bash
# Copia las salidas de una sesion de Kaggle a WSL y ejecuta `pipeline.py prepare`.
# Uso: prepare_session.sh <carpeta_out_windows>
#   prepare_session.sh "/mnt/c/Users/jhona/Documents/Projects/CS_Artículo/kaggle_out/A/out"
set -euo pipefail
SRC="$1"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd ~/apr
mkdir -p out work
cp "$SRC"/*.jsonl "$SRC"/*_meta.json "$SRC"/*.log out/ 2>/dev/null || true

# Instancias validas: el parche del desarrollador resuelve la instancia en nuestro entorno
.venv/bin/python - <<'EOF'
import glob, json
for run, name in (("gold_dev", "valid_dev.txt"), ("gold_test50", "valid_test50.txt")):
    ok = []
    for rep in glob.glob(f"logs/run_evaluation/{run}/gold/*/report.json"):
        iid = rep.split("/")[-2]
        if json.load(open(rep))[iid]["resolved"]:
            ok.append(iid)
    open(name, "w").write("\n".join(sorted(ok)) + "\n")
    print(name, len(ok))
EOF

for f in "$SRC"/*.jsonl; do
  stem="$(basename "$f" .jsonl)"
  case "$stem" in
    *_dev) valid=valid_dev.txt ;;
    *_test50) valid=valid_test50.txt ;;
    *) continue ;;
  esac
  .venv/bin/python "$REPO/src/pipeline.py" prepare --gen "out/$stem.jsonl" --work work --valid "$valid"
done
