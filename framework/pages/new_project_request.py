import re
from pathlib import Path
from playwright.sync_api import Page

class NewProjectRequestPage:
    def __init__(self,page):
        self.page = page
        self.project_title_locator = page.get_by_role("textbox", name="Project Title", exact=True)
        self.next_locator = page.get_by_role("button", name="Next")
        self.select_framework_locator = page.get_by_text("Please select the Framework")
        self.project_summary_locator = page.get_by_role("heading", name="Project Summary")
        self.overview_project_title_locator = page.get_by_role("textbox", name="Project Title *")
        self.save_and_exit_locator = page.get_by_role("button", name="Save and Exit")
        self.next_button_locator = page.get_by_role('button',name='Next')
        self.milestone_link_locator = page.locator('a[href*="/milestone/"]')
        self.current_milestone_locator = page.locator('a[href*="/milestone/"][aria-current="step"]')
        self.milestone_complete_icon_locator = page.locator('svg path[d^="M9 16.2"]')
        # Summary milestone: one collapsible section per milestone; only one section is open at a time.
        self.summary_section_button_locator = page.get_by_role("heading", level=3).get_by_role("button")
        self.submit_request_locator = page.get_by_role("button", name="Submit Request")
        # Success / error messages are react-toastify toasts.
        self.toast_locator = page.locator('.Toastify')
        # Renamed from project_summary_locator - that name was already used for the "Project Summary" heading above
        # and silently overwrote it.
        self.project_overview_locator = page.get_by_placeholder('Project Overview')
        self.department_locator = page.get_by_placeholder('e.g. Finance')
        self.project_service_locator = page.get_by_placeholder('e.g. Payroll')
    def enter_project_title(self,project_title):
        self.project_title_locator.fill(project_title)

    def click_next(self):
        self.next_locator.click()

    def select_framework(self,framework):
        # Framework cards have no role; the name comes from test data, so the locator is built here.
        self.page.get_by_text(framework, exact=True).click()

    def save_and_exit(self):
        self.save_and_exit_locator.click()

    def get_project_id(self):
        # Every draft page URL carries ?...&projectId=<id>; used to open the project directly later (no search needed).
        return re.search(r"projectId=(\d+)", self.page.url).group(1)

    def fill_requirement_overview(self,project_summary,project_department,project_service,category,sub_category):
        self.project_overview_locator.fill(project_summary)
        self.department_locator.fill(project_department)
        self.project_service_locator.fill(project_service)
        # Pick from the open list by role: get_by_text also matches the dropdown itself once it shows a value.
        self.page.get_by_role('combobox').nth(0).click()
        self.page.get_by_role("option", name=category, exact=True).click()
        self.page.get_by_role('combobox').nth(1).click()
        self.page.get_by_role("option", name=sub_category, exact=True).click()
    def form_next_button(self):
        self.next_button_locator.click()

    def get_current_milestone(self):
    # name of the milestone page currently open. A partly filled milestone also shows its progress
    # (e.g. "Requirement Overview\n\n17%"), so keep only the first line - the milestone name.
        return self.current_milestone_locator.inner_text().strip().split("\n")[0].strip()

    def wait_for_milestone_status(self):
    # After Next / page load the sidebar reloads milestone progress. While loading, the current
    # milestone shows a spinner (progressbar without "%") instead of its check icon, and may briefly
    # show its old icon first. Wait until the current milestone shows no spinner and its state has
    # stayed the same for 500ms, so the check icon is read only after the refresh has finished.
        self.page.wait_for_function("""() => {
            const link = document.querySelector('a[href*="/milestone/"][aria-current="step"]');
            if (!link) return false;
            const loading = !!link.querySelector('[role=progressbar]') && !link.innerText.includes('%');
            const state = loading ? 'loading' : link.innerText + (link.querySelector('svg path[d^="M9 16.2"]') ? ':complete' : ':incomplete');
            if (state !== window.__milestoneState) {
                window.__milestoneState = state;
                window.__milestoneStateSince = Date.now();
                return false;
            }
            return !loading && Date.now() - window.__milestoneStateSince >= 500;
        }""", polling=100, timeout=30000)

    def is_milestone_complete(self,milestone_name):
    # True if that milestone's sidebar link shows the check SVG
        self.wait_for_milestone_status()
        milestone = self.milestone_link_locator.filter(has_text=milestone_name)
        return milestone.locator(self.milestone_complete_icon_locator).count() > 0

    def check_milestones_and_move_next(self):
    # Check the open page; if complete, click Next and check the next page.
    # Stop at the first incomplete milestone or at the last one ("Summary").
        milestone_status = {}
        while True:
            milestone_name = self.get_current_milestone()
            is_complete = self.is_milestone_complete(milestone_name)
            milestone_status[milestone_name] = is_complete
            if not is_complete or milestone_name == 'Summary':
                return milestone_status
            self.form_next_button()
        # wait until the open milestone changes before checking again
            self.current_milestone_locator.filter(has_not_text=milestone_name).wait_for()
    def fill_project_stakeholder(self):
        # Search-as-you-type: type like a user so the member search fires, pick the option, confirm it was added.
        self.page.get_by_role("combobox", name="Additional Stakeholders").press_sequentially('Additional Stakeholder 01 Test')
        self.page.get_by_role("option", name='Sawan - Additional Stakeholder 01 Test', exact=True).click()
        self.page.get_by_role("button", name='remove Sawan - Additional Stakeholder 01 Test').wait_for()
        # First radio group = "Is Project Approval Required?" (answering Yes adds the Pre Approval group below it).
        self.page.get_by_role("radiogroup").first.get_by_role("radio", name="Yes").click()
        self.page.locator('input[name$="projectPreApproval"][value="no"]').click()
        self.page.locator('input[name$=".approverName"]').locator('xpath=preceding-sibling::*[@role="combobox"]').click()
        self.page.get_by_role("option", name='Sawan - Project Approver Test', exact=True).click()
        self.page.locator('input[name$="paymentApproverName"]').locator('xpath=preceding-sibling::*[@role="combobox"]').click()
        self.page.get_by_role("option", name='Sawan - Budget Approver Test', exact=True).click()
    def fill_project_details(self,publication_date,clarification_deadline,submission_deadline,project_start_date,project_end_date,
                             is_retrospective,covid_related,itt_approval_required,project_cost,budget_code,sub_code,
                             attachment_path,supporting_documents=None):
        # Dates       : 'DD/MM/YYYY hh:mm AM' strings, e.g. '20/10/2026 10:00 AM' (keep them in logical order)
        # Yes/No args : 'Yes' or 'No'
        # Files       : attachment_path = one file path; supporting_documents = list of paths or None
        from datetime import datetime
        from pathlib import Path

        def field_locator(question_text,control_xpath):
            # Questions here have no linked label / stable id: find the question text, then the nearest container holding the control.
            return self.page.get_by_text(question_text).locator(f"xpath=ancestor::div[.//{control_xpath}][1]")

        def select_date(question_text,date_time):
            # Typing into the Day section auto-advances through Day/Month/Year/Hours/Minutes/AM-PM.
            value = datetime.strptime(date_time, "%d/%m/%Y %I:%M %p")
            date_picker = field_locator(question_text, "*[@role='group']")
            date_picker.get_by_role("spinbutton", name="Day").press_sequentially(value.strftime("%d%m%Y%I%M") + value.strftime("%p")[0])

        def upload_files(question_text,file_paths):
            # Each file goes to POST /file/upload (box shows "Uploading..."); once the server accepts it the page
            # lists the file as "<name> | Uploaded" with a "Remove <name>" button. Wait for that button per file,
            # so the next step only runs after every upload has finished. A failed upload never shows it -> timeout.
            field_locator(question_text, "input[@type='file']").locator("input[type=file]").set_input_files(file_paths)
            for file_path in (file_paths if isinstance(file_paths, list) else [file_paths]):
                self.page.get_by_role("button", name=f"Remove {Path(file_path).name}", exact=True).wait_for(timeout=60000)

        # Project Timeline - date-time pickers
        select_date("Publication Date", publication_date)
        select_date("Clarification Deadline", clarification_deadline)
        select_date("Submission Deadline", submission_deadline)

        # Retrospective checkbox (optional)
        retrospective_locator = field_locator("Is this a retrospective project?", "input[@type='checkbox']").get_by_role("checkbox")
        if is_retrospective:
            retrospective_locator.check()
        else:
            retrospective_locator.uncheck()

        select_date("Project Start Date", project_start_date)
        select_date("Project End Date", project_end_date)

        # Yes/No questions - scoped by question because there are two radio groups on the page
        field_locator("Is this requirement related to COVID-19?", "*[@role='radiogroup']").get_by_role("radio", name=covid_related, exact=True).check()
        field_locator("Do you require the ITT pack to be approved", "*[@role='radiogroup']").get_by_role("radio", name=itt_approval_required, exact=True).check()

        # Cost and codes - labels are linked, so role locators work
        self.page.get_by_role("textbox", name="Cost for this Project (Excluding VAT) *").fill(project_cost)
        self.page.get_by_role("textbox", name="Budget Code").fill(budget_code)
        self.page.get_by_role("textbox", name="Sub Code").fill(sub_code)

        # File uploads - set_input_files works on the hidden file inputs; each call waits until the upload is confirmed
        upload_files("Attachments", attachment_path)
        if supporting_documents:
            upload_files("Add Supporting Documents", supporting_documents)
    def fill_procurement_route(self):
        self.page.get_by_role("radio", name="Mini Competition", exact=True).click()
        self.page.get_by_role("textbox", name="How many suppliers do you want to include? *").fill("3")
        # Company Name / Named Contact only appear when "specific Suppliers" is Yes. Scope the radio by its question:
        # a bare label filter on "No" also matches region labels such as "North East England".
        specific_suppliers = self.page.get_by_text("Are there any specific Suppliers you would like Bloom to include?").locator("xpath=ancestor::div[.//*[@role='radiogroup']][1]")
        specific_suppliers.get_by_role("radio", name="Yes", exact=True).click()
        Supplier_name = self.page.get_by_role("combobox", name="Company Name")
        Supplier_name.press_sequentially('Bloom Test Supplier 01')
        self.page.get_by_role("option", name='Bloom Test Supplier 01', exact=True).click()
        # The picked company is listed below the field with a "remove <name>" button (the input itself is cleared).
        self.page.get_by_role("button", name='remove Bloom Test Supplier 01').wait_for()
        self.page.get_by_role("textbox", name="Named Contact").fill('Test Supplier Contact')
        supplier_shortlist_approval = self.page.get_by_text("Do you require the Supplier Shortlist to be approved by the requirement owner?").locator("xpath=ancestor::div[.//*[@role='radiogroup']][1]")
        supplier_shortlist_approval.get_by_role("radio", name="Yes", exact=True).click()
        #-------Supplier Shortlisting Criteria-------------
        #******Region*******
        self.page.get_by_text("Belfast",exact=True).click()
        #******Technical Accreditation*****
        self.page.get_by_role("textbox", name="Please list accreditations required").fill('Test Technical Accreditations')
        #******Size of Supplier*******
        self.page.get_by_text("Medium",exact=True).click()
        #******Security********
        self.page.get_by_text('Cloud Security Alliances Cloud Controls Matrix (CCM)',exact=True).click()
        #*****Security Claerance******
        self.page.get_by_text('Baseline Personnel Security Standard (BPSS)',exact=True).click()
        #*****Industry Standard******
        self.page.get_by_text('BES6001',exact=True).click()
        #******DBS******
        self.page.get_by_text('Standard',exact=True).click()

    def field_locator(self,question_text,control_xpath):
        # Questions have no linked label / stable id: find the question text, then the nearest container holding the control.
        return self.page.get_by_text(question_text).locator(f"xpath=ancestor::div[.//{control_xpath}][1]")

    def answer_question(self,question_text,answer):
        # Yes/No radio question, scoped by its question text (many Yes/No groups on one page).
        self.field_locator(question_text, "*[@role='radiogroup']").get_by_role("radio", name=answer, exact=True).click()

    def select_dropdown(self,question_text,option_name):
        # Dropdowns have no accessible name, so scope by question text, then pick the option from the open list.
        self.field_locator(question_text, "*[@role='combobox']").get_by_role("combobox").click()
        self.page.get_by_role("option", name=option_name, exact=True).click()

    def fill_text_after_question(self,question_text,value):
        # Conditional text fields appear outside the question's container: take the first text input after the question.
        # Only valid once the field is shown (answer the question first).
        self.page.get_by_text(question_text).locator("xpath=following::input[@type='text'][1]").fill(value)

    def upload_file_after_question(self,question_text,file_path):
        # Conditional upload fields appear outside the question's container: take the first file input after the question.
        # A confirmed upload adds a "Remove <file name>" button. The same file may already be uploaded for another
        # question, so wait for one more such button than before.
        remove_button = self.page.get_by_role("button", name=f"Remove {Path(file_path).name}", exact=True)
        uploaded_before = remove_button.count()
        self.page.get_by_text(question_text).locator("xpath=following::input[@type='file'][1]").set_input_files(file_path)
        remove_button.nth(uploaded_before).wait_for(timeout=60000)

    def fill_complaince_milestone(self,file_path_1):
        #-------Insurance-------------
        self.answer_question("Enhanced Service Delivery Agreement", "No")
        self.page.get_by_role("textbox", name="Public Liability (£) *").fill('10.25')
        self.page.get_by_role("textbox", name="Professional Indemnity (£) *").fill('11.25')
        self.page.get_by_role("textbox", name="Employer Liability (£) *").fill('12.25')
        self.answer_question("Any other insurance required?", "Yes")
        self.fill_text_after_question("Any other insurance required?", "Test Other Insurance")
        #-------Special Considerations-------------
        self.answer_question("Do you require any special clauses to be included", "Yes")
        self.upload_file_after_question("Do you require any special clauses to be included", file_path_1)
        self.answer_question("Do you confirm that this requirement is outside of IR35?", "Yes")
        self.answer_question("in respect of the creation of social value", "Yes")
        self.fill_text_after_question("in respect of the creation of social value", "Test Social Value")
        self.answer_question("to be agreed by all suppliers", "Yes")
        self.upload_file_after_question("to be agreed by all suppliers", file_path_1)
        self.answer_question("to be agreed by the successful supplier", "No")
        self.answer_question("Is a collateral warranty required?", "No")
        #-------Commercial Envelope-------------
        self.select_dropdown("Which commercial model do you want to follow?", "Milestones")
        self.select_dropdown("Which payment schedule would you like to follow?", "Milestones")
        self.select_dropdown("Will you accept expenses?", "No")
        self.answer_question("Best and Final Offer", "No")
        self.answer_question("funded by external agencies", "No")
        self.select_dropdown("Do you want Bloom to share the budget with suppliers?", "Yes - show budget")
        self.select_dropdown("Who do you want to evaluate the commercial envelope?", "Bloom")
        #-------Technical Envelope-------------
        self.select_dropdown("What Evaluation Methodology do you want to use?", "Price & Quality (MEAT)")
        self.answer_question("provide resumes in respect of their delivery team?", "No")
        self.answer_question("Is there currently an Incumbent Provider", "No")
        self.answer_question("to be used as a Case Study?", "No")

    #-------Summary milestone-------------
    def open_summary_milestone(self):
        self.milestone_link_locator.filter(has_text="Summary").click()
        self.submit_request_locator.wait_for()

    def open_summary_section(self,section_name):
        # Sections are collapsible and only one is open at a time; a closed section's table is not in the page.
        section_button = self.summary_section_button_locator.filter(has_text=section_name)
        if section_button.get_attribute("aria-expanded") != "true":
            section_button.click()
        self.page.get_by_role("table", name=f"{section_name} details").wait_for()

    def get_summary_section_details(self,section_name):
        # Returns {label: value} for one section. Value is a list for multi-value answers (regions, companies,
        # uploaded files ...), otherwise the displayed text ("-" when the question was not answered).
        self.open_summary_section(section_name)
        section_details = {}
        for row in self.page.get_by_role("table", name=f"{section_name} details").get_by_role("row").all():
            label = row.get_by_role("rowheader").inner_text().strip()
            answer = row.get_by_role("cell")
            list_items = answer.locator("li")
            # Some answers contain non-breaking spaces (e.g. "Project Value (ex VAT): £..."); normalise them to plain spaces.
            if list_items.count():
                section_details[label] = [item.replace(" ", " ").strip() for item in list_items.all_inner_texts()]
            else:
                section_details[label] = answer.inner_text().replace(" ", " ").strip()
        return section_details

    def get_summary_details(self):
        # Returns {section: {label: value}} for every section on the Summary page.
        section_names = [name.strip() for name in self.summary_section_button_locator.all_inner_texts()]
        return {section_name: self.get_summary_section_details(section_name) for section_name in section_names}

    def submit_request(self):
        # Submit can take a few seconds. Wait for POST /frameworks/submit-request; the app then shows the success
        # toast and redirects to the Dashboard. Returns the API status code.
        with self.page.expect_response(lambda response: "/frameworks/submit-request" in response.url, timeout=60000) as response_info:
            self.submit_request_locator.click()
        return response_info.value.status

    def get_summary_mismatches(self,expected_details):
        # expected_details: {section: {label: expected value}} - only the labels given are checked.
        # Labels are the Summary page labels (e.g. "Number Of Suppliers"), not the form question text.
        # Returns a list of readable mismatches; an empty list means everything matched.
        mismatches = []
        for section_name, expected_fields in expected_details.items():
            actual_fields = self.get_summary_section_details(section_name)
            for label, expected_value in expected_fields.items():
                actual_value = actual_fields.get(label, "<label not found>")
                if actual_value != expected_value:
                    mismatches.append(f"{section_name} > {label}: expected {expected_value!r}, got {actual_value!r}")
        return mismatches