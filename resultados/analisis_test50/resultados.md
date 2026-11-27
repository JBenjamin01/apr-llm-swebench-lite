# Resultados del analisis

## Embudo por etapa (absoluto sobre n; IC Wilson 95 %)

| Modelo | n | E1 | E2 | E3 | E4 | E5 | RESOLVED |
|---|---|---|---|---|---|---|---|
| qwen14 | 50 | 45 (90.0 %; 78.6–95.7) | 31 (62.0 %; 48.2–74.1) | 30 (60.0 %; 46.2–72.4) | 4 (8.0 %; 3.2–18.8) | 7 (14.0 %; 7.0–26.2) | 3 (6.0 %; 2.1–16.2) |
| qwen7 | 50 | 43 (86.0 %; 73.8–93.0) | 26 (52.0 %; 38.5–65.2) | 24 (48.0 %; 34.8–61.5) | 5 (10.0 %; 4.3–21.4) | 7 (14.0 %; 7.0–26.2) | 5 (10.0 %; 4.3–21.4) |

## Tasas condicionales

| Modelo | E2/E1 | E3/E2 | E4/E3 | E5/E3 | E5/E4 |
|---|---|---|---|---|---|
| qwen14 | 31/45 (69 %) | 30/31 (97 %) | 4/30 (13 %) | 7/30 (23 %) | 1/4 (25 %) |
| qwen7 | 26/43 (60 %) | 24/26 (92 %) | 5/24 (21 %) | 7/24 (29 %) | 0/5 (0 %) |

## Causas de fallo (primera etapa fallida)

| Causa | qwen14 | qwen7 |
|---|---|---|
| empty_diff | 1 | 2 |
| no_blocks | 3 | 0 |
| not_executable | 1 | 2 |
| overlap | 1 | 1 |
| search_ambiguous | 1 | 1 |
| search_not_found | 10 | 13 |
| truncated_output | 2 | 7 |
| wrong_path | 1 | 0 |

## Costo (RQ4)

| Modelo | t. gen. mediana [IQR] (s) | tokens salida mediana | pesos en GPU (GiB) | energía total (Wh) | Wh por instancia | GPU-s por resuelta | prompts recortados | salidas truncadas |
|---|---|---|---|---|---|---|---|---|
| qwen14 | 68.2 [30.1–143.2] | 224 | 9.34 | 199.7 | 3.99 | 3777 | 1 | 3 |
| qwen7 | 43.6 [13.3–118.9] | 220 | 5.29 | 75.6 | 1.51 | 806 | 1 | 8 |

## Comparaciones apareadas (McNemar exacto, Holm)

| Métrica | Par | b (A sí, B no) | c (A no, B sí) | p | p Holm |
|---|---|---|---|---|---|
| E1 | qwen14 vs qwen7 | 5 | 3 | 0.727 | 0.727 |
| E2 | qwen14 vs qwen7 | 15 | 10 | 0.424 | 0.424 |
| E3 | qwen14 vs qwen7 | 16 | 10 | 0.327 | 0.327 |
| E4 | qwen14 vs qwen7 | 3 | 4 | 1.000 | 1.000 |
| E5 | qwen14 vs qwen7 | 4 | 4 | 1.000 | 1.000 |
| RESOLVED | qwen14 vs qwen7 | 2 | 4 | 0.688 | 0.688 |

## Tiempo de generación (Wilcoxon apareado, delta de Cliff, Holm)

| Par | mediana A (s) | mediana B (s) | p | p Holm | δ de Cliff |
|---|---|---|---|---|---|
| qwen14 vs qwen7 | 68.2 | 43.6 | 0.0003 | 0.0003 | +0.24 |

## Resueltas por repositorio (exploratorio)

| Repositorio | n | qwen14 | qwen7 |
|---|---|---|---|
| astropy/astropy | 2 | 0 | 0 |
| django/django | 13 | 1 | 3 |
| matplotlib/matplotlib | 2 | 0 | 0 |
| pallets/flask | 2 | 0 | 0 |
| pydata/xarray | 2 | 1 | 1 |
| pylint-dev/pylint | 1 | 0 | 0 |
| pytest-dev/pytest | 3 | 0 | 1 |
| scikit-learn/scikit-learn | 5 | 1 | 0 |
| sphinx-doc/sphinx | 3 | 0 | 0 |
| sympy/sympy | 17 | 0 | 0 |
