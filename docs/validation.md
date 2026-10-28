# Validação desta evolução

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

## Não executado

| Validação | Motivo / alcance |
| --- | --- |
| Benchmark com embeddings reais | Sem chave Gemini configurada nesta sessão; nenhuma métrica semântica publicada |
| Qualidade das respostas e citações reais | Geração simulada nos testes; ainda exige avaliação por fatos esperados |
| Build e execução Docker | Serviço Docker local indisponível; comando de versão não conectou ao daemon |
| Novo deploy OCI ou teste do endereço antigo | Sem acesso à infraestrutura; capturas são registros históricos |

O próximo experimento é comparar top-1/top-4 e calibrar abstenção em exemplos separados. O ganho de qualidade semântica da mudança não foi presumido a partir dos testes.
