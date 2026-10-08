from urllib.parse import urljoin
from playwright.sync_api import Page
class ProjectPage:
    def __init__(self,page):
        self.page = page
        self.project_menu_locator = page.get_by_role("link", name="Projects", exact=True)
        self.search_project_locator = page.get_by_role("combobox", name="Search for Project Name, Project ID")
        self.column_header_locator = page.get_by_role("table").get_by_role("columnheader")
        self.project_row_locator = page.get_by_role("table").get_by_role("link")
        # Status chip has no label/role linking it to "CURRENT STATUS", so take the label's next sibling.
        self.current_status_locator = page.get_by_text("CURRENT STATUS", exact=True).locator("xpath=following-sibling::*[1]")
        self.summary_tab_locator = page.get_by_role("tabpanel", name="Summary")
        # Task cards carry their status in aria-label; 'has p' skips the assignee avatar (also aria-labelled).
        self.task_card_locator = self.summary_tab_locator.get_by_text("Tasks", exact=True).locator("xpath=..").locator("[aria-label]").filter(has=page.locator("p"))

    def navigate_to_projects(self):
        self.project_menu_locator.click()

    def search_project(self,project_name):
        # Wait for the search API so the table shows filtered results before it is read.
        with self.page.expect_response(lambda response: "/project/all" in response.url and "search=" in response.url):
            self.search_project_locator.fill(project_name)

    def get_project_details(self,project_name):
        # Returns {column name: value} for the first (latest) row matching the project name.
        project_row = self.project_row_locator.filter(has=self.page.get_by_role("cell", name=project_name, exact=True)).first
        project_row.wait_for()
        column_names = [name.strip() for name in self.column_header_locator.all_inner_texts()]
        column_values = []
        for cell in project_row.get_by_role("cell").all():
            value = cell.inner_text().strip()
            # Long values are shown shortened with "..."; the full value is kept in the inner element's aria-label.
            full_value = cell.locator("[aria-label]")
            if value.endswith("...") and full_value.count():
                value = full_value.first.get_attribute("aria-label").strip()
            column_values.append(value)
        return {name: value for name, value in zip(column_names, column_values) if name != "Actions"}
    def navigate_to_project_detail_page(self,project_name):
        self.project_row_locator.filter(has=self.page.get_by_role("cell", name=project_name, exact=True)).first.click()

    def open_project_detail_by_id(self,project_id):
        # Opens /projects/<id>/npr on the current environment directly (no Projects search needed).
        self.page.goto(urljoin(self.page.url, f"/projects/{project_id}/npr"))
        self.current_status_locator.wait_for()

    def get_current_status(self):
        return self.current_status_locator.inner_text().strip()

    def wait_for_current_status(self,expected_status,retries=10,interval_ms=3000):
        # The status is updated in the background after an action (e.g. Submit Request) and the detail page does not
        # refresh by itself, so reload and re-read until it shows the expected status or the retries run out.
        # Returns the last status read, so the test can assert on it with a clear message.
        current_status = self.get_current_status()
        for _ in range(retries):
            if current_status == expected_status:
                break
            self.page.wait_for_timeout(interval_ms)
            self.page.reload()
            current_status = self.get_current_status()
        return current_status

    def get_milestone_tasks(self,milestone_name):
        # Selecting a milestone switches the Tasks list to that milestone's tasks.
        self.summary_tab_locator.get_by_text(milestone_name, exact=True).click()
        self.task_card_locator.first.wait_for()
        return [card.locator("p").first.inner_text().strip() for card in self.task_card_locator.all()]

    def get_task_card(self,task_name):
        return self.task_card_locator.filter(has=self.page.get_by_text(task_name, exact=True))

    def get_task_status(self,task_name):
        return self.get_task_card(task_name).get_attribute("aria-label")

    def open_task(self,task_name):
        self.get_task_card(task_name).click()