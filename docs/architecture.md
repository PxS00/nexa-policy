# Arquitetura e decisões

`document_loader.py` extrai texto e metadados; `text_processing.py` normaliza, divide por caracteres e produz IDs determinísticos. `indexing.py` gera embeddings em lotes de 50 e confere a quantidade antes de substituir o índice. `vector_store.py` encapsula Chroma por cosseno. `rag.py` valida pergunta, recupera evidências e monta o prompt. `ai_client.py` encapsula Gemini com retries e alternativa de geração em erro 503. `app.py` apresenta conversa e evidências. `evaluation.py` avalia recuperação sem geração.

| Decisão | Motivo | Trade-off |
| --- | --- | --- |
| Manter Streamlit e Chroma local | Demonstração pequena e executável | Sem API independente ou escala distribuída |
| Todos os trechos elegíveis até top-k | Perguntas que cruzam documentos | Mais contexto e distrações; comparar com top-1 |
| Separar recuperação e resposta | Isolar erros de busca dos erros de geração | Avaliação da resposta ainda pendente |
| Referência por trecho na ordem do prompt | Preservar evidências diferentes de um arquivo | Pode repetir documentos; sustentação semântica não é verificada |
| Mostrar texto e caminho da evidência | Permitir conferência | Sem controle de acesso |
| Chroma em memória na avaliação | Preservar índice da aplicação | Benchmark não testa persistência |
| Construir coleção separada e trocar ponteiro após concluir | Falhas de escrita não substituem o índice ativo | Coleções antigas permanecem; concorrência entre processos não é coordenada |

## Fronteiras de confiabilidade

- O filtro ordena resultados e rejeita distâncias não finitas; não detecta se um trecho responde à pergunta. Distância não é confiança calibrada.
- Perguntas sem resposta podem recuperar conteúdo parecido e chegar ao gerador. O prompt não garante fundamentação ou resistência a prompt injection.
- Fontes representam contexto fornecido ao modelo, não prova de sustentação de cada afirmação. Respostas sem citações ou com números inválidos resultam em abstenção; essa verificação sintática não valida a relação entre afirmação e trecho. Só a mensagem padrão de abstenção é reconhecida; paráfrases não são detectadas automaticamente.
- Um fingerprint inclui arquivos, modelo/dimensão e parâmetros de chunking; a interface bloqueia consultas se houver divergência ou índice legado. Isso não captura mudanças na implementação do extrator nem detecta modificações durante a leitura que sejam revertidas antes da segunda verificação.
- A troca do ponteiro só acontece após preparar a coleção. Não há transação distribuída, rollback automático após troca, coleta de coleções antigas ou coordenação entre reindexações simultâneas; uma falha ambígua na atualização do ponteiro precisa ser investigada antes de remover coleções.
- Deduplicação por texto preserva apenas a primeira origem. Data de atualização é o mtime do arquivo, não vigência da política; não há resolução de versões conflitantes.
- O histórico não é memória do LLM. Reindexação concorrente não tem coordenação dedicada. A coleção é compartilhada pelo processo.

## Contratos

Perguntas vazias ou acima de 2000 caracteres falham antes da API. A ordem de `[FONTE n]` coincide com as referências. Caminhos relativos distinguem arquivos homônimos. A avaliação usa o mesmo filtro da aplicação. Relatórios não salvam a chave. Testes normais não precisam de credenciais nem rede.
