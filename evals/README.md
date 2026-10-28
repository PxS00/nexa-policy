# Avaliação de recuperação

O dataset contém 15 perguntas curadas manualmente a partir dos cinco documentos fictícios: 11 respondíveis (duas com múltiplas fontes) e quatro ausentes da base. `expected_sources` contém caminhos relativos; lista vazia indica expectativa de abstenção. Não é uma amostra de usuários ou conjunto representativo de produção.

Na raiz do projeto, com chave e dependências configuradas:

```bash
python -m src.evaluation --dataset evals/policy_questions.json --output evals/reports/retrieval.json
```

Reconstrói Chroma em memória com embeddings reais Gemini; não altera a coleção persistida nem chama geração. Pode consumir quota/cobrança. Falhas interrompem a execução sem novo relatório parcial. A saída é sobrescrita: use nomes distintos por experimento.

## Métricas

Todas usam os resultados aprovados pelo limiar e até `TOP_K` chunks. No ranking, caminhos repetidos são reduzidos à primeira ocorrência.

| Campo | Definição |
| --- | --- |
| `mean_source_recall_at_k` | Média nas perguntas respondíveis: fontes esperadas recuperadas / total esperado |
| `source_mrr_at_k` | Média do inverso da posição da primeira fonte correta; zero se ausente |
| `all_sources_found_rate` | Fração das respondíveis com todas as fontes esperadas |
| `correct_abstention_rate` | Fração das negativas com zero trechos aprovados |
| `retrieval_ms` | Tempo por pergunta: embedding de consulta e busca; exclui ingestão e geração |

Classe ausente produz `null`. Recuperar todas as fontes não penaliza fontes extras. As métricas são por documento, não por fato: o arquivo certo pode conter o chunk errado. A abstenção do gerador está fora do escopo. Revise também os resultados por pergunta.

O relatório registra configuração, contagens indexadas, hashes SHA-256 do corpus/dataset, timestamp UTC, revisão Git e indicador de alterações locais, sem chave. Dependências não estão travadas; registre `python -m pip freeze` para comparações rigorosas. Revisão com alterações locais não identifica todos os bytes do código executado.

## Próximo experimento

1. Execute com `TOP_K=1` e depois `TOP_K=4`, mantendo corpus, dataset e modelo. Preserve ambos os relatórios.
2. Compare perguntas compostas e negativas, sem assumir melhora geral.
3. Crie exemplos separados de desenvolvimento e teste antes de calibrar limiar. Não ajuste e declare melhora usando apenas os mesmos 15 exemplos.
4. Avalie respostas reais por fatos esperados e validade das citações; registre falhas, tempo e custo reais.

Para preparar uma revisão manual de respostas reais:

```bash
python -m src.evaluate_answers --output evals/reports/answers-review.json
```

O comando indexa o corpus com embeddings reais em memória e chama o modelo para cada caso, podendo consumir quota. O relatório salva resposta, trechos e campos `facts_supported`, `citations_supported` e `notes` para preenchimento manual. Ele registra resultados a cada caso e interrompe no primeiro erro, inclusive quota ou geração incompleta; `complete=false` indica rodada parcial. A saída é sobrescrita, portanto use nomes diferentes. Os campos de revisão começam em `null`: não representam avaliação automática. Revise cada afirmação e sua citação contra os trechos e os documentos originais, inclusive casos de abstenção indevida.

Os relatórios versionados em `baselines/` registram uma execução real com o corpus e dataset atuais. Valores controlados dos testes validam o cálculo, não o sistema de embeddings. As métricas das 15 perguntas são exploratórias e não substituem uma avaliação independente.
