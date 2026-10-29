# Demonstração curta (aproximadamente 60 segundos)

Execute a aplicação seguindo o README, com a base fictícia indexada e a API disponível. A indexação e as consultas consomem quota. Uma instância antiga pode exigir reindexação manual.

1. Apresente o objetivo: localizar regras em documentos de RH, financeiro e onboarding e permitir que o colaborador confira os trechos.
2. Pergunte: **“Qual a duração mínima dos períodos quando as férias são divididas?”** Abra “Fontes citadas” e mostre a política de férias e a citação. A política estabelece um período de pelo menos 14 dias corridos e os demais de pelo menos 5 dias.
3. Pergunte: **“Qual o valor do auxílio creche?”** A resposta esperada é abstenção porque essa informação não consta da base. O modelo é não determinístico: verifique a resposta, sem prometer que sempre vai se abster.
4. Abra o README e mostre a comparação de recuperação: um limiar pode reduzir resultados em perguntas negativas, mas também eliminar evidências relevantes. Apresente uma falha documentada, como `MAX_TOKENS` na pergunta com duas fontes, e explique que a aplicação evita exibir a resposta interrompida.

Esses passos são um roteiro para gravação, não uma gravação realizada. As capturas OCI são históricas e não mostram esta revisão.
