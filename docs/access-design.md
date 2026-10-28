# Escopo proposto para controle de acesso

O aplicativo atual não autentica pessoas nem filtra documentos por permissão. Use apenas dados fictícios. Este documento é uma proposta, não um controle implementado.

## Próximo corte

Para uma demonstração local, criar usuários fictícios com papéis `rh`, `financeiro` e `colaborador`, e documentos marcados por categoria. Recuperar somente os trechos autorizados antes de enviá-los ao modelo e aplicar a mesma regra às evidências exibidas. Testar consultas diretas e indiretas, documentos sem classificação e tentativas de acessar trechos de outra categoria. Negar por padrão quando identidade ou classificação estiver ausente.

Credenciais de demonstração e sessão local não equivalem a identidade corporativa. Para um ambiente real são necessários provedor de identidade, autenticação confiável, autorização validada no servidor, políticas por usuário e documento, criptografia, auditoria, revisão de exposição ao provedor e testes de isolamento. O filtro precisa ocorrer na consulta ao índice e em qualquer outra via de acesso; filtrar apenas a interface não protege os dados.

## Critérios de aceite

- Um usuário fictício sem permissão não consegue recuperar texto nem metadados de outra categoria, inclusive em perguntas compostas.
- Evidências e citações nunca contêm documentos fora do conjunto autorizado.
- Uma reindexação preserva e valida as permissões dos documentos; conteúdo sem política definida não é exposto.
- Testes cobrem usuário autorizado, não autorizado, ausência de identidade, alterações de permissão e fontes múltiplas.
- A documentação distingue a demonstração local de uma implantação corporativa e registra os riscos que continuam abertos.
