Feature: Autenticação com Magic Link
  Como um usuário do sistema
  Eu quero fazer login usando magic link
  Para acessar a aplicação com segurança
  
  @auth @login
  Scenario: Login bem-sucedido com magic link
    Given que estou na página de login
    When insiro "danrley.pereira@udf.edu.br" no campo de email
    And clico no botão "Próximo"
    And recebo o magic link da API
    And acesso o magic link
    Then devo ver o token salvo no localStorage
    And devo ser redirecionado para o dashboard
    
  @auth @login @validation
  Scenario: Validação de email com domínio obrigatório
    Given que estou na página de login
    When insiro "usuario.invalido@gmail.com" no campo de email
    And clico no botão "Próximo"
    Then devo ver uma mensagem de erro indicando o domínio obrigatório