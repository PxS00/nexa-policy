# Comparação exploratória de termos e similaridade

Doze perguntas foram escritas antes desta execução: oito compostas respondíveis e quatro sem resposta. São exemplos sintéticos do mesmo corpus fictício, elaborados nesta tarefa; não constituem avaliação independente. [Casos](hybrid_prospective.json) e [resultados](baselines/hybrid-prospective.json).

O módulo `python -m src.hybrid_experiment` reconstrói o índice em memória com Ollama, consulta os cinco chunks e compara: seleção semântica atual; até dois candidatos com pelo menos dois termos compartilhados após normalização de acentos e remoção de palavras comuns; união por soma de inversos de posição, com constante 60 e teto top-4. Os parâmetros foram fixados antes de executar esta amostra. A união permite candidatos lexicais que não passam pelo teto semântico. Essa regra de termos é simples e não equivale a um mecanismo lexical robusto com flexões, sinônimos ou pesos por frequência.

| Estratégia | Todas as fontes nas respondíveis | Extras | Negativas sem trechos | Tempo de consultas |
| --- | ---: | ---: | ---: | ---: |
| Atual | 8/8 | 10 | 0/4 | 1,714 s |
| Termos | 2/8 | 0 | 4/4 | 1,688 s |
| União | 8/8 | 10 | 0/4 | 1,600 s |

O protocolo realiza 12 chamadas de embeddings por estratégia para obter a mesma lista completa de candidatos; a estratégia de termos não é uma implementação lexical independente e herda o desempate da ordem vetorial. Os tempos incluem consultas e seleção, excluem indexação, vêm de uma única passagem em ordem fixa e sofrem influência de caches internos e carga. Não demonstram vantagem de velocidade. Não houve geração ou API externa; custo monetário, energia e uso de memória não foram medidos. Consultar todos os chunks é adequado somente a este experimento pequeno e não descreve desempenho em bases maiores.

A união não melhorou nenhum dos totais desta amostra. A rejeição das negativas pelo filtro lexical veio acompanhada de perda de fontes em seis perguntas respondíveis. Fontes extras são caminhos não incluídos nas expectativas, e podem conter informação útil; as métricas não verificam sustentação das respostas. A recomendação permanece manter a aplicação e integrar os experimentos como registro após revisão dos checks, sem adotar as regras testadas. Isso não descarta busca híbrida em outros corpora: uma próxima investigação deve usar documentos maiores, vários chunks e expectativas revisadas por outra pessoa.

Na revisão do experimento de divisão foi corrigida a perda silenciosa das partes após a terceira: se a heurística produzir mais de três partes, mantém a pergunta inteira. Três testes locais passaram cobrindo esse limite, termos coordenados e normalização/seleção lexical. Os relatórios anteriores permanecem históricos; nenhum deles foi regenerado por essa correção.
