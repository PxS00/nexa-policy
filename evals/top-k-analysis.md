# Comparação de quantidade de trechos

Em 29/10/2026 foram executadas novas buscas com `embeddinggemma` local, limiar 0,65 e top-2, com os mesmos cinco documentos e conjuntos usados nos relatórios top-4. As perguntas e a base são fictícias. A contagem de fontes extras abaixo considera os caminhos distintos recuperados nas perguntas respondíveis que não constam na lista de fontes esperadas; uma fonte extra pode conter informação útil e não é automaticamente irrelevante.

| Conjunto | Top-k | Casos respondíveis com todas as fontes | Fontes extras somadas | Negativas sem trecho recuperado |
| --- | --- | --- | --- | --- |
| Desenvolvimento | 4 | 11/11 | 12 | 2/4 |
| Desenvolvimento | 2 | 11/11 | 5 | 2/4 |
| Separado | 4 | 11/11 | 13 | 0/4 |
| Separado | 2 | 11/11 | 6 | 0/4 |

[Top-2 desenvolvimento](baselines/ollama-top2-development.json), [top-2 separado](baselines/ollama-top2-holdout.json), [top-4 desenvolvimento](baselines/ollama-development.json), [top-4 separado](baselines/ollama-holdout.json). Os relatórios top-2 foram gerados antes das mudanças de código neste PR e registram a revisão base; foram executados usando `TOP_K=2` explicitamente. A análise compara apenas recuperação por caminho, não fidelidade das respostas.

Top-2 parecia promissor nesses dados, mas o conjunto separado já foi utilizado em análises anteriores e não é um teste independente cego. O novo conjunto de estresse inclui três perguntas com três fontes: top-2 recuperou todas as fontes em apenas 2/5 perguntas respondíveis, enquanto top-4 recuperou todas em 5/5. Ambos aceitaram trechos nas 3/3 negativas. [Resultados top-2](baselines/stress-top2.json) e [top-4](baselines/stress-top4.json). Por isso o padrão permanece 4. Fontes extras podem entrar no contexto; são apresentadas separadamente das fontes citadas, sem comprovar sustentação semântica. Os oito casos também são sintéticos e não demonstram qualidade em produção.

Dois testes de geração reais com Groq e top-2 no índice persistente: a pergunta sobre acessos e TI recuperou e citou o FAQ e onboarding; a pergunta sobre auxílio creche recebeu a abstenção padrão. Os resultados são exemplos individuais, não uma medida de qualidade geral.

Na comparação real posterior da pergunta sobre férias, hospedagem e treinamentos, top-2 não recuperou a fonte financeira e o modelo declarou a lacuna; top-4 respondeu às três partes usando as três fontes. Uma referência foi escrita como `[ FONTE 2]` e inicialmente não foi reconhecida pelo parser; a identificação agora aceita espaços ao redor da referência, com testes para fontes válidas e inválidas. Esses exemplos não estabelecem qualidade média de geração.
