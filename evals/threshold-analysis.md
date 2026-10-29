# Análise exploratória de limiar

Em 29/10/2026, os quatro resultados por consulta do [baseline de desenvolvimento top-4](baselines/retrieval-top4.json) foram filtrados novamente por distância, sem novas chamadas. Há cinco documentos e cinco chunks neste corpus; os caminhos recuperados são únicos por consulta, de modo que é possível associá-los às distâncias no relatório. Perguntas respondíveis contam como acerto quando **todas** as fontes esperadas passam pelo limiar; negativas contam como abstenção quando nenhum trecho passa.

| Distância máxima | Respondíveis com todas as fontes | Negativas sem trechos |
| --- | --- | --- |
| 0,25 | 1/11 | 4/4 |
| 0,30 | 6/11 | 4/4 |
| 0,35 | 10/11 | 3/4 |
| 0,40 | 11/11 | 3/4 |
| 0,45 | 11/11 | 1/4 |
| 0,65 (atual) | 11/11 | 0/4 |

O limiar 0,40 é um candidato de experimento, não um valor validado: foi escolhido observando os mesmos 15 casos. O conjunto separado não foi avaliado integralmente, e essas métricas são de recuperação por documento, não de fidelidade da resposta. Não foi alterado o padrão da aplicação.
