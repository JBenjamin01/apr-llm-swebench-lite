# Resultados del analisis

## Embudo por etapa (absoluto sobre n; IC Wilson 95 %)

| Modelo | n | E1 | E2 | E3 | E4 | E5 | RESOLVED |
|---|---|---|---|---|---|---|---|
| qwen7 | 35 | 32 (91.4 %; 77.6–97.0) | 20 (57.1 %; 40.9–72.0) | 18 (51.4 %; 35.6–67.0) | 3 (8.6 %; 3.0–22.4) | 6 (17.1 %; 8.1–32.7) | 3 (8.6 %; 3.0–22.4) |

## Tasas condicionales

| Modelo | E2/E1 | E3/E2 | E4/E3 | E5/E3 | E5/E4 |
|---|---|---|---|---|---|
| qwen7 | 20/32 (62 %) | 18/20 (90 %) | 3/18 (17 %) | 6/18 (33 %) | 0/3 (0 %) |

## Causas de fallo (primera etapa fallida)

| Causa | qwen7 |
|---|---|
| empty_diff | 2 |
| not_executable | 2 |
| search_ambiguous | 1 |
| search_not_found | 9 |
| truncated_output | 3 |

## Costo (RQ4)

| Modelo | t. gen. mediana [IQR] (s) | tokens salida mediana | memoria GPU máx. (GB) | energía total (Wh) | Wh por instancia | GPU-s por resuelta | prompts recortados | salidas truncadas |
|---|---|---|---|---|---|---|---|---|
| qwen7 | 22.8 [11.3–129.7] | 211 | 15.0 | 54.7 | 1.56 | 972 | 1 | 3 |

## Resueltas por repositorio (exploratorio)

| Repositorio | n | qwen7 |
|---|---|---|
| astropy/astropy | 2 | 0 |
| django/django | 13 | 3 |
| matplotlib/matplotlib | 2 | 0 |
| pallets/flask | 1 | 0 |
| sympy/sympy | 17 | 0 |
