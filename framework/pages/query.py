from playwright.sync_api import Page as page
from framework.utils.date_picker import select_date_time

class Query:
    def __init__(self,page:page):
        self.page = page
        self.task_menu_locator = page.get_by_role("link", name="Tasks")
        self.default_tab_locator = page.get_by_role("tab", name="New Project Request")
        self.query_tab_locator = page.get_by_role("tab", name="Queries")
        self.raise_query_button_locator = page.get_by_role("button", name="+ Raise Query")
        self.raise_query_dialog_locator = page.get_by_role("dialog")
        self.raise_query_heading_locator = page.get_by_role("heading", name="Raise Query")
        self.query_title_locator = page.get_by_placeholder('Eg. Issue with purchase order')
        self.search_project_locator = page.get_by_placeholder('Search Related Project')
        self.query_description_locator = page.get_by_placeholder("Enter your query description")
        self.deadline_locator = page.locator('#query-deadline')
        self.related_task_locator = page.locator('#query-task')
        self.query_responder_locator = page.locator('#query-responder-project')
        self.submit_locator = page.get_by_role("dialog").get_by_role("button", name="Submit")
        self.toast_locator = page.locator('.Toastify')
        self.query_row_locator = page.get_by_role("tabpanel", name="Queries").get_by_role("table").get_by_role("link")

    def navigate_to_the_task_menu(self):
       self.task_menu_locator.visible.click()
       get_default_tab = self.default_tab_locator.inner_text()
       return get_default_tab

    def move_to_query_tab(self):
        self.query_tab_locator.click()

    def open_query_pop_up(self):
        self.raise_query_button_locator.click()

    def raise_query(self,query_title,project_name,query_description,deadline,related_task,query_responder):
        self.query_title_locator.fill(query_title)
        self.search_project_locator.fill(project_name)
        self.select_option(project_name)
        self.query_description_locator.fill(query_description)
        self.select_deadline(deadline)
        self.related_task_locator.click()
        self.select_option(related_task)
        self.query_responder_locator.click()
        self.select_option(query_responder)

    def select_option(self,option_name):
        # Dropdown options come from test data, so the locator is built here.
        # Role 'option' targets only the open dropdown, not matching text elsewhere on the page.
        self.page.get_by_role("option", name=option_name, exact=True).click()

    def select_deadline(self,deadline):
        select_date_time(self.page, 'query-deadline', deadline)

    def submit_query(self):
        # Waits for the save API so validation happens after the query is really saved.
        with self.page.expect_response(lambda response: "/queries/saveQuery" in response.url) as response_info:
            self.submit_locator.click()
        return response_info.value.status

    def get_query_row(self,query_title):
        return self.query_row_locator.filter(has=self.page.get_by_role("cell", name=query_title, exact=True))
