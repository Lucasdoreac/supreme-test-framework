# Telas logadas dos Drafts do Web (#44 Sair, #45 indicador de etapa, #51 pedido de alterações).
# Tag @drafts: só rodam contra um Web que tenha esses Drafts (integração); sem a tag --tags=drafts
# o `behave` padrão as ignora (behave.ini), então a execução contra a main continua verde.
Feature: Telas logadas
  Como organizador autenticado
  Eu quero sair, acompanhar as etapas do pedido e ver o que a Coordenação pediu
  Para usar o sistema sem ficar perdido

  @drafts @logout
  Scenario: Sair encerra a sessão
    Given que estou logado como "e2e-ci@udf.edu.br"
    When clico em "Sair"
    Then devo ser levado para a página "/organizer"
    And a sessão não deve mais existir no localStorage
    And uma rota privada deve me mandar embora ao abri-la

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
