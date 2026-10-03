# Automação de Testes para Aplicação React

Projeto de automação de testes para uma aplicação React (SPA) utilizando Python, Selenium WebDriver, e Behave (BDD Framework), seguindo o padrão Page Object.

## Visão Geral

Este projeto implementa uma suíte de testes automatizados para o fluxo de autenticação com Magic Link em uma aplicação React. Os testes seguem a metodologia BDD (Behavior-Driven Development) utilizando Behave como framework e implementando o padrão Page Object para separação de responsabilidades.

## Requisitos

- Python 3.14.7+
- Poetry 2.4.1
- Google Chrome
- Aplicação React rodando em: `localhost:3000`
- API de autenticação rodando em: `http://localhost:5000`
- Email para testes deve terminar com: `@udf.edu.br`

## Estrutura do Projeto

```
project/
  features/
    steps/
      __init__.py
      login_steps.py
      navigation_steps.py
    environment.py
    login.feature
  page_objects/
    __init__.py
    base_page.py
    login_page.py
  utils/
    __init__.py
    browser_setup.py
    helpers.py
  .env
  behave.ini
  pyproject.toml
  poetry.lock
  README.md
```

## Setup

### 1. Preparação do Ambiente

```bash
# Clonar o repositório
git clone <repository-url>
cd project

# Instalar as dependências fixadas pelo lockfile
poetry install --no-interaction --no-ansi --no-root
```

### 2. Configuração

Edite o arquivo `.env` para configurar as URLs e outras variáveis de ambiente:

```env
BASE_URL=localhost:3000
API_URL=http://localhost:5000
ENV=development
WINDOW_WIDTH=1920
WINDOW_HEIGHT=1080
```

## Executando os Testes

### Todos os Testes

```bash
poetry run behave
```

### Filtrar por Tags

```bash
# Executar apenas testes de autenticação
poetry run behave --tags=@auth

# Executar testes de login
poetry run behave --tags=@login

# Executar testes de validação
poetry run behave --tags=@validation
```

### Cenários dos Drafts com duas abas ou serviço fora do ar (`@drafts`)

Rodam só com `--tags=drafts`, contra um Web que tenha os Drafts, e só no Docker local com conta isolada:

- Duas abas (#47): a etapa de logística abre em duas janelas do mesmo navegador. O Web usa `navigator.locks`,
  que só existe em contexto seguro; na rede Docker em HTTP, `E2E_TREAT_ORIGIN_AS_SECURE=<origem do Web>` faz o
  Chrome tratar essa origem como segura (em Production o HTTPS já basta).
- API ou Auth fora do ar (#42, #53): os cenários param o serviço pelo socket do Docker. Exige
  `E2E_ALLOW_SERVICE_CONTROL=1`, o socket montado no runner e `E2E_COMPOSE_PROJECT=<projeto Compose>`; só `api` e
  `auth` desse projeto podem ser parados, e o `after_scenario` sempre os religa.
- O que o cenário cria pela UI (rascunhos, pedido enviado, reserva, PDF) é removido por id ao final; o Mongo tem de
  ser o local (`E2E_MONGO_URI`).

### Teste Específico

```bash
# Executar apenas o arquivo login.feature
poetry run behave features/login.feature
```

### Gerar Relatório HTML

```bash
poetry run behave -f html -o reports/test_report.html
```

## Arquitetura

### Page Objects

Os page objects são responsáveis por encapsular a interação com os elementos da página web. A classe `BasePage` fornece métodos comuns, enquanto classes específicas como `LoginPage` implementam funcionalidades relacionadas às respectivas páginas.

#### Exemplo:

```python
class LoginPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.email_input = (By.NAME, "email")
        self.submit_button = (By.CSS_SELECTOR, "button[type='submit']")

    def enter_email(self, email):
        self.enter_text(self.email_input, email)

    def click_next(self):
        self.click_element(self.submit_button)
```

### Features e Steps

As features são descritas em arquivos `.feature` usando a linguagem Gherkin, enquanto os steps implementam o comportamento de cada etapa.

#### Exemplo Feature:

```gherkin
Feature: Autenticação com Magic Link

  @auth @login
  Scenario: Login bem-sucedido com magic link
    Given que estou na página de login
    When insiro "danrley.pereira@udf.edu.br" no campo de email
    And clico no botão "Próximo"
    And recebo o magic link da API
    And acesso o magic link
    Then devo ver o token salvo no localStorage
    And devo ser redirecionado para os eventos
```

## Pontos Importantes

### Fluxo de Autenticação Magic Link

1. Usuário acessa a página de login
2. Insere o email (deve terminar com @udf.edu.br)
3. Clica no botão "Próximo"
4. Sistema gera e envia magic link (simulado via API)
5. Usuário acessa o magic link recebido
6. Sistema autentica o usuário e salva token no localStorage
7. Usuário é redirecionado para o event

### Interceptação de Resposta da API (CDP)

A suíte de testes utiliza o Chrome DevTools Protocol (CDP) para interceptar respostas de rede, especialmente para o fluxo de login com magic link. Isso permite que os testes capturem o magic link diretamente da resposta da API sem a necessidade de chamadas adicionais.

Principais pontos da implementação:

- Utilizamos JavaScript para fazer monkey-patch das funções `fetch` e `XMLHttpRequest` para interceptar respostas
- Quando o endpoint de API do magic link é chamado, armazenamos os dados da resposta em uma variável global no navegador
- O step do Behave então recupera esses dados diretamente do navegador

Vantagens:

- Testes mais rápidos e confiáveis por eliminar chamadas HTTP adicionais
- Simulação mais precisa do fluxo real do usuário
- Menos dependência de APIs externas

A implementação pode ser encontrada em `features/steps/login_steps.py`.

### Capturas de Tela

Screenshots são capturados automaticamente quando um teste falha e salvos no diretório `screenshots/`.

### Logs

Os logs do console do navegador são capturados e exibidos no log do Behave para facilitar a depuração.

## Troubleshooting

### WebDriver não encontrado

Verifique se o Chrome está instalado e atualizado. O Selenium Manager, incluído no Selenium, localiza ou obtém o driver compatível.

### Timeout nas Esperas

Para aplicações React com tempo de carregamento lento, ajuste os timeouts no arquivo `.env`:

```env
PAGE_LOAD_TIMEOUT=60
IMPLICIT_WAIT=15
```

### Erro de Conexão com a API

Verifique se a API de autenticação está rodando na URL configurada em `API_URL`.

## Convenções de Código

- Todas as funções e métodos possuem type hints
- Docstrings descritivos para todas as funções e classes
- Uso de PascalCase para classes
- Uso de snake_case para funções e variáveis
- Tratamento de exceções para operações críticas

## Recursos Adicionais

- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Behave Documentation](https://behave.readthedocs.io/en/latest/)
- [Page Object Pattern](https://www.selenium.dev/documentation/en/guidelines_and_recommendations/page_object_models/)
