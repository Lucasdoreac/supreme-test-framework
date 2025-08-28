Feature: Criação de Evento
  Como um usuário autenticado do sistema
  Eu quero criar um novo evento
  Para organizar atividades e gerenciar participantes

  Background:
    Given que estou autenticado no sistema
    And estou na página de meus eventos

  @event @create
  Scenario: Criar evento básico com fluxo completo
    When clico no botão "Cadastrar Novo Evento"
    Then devo estar na página de seleção de tipo de evento
    When seleciono o tipo de evento "Mão na massa"
    And clico no botão "Próximo"
    Then devo estar na página de informações básicas
    When preencho o título do evento "Workshop de Automação"
    And seleciono a ODS "4 - Educação de qualidade (EDQ)"
    And clico no botão "Próximo"
    Then devo estar na página de detalhes do evento
    When preencho a descrição "Workshop sobre testes automatizados com Selenium"
    And busco e seleciono o curso "Engenharia" com opção "ENGENHARIA DE SOFTWARE (BACHARELADO)"
    And seleciono público alvo "Professores, Alunos UDF"
    And seleciono recursos necessários "Humanas, Tecnologias"
    And clico no botão "Próximo"
    Then devo estar na página de logística

  @event @create @quick
  Scenario: Testar navegação até página de detalhes
    When clico no botão "Cadastrar Novo Evento"
    Then devo estar na página de seleção de tipo de evento
    When seleciono o tipo de evento "Palestra"
    And clico no botão "Próximo"
    Then devo estar na página de informações básicas
    When preencho o título do evento "Palestra sobre IA"
    And preencho o telefone "(61) 9 9999-9999"
    And seleciono a ODS "4 - Educação de qualidade (EDQ)"
    And clico no botão "Próximo"
    Then devo estar na página de detalhes do evento
