import re
import json
import allure
from datetime import datetime
from playwright.sync_api import expect
from framework.pages.dashboard import DashboardPage
from framework.pages.new_project_request import NewProjectRequestPage
from framework.pages.project import ProjectPage
from framework.data.new_project_data import requirement_overview, select_framework, project_details_data, compliance_test_data, submit_request_data, project_stakeholders_summary, procurement_route_summary, compliance_summary
from framework.utils.date_picker import to_app_display_time
import pytest

# ---------- reusable steps for the tests in this module ----------
def create_draft_project(page,project_title):
    # Starts a new NPR (title + framework) and stays on the first milestone, ready to be filled in one go.
    # Returns the NewProjectRequestPage and the new project's id (read from the URL).
    dashboard = DashboardPage(page)
    new_project_request = NewProjectRequestPage(page)
    dashboard.open_new_project_request()
    expect(new_project_request.project_title_locator, "Create New Request page did not load").to_be_visible()
    new_project_request.enter_project_title(project_title)
    new_project_request.click_next()
    expect(new_project_request.select_framework_locator, "Select Framework step did not load").to_be_visible(timeout=30000)
    new_project_request.select_framework(select_framework['framework'])
    expect(new_project_request.next_locator).to_be_enabled()
    new_project_request.click_next()
    expect(new_project_request.current_milestone_locator, "Requirement Overview milestone did not load").to_contain_text("Requirement Overview", timeout=30000)
    expect(new_project_request.overview_project_title_locator, "Project title not carried into the request").to_have_value(project_title)
    return new_project_request, new_project_request.get_project_id()


def fill_all_milestones(new_project_request):
    # Fills every incomplete milestone in order, checking each is marked complete, until Summary is reached.
    fill_milestone = {
        'Requirement Overview': lambda: new_project_request.fill_requirement_overview(
            requirement_overview['Please provide a summary of the project'],
            requirement_overview['Which Directorate / Department does this relate to?'],
            requirement_overview['Which service within the Directorate / Department does this requirement relate to?'],
            requirement_overview['Category'],
            requirement_overview['Subcategory']),
        'Project Stakeholders': new_project_request.fill_project_stakeholder,
        'Project Details': lambda: new_project_request.fill_project_details(
            project_details_data['publication_date'],
            project_details_data['clarification_deadline'],
            project_details_data['submission_deadline'],
            project_details_data['project_start_date'],
            project_details_data['project_end_date'],
            False,
            project_details_data['covid_19'],
            project_details_data['itt_approval'],
            project_details_data['cost_of_project'],
            project_details_data['budget_code'],
            project_details_data['sub_code'],
            project_details_data['t3_specification_path']),
        'Procurement Route': new_project_request.fill_procurement_route,
        'Compliance': lambda: new_project_request.fill_complaince_milestone(compliance_test_data['file_path']),
    }
    while True:
        current_milestone = list(new_project_request.check_milestones_and_move_next())[-1]
        if current_milestone == 'Summary':
            break
        assert current_milestone in fill_milestone, f"No fill step implemented for milestone: {current_milestone}"
        with allure.step(f"Fill milestone: {current_milestone}"):
            fill_milestone[current_milestone]()
            new_project_request.form_next_button()
            # Wait for the next milestone to open, then confirm the one just filled is marked complete
            # (fails with a clear message instead of refilling the same milestone forever).
            new_project_request.current_milestone_locator.filter(has_not_text=current_milestone).wait_for(timeout=30000)
            assert new_project_request.is_milestone_complete(current_milestone), f"'{current_milestone}' is not complete after filling - check its required fields"
    expect(new_project_request.submit_request_locator, "Summary milestone not reached").to_be_visible()


def build_expected_summary(project_title):
    # Expected Summary page values (Summary labels) for the data entered by fill_all_milestones().
    project_cost = f"£{float(project_details_data['cost_of_project']):,.2f}"   # 500000.25 -> £500,000.25
    # The app shows dates in UK time (GMT/BST), so convert the entered values before comparing.
    project_start = to_app_display_time(project_details_data['project_start_date'])
    project_end = to_app_display_time(project_details_data['project_end_date'])
    compliance_file = compliance_test_data['file_path'].name
    return {
        'Requirement Overview': {
            'Project Name': project_title,
            'Project Summary': requirement_overview['Please provide a summary of the project'],
            'Directorate / Department': requirement_overview['Which Directorate / Department does this relate to?'],
            'Service / Requirements': requirement_overview['Which service within the Directorate / Department does this requirement relate to?'],
            'Main Category': requirement_overview['Category'],
            'Sub Category': requirement_overview['Subcategory'],
        },
        'Project Stakeholders': project_stakeholders_summary,
        'Project Details': {
            'Publication Date': to_app_display_time(project_details_data['publication_date']),
            'Clarification Deadline': to_app_display_time(project_details_data['clarification_deadline']),
            'Submission Deadline': to_app_display_time(project_details_data['submission_deadline']),
            'Project Start Date': project_start,
            'Project End Date': project_end,
            'Retrospective Project': 'No',
            'Covid 19 Related': project_details_data['covid_19'],
            'Itt Approval Required': project_details_data['itt_approval'],
            'Cost Excluding Vat': project_cost,
            'Budget Code': project_details_data['budget_code'],
            'Sub Code': project_details_data['sub_code'],
            'Statement Of Requirements': [project_details_data['t3_specification_path'].name],
        },
        'Procurement Route': procurement_route_summary,
        'Compliance': {
            **compliance_summary,
            'Insurance Summary': f"Project Value (ex VAT): {project_cost}\nStart Date: {project_start}\nEnd Date: {project_end}",
            'Special Clauses Attachment': [compliance_file],
            'Nda Attachment': [compliance_file],
        },
    }


# ---------- tests ----------
@allure.feature("New Project Request")
@allure.story("Submit NPR with project approval")
@allure.title("Submit a fully filled NPR: Summary data, success alert, Dashboard redirect and 'Buyer Approver' status")
@pytest.mark.regression
def test_submit_npr_with_approval_shows_success_alert_and_buyer_approver_status(project_owner_login):
    page = project_owner_login
    dashboard = DashboardPage(page)
    project = ProjectPage(page)
    # A submitted request can't go back to draft, so this test creates its own draft with a unique title.
    project_title = f"{submit_request_data['project_title_prefix']} {datetime.now().strftime('%d%m%Y%H%M%S')}"
    allure.dynamic.parameter("Project title", project_title)

    with allure.step(f"Create draft '{project_title}'"):
        new_project_request, project_id = create_draft_project(page, project_title)
        allure.dynamic.parameter("Project id", project_id)

    with allure.step("Fill all milestones in one go up to Summary"):
        fill_all_milestones(new_project_request)

    with allure.step("Verify the Summary page matches all entered data"):
        # Attach what the Summary page shows as evidence, then compare it with the entered data.
        allure.attach(json.dumps(new_project_request.get_summary_details(), indent=2, ensure_ascii=False), name="Summary page details", attachment_type=allure.attachment_type.JSON)
        mismatches = new_project_request.get_summary_mismatches(build_expected_summary(project_title))
        assert not mismatches, "Summary page does not match the entered data:\n" + "\n".join(mismatches)

    with allure.step("Submit the request"):
        submit_status = new_project_request.submit_request()
        assert submit_status < 400, f"Submit Request API failed with status {submit_status}"

    with allure.step("Verify success alert and Dashboard redirect"):
        expect(new_project_request.toast_locator, "Submit success alert not displayed").to_contain_text(submit_request_data['success_message'], timeout=30000)
        expect(page).to_have_url(re.compile(r"test\.bloom\.engineering/$"), timeout=30000)
        expect(dashboard.welcome_locator, "Dashboard not displayed after Submit Request").to_be_visible()

    with allure.step(f"Verify project status is '{submit_request_data['status_after_submit']}'"):
        # Opened directly by id; the status updates in the background, so wait_for_current_status reloads and retries.
        project.open_project_detail_by_id(project_id)
        status_after_submit = project.wait_for_current_status(submit_request_data['status_after_submit'])
        assert status_after_submit == submit_request_data['status_after_submit'], f"Status after submit not matched: {status_after_submit}"
