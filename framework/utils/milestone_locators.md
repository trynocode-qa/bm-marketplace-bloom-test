# New Project Request — Milestone Locators

Locators captured with Playwright MCP on `test.bloom.engineering` (project 13917, framework NEPRO 3, 07-10-2026).
Every locator below was verified to match exactly **one** element on the live page.

Milestone URL pattern: `/project-requests/<frameworkId>/milestone/<milestoneId>?submissionId=...&taskId=...&projectId=...`

---

## Common to every milestone

| Element | Locator |
|---|---|
| Next | `page.get_by_role("button", name="Next")` |
| Previous | `page.get_by_role("button", name="Previous")` |
| Save and Exit | `page.get_by_role("button", name="Save and Exit")` |
| Sidebar milestone links | `page.locator('a[href*="/milestone/"]')` |
| Current milestone | `page.locator('a[href*="/milestone/"][aria-current="step"]')` |
| Milestone complete (check icon) | `page.locator('svg path[d^="M9 16.2"]')` inside the milestone link |
| Dropdown / autocomplete option | `page.get_by_role("option", name=<value>, exact=True)` |

### Behaviour
- Answers are **not auto-saved**. Only **Next** or **Save and Exit** saves (`POST /api/v1/frameworks/questions/answers`).
- Leaving a page with unsaved changes triggers a browser `beforeunload` ("leave page?") dialog. Playwright dismisses it by default, so the page stays put; accept it with `page.on("dialog", lambda dialog: dialog.accept())` or save first.
- After Next/page load the sidebar reloads progress twice; meanwhile the current milestone shows a spinner instead of its check icon. Use `NewProjectRequestPage.wait_for_milestone_status()` before reading completion.
- Milestone sidebar states: **check SVG** = complete, **progress bar + "NN%"** = partly filled, **nothing** = not started.

### Choosing options — avoid `get_by_text`
Once a dropdown has a value, the selected text is shown in the dropdown itself as well as in the option list, so `get_by_text(value)` causes a strict-mode violation. Always select with `get_by_role("option", name=value, exact=True)`.

### Generic field helper (for questions without a linked label)
Many questions are plain text next to the control, with only generated ids (`_r_xx_`) or hex ids. Find the question text, step up to the nearest container that holds the control, then find the control:

```python
def field_locator(self,question_text,control_xpath):
    return self.page.get_by_text(question_text).locator(f"xpath=ancestor::div[.//{control_xpath}][1]")
```

| Control | `control_xpath` value |
|---|---|
| Date-time picker | `"*[@role='group']"` |
| Radio group | `"*[@role='radiogroup']"` |
| Checkbox | `"input[@type='checkbox']"` (native input — has no `role` attribute) |
| File upload | `"input[@type='file']"` |

### Do not use
- `_r_f_`, `_r_j_`, `_r_g_` … — React-generated ids, change between renders.
- Long hex ids/names such as `6986e6ce2fff3da50569a5c8` — form template question ids; only use the readable suffix of a `name` (e.g. `paymentApproverName`).
- `mui-xxxxxx` classes — generated.

---

## Milestone: Project Stakeholders

Page loaded check: `page.get_by_role("heading", name="Requirement Owner Details")`

### Fields

| Field | Required | Shown when | Type | Locator |
|---|---|---|---|---|
| Additional Stakeholders | No | always | search-as-you-type autocomplete | `page.get_by_role("combobox", name="Additional Stakeholders")` |
| Is Project Approval Required? — Yes / No | Yes | always | radio | `page.get_by_role("radiogroup").first.get_by_role("radio", name="Yes")` (or `"No"`) |
| Do you have Project Pre Approval? — Yes | Yes | Approval Required = Yes | radio | `page.locator('input[name$="projectPreApproval"][value="yes"]')` |
| Do you have Project Pre Approval? — No | Yes | Approval Required = Yes | radio | `page.locator('input[name$="projectPreApproval"][value="no"]')` |
| Upload supporting documents | — | Pre Approval = Yes | file | `page.get_by_label("Upload supporting documents")` → `.set_input_files(path)` |
| Approver Name | Yes | Pre Approval = No | dropdown | `page.locator('input[name$=".approverName"]').locator('xpath=preceding-sibling::*[@role="combobox"]')` |
| Approver Email | Yes | Pre Approval = No | text, **read-only** (auto-filled) | `page.locator('input[name$=".approverEmail"]')` |
| Who will be responsible to support Payment Request? | Yes | always | dropdown | `page.locator('input[name$="paymentApproverName"]').locator('xpath=preceding-sibling::*[@role="combobox"]')` |
| Payment Request Approver Email | Yes | always | text, **read-only** (auto-filled) | `page.get_by_label("Payment Request Approver Email*")` |

### Conditional flow

```
Is Project Approval Required?*
├── No / not answered → nothing extra
└── Yes → "Approver Details" section:
        Do you have Project Pre Approval?*
        ├── Yes → Upload supporting documents (file)
        └── No  → Approver Name (dropdown) + Approver Email* (read-only)
```

### Notes
- **Additional Stakeholders**: clicking shows no list; type to search (`GET /api/v1/members?searchTerm=<text>`), then pick the option:
  ```python
  stakeholders_locator.press_sequentially(name)
  page.get_by_role("option", name=name, exact=True).click()
  ```
  A selected stakeholder is shown as a list item below the field with a `remove <name>` button.
- **Is Project Approval Required?** — once Yes is selected a second radio group (Pre Approval) appears, so an unscoped `get_by_role("radiogroup").get_by_role("radio", name="Yes")` matches 2 elements. Use `.first` (this group is always first).
- **`.approverName`** — keep the leading dot so it does not also match `paymentApproverName`.
- **Read-only emails** — do not fill; validate with `expect(locator).to_have_value(...)`.
- Payment Request dropdown has no accessible name (shows the question as placeholder text, then the selected name), hence the hidden-input + sibling locator. The question text appears twice on the page, so do not use `get_by_text` for it.

### Options seen (test environment)
Approver Name and Payment Request dropdowns:
Akash saxena · Approver AKash · Sawan - Additional Stakeholder 01 Test · Sawan - Budget Approver Test · Sawan - C.Warranty Test · Sawan PBP PBP · Sawan - Project Approver Test · Sawan - Project Owner Test

---

## Milestone: Project Details

Page loaded check: `page.get_by_role("heading", name="Project Timeline")`

### Date-time pickers (all required)

| Field | Locator (picker container) |
|---|---|
| Publication Date | `field_locator("Publication Date", "*[@role='group']")` |
| Clarification Deadline | `field_locator("Clarification Deadline", "*[@role='group']")` |
| Submission Deadline | `field_locator("Submission Deadline", "*[@role='group']")` |
| Project Start Date | `field_locator("Project Start Date", "*[@role='group']")` |
| Project End Date | `field_locator("Project End Date", "*[@role='group']")` |

- Same MUI Day / Month / Year / Hours / Minutes / AM-PM picker as the query Deadline. Typing into **Day** auto-advances through all sections:
  ```python
  picker.get_by_role("spinbutton", name="Day").press_sequentially("201020261000A")   # 20/10/2026 10:00 AM
  ```
- Read the value: `picker.locator('input[aria-hidden="true"]')` → `to_have_value("20/10/2026 10:00 AM")`.
- `select_date_time()` in `framework/utils/date_picker.py` looks the picker up by input **id**, and these pickers only have generated ids. Use a locator-based variant:
  ```python
  def select_date_time_in(date_picker,date_time):
      value = datetime.strptime(date_time, DATE_TIME_FORMAT)
      date_picker.get_by_role("spinbutton", name="Day").press_sequentially(value.strftime("%d%m%Y%I%M") + value.strftime("%p")[0])
  ```
- Keep dates in a logical order (Publication → Clarification → Submission → Start → End); only Publication Date was tested on its own, ordering validation was not checked.

### Checkbox and radios

| Field | Required | Locator |
|---|---|---|
| Is this a retrospective project? | No | `field_locator("Is this a retrospective project?", "input[@type='checkbox']").get_by_role("checkbox")` |
| Is this requirement related to COVID-19? — Yes / No | Yes | `field_locator("Is this requirement related to COVID-19?", "*[@role='radiogroup']").get_by_role("radio", name="No")` |
| Do you require the ITT pack to be approved by the requirement owner prior to publication? — Yes / No | Yes | `field_locator("Do you require the ITT pack to be approved", "*[@role='radiogroup']").get_by_role("radio", name="No")` |

Two Yes/No groups on this page → always scope by question (radio `name`s are hex ids only).

### Text fields (labels are linked)

| Field | Required | Locator |
|---|---|---|
| Cost for this Project (Excluding VAT) | Yes | `page.get_by_role("textbox", name="Cost for this Project (Excluding VAT) *")` (placeholder "Amount", "£" prefix) |
| Budget Code | No | `page.get_by_role("textbox", name="Budget Code")` |
| Sub Code | No | `page.get_by_role("textbox", name="Sub Code")` |

### File uploads

| Field | Required | Locator | Accepts |
|---|---|---|---|
| Attachments | Yes | `field_locator("Attachments", "input[@type='file']").locator("input[type=file]")` | single file — pdf, doc/docx, xls/xlsx, png, max 10 MB |
| Add Supporting Documents | No | `field_locator("Add Supporting Documents", "input[@type='file']").locator("input[type=file]")` | multiple files |

- Upload with `.set_input_files("path/to/file.pdf")` (works on the hidden input).
- Use a **non-exact** `get_by_text("Attachments")` — the `*` is a separate element, so exact match fails.

### Other

| Element | Locator |
|---|---|
| Statement of Requirements template | `page.get_by_role("link", name="T3 - Service Specification Template")` |

### Notes
- No conditional fields: ticking *retrospective* or answering Yes to COVID-19 / ITT did not reveal any extra fields.
- Each answer updates the sidebar percentage immediately (e.g. 11%, 22%), but nothing is saved until Next / Save and Exit.

---

## Milestone: Procurement Route → Mini Competition

Page loaded check: `page.get_by_role("heading", name="Submission Details")`

### Procurement process (always shown)

| Field | Required | Locator |
|---|---|---|
| Preferred Procurement Process — Mini Competition | Yes | `page.get_by_role("radio", name="Mini Competition", exact=True)` |
| Preferred Procurement Process — Direct | Yes | `page.get_by_role("radio", name="Direct", exact=True)` |

Selecting **Mini Competition** reveals everything below.

### Submission details

| Field | Required | Shown when | Type | Locator |
|---|---|---|---|---|
| How many suppliers do you want to include? | Yes | Mini Competition | text (`inputmode=decimal`, placeholder "Number of Suppliers") | `page.get_by_role("textbox", name="How many suppliers do you want to include? *")` |
| Are there any specific Suppliers you would like Bloom to include? — Yes / No | Yes | Mini Competition | radio | `field_locator("Are there any specific Suppliers you would like Bloom to include?", "*[@role='radiogroup']").get_by_role("radio", name="Yes")` |
| Company Name | Yes | Specific Suppliers = Yes | search-as-you-type autocomplete | `page.get_by_role("combobox", name="Company Name")` |
| Named Contact | No | Specific Suppliers = Yes | text | `page.get_by_role("textbox", name="Named Contact")` |

- **Company Name**: shows no list on click; typing searches `GET /api/v1/companies?q=<text>`. Typing just "a" returned **5133** companies, so type the full name, then pick it:
  ```python
  company_locator.press_sequentially(company_name)
  page.get_by_role("option", name=company_name, exact=True).click()
  ```
  Some company names contain special characters; prefer a plain test company (e.g. "Acme LTD").

### Supplier Shortlisting Criteria (all optional, Mini Competition only)

Checkbox sections have no group role, so scope each one by its heading text:

```python
section = field_locator("<section heading>", "input[@type='checkbox']")
section.get_by_role("checkbox", name="<option>", exact=True).click()
```

| Section heading | Checkboxes | Options |
|---|---|---|
| Region | 27 | Belfast, Central Scotland, East Midlands, East of England, East of Northern Ireland, Glasgow, Highlands & Islands, London, Lothians, Mid Scotland & Fife, Mid Wales, North East England, North East Scotland, North East Wales, North of Northern Ireland, North West England, North West Wales, Outer Belfast, South East England, South East Wales, South Scotland, South West England, South West Wales, West Midlands, West Scotland, West & South of Northern Ireland, Yorkshire & the Humber |
| Size of Supplier | 4 | Micro, Small, Medium, Large |
| Security (inc data security) | 12 | Cloud Security Alliances Cloud Controls Matrix (CCM), Cyber Essentials, Cyber Essentials Plus, ISO22301, ISO27001, ISO27017, ISO27018, ISO27031, ISO27032, ISO27035, Other, PAS555 |
| Security Clearance | 6 | Baseline Personnel Security Standard (BPSS), Security Check (SC), Developed Vetting (DV), Counter Terrorist Check (CTC), Enhanced Security Check (eSC), Enhanced Developed Vetting (eDV) |
| Industry Standards | 30 | BES6001, BS10008, BS10012, BS10500, BS11000, BS13500, BS8543, ISO13053, ISO14001, ISO14064-1, ISO20000, ISO20121, ISO22301, ISO26000, ISO27001, ISO28000, ISO31000, ISO37001, ISO44001, ISO45001, ISO5001, ISO55000, ISO9001, Other, PAS2010, PAS2060, PAS99, PCI DSS, SA8000, TL9000 |
| DBS | 4 | Basic, Standard, Enhanced without barred list, Enhanced with barred list |

| Field | Required | Shown when | Locator |
|---|---|---|---|
| Technical Accreditation | No | Mini Competition | `page.get_by_role("textbox", name="Please list accreditations required")` (textarea, 0/4096 counter) |
| Other Supplier Security | Yes | Security → **Other** ticked | `page.get_by_role("textbox", name="Any Additional Security Check")` (textarea) |

### Notes
- **Duplicate checkbox names**: `ISO22301`, `ISO27001` and `Other` exist in both *Security* and *Industry Standards* — an unscoped `get_by_role("checkbox", name="ISO27001")` matches 2 elements. Always scope by section.
- **Tick with `click()` + assert**, not `check()`: once `check()` failed with *"Clicking the checkbox did not change its state"* (the controlled checkbox updates after a re-render). Use `click()` then `expect(checkbox).to_be_checked()`.
- Industry Standards → **Other** does not reveal any extra field (only Security → Other does).
- Like the other milestones, nothing is saved until Next / Save and Exit; each answer only updates the sidebar percentage.

---

## Milestone: Compliance

Page loaded check: `page.get_by_role("heading", name="Insurance")`

Read-only summary at the top (calculated from Project Details): `Project Value (ex VAT): £…`, `Start Date: …`, `End Date: …` — e.g. `page.get_by_text("Project Value (ex VAT):")`.

None of the questions have a linked label, so every control is scoped by its question text with `field_locator(question, control_xpath)` (see *Generic field helper*). The question strings below are substrings that match exactly **one** element (`get_by_text` non-exact).

### Yes / No questions (13 radio groups)

```python
field_locator("<question>", "*[@role='radiogroup']").get_by_role("radio", name="Yes", exact=True)   # or "No"
```

| Section | Question substring to use | Required | Reveals |
|---|---|---|---|
| Insurance | `Enhanced Service Delivery Agreement` (ESDA insurance levels apply?) | Yes | **No** → Public Liability / Professional Indemnity / Employer Liability amounts |
| Insurance | `Any other insurance required?` | Yes | **Yes** → details text field |
| Special Considerations | `Do you require any special clauses to be included` | Yes | **Yes** → file upload |
| Special Considerations | `Do you confirm that this requirement is outside of IR35?` | Yes | nothing |
| Special Considerations | `in respect of the creation of social value` | Yes | **Yes** → details text field |
| Special Considerations | `to be agreed by all suppliers` (NDA before releasing brief / ITT) | No | **Yes** → file upload |
| Special Considerations | `to be agreed by the successful supplier` (NDA before award) | No | **Yes** → file upload |
| Special Considerations | `Is a collateral warranty required?` | No | **Yes** → signatory search |
| Commercial Envelope | `Best and Final Offer` | No | nothing |
| Commercial Envelope | `funded by external agencies` | Yes | **Yes** → details text field |
| Technical Envelope | `provide resumes in respect of their delivery team?` | Yes | nothing |
| Technical Envelope | `Is there currently an Incumbent Provider` | No | nothing |
| Technical Envelope | `to be used as a Case Study?` | Yes | nothing |

The two NDA questions share the same opening words — always use the distinguishing ending (`by all suppliers` / `by the successful supplier`).

### Dropdowns (6, all required)

```python
field_locator("<question>", "*[@role='combobox']").get_by_role("combobox").click()
page.get_by_role("option", name="<option>", exact=True).click()
```

| Section | Question | Options | Reveals |
|---|---|---|---|
| Commercial Envelope | `Which commercial model do you want to follow?` | Milestones · Day Rates · Consumption Based (Inclusive of Time and Materials) | nothing |
| Commercial Envelope | `Which payment schedule would you like to follow?` | Milestones · Quarterly · Monthly · Weekly · Other | **Other** → "Please state if other" |
| Commercial Envelope | `Will you accept expenses?` | Yes - capped · No · Yes - uncapped | **Yes - capped** → maximum expenses amount |
| Commercial Envelope | `Do you want Bloom to share the budget with suppliers?` | Yes - show budget · Yes - show a target cost · No - hide the budget completely | nothing |
| Commercial Envelope | `Who do you want to evaluate the commercial envelope?` | Bloom · Customer Evaluation · A Combination of both | **Customer Evaluation / A Combination of both** → point-of-contact search |
| Technical Envelope | `What Evaluation Methodology do you want to use?` | Price & Quality (MEAT) · Price Only | nothing |

The dropdowns have no accessible name (they show "Please Select", then the chosen value), so always scope by question.

### Conditional fields

| Field | Shown when | Required | Locator |
|---|---|---|---|
| Public Liability (£) | ESDA = **No** | Yes | `page.get_by_role("textbox", name="Public Liability (£) *")` (placeholder "0") |
| Professional Indemnity (£) | ESDA = **No** | Yes | `page.get_by_role("textbox", name="Professional Indemnity (£) *")` |
| Employer Liability (£) | ESDA = **No** | Yes | `page.get_by_role("textbox", name="Employer Liability (£) *")` |
| Other insurance details | Other insurance = **Yes** | — | `page.get_by_text("Any other insurance required?").locator("xpath=following::input[@type='text'][1]")` (placeholder "Enter details") |
| Special clauses file | Special clauses = **Yes** | Yes ("Choose File *") | `page.get_by_text("Do you require any special clauses to be included").locator("xpath=following::input[@type='file'][1]")` |
| Social value details | Social value = **Yes** | — | `page.get_by_text("in respect of the creation of social value").locator("xpath=following::input[@type='text'][1]")` (placeholder "Enter Details") |
| NDA (all suppliers) file | NDA all suppliers = **Yes** | Yes | `page.get_by_text("to be agreed by all suppliers").locator("xpath=following::input[@type='file'][1]")` |
| NDA (successful supplier) file | NDA successful supplier = **Yes** | Yes | `page.get_by_text("to be agreed by the successful supplier").locator("xpath=following::input[@type='file'][1]")` |
| Collateral Warranty Signatory | Collateral warranty = **Yes** | — | `page.get_by_placeholder("Add Collateral Warranty Signatory")` (search: `GET /members?searchTerm=…`) |
| External funding details | External funding = **Yes** | — | `page.get_by_text("funded by external agencies").locator("xpath=following::input[@type='text'][1]")` or `page.locator('input[name$="external_funding_details"]')` |
| Please state if other | Payment schedule = **Other** | — | `page.get_by_placeholder("Please state if other")` |
| Maximum expenses amount | Expenses = **Yes - capped** | Yes | `page.get_by_role("textbox", name=re.compile("maximum value of expenses"))` or `page.locator('input[name$="expense_cap"]')` (placeholder "Amount") |
| Commercial Evaluation point of contact | Evaluator = **Customer Evaluation / A Combination of both** | Yes | `page.get_by_placeholder("Search and add commercial evaluator contacts")` (search: `GET /members?searchTerm=…`) |

### Notes
- **`following::…[1]` is only valid once the conditional field is shown.** These fields are rendered outside the question's own container, so the "nearest container" helper matches 3–10 inputs; instead take the first input of that type *after* the question. If the answer is still No, the same XPath would grab a later question's field — select Yes first, then locate.
- The two "Enter Details" fields (social value, external funding) and three file uploads share placeholders/labels — never locate them by placeholder alone.
- Search fields (signatory, commercial contact) show nothing on click: type, then pick `get_by_role("option", name=…, exact=True)`. Options seen for "Sawan": Sawan - Additional Stakeholder 01 Test, Sawan - Budget Approver Test, Sawan - C.Warranty Test, Sawan PBP PBP, Sawan - Project Approver Test, Sawan - Project Owner Test.
- File uploads: wait for the `Remove <file name>` button after `set_input_files` (same as Project Details).
- Pressing Escape on an open Evaluation Methodology dropdown without choosing shows "What Evaluation Methodology do you want to use? is required" — harmless, disappears once a value is chosen.
