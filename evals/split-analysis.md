# Busca dividida para perguntas com várias partes

Em 29/10/2026, a comparação local com Ollama reindexou os cinco documentos em memória e avaliou os cinco conjuntos, totalizando 50 casos (35 respondíveis e 15 negativos). Nenhuma resposta foi gerada. [Resultados por caso e diagnóstico](baselines/split-comparison.json).

## Causa observada

Na pergunta sobre alimentação e treinamentos, onboarding foi o terceiro resultado com distância 0,660996, acima do teto 0,65. A posição estava dentro de top-4: aumentar top-k não resolveria este caso. Perguntando apenas pelos cursos obrigatórios da primeira semana, a distância foi 0,646560 e passou pelo filtro. Esses valores descrevem este modelo e corpus.

## Alternativas

A divisão experimental ocorre somente em `e` seguido de palavra interrogativa explícita, como `qual`, `quanto`, `onde` ou `como`, e usa até três partes. Combina os resultados da pergunta original com os das partes; deduplica por caminho, localização e texto, guarda a menor distância e mantém até quatro resultados. Distâncias de consultas diferentes são usadas como heurística de ordenação; não são confiança calibrada. A divisão pode perder contexto, não reconhece toda pergunta composta e aumenta as chamadas de embeddings.

| Estratégia | Respondíveis com todas as fontes | Fontes extras somadas | Negativas sem trechos |
| --- | ---: | ---: | ---: |
| Atual | 34/35 | 38 | 4/15 |
| Distância relativa 0,15 | 34/35 | 28 | 4/15 |
| Divisão e união | 35/35 | 42 | 4/15 |
| Divisão e distância relativa | 34/35 | 31 | 4/15 |

A divisão recuperou onboarding sem perda de fonte esperada nos outros casos, mas trouxe mais fontes extras. Combinar as duas regras eliminou novamente onboarding: a distância relativa global usa o melhor resultado da pergunta original e remove a evidência obtida pela subconsulta. O filtro relativo continua melhor para reduzir extras nesta amostra; a divisão foi melhor para preservar as fontes esperadas. Nenhuma alternativa melhorou as perguntas negativas.

## Reprodução e decisão

Com `.env` configurado para embeddings Ollama, execute `python -m src.retrieval_experiment`. O comando usa apenas embeddings locais, cria índice em memória e grava o relatório. Registra revisão, estado da árvore e hashes dos conjuntos; a revisão com árvore alterada não identifica o código inteiro da execução. As métricas incluem caminhos esperados, não sustentação semântica. Fonte extra pode ser útil.

O experimento permanece separado da aplicação. Os conjuntos são pequenos, sintéticos e reutilizados na escolha das regras, sem avaliação independente nem corpus com múltiplos chunks por documento. A divisão é a candidata para ampliar cobertura de perguntas compostas, mas a melhora observada é de um único caso; a decisão de adotar exige validar custo, latência, contexto perdido e respostas efetivas em mais casos. Não há uma estratégia vencedora em todas as métricas.

## Verificação prospectiva e custo local

Oito perguntas foram escritas antes de executar esta rodada, com expectativas definidas pelo corpus, sem ajustar as regras após observar as respostas. Não é avaliação independente: mesma tarefa, mesmo autor e mesma base. [Casos](retrieval_prospective.json) e [relatório](baselines/prospective-comparison.json).

| Estratégia | Todas as fontes | Extras | Negativas sem trechos | Chamadas de embeddings | Tempo total de consultas |
| --- | ---: | ---: | ---: | ---: | ---: |
| Atual | 6/6 | 7 | 0/2 | 8 | 0,958 s |
| Relativa | 6/6 | 3 | 0/2 | 8 | 0,829 s |
| Dividida | 6/6 | 8 | 0/2 | 24 | 5,920 s |
| Dividida e relativa | 6/6 | 4 | 0/2 | 24 | 2,465 s |

O cache do experimento foi limpo antes de cada estratégia para não esconder chamadas de embeddings, mas o serviço Ollama já estava ativo e pode manter caches internos. Cada consulta repetida dentro da mesma estratégia é reutilizada. Tempos são uma única medição local, em ordem fixa, sem controle de carga ou aquecimento; excluem indexação e o diagnóstico adicional, portanto não são benchmark nem comparação causal de velocidade. A divisão fez três vezes mais chamadas nesta amostra e não melhorou cobertura. Não houve geração nem consumo de API externa; custo monetário e energia locais não foram medidos.

Decisão: manter a busca atual e o PR como registro experimental. A melhora anterior de uma pergunta não se repetiu como ganho de cobertura nesta rodada, e fontes extras aumentaram. A regra relativa reduziu extras, mas o experimento anterior mostrou que sua combinação com a divisão perde uma fonte; não há validação suficiente para adoção.

Para repetir esta rodada, defina `EXPERIMENT_DATASETS=retrieval_prospective` e `EXPERIMENT_OUTPUT=evals/baselines/prospective-comparison.json` antes de executar o módulo. O diagnóstico fixo antigo também é executado, separadamente das medições da tabela.
