# Revisão funcional e de confiabilidade — 29/10/2026

Revisão de leitura do pipeline, adaptadores, persistência, ingestão e interface, acompanhada de testes de regressão. Não é uma prova de ausência de falhas nem uma auditoria de segurança completa. Esta rodada usa serviços simulados e Chroma real local; não consome APIs externas. Testes reais anteriores têm seus próprios relatórios em `evals/baselines`.

## Falhas encontradas e corrigidas

- **Erro de geração confundido com ausência de informação:** uma resposta sem referência válida era convertida na mesma mensagem usada quando faltam evidências. Agora gera erro explícito, registrado como erro na avaliação e mostrado na interface. Só a ausência de trechos ou a abstenção padrão do modelo gera a mensagem de ausência de informação.
- **Citação malformada ignorada:** uma resposta com uma referência válida e outra inválida podia passar pela validação. Agora todos os marcadores são verificados, incluindo marcadores incompletos, números inválidos e espaços.
- **Erros Groq sem classificação:** o código HTTP era perdido no relatório. A exceção agora preserva o código (como 429) sem guardar o texto retornado pelo provedor. Timeouts de rede recebem mensagem limpa.
- **Vetores malformados:** são rejeitados vetores vazios, nulos, de dimensão incorreta, com tipos não numéricos, NaN, infinito ou somente zeros, antes de indexar ou consultar. IDs duplicados são rejeitados antes da escrita.
- **Quota:** o adaptador Gemini deixa de repetir automaticamente erros 429. Ainda pode repetir erros transitórios de servidor configurados.

## Matriz verificada

| Área | Cenário | Evidência |
| --- | --- | --- |
| Entrada | Pergunta vazia, só espaços ou longa demais | Testes RAG: rejeita antes de consultar provedor |
| Recuperação | Índice vazio, limiar, ordenação, distância não finita | Testes RAG e Chroma |
| Múltiplas fontes | Duas e três fontes, top-2 versus top-4 | Relatórios locais e teste de estresse; padrão mantido em quatro |
| Citações | Válidas, com espaços, fora do intervalo e malformadas | Testes RAG; validação sintática, sem prova semântica |
| Provedores | Interrupção por tokens, erro HTTP, timeout, formato inválido e texto vazio | Testes com respostas controladas |
| Embeddings | Quantidade, dimensão, NaN, infinito, zero e tipo inválido | Validação compartilhada e testes |
| Persistência | Reabrir coleção, substituir conteúdo, apagar documento | Testes Chroma locais; reabertura no mesmo processo |
| Indexação | Falha de escrita, documento alterado durante embeddings, IDs duplicados | Índice anterior preservado nos testes |
| Concorrência local | Segunda reconstrução em outro processo | Bloqueio local testado |
| Configuração | Valores inválidos e chave ausente | Testes de configuração |
| Interface | Histórico, grupos de fontes, 429, geração interrompida, erro de referência | Testes Streamlit com cache isolado |
| Avaliação | Métricas, fontes extras/ausentes, classes ausentes, relatório parcial | Testes de avaliação com dados controlados |
| Ingestão | Formatos suportados e metadados | Testes existentes com arquivos pequenos gerados |

## Pontos ainda abertos

- Similaridade não prova que o trecho responde à pergunta. As negativas continuam dependendo também da abstenção do gerador; isso precisa de avaliação mais ampla e independente.
- Citações sintaticamente válidas podem sustentar apenas parte da resposta. Não há verificador semântico nem garantia contra prompt injection.
- DOCX extrai parágrafos, não tabelas; PDF escaneado exige OCR. CSV irregular e documentos grandes/corrompidos não têm cobertura completa. A deduplicação global por texto pode omitir origens duplicadas.
- Fingerprint não captura mudança no código do extrator ou atualização do modelo sob a mesma tag. Não há resolução de versões conflitantes de políticas.
- Coleções antigas são preservadas; falta coleta segura. Falhas de energia e resultado ambíguo da troca não foram simulados. O bloqueio é local, não distribuído.
- Autenticação e autorização por documento não foram implementadas; só usar dados fictícios. Conexão Ollama–Docker e nova implantação OCI permanecem sem validação.
- A avaliação de geração ainda não possui limite de casos configurável ou retomada automática por checkpoint; relatórios parciais precisam ser preservados antes de repetir.

Esses pontos são limites documentados e trabalho futuro; não são marcados como resolvidos por testes simulados. O PR permanece em revisão.

## Rodada real complementar

Em 29/10/2026, três consultas executadas pelo avaliador com Ollama e Groq concluíram: férias e consulta de duas fontes tiveram fatos e citações conferidos manualmente contra os documentos; auxílio creche gerou a abstenção esperada. A consulta composta também recuperou um trecho de conduta não citado. [Casos](../evals/baselines/live-smoke-cases.json) e [respostas e revisão](../evals/baselines/live-smoke-result.json). São casos reutilizados e avaliados pelo autor desta tarefa, sem avaliação independente.

Uma consulta adicional à interface Streamlit, executada com AppTest e serviços reais, exibiu os grupos de fontes citadas e outros trechos consultados sem erro. Isso não é um teste visual em navegador. A geração é variável e a recuperação de conteúdo irrelevante segue como limitação.
