# Anomalias investigadas

Cada item foi observado na fonte real. O pipeline **não corrige** dados oficiais: sinaliza, mede e preserva o valor
publicado. As sinalizações por município ficam em `gold.indicador_municipal` (`flag_*` e `selo_confianca`).

| # | Anomalia | Como aparece | Tratamento |
|---|---|---|---|
| 1 | Rede `0` (total) quase vazia em 2024 | Em `uf`, só 1 UF tem a linha de rede 0 | O Termômetro usa as redes 2, 3 e 5; rede 0 não é base de comparação |
| 2 | Municípios sem meta em 2024 | 120 linhas de `meta_alfabetizacao_municipio` com meta nula: 22 são todo o Acre; as outras 98 estão em 15 UFs (RS 20, MG 17, SC 16, RN 12, AM 7, PA 6, SP 5, BA 4, demais ≤ 3) | Status `sem_meta` (nunca zero, nunca "não atingiu") |
| 3 | SP, AC e DF ausentes nos microdados de 2023 | Sem linhas em `alunos` para essas UFs/ano | Flag `sem_microdados`; selo máximo `media` |
| 4 | Metas nulas para AC, DF e RR (nível UF) | AC e DF em 2024 e RR em 2025 têm taxa, mas meta nula | `sem_meta`; regra informativa `gold.termometro.sem_meta_rara` acompanha a proporção |
| 4b | Roraima sem resultado em 2024 | `taxa_alfabetizacao` e meta nulas para RR/2024 (rede 5) | Status `sem_resultado`; o valor nunca vira zero |
| 5 | Valores de 2025 arredondados para inteiro | `meta_brasil` e `meta_uf` de 2025 | Preservado como publicado; documentado para não ser lido como precisão |
| 6 | Mudança de *vintage* da meta | A meta de uma mesma célula mudou entre publicações (ex.: 63,77 → 64,0) | A Bronze versionada guarda ambas; o Gold usa a versão vigente |
| 7 | Recálculo nacional de 2023 difere do oficial | Microdados dão 57,46; oficial 55,9 | Hipótese principal: ausência de SP/AC/DF nos microdados de 2023. `gold.reconciliacao` mede a diferença; a regra `gold.reconciliacao.diferenca_nacional_pp` a registra |

## Regras de sinalização por município

* `sem_microdados`: não há alunos avaliados no município/ano.
* `amostra_pequena`: menos de 30 avaliados.
* `divergencia_oficial`: |recalculado − oficial| > 1,0 p.p.
* `queda_brusca`: variação ≤ −15 p.p. frente ao ano anterior.

**Selo de confiança:** `baixa` se divergência ou amostra pequena; `media` se queda brusca ou sem microdados; senão `alta`.
Limiares em `config/sources.yaml` (`anomaly`).

**Selo de confiança na primeira execução:** 10,07% dos indicadores municipais receberam o selo `baixa`, um pouco
acima do limite informativo de 10% (`gold.indicador_municipal.selo_baixo_raro`). A regra é informativa e foi mantida
assim de propósito: o limite não foi ajustado para esconder o achado.

> Os itens 1–7 vêm da medição da fonte (ver [`fase1/medicao-fonte.md`](fase1/medicao-fonte.md)). Os números de
> reconciliação de cada execução ficam em `docs/execucao-cloud/evidencias.md` e em `gold.reconciliacao`.
