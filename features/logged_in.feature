# Telas logadas dos Drafts do Web (#44 Sair, #45 indicador de etapa, #51 pedido de alterações).
# Tag @drafts: só rodam contra um Web que tenha esses Drafts (integração); sem a tag --tags=drafts
# o `behave` padrão as ignora (behave.ini), então a execução contra a main continua verde.
Feature: Telas logadas
  Como organizador autenticado
  Eu quero sair, acompanhar as etapas do pedido e ver o que a Coordenação pediu
  Para usar o sistema sem ficar perdido

  @drafts @steps
  Scenario Outline: O indicador mostra em que etapa do pedido estou
    Given que estou logado como "e2e-ci@udf.edu.br"
    When navego para "<rota>"
    Then devo ver o indicador "Etapa <n> de 6"

    Examples:
      | rota                  | n |
      | /event/type-selection | 1 |
      | /event/basic-info     | 2 |
      | /event/details        | 3 |
      | /event/logistics      | 4 |
      | /event/schedule       | 5 |
      | /event/confirm-data   | 6 |

  @drafts @change-request @seed
  Scenario: O organizador vê o que a Coordenação pediu e corrige
    Given que estou logado como "e2e-ci@udf.edu.br"
    And existe um evento meu em "requested_change" com o motivo "Trocar a sala <b>agora</b> e informar o número de inscritos."
    When abro Meus Eventos
    Then devo ver o aviso de alterações com o motivo como texto
    When clico em "Corrigir e reenviar"
    Then devo estar no fluxo de edição do evento semeado

  # Web #47: duas abas do mesmo navegador avançando antes de existir um rascunho criavam dois.
  @drafts @tabs
  Scenario: Duas abas avançando juntas na logística criam um único rascunho
    Given que estou logado como "e2e-ci@udf.edu.br"
    And a conta isolada não tem pedido em andamento
    And abro a etapa de logística em duas abas sem rascunho
    When avanço na primeira aba e depois na segunda
    Then a conta deve ter exatamente 1 rascunho novo
    And as duas abas devem estar na agenda do mesmo rascunho

  # Web #47 e #29: o envio final limpa o id guardado; a outra aba cria um rascunho novo em vez de dar 409.
  @drafts @tabs
  Scenario: Depois do envio final numa aba, a outra aba cria um rascunho novo
    Given que estou logado como "e2e-ci@udf.edu.br"
    And a conta isolada não tem pedido em andamento
    And abro a etapa de logística em duas abas sem rascunho
    When avanço na primeira aba
    And envio o pedido pela primeira aba
    And avanço na segunda aba
    Then a segunda aba deve estar na agenda de um rascunho diferente do enviado
    And a conta deve ter 1 pedido enviado e 1 rascunho novo

  # Web #42: a lista de salas ganha "Tentar novamente" quando a API falha.
  @drafts @rooms
  Scenario: A lista de salas oferece nova tentativa quando a API cai e volta
    Given que estou logado como "e2e-ci@udf.edu.br"
    And abro a agenda com a lista de salas carregada
    When a API fica fora do ar
    And mudo o período da agenda
    Then devo ver o alerta da lista de salas com o botão "Tentar novamente"
    When a API volta ao ar
    And clico em "Tentar novamente"
    Then a lista deve mostrar salas e nenhum alerta

  # Web #53: Sair com o Auth parado leva ao login com o aviso. A sessão continua válida no servidor
  # (a revogação falhou), então o cenário seguinte ainda pode reaproveitá-la.
  @drafts @logout-unconfirmed
  Scenario: Sair com o Auth parado avisa na tela de login
    Given que estou logado como "e2e-ci@udf.edu.br"
    And o Auth está fora do ar
    When clico em "Sair"
    Then devo ser levado para a página "/organizer"
    And a tela de login deve avisar que o encerramento não foi confirmado
    And o Auth volta ao ar

  # Web #43: Enter no campo de e-mail envia o formulário (antes só o clique no botão enviava). O e-mail de outro
  # domínio mostra o erro de validação sem pedir link, então não gasta o limite de pedidos do Auth.
  @drafts @enter
  Scenario: Enter envia o formulário de login
    Given que estou na página de login
    When insiro "usuario.invalido@gmail.com" no campo de email
    And pressiono Enter no campo de email
    Then devo ver uma mensagem de erro indicando o domínio obrigatório

  # Último de propósito: encerra no servidor a sessão que os outros cenários reaproveitam.
  @drafts @logout
  Scenario: Sair encerra a sessão no navegador e no servidor
    Given que estou logado como "e2e-ci@udf.edu.br"
    And guardo o token e o e-mail da sessão
    When clico em "Sair"
    Then devo ser levado para a página "/organizer"
    And a tela de login não deve avisar sobre o encerramento
    And a sessão não deve mais existir no localStorage
    And a API deve recusar o token guardado
    And uma rota privada deve me mandar embora ao abri-la
