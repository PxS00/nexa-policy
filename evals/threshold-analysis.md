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

## EmbeddingGemma local: conjunto separado

Filtrando os resultados já registrados em [ollama-holdout.json](baselines/ollama-holdout.json), com os mesmos critérios por documento:

| Distância máxima | Respondíveis com todas as fontes | Negativas sem trechos |
| --- | --- | --- |
| 0,40 | 1/11 | 4/4 |
| 0,45 | 3/11 | 4/4 |
| 0,50 | 4/11 | 4/4 |
| 0,55 | 9/11 | 3/4 |
| 0,60 | 10/11 | 3/4 |
| 0,65 (atual) | 11/11 | 0/4 |

Limiar menor remove evidências esperadas neste conjunto, inclusive em perguntas compostas. Os valores não são diretamente comparáveis aos do Gemini. A geração Groq pode se abster mesmo quando a recuperação encontra trechos: isso foi observado separadamente na avaliação de respostas. Manter o padrão até existir uma validação independente maior.

---

# Comparação de limiares de recuperação

Comparação exploratória em 29/10/2026 com EmbeddingGemma no Ollama, top-4 e os cinco documentos fictícios. A partir dos resultados registrados com limiar 0,65, foram aplicados limiares menores às distâncias já recuperadas. Nos relatórios usados, cada resultado tem um caminho por distância; isso não se aplica automaticamente a bases com vários trechos do mesmo documento.

| Conjunto | Limiar | Respondíveis com todas as fontes | Fontes extras somadas | Negativas sem trechos |
| --- | ---: | ---: | ---: | ---: |
| Desenvolvimento | 0,50 | 6/11 | 0 | 3/4 |
| Desenvolvimento | 0,55 | 6/11 | 1 | 3/4 |
| Desenvolvimento | 0,60 | 10/11 | 2 | 2/4 |
| Desenvolvimento | 0,65 | 11/11 | 12 | 2/4 |
| Separado reutilizado | 0,50 | 4/11 | 0 | 4/4 |
| Separado reutilizado | 0,55 | 9/11 | 2 | 3/4 |
| Separado reutilizado | 0,60 | 10/11 | 3 | 3/4 |
| Separado reutilizado | 0,65 | 11/11 | 13 | 0/4 |
| Estresse | 0,50 | 1/5 | 1 | 2/3 |
| Estresse | 0,55 | 2/5 | 1 | 1/3 |
| Estresse | 0,60 | 4/5 | 1 | 0/3 |
| Estresse | 0,65 | 5/5 | 5 | 0/3 |
| Novos exemplos | 0,50 | 1/4 | 0 | 1/2 |
| Novos exemplos | 0,55 | 2/4 | 0 | 1/2 |
| Novos exemplos | 0,60 | 4/4 | 4 | 1/2 |
| Novos exemplos | 0,65 | 4/4 | 6 | 1/2 |

Os [novos casos](retrieval_extra_cases.json) incluem perguntas de uma e duas fontes e duas perguntas sem resposta. O [relatório](baselines/retrieval-extra-top4.json) foi gerado com Ollama local, sem chamadas de geração; registra árvore alterada porque os casos ainda não estavam commitados. Os demais dados são [desenvolvimento](baselines/ollama-development.json), [separado](baselines/ollama-holdout.json) e [estresse](baselines/stress-top4.json).

Uma fonte extra é um caminho não listado como esperado; pode conter informação útil. Preservar todas as fontes esperadas não comprova que a resposta gerada será correta. Os conjuntos são pequenos, sintéticos e usam o mesmo corpus; o conjunto separado foi reutilizado e não é independente. O limite 0,60 eliminou fontes extras, mas perdeu pelo menos uma fonte esperada em cada um dos três conjuntos anteriores. Portanto, não há evidência suficiente para alterar o padrão 0,65. A comparação top-2 versus top-4 e seus limites estão em [top-k-analysis.md](top-k-analysis.md). Uma alternativa futura exige mais casos e avaliação independente antes de modificar a busca.
