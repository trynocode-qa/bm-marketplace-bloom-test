from framework.pages.login import LoginPage
from framework.data.test_data import project_owner_credential
def test_successful_login(open_browser_test_environment):
    page = open_browser_test_environment
    buyer_login = LoginPage(page)
    buyer_login.buyer_login(project_owner_credential['email'],project_owner_credential['password'])
    page.pause()