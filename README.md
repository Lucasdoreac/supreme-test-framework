# LabTech QA

Suíte Behave/Selenium para o login com magic link da aplicação LabTech. O
contrato vigente usa `POST /auth/send-link?email=...` (HTTP 201 em development)
e `GET /auth/validate?email=...&token=...`. A SPA valida o hash do link e
armazena esse mesmo valor em `localStorage`.

## Instalação e execução

O caminho de execução integrado é `dev-local/run-tests.sh e2e`, em Docker
Linux. O runner monta esta fonte, instala `poetry.lock`, abre um Chromium em
Selenium Grid e usa uma conta sintética isolada. Confira a plataforma via
`DOCKER_PLATFORM` e o Compose resolvido antes de executar. A suíte de login
cria tokens de autenticação; use somente o banco descartável da pilha de testes
e confira a limpeza do runner.

Para executar os checks sem navegador em um contêiner Linux com Python
3.14.8 ou superior:

```sh
poetry install --no-interaction --no-ansi --no-root
poetry run pip check
poetry run python -m unittest discover -s tests -v
poetry run behave --dry-run
```

O E2E recebe `BASE_URL` (origem vista pelo Chrome), `API_URL` (gateway de
Auth visto pelo executor) e `SELENIUM_REMOTE_URL` (Grid). Sem Grid, Selenium
Manager precisa de Chrome disponível **dentro do contêiner Linux**. O retorno
de `magic_link` exige Auth em development; a UI envia o primeiro pedido de
link e o teste faz outro pedido para obter o link que a UI não expõe. Isso
exercita navegação e validação no navegador, mas não entrega de email externo.

Os cenários atuais cobrem login com conta sintética e rejeição de domínio
inválido. A suíte não comprova decisão administrativa, envio externo,
geração/leitura de PDF nem revogação de sessão no servidor. O callback vigente
não cria token de sessão novo e Auth não expõe exchange/logout. Cenários de
alterações solicitadas precisam de catálogo e banco descartáveis, fixture
própria, limpeza de evento/reserva/token/PDF e navegação pelo link renderizado
do email antes de integrar ao E2E.
