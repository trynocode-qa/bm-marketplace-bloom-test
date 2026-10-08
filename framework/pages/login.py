from playwright.sync_api import Page

class LoginPage:
    def __init__(self,page):
        self.page = page
        # Placeholders are stable on the Cognito page; the textbox accessible names vary ("Email Email" vs "name@host.com").
        self.email_locator = page.get_by_placeholder("name@host.com")
        self.password_locator = page.get_by_placeholder("Password")
        self.sign_in_locator = page.get_by_role("button", name="submit")

    def buyer_login(self,email,password):
        self.email_locator.filter(visible=True).fill(email)
        self.password_locator.filter(visible=True).fill(password)
        self.sign_in_locator.filter(visible=True).click()
