import re
from playwright.sync_api import expect
from framework.pages.dashboard import DashboardPage
from framework.pages.new_project_request import NewProjectRequestPage
from framework.data.new_project_data import requirement_overview, select_framework, project_detail_draft,project_details_data,compliance_test_data,project_stakeholders_summary,procurement_route_summary,compliance_summary,submit_request_data
from framework.utils.date_picker import to_app_display_time
from framework.pages.project import ProjectPage
import pytest
@pytest.mark.smoke
def test_create_new_project_request_and_save_as_draft(project_owner_login):
    page = project_owner_login
    dashboard = DashboardPage(page)
    new_project_request = NewProjectRequestPage(page)

    dashboard.open_new_project_request()
    expect(new_project_request.project_title_locator, "Create New Request page did not load").to_be_visible()

    new_project_request.enter_project_title(requirement_overview['project_title'])
    new_project_request.click_next()
    expect(page).to_have_url(re.compile(r"/project-requests/select-framework"))
    expect(new_project_request.select_framework_locator, "Select Framework step did not load").to_be_visible()

    new_project_request.select_framework(select_framework['framework'])
    expect(new_project_request.next_locator).to_be_enabled()
    new_project_request.click_next()
    expect(new_project_request.project_summary_locator, "Requirement Overview milestone did not load").to_be_visible(timeout=30000)
    expect(new_project_request.overview_project_title_locator, "Project title on Requirement Overview does not match test data").to_have_value(requirement_overview['project_title'])

    new_project_request.save_and_exit()
    expect(page).to_have_url(re.compile(r"test\.bloom\.engineering/$"), timeout=30000)
    expect(dashboard.welcome_locator, "Dashboard not displayed after Save and Exit").to_be_visible()
@pytest.mark.smoke
def test_create_fill_verify_and_submit_new_project_request(project_owner_login):
    page = project_owner_login
    dashboard = DashboardPage(page)
    project = ProjectPage(page)
    project_title = requirement_overview['project_title']

    # -------- Find the draft and open its task --------
    project.navigate_to_projects()
    expect(project.search_project_locator, "Projects page did not load").to_be_visible()

    project.search_project(project_title)
    project_details = project.get_project_details(project_title)
    print(project_details)

    assert project_details['Name'] == project_title, f"Searched project not found: {project_details}"
    assert project_details['Status'] == 'In Draft', f"Searched project status not matched: {project_details['Status']}"
    project.navigate_to_project_detail_page(project_title)

    current_status = project.get_current_status()
    assert current_status == project_detail_draft['current_status'], f"Current status mismatch: {current_status}"

    milestone_tasks = project.get_milestone_tasks(project_detail_draft['milestone'])
    print(milestone_tasks)
    assert project_detail_draft['task_name'] in milestone_tasks, f"Task not found under {project_detail_draft['milestone']}: {milestone_tasks}"

    task_status = project.get_task_status(project_detail_draft['task_name'])
    # assert task_status == project_detail_draft['task_status'], f"Task status mismatch: {task_status}"

    project.open_task(project_detail_draft['task_name'])
    expect(page).to_have_url(re.compile(r"taskId="))
    expect(NewProjectRequestPage(page).project_summary_locator, "Task did not open").to_be_visible(timeout=30000)
    new_project_request = NewProjectRequestPage(page)

    # Fill step for each milestone, in order.
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

    # Skip completed milestones, fill the first incomplete one, Next, and repeat until Summary is reached.
    while True:
        milestone_status = new_project_request.check_milestones_and_move_next()
        print(milestone_status)
        current_milestone = list(milestone_status)[-1]
        if current_milestone == 'Summary':
            break
        assert current_milestone in fill_milestone, f"No fill step implemented for milestone: {current_milestone}"

        fill_milestone[current_milestone]()
        new_project_request.form_next_button()
        # Wait until the next milestone opens, then confirm the one just filled is now marked complete
        # (stops the loop with a clear message instead of refilling the same milestone forever).
        new_project_request.current_milestone_locator.filter(has_not_text=current_milestone).wait_for()
        assert new_project_request.is_milestone_complete(current_milestone), f"'{current_milestone}' is not complete after filling - check its required fields"

    expect(new_project_request.current_milestone_locator, "Summary milestone not reached").to_contain_text('Summary')
    new_project_request.submit_request_locator.wait_for()

    # -------- Verify every milestone's answers on the Summary page --------
    print(new_project_request.get_summary_details())
    project_cost = f"£{float(project_details_data['cost_of_project']):,.2f}"   # 500000.25 -> £500,000.25
    project_start = to_app_display_time(project_details_data['project_start_date'])
    project_end = to_app_display_time(project_details_data['project_end_date'])
    compliance_file = compliance_test_data['file_path'].name
    expected_summary = {
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
            # The app shows dates in UK time (GMT/BST), so convert the entered values before comparing.
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
    mismatches = new_project_request.get_summary_mismatches(expected_summary)
    assert not mismatches, "Summary page does not match the entered data:\n" + "\n".join(mismatches)

    # -------- Submit the request --------
    submit_status = new_project_request.submit_request()
    assert submit_status < 400, f"Submit Request API failed with status {submit_status}"
    expect(new_project_request.toast_locator, "Submit success message not displayed").to_contain_text(submit_request_data['success_message'], timeout=30000)
    expect(page).to_have_url(re.compile(r"test\.bloom\.engineering/$"), timeout=30000)
    expect(dashboard.welcome_locator, "Dashboard not displayed after Submit Request").to_be_visible()

    # -------- Status on the project detail page (updated in the background, so retry) --------
    project.navigate_to_projects()
    project.search_project(project_title)
    project.navigate_to_project_detail_page(project_title)
    status_after_submit = project.wait_for_current_status(submit_request_data['status_after_submit'])
    print(status_after_submit)
    assert status_after_submit == submit_request_data['status_after_submit'], f"Status after submit not matched: {status_after_submit}"


