# Rubrica para revisão de respostas

Use `policy_questions.json` para desenvolvimento e `policy_holdout.json` para avaliação separada. Ambos foram escritos a partir dos mesmos cinco documentos fictícios; o holdout não é uma amostra independente de usuários reais. Evite ajustar o limiar com base no holdout e depois apresentar sua pontuação como teste independente. Uma rodada parcial real foi registrada em `baselines/holdout-2026-10-29-partial.json`; não há avaliação completa do holdout.

Para cada caso respondido, confira `expected_facts` e os documentos originais. Marque:

1. `facts_supported=true` apenas se todos os fatos esperados estão presentes, corretos e não há afirmações extras sem sustentação. Caso contrário, `false` e explique em `notes`.
2. `citations_supported=true` apenas se cada afirmação factual possui citação e o trecho citado a sustenta; citar a fonte certa uma vez não garante o restante. A checagem sintática da aplicação não substitui esta revisão.
3. Para perguntas negativas, abstenção sem resposta inventada é correta; uma resposta específica é falha. Para perguntas respondíveis, abstenção é falha de cobertura. Registre o motivo observado sem especular.
4. Erros de API e interrupções não são respostas corretas nem incorretas: registre-os como erros e reporte seus números separadamente, mantendo o denominador total.

Relate contagens de casos totais, respondidos, abstenções, erros, respostas revisadas e falhas por tipo. Não calcule taxa de qualidade sobre casos não revisados e não use `null` como aprovação. Preserve os relatórios originais e uma cópia revisada, com data e método da revisão.
