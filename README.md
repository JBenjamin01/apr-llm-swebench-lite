# APR con LLM de pesos abiertos en SWE-bench Lite

Paquete de replicación del artículo *«Evaluación experimental de modelos de lenguaje de código abierto para la reparación automática de issues reales en SWE-bench Lite»* (J. Mamani, A. Ore — Escuela Profesional de Ingeniería de Sistemas, UNSA).

El estudio descompone el resultado de cada instancia en cinco etapas:

| Etapa | Criterio |
|---|---|
| E1 Formato válido | La salida contiene al menos un bloque SEARCH/REPLACE completo |
| E2 Aplicable | Ruta existente, fragmento SEARCH único, sin solapes, diff no vacío y `git apply --check` correcto |
| E3 Ejecutable | El harness ejecuta las pruebas y produce resultados interpretables |
| E4 Corrige el defecto | Todas las pruebas FAIL_TO_PASS pasan |
| E5 Regresión | Alguna PASS_TO_PASS falla (en dos ejecuciones) |
| Resuelto | E4 ∧ ¬E5 (criterio de SWE-bench) |

## Estructura

```
kaggle/      gen.py y notebook de generación (vLLM, GPU T4 x2 en Kaggle)
src/         convert.py (SEARCH/REPLACE -> diff, E1/E2)
             pipeline.py (E1-E5 a partir de los informes del harness)
             analysis.py (Wilson, McNemar, Wilcoxon, Cliff, Holm, figura)
scripts/     utilidades para WSL
resultados/  salidas crudas, predicciones, informes del harness y análisis
```

## Reproducir

1. **Generación** (Kaggle, GPU T4 x2, Internet activado): importar `kaggle/apr_piloto_generacion.ipynb` y ejecutar. Produce `out/<modelo>_<split>.jsonl` con el prompt, la salida cruda, los tokens, el tiempo, la energía y la memoria de la GPU por instancia.
2. **Validación** (Linux o WSL2 con Docker; `swebench==5.0.2`, Python 3.11):

   ```bash
   python src/pipeline.py prepare --gen out/qwen7_dev.jsonl --work work/
   python -m swebench.harness.run_evaluation -d SWE-bench/SWE-bench_Lite -s dev \
       -p work/qwen7_dev_preds.jsonl -id qwen7_dev --max_workers 3
   python src/pipeline.py collect --gen out/qwen7_dev.jsonl --work work/ --run-id qwen7_dev
   ```
3. **Análisis**: `python src/analysis.py --results "work/*_results.csv" --meta "out/*_meta.json" --out analisis/`

## Verificación del entorno (parches de referencia, split dev)

Con los parches de los desarrolladores, el harness oficial resuelve **15 de 23** instancias. Las 8 restantes fallan por deriva del entorno y se excluyen del piloto:

| Instancias | Causa |
|---|---|
| pvlib-python 1072, 1154, 1606, 1707, 1854 | NumPy 2.x en la imagen: `np.Inf` eliminado; falla `conftest.py` |
| pyvista 4315 | Falta `libGL.so.1` en la imagen |
| pydicom 1139, 1413 | pytest reciente no ejecuta `setup` estilo nose (`TestBadValueRead`) |

Los informes completos están en `resultados/harness/gold_dev/`.

## Resultados

**Prueba de viabilidad** (15 instancias dev válidas; criterios en la Tabla V del artículo):

| Modelo (AWQ 4 bits) | E1 | E3 | Mediana gen. | Decisión |
|---|---|---|---|---|
| Qwen2.5-Coder-7B | 13/15 | 9/15 | 20 s | Seleccionado |
| Llama-3.1-8B | 2/15 | 1/15 | 43 s | Excluido (omite el separador `=======`) |
| Qwen2.5-Coder-14B | 13/15 | 7/15 | 37 s | Excluido (E3 < 50 %); análisis complementario |
| Qwen2.5-Coder-32B | — | — | — | No carga: la T4 no admite caché KV FP8 |

**Muestra de test** (50 instancias aleatorias, semilla 2026; las 50 verificadas con el parche gold):

| | E1 | E2 | E3 | E4 | E5 | Resueltas |
|---|---|---|---|---|---|---|
| Qwen2.5-Coder-7B | 43 | 26 | 24 | 5 | 7 | **5 (10 %)** |
| Qwen2.5-Coder-14B (compl.) | 45 | 31 | 30 | 4 | 7 | **3 (6 %)** |

Análisis completo en `resultados/analisis_dev/` y `resultados/analisis_test50/`; salidas crudas en
`resultados/generacion/`; informes del harness en `resultados/harness/`. Los resultados con la primera
versión del conversor (sin re-indentación relativa) se conservan como `*_v1` en el entorno de validación.
