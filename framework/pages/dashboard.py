from playwright.sync_api import Page

class DashboardPage:
    def __init__(self,page):
        self.page = page
        self.welcome_locator = page.get_by_role("heading", name="Welcome")
        self.new_project_request_locator = page.get_by_role("link", name="New Project Request")

    def open_new_project_request(self):
        self.new_project_request_locator.click()
