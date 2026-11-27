#!/usr/bin/env bash
# Muestra por que fallan E3 las instancias que superan E2.
# Uso: inspect_e3.sh <stem>
stem="$1"
cd ~/apr || exit 1
model="${stem%%_*}"
python3 - "$stem" "$model" <<'EOF'
import csv, sys, json, re, os
stem, model = sys.argv[1], sys.argv[2]
for r in csv.DictReader(open(f"work/{stem}_results.csv")):
    if r["e2"] == "True" and r["e3"] == "False":
        d = f"logs/run_evaluation/{stem}/{model}/{r['instance_id']}"
        rep = json.load(open(f"{d}/report.json"))[r["instance_id"]] if os.path.exists(f"{d}/report.json") else {}
        log = open(f"{d}/test_output.txt", errors="ignore").read() if os.path.exists(f"{d}/test_output.txt") else ""
        errs = re.findall(r"^(?:E\s+)?(\w*Error: .{0,120})", log, re.M)
        print(r["instance_id"], r["cause"], "applied=", rep.get("patch_successfully_applied"))
        print("    ", (errs[-1] if errs else log[-300:].replace("\n", " | ")))
EOF
