#!/usr/bin/env bash
# Borra imagenes de evaluacion de SWE-bench que coinciden con los patrones dados.
# Uso: rm_images.sh <patron> [<patron> ...]   p. ej.: rm_images.sh pvlib pyvista
for pat in "$@"; do
  docker images --format '{{.Repository}}:{{.Tag}}' | grep '^swebench/sweb.eval' | grep -- "$pat" |
    while read -r img; do docker rmi -f "$img" >/dev/null && echo "borrada $img"; done
done
docker system df | head -2
