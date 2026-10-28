# Diagnóstico e plano de portfólio

## Estado inicial

Referência auditada: `da53e6f`, branch `main`, em 28/10/2026.

| Área | Evidência | Oportunidade |
| --- | --- | --- |
| Problema | Consulta a cinco documentos fictícios | Explicitar usuário e decisão apoiada |
| Arquitetura | Extração, chunks, Gemini, Chroma e Streamlit | Fronteira de recuperação reutilizável e trade-offs documentados |
| Busca | Top-k seguido de seleção de um único trecho | Perguntas compostas precisam de várias evidências |
| README | Completo para challenge, com alegações de fallback sem alucinação | Priorizar demonstração e limites verificáveis |
| Execução | `.env.example`, requirements, Docker e Compose | Falta lockfile; modelos dependem da conta |
| Testes | 12 testes de extração, chunking e RAG com serviços simulados | Faltavam Chroma real, interface, avaliação e CI |
| Deploy | Duas capturas e relato OCI Compute | Evidência histórica, sem prova de disponibilidade atual ou IaC |
| Produto | Consulta sem ferramentas de ação | Posicionar como assistente RAG, evitando promessa de autonomia |

As capturas mostram uma resposta sobre férias e uma abstenção ainda acompanhada de `faq.md`. Não demonstram ausência geral de alucinações.

## Nome e posicionamento

**NexaPolicy — Assistente de políticas internas** é a recomendação: conecta a NexaCorp já existente ao domínio de políticas e explica o produto para recrutadores. Alternativas: **PolicyLens** (ênfase em evidências) e **NexaGuide** (domínio mais amplo). Não foi feita pesquisa de marca. Preservar crédito ONE, autoria e badge; manter o slug atual para preservar links.

Proposta: “Assistente RAG para consultar políticas internas com trechos verificáveis e avaliação reproduzível de recuperação”. Não prometer redução de chamados, ROI ou precisão sem medir.

## Implementado nesta revisão

Contexto com múltiplas fontes, evidências por trecho com caminho e distância, remoção de fontes da abstenção padrão, recuperação compartilhada, dataset com 15 perguntas, CLI de avaliação, testes e CI. A interface adota o nome proposto. Documentação separa implementação, validação local e propostas.

## Próximos marcos

Estimativas são de esforço, não compromisso de calendário. Encerrar um marco antes do seguinte.

| Prioridade / estimativa | Entrega | Critério de conclusão |
| --- | --- | --- |
| 1 — 1 a 2 dias | Baseline real top-1/top-4 | Relatórios com mesma base/modelo, revisão, configuração e análise de falhas, incluindo negativas e compostas |
| 2 — 2 a 3 dias | 30 a 50 casos e avaliação de respostas | Desenvolvimento/teste separados; fatos esperados e rubrica de sustentação/citações; modelo real identificado |
| 3 — 2 a 3 dias | Integridade do índice | Fingerprint modelo/dimensão/corpus, staging/rollback e testes de alteração, exclusão e falha de escrita |
| 4 — 1 a 2 dias | Reprodutibilidade e nova demo | Dependências travadas, build validado, gravação curta, revisão implantada identificada e rollback documentado |
| 5 — condicionado a evidência | Busca híbrida ou reranker | Ganho medido em teste separado com custo/latência; manter somente se justificar |

Próximo corte: marcos 1 e 2. Evitar expandir simultaneamente para multiagentes, conectores, Kubernetes ou vários provedores. Autenticação e autorização por documento são pré-requisitos para qualquer dado interno real.

## Evidências para entrevista

Mostrar pergunta simples, composta, negativa e um caso de falha. Explicar distância versus confiança calibrada, recuperação versus geração e cobertura versus abstenção. Apresentar relatórios reais quando existirem, além das capturas históricas. O diferencial demonstrável será medir e explicar os limites do sistema.
