# Diagnóstico de consolidação E2E — NÃO PRONTO PARA MERGE

Esta branch, criada a partir de `master` fe09a63c91e8b4e947ce3d1cd5af51b66a03df6d, acrescenta somente este diagnóstico. **Não integra nem resolve os branches**, não altera código, testes, lock, workflows ou configurações. Não execute E2E contra serviços reais a partir deste diagnóstico.

## Referências comparadas

- `consolidate/2026-10-19` dfbf172ee3aa3495af78320cd1bc13e8dd375daa: simplificação de login, testes, Python ^3.12, requirements exportado do lock.
- `test/e2e-logged-in-screens` a92aaf6e8de723c06659597025e977d92599d8f0: testes autenticados e regressões de drafts; já inclui o ancestral `fix/e2e-selectors-new-markup` 88dc3d17b2874be47b37ee3ed829302a57ccfeb9.
- `form-flow-tests` b091c247c9e69eb4262fa36f19543f3686fac6c3: cenários de criação, steps e page objects. Não é ancestral dos outros; exige integração explícita.
- `chore/dependency-refresh` 10f304f94bdbdde54d1e7fa2a39197044cf4dd6e: atualiza ast-serialize para 0.12.1, mas não contém os testes logados mais recentes; não substituir a árvore mais recente por ele.

## Bloqueios concretos

1. Merge experimental local de logged-in com consolidate apresentou sete arquivos em conflito: `README.md`, `features/steps/login_steps.py`, `page_objects/login_page.py`, `poetry.lock`, `pyproject.toml`, `requirements.txt` (delete/modify) e `utils/helpers.py`. O merge não foi publicado.
2. Os contratos de autenticação são incompatíveis: consolidate verifica que o token armazenado é o hash do link; logged-in clica Entrar e exige token de sessão diferente do hash, enquanto seu step de verificação de token é um `pass`. Não foi possível confirmar qual contrato corresponde aos serviços e SPA que serão usados. Decidir por evidência e preservar regressões para cada configuração suportada, sem aceitar automaticamente ambos como sucesso.
3. A branch form-flow contém `ensure_authenticated` com endereço pessoal fixo e interceptação de link, além de hook que considera tags `auth`, `event` e `authenticated`; fundir o hook sem ajuste pode autenticar antes do próprio cenário de login. Usar apenas conta sintética, isolar autenticação por tag e consolidar o código duplicado após validar os contratos. Alguns fluxos manipulam eventos: requerem infraestrutura descartável e limpeza comprovada.
4. Logged-in registra o hash do magic link em log. Evitar publicar segredo e resposta HTTP em logs antes de habilitar testes. Inspecionar seeding, isolamento e limpeza antes de qualquer execução real; os guardas de hostname local não demonstram por si só que a base seja descartável.
5. `consolidate` aceita apenas HTTP 201 para magic link; logged-in aceita 200/201. Confirmar o contrato de API em vez de escolher arbitrariamente. Seletores também diferem entre markup corrente e drafts; preservar cobertura de ambos sem ambiguidade.
6. Dependências: Python ^3.12 e requirements exportado versus Python >=3.14.8 e instalação só por Poetry, com pymongo e grupo dev. Escolher faixa validada para os alvos, manter uma única fonte de verdade e gerar artefatos coerentes; não colar trechos de locks. O ambiente disponível tinha Python 3.14.4 e não tinha Poetry, Selenium, Behave nem PyMongo. Não houve resolução de dependências.
7. A branch logged-in introduz workflow que instala dependências e ações via serviços externos em push/PR; esta branch diagnóstica não o incorpora. Antes de habilitar CI, alinhar com a exigência de não usar serviços de terceiros.

## Verificação real offline

Cinco testes unitários sintéticos, executados em Python 3.14.4, extraíram por AST as funções originais `verify_token` (consolidate) e `step_impl_access_magic_link` (logged-in), com driver/page mocks e sem rede: consolidate aceitou o hash e rejeitou token distinto; logged-in aceitou token distinto e clicou Entrar, rejeitou hash igual e rejeitou token ausente. Resultado: **5/5 passaram**. Esta prova mostra divergência de expectativas, não valida o comportamento de uma aplicação real e não é teste da implementação integrada.

Não foram executados Behave, testes da suíte completa, `pip check`, Selenium ou E2E, nem instalações, acessos a banco, emails ou serviços externos. Falta integrar preservando os cenários e testes, resolver os sete conflitos, conferir conflito/duplicação de steps do formulário, revisar segurança e cobertura, validar o lock e executar os testes em stack local descartável antes de retirar o draft.
