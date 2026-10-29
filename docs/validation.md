# Validação desta evolução

## Atualização posterior: execução real

Em 29/10/2026, no código da revisão `41c8d75`, foi iniciada uma avaliação real com o conjunto separado, índice em memória, limiar 0,65, top-4, limite de 700 tokens, sem retries automáticos e sem modelo alternativo. A rodada foi interrompida após três erros 503 consecutivos; uma solicitação seguinte estava em andamento e não teve resultado registrado. Dos 15 casos planejados, seis têm resultado registrado: uma resposta sobre férias corretamente citada e uma abstenção correta foram revisadas manualmente; uma pergunta composta terminou em `MAX_TOKENS` e três chamadas falharam com 503. Os outros nove não foram avaliados. [Relatório parcial](../evals/baselines/holdout-2026-10-29-partial.json). Não se deve inferir taxas gerais a partir destes resultados.

O [guia oficial de thinking do Gemini](https://ai.google.dev/gemini-api/docs/generate-content/thinking) informa que `max_output_tokens` inclui tokens de raciocínio e saída; isso é uma hipótese plausível para a interrupção, mas os dados desta execução não capturam a contagem de tokens de raciocínio e não estabelecem sua causa. Um experimento direto anterior com limites 700 e 2048 terminou normalmente, mas não reproduziu o mesmo prompt completo. Ainda falta comparar configurações no fluxo RAG e avaliar custo e qualidade; nenhuma configuração foi alterada.

Em outra evolução local, 48 testes passaram usando as versões fixadas em `requirements-dev.lock`. Testes incluem bloqueio do mesmo índice em outro processo local, remoção da coleção temporária quando a escrita falha antes da promoção e validação do novo conjunto separado de perguntas. Nenhuma chamada Gemini foi feita nessa evolução. O bloqueio não garante coordenação em instalações distribuídas; coleções antigas continuam preservadas.

Na evolução da integridade do índice, 46 testes locais passaram sem chamadas Gemini. Uma falha simulada de escrita na coleção temporária preservou os resultados e o fingerprint do índice anterior; uma alteração dos documentos durante a geração de embeddings também impediu a troca. Os testes não simulam interrupção de energia, múltiplos processos ou falhas ambíguas da operação de troca.

Na rodada seguinte, o novo avaliador registrou dois casos respondidos e interrompeu o terceiro por `MAX_TOKENS`; a execução ficou incompleta (3/15). As duas respostas sobre férias e suas citações foram conferidas manualmente contra a política. O código agora rejeita respostas interrompidas; o teste real identificou o motivo, mas não demonstra que todas as perguntas podem ser respondidas dentro do limite atual.

Com a chave configurada, foram executados os baselines de recuperação real ([top-1](../evals/baselines/retrieval-top1.json), [top-4](../evals/baselines/retrieval-top4.json)); os detalhes e limites estão no README. A imagem Docker foi construída e o container ficou saudável. Uma pergunta sobre férias recebeu resposta citada e uma pergunta sobre estacionamento recebeu abstenção. Esses dois exemplos não constituem uma avaliação estatística da geração. A validação sintática de citações foi adicionada posteriormente e a suíte passou com 38 testes.

Uma rodada exploratória posterior em 28/10/2026 usou o mesmo dataset, `TOP_K=4`, limiar 0,65, `gemini-3.5-flash` e a validação de citações ativa no código local. [Resultados brutos](../evals/baselines/answers-exploratory.json): dez respostas e cinco erros 429. Das dez respostas, quatro negativas tiveram abstenção; uma pergunta respondível teve abstenção e uma resposta terminou incompleta. As fontes listadas são todo o contexto recuperado, não necessariamente as fontes efetivamente citadas. Não houve avaliação manual sistemática de todas as afirmações; a execução não é um benchmark completo.

Data: 28/10/2026. Base auditada: `da53e6f`. Ambiente local Windows, Python 3.12.14, ChromaDB 1.5.9, Streamlit 1.66.1, pytest 8.4.2. Dependências instaladas a partir dos intervalos de `requirements-dev.txt` em ambiente virtual isolado.

Na validação posterior, a suíte passou com **34 testes**; foi acrescentado um teste que reabre uma coleção Chroma persistente e consulta seu conteúdo. A reabertura ocorre no mesmo processo, portanto não comprova reinício completo da aplicação.

## Executado

```text
python -m pytest -q --cov=src --cov-report=term-missing
33 passed in 11.84s
TOTAL: 467 statements, 48 missed, 90% coverage
```

Foram usados diretórios temporários graváveis no workspace; o teste Streamlit precisou de comunicação local liberada pelo ambiente de execução. Não houve chamada ao Gemini.

- Extração dos formatos suportados, metadados, deduplicação, limpeza e IDs estáveis.
- RAG com múltiplas fontes, ordenação, limiar, distâncias não finitas, entrada inválida, índice vazio e abstenção.
- Chroma real em memória com vetores controlados: busca, metadados e substituição.
- Quantidade incorreta de embeddings interrompe indexação antes de substituir dados.
- Interface Streamlit: pergunta, resposta, trecho de evidência e preservação no histórico, com serviços simulados.
- Métricas com resultados controlados, incluindo fontes ausentes, duplicatas e falsas aceitações.
- CLI de avaliação com embeddings controlados: relatório, caminho das fontes, ausência de chave na saída e preservação do índice persistido.
- Dataset validado contra os documentos existentes, compilação Python, ajuda da CLI e `git diff --check`.

Cobertura de código não é qualidade das respostas. O adaptador Gemini tem apenas 26% de cobertura nesta suíte; erros, quotas, retries e disponibilidade real dos modelos não foram validados. O workflow CI foi adicionado; seu resultado deve ser conferido no GitHub.

## Não executado na validação inicial

| Validação | Motivo / alcance |
| --- | --- |
| Benchmark com embeddings reais | Sem chave Gemini configurada nesta sessão; nenhuma métrica semântica publicada |
| Qualidade das respostas e citações reais | Geração simulada nos testes; ainda exige avaliação por fatos esperados |
| Build e execução Docker | Serviço Docker local indisponível; comando de versão não conectou ao daemon |
| Novo deploy OCI ou teste do endereço antigo | Sem acesso à infraestrutura; capturas são registros históricos |

Os baselines posteriores não demonstram ganho de qualidade semântica das respostas. Calibrar abstenção exige exemplos separados.
