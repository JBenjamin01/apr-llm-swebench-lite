# Resultados del analisis

## Embudo por etapa (absoluto sobre n; IC Wilson 95 %)

| Modelo | n | E1 | E2 | E3 | E4 | E5 | RESOLVED |
|---|---|---|---|---|---|---|---|
| llama8 | 15 | 2 (13.3 %; 3.7–37.9) | 1 (6.7 %; 1.2–29.8) | 1 (6.7 %; 1.2–29.8) | 0 (0.0 %; 0.0–20.4) | 0 (0.0 %; 0.0–20.4) | 0 (0.0 %; 0.0–20.4) |
| qwen14 | 15 | 13 (86.7 %; 62.1–96.3) | 7 (46.7 %; 24.8–69.9) | 7 (46.7 %; 24.8–69.9) | 2 (13.3 %; 3.7–37.9) | 0 (0.0 %; 0.0–20.4) | 2 (13.3 %; 3.7–37.9) |
| qwen7 | 15 | 13 (86.7 %; 62.1–96.3) | 11 (73.3 %; 48.0–89.1) | 9 (60.0 %; 35.7–80.2) | 0 (0.0 %; 0.0–20.4) | 2 (13.3 %; 3.7–37.9) | 0 (0.0 %; 0.0–20.4) |

## Tasas condicionales

| Modelo | E2/E1 | E3/E2 | E4/E3 | E5/E3 | E5/E4 |
|---|---|---|---|---|---|
| llama8 | 1/2 (50 %) | 1/1 (100 %) | 0/1 (0 %) | 0/1 (0 %) | — |
| qwen14 | 7/13 (54 %) | 7/7 (100 %) | 2/7 (29 %) | 0/7 (0 %) | 0/2 (0 %) |
| qwen7 | 11/13 (85 %) | 9/11 (82 %) | 0/9 (0 %) | 2/9 (22 %) | — |

## Causas de fallo (primera etapa fallida)

| Causa | llama8 | qwen14 | qwen7 |
|---|---|---|---|
| no_blocks | 12 | 2 | 1 |
| not_executable | 0 | 0 | 2 |
| search_not_found | 1 | 6 | 2 |
| truncated_output | 1 | 0 | 1 |

## Costo (RQ4)

| Modelo | t. gen. mediana [IQR] (s) | tokens salida mediana | pesos en GPU (GiB) | energía total (Wh) | Wh por instancia | GPU-s por resuelta | prompts recortados | salidas truncadas |
|---|---|---|---|---|---|---|---|---|
| llama8 | 42.6 [28.9–62.3] | 514 | 5.39 | 19.9 | 1.33 | inf | 1 | 1 |
| qwen14 | 36.7 [22.6–69.8] | 141 | 9.34 | 31.6 | 2.11 | 941 | 1 | 0 |
| qwen7 | 20.2 [8.3–32.4] | 95 | 5.29 | 10.9 | 0.73 | inf | 1 | 1 |

## Comparaciones apareadas (McNemar exacto, Holm)

| Métrica | Par | b (A sí, B no) | c (A no, B sí) | p | p Holm |
|---|---|---|---|---|---|
| E1 | llama8 vs qwen14 | 0 | 11 | 0.001 | 0.003 |
| E1 | llama8 vs qwen7 | 0 | 11 | 0.001 | 0.003 |
| E1 | qwen14 vs qwen7 | 2 | 2 | 1.000 | 1.000 |
| E2 | llama8 vs qwen14 | 1 | 7 | 0.070 | 0.141 |
| E2 | llama8 vs qwen7 | 0 | 10 | 0.002 | 0.006 |
| E2 | qwen14 vs qwen7 | 2 | 6 | 0.289 | 0.289 |
| E3 | llama8 vs qwen14 | 1 | 7 | 0.070 | 0.141 |
| E3 | llama8 vs qwen7 | 0 | 8 | 0.008 | 0.023 |
| E3 | qwen14 vs qwen7 | 3 | 5 | 0.727 | 0.727 |
| E4 | llama8 vs qwen14 | 0 | 2 | 0.500 | 1.000 |
| E4 | llama8 vs qwen7 | 0 | 0 | 1.000 | 1.000 |
| E4 | qwen14 vs qwen7 | 2 | 0 | 0.500 | 1.000 |
| E5 | llama8 vs qwen14 | 0 | 0 | 1.000 | 1.000 |
| E5 | llama8 vs qwen7 | 0 | 2 | 0.500 | 1.000 |
| E5 | qwen14 vs qwen7 | 0 | 2 | 0.500 | 1.000 |
| RESOLVED | llama8 vs qwen14 | 0 | 2 | 0.500 | 1.000 |
| RESOLVED | llama8 vs qwen7 | 0 | 0 | 1.000 | 1.000 |
| RESOLVED | qwen14 vs qwen7 | 2 | 0 | 0.500 | 1.000 |

## Tiempo de generación (Wilcoxon apareado, delta de Cliff, Holm)

| Par | mediana A (s) | mediana B (s) | p | p Holm | δ de Cliff |
|---|---|---|---|---|---|
| llama8 vs qwen14 | 42.6 | 36.7 | 0.4887 | 0.4887 | +0.09 |
| llama8 vs qwen7 | 42.6 | 20.2 | 0.0043 | 0.0128 | +0.45 |
| qwen14 vs qwen7 | 36.7 | 20.2 | 0.0043 | 0.0128 | +0.45 |

## Resueltas por repositorio (exploratorio)

| Repositorio | n | llama8 | qwen14 | qwen7 |
|---|---|---|---|---|
| marshmallow-code/marshmallow | 2 | 0 | 0 | 0 |
| pydicom/pydicom | 3 | 0 | 1 | 0 |
| pylint-dev/astroid | 5 | 0 | 1 | 0 |
| sqlfluff/sqlfluff | 5 | 0 | 0 | 0 |
