import os

from behave import given, then, when
from selenium.webdriver.common.by import By

from page_objects.login_page import LoginPage
from utils.helpers import extract_hash_from_link, get_magic_link, rebase_magic_link


DOMAIN_ERROR_LOCATOR = (
    By.XPATH,
    "//*[@role='alert' and contains(normalize-space(.), 'fora do formato permitido')]",
)


@given('que estou na página de login')
def access_login_page(context):
    base_url = context.config.userdata.get('BASE_URL', 'http://localhost:3000')
    if '://' not in base_url:
        base_url = f'http://{base_url}'
    context.driver.get(f"{base_url.rstrip('/')}/organizer")
    context.login_page = LoginPage(context.driver)


@when('insiro "{email}" no campo de email')
def enter_email(context, email):
    if email == 'e2e-ci@udf.edu.br':
        email = os.environ.get('TEST_EMAIL', email)
    context.email = email
    context.login_page.enter_email(email)


@when('clico no botão "{button_text}"')
def click_button(context, button_text):
    assert button_text == 'Próximo', f'Botão não previsto neste cenário: {button_text}'
    context.login_page.click_next()


@when('recebo o magic link da API')
def receive_magic_link(context):
    assert context.email == os.environ.get('TEST_EMAIL', 'e2e-ci@udf.edu.br'), (
        'O envio de link exige a conta sintética isolada do runner'
    )
    # A UI não expõe o link; development devolve magic_link em uma chamada controlada.
    context.magic_link = get_magic_link(context.email)
    assert context.magic_link, 'Auth não retornou magic_link em development'
    context.hash = extract_hash_from_link(context.magic_link)
    assert context.hash, 'magic_link sem hash'


@when('acesso o magic link')
def access_magic_link(context):
    base_url = context.config.userdata.get('BASE_URL', 'http://localhost:3000')
    callback = rebase_magic_link(context.magic_link, base_url)
    context.driver.get(callback)
    assert context.login_page.is_redirected_to_events_page(), (
        'Callback não chegou a Meus Eventos'
    )


@then('devo ver o token salvo no localStorage')
def verify_token(context):
    token = context.login_page.verify_token_in_local_storage(expected_hash=context.hash)
    assert token == context.hash, 'A SPA vigente deve armazenar o hash validado pela Auth'


@then('devo ser redirecionado para os eventos')
def verify_redirect(context):
    assert context.login_page.is_redirected_to_events_page(), 'Não chegou a Meus Eventos'
    assert context.login_page.verify_events_heading(), 'Título Meus Eventos ausente'


@then('devo ver uma mensagem de erro indicando o domínio obrigatório')
def verify_domain_error(context):
    assert context.login_page.is_element_visible(DOMAIN_ERROR_LOCATOR), (
        'Mensagem de domínio obrigatório ausente'
    )
