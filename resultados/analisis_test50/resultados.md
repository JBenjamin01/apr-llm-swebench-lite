# Resultados del analisis

## Embudo por etapa (absoluto sobre n; IC Wilson 95 %)

| Modelo | n | E1 | E2 | E3 | E4 | E5 | RESOLVED |
|---|---|---|---|---|---|---|---|
| qwen14 | 35 | 31 (88.6 %; 74.0–95.5) | 20 (57.1 %; 40.9–72.0) | 19 (54.3 %; 38.2–69.5) | 2 (5.7 %; 1.6–18.6) | 2 (5.7 %; 1.6–18.6) | 1 (2.9 %; 0.5–14.5) |
| qwen7 | 35 | 32 (91.4 %; 77.6–97.0) | 20 (57.1 %; 40.9–72.0) | 18 (51.4 %; 35.6–67.0) | 3 (8.6 %; 3.0–22.4) | 6 (17.1 %; 8.1–32.7) | 3 (8.6 %; 3.0–22.4) |

## Tasas condicionales

| Modelo | E2/E1 | E3/E2 | E4/E3 | E5/E3 | E5/E4 |
|---|---|---|---|---|---|
| qwen14 | 20/31 (65 %) | 19/20 (95 %) | 2/19 (11 %) | 2/19 (11 %) | 1/2 (50 %) |
| qwen7 | 20/32 (62 %) | 18/20 (90 %) | 3/18 (17 %) | 6/18 (33 %) | 0/3 (0 %) |

## Causas de fallo (primera etapa fallida)

| Causa | qwen14 | qwen7 |
|---|---|---|
| empty_diff | 1 | 2 |
| no_blocks | 2 | 0 |
| not_executable | 1 | 2 |
| search_ambiguous | 1 | 1 |
| search_not_found | 8 | 9 |
| truncated_output | 2 | 3 |
| wrong_path | 1 | 0 |

## Costo (RQ4)

| Modelo | t. gen. mediana [IQR] (s) | tokens salida mediana | pesos en GPU (GiB) | energía total (Wh) | Wh por instancia | GPU-s por resuelta | prompts recortados | salidas truncadas |
|---|---|---|---|---|---|---|---|---|
| qwen14 | 66.5 [25.8–177.2] | 204 | 9.34 | 154.6 | 4.42 | 8714 | 1 | 3 |
| qwen7 | 22.8 [11.3–129.7] | 211 | 5.29 | 54.7 | 1.56 | 972 | 1 | 3 |

## Comparaciones apareadas (McNemar exacto, Holm)

| Métrica | Par | b (A sí, B no) | c (A no, B sí) | p | p Holm |
|---|---|---|---|---|---|
| E1 | qwen14 vs qwen7 | 2 | 3 | 1.000 | 1.000 |
| E2 | qwen14 vs qwen7 | 8 | 8 | 1.000 | 1.000 |
| E3 | qwen14 vs qwen7 | 9 | 8 | 1.000 | 1.000 |
| E4 | qwen14 vs qwen7 | 2 | 3 | 1.000 | 1.000 |
| E5 | qwen14 vs qwen7 | 0 | 4 | 0.125 | 0.125 |
| RESOLVED | qwen14 vs qwen7 | 1 | 3 | 0.625 | 0.625 |

## Tiempo de generación (Wilcoxon apareado, delta de Cliff, Holm)

| Par | mediana A (s) | mediana B (s) | p | p Holm | δ de Cliff |
|---|---|---|---|---|---|
| qwen14 vs qwen7 | 66.5 | 22.8 | 0.0001 | 0.0001 | +0.33 |

## Resueltas por repositorio (exploratorio)

| Repositorio | n | qwen14 | qwen7 |
|---|---|---|---|
| astropy/astropy | 2 | 0 | 0 |
| django/django | 13 | 1 | 3 |
| matplotlib/matplotlib | 2 | 0 | 0 |
| pallets/flask | 1 | 0 | 0 |
| sympy/sympy | 17 | 0 | 0 |
