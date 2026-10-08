# Bloom Elevate Marketplace — Test Automation Strategy

Status: **Draft for client approval** · Prepared: 08-10-2026 · Client deck: [Bloom_Elevate_Test_Automation_Strategy.pptx](Bloom_Elevate_Test_Automation_Strategy.pptx)

This is the working reference for automation on `test.bloom.engineering`. It records what the read-only exploration found (Playwright MCP, Project Owner account, 08-10-2026 — no forms filled, nothing submitted), the agreed approach, and the phased plan to follow once the client approves.

Related: [CODING_STANDARDS.md](../../CODING_STANDARDS.md) · [milestone_locators.md](../../framework/utils/milestone_locators.md) (verified locators per milestone)

---

## 1. Objectives
- Fast, repeatable regression of the buyer journey and approval workflow before every release.
- End-to-end coverage across all roles (buyer side + Bloom Ops), not just single screens.
- Early detection of form/workflow regressions in the highly conditional New Project Request (NPR) forms.
- Reduce manual effort; free testers for exploratory work.

## 2. Application landscape (Buyer / Project Owner view)

| Module | What it contains |
|---|---|
| **Dashboard** | KPI tiles (Projects by stage, Tasks overdue/due, Queries awaiting response/overdue), "New Project Request" entry point, my-tasks table, spend-expiration / end-date / notification widgets |
| **Projects** | Tabs *New Project Request* / *Delivery*; search (name/ID), filters: Project Status, Stage, Supplier; 11-column paginated table (ID, Name, Stage, Status, Budget, Supplier, Buyer, Start, End, Submitted, Actions) |
| **Project detail** | Header (budget, start date, current status, team members), stage stepper (New Project Request → In Sourcing → In Delivery → Satisfied), milestone stepper + task cards; tabs Summary, Specification (read-only answers), Queries, Documents (versioned, tagged e.g. T3), History (audit log, activity-type filter); Action menu: Raise Query, Add Document |
| **Tasks** | Tabs *New Project Request* / *Delivery* / *Queries*; KPI tiles; filters (task name, project, task status, project status, stage); Queries: search, status filter, assignee chips, **+ Raise Query** |
| **Invoices** | List with sort/paging (empty for the test buyer org) |
| **My Org.** | Overview (company details, addresses), Users (Add New User), Finance (payment/invoice method, VAT, finance contact, edit), Documents (Insurance, Call Off, Certificate) |
| **Global** | Org switcher, profile menu (Privacy Notice, Help Centre, Logout), notifications region, Cognito hosted login |

## 3. Core business journey — New Project Request lifecycle

1. **Create request**: title → select framework (e.g. NEPRO 3) → draft created with task *Submit Project Request*.
2. **Draft milestones** (sidebar, each shows ✓ when complete or a % when partly filled):
   Requirement Overview → Project Stakeholders → Project Details → Procurement Route (Direct / Mini Competition) → Compliance → **Summary** (read-only review + **Submit Request**).
3. **Bloom Ops review tasks** (observed on a submitted project): Validate buyer onboarding (PBP) · Review Supplier Accreditation (PBP) · Initial Project Review (Procurement Assurance) · Review and Clarify Project (PBP) · Review Feedback for New Project Request (Buyer) · Final Check for New Project Request (Procurement Assurance).
4. NPR milestones: New Project Draft → Submitted & In Review → Approved and Issued.
5. Stages after NPR: **In Sourcing → In Delivery → Satisfied**.

**Project statuses seen:** In Draft, Submitted & In Review, Buyer Approver, Buyer Approval Rejected, Approved, Preparing for Sourcing, In Progress, Awarded, Completed, On Hold, Set Up Incomplete, Not Started, Archived.
**Stages:** New Request, Sourcing, Closed (+ Delivery tab). **Task statuses:** Created, Open, On Hold, Cancelled, Rejected, Closed, In Progress, Completed. **Query statuses:** Open, Closed, In Progress, Pending, Overdue.

### Form complexity (drives test design)
- 100+ inputs across milestones; heavy conditional logic — e.g. ESDA = No → 3 liability amounts; Yes answers reveal uploads/detail fields; Mini Competition reveals supplier count, named suppliers and 6 criteria sections (27 regions, 30 industry standards …).
- Search-as-you-type pickers (members; 5,000+ companies), MUI date-time pickers, multi-file uploads (pdf/doc/xls/png ≤ 10 MB).
- Answers are saved only on **Next / Save and Exit**; leaving with unsaved answers triggers a browser "leave page?" prompt.

## 4. Roles & personas (all accounts to be provided)

| Organisation | Role | Main activities |
|---|---|---|
| Buyer | Project Owner | Create/complete/submit NPR, raise queries, review feedback |
| Buyer | Project Approver | Approve project (Approval Required = Yes path) |
| Buyer | Budget Approver | Payment request approval |
| Buyer | Additional Stakeholder | Collaborate on project |
| Buyer | Collateral Warranty signatory | Warranty sign-off |
| Bloom Ops | Procurement Business Partner (PBP) | Buyer onboarding validation, supplier accreditation, clarification |
| Bloom Ops | Procurement Assurance | Initial review, final check |
| Supplier | Supplier users | Sourcing / delivery stages (later phases) |

## 5. Scope & prioritisation

| Priority | Coverage |
|---|---|
| **P1** | Login/logout per role · Create NPR · all milestone forms incl. key conditional paths · Submit Request · Bloom Ops review tasks & approvals · Raise/respond to queries |
| **P2** | Projects & Tasks search/filters/sorting/paging · project detail tabs (Specification, Documents upload/versioning, History) · My Org. (users, finance, documents) · dashboard KPIs vs data |
| **P3** | Invoices · dashboard widgets · field validations & negative paths · Sourcing/Delivery stages (once data & roles exist) |

Out of scope for automation (stay manual): exploratory testing, visual/UX review, one-off data migrations.

## 6. Test approach
- **Smoke** (every build/PR): login, create draft, open project, raise query — < 5 min.
- **Regression** (nightly): full NPR journey, milestones, filters, documents, history.
- **Multi-role E2E**: one test drives buyer → Bloom Ops → buyer with a browser context per role.
- **Data-driven conditional paths**: parametrised answers (e.g. Direct vs Mini Competition, ESDA Yes/No).
- **API-assisted setup/cleanup**: create/seed/clean data through the app's APIs to keep UI tests short and independent. Endpoints observed: `/api/v1/elevate/project/all` (search), `/api/v1/frameworks/questions/answers` (save milestone), `/api/v1/file/upload`, `/api/v1/queries/saveQuery`, `/api/v1/members`, `/api/v1/companies`, `/api/v1/milestones/framework/...`.

## 7. Framework (built — Phase 0)
- **Stack:** Playwright (sync) + Python 3.12 + Pytest, Page Object Model, Allure reporting, pytest-xdist, pytest-rerunfailures.
- **Layout:** `framework/pages/` (page objects), `framework/data/` (test data), `framework/utils/` (date picker, locator catalogue), `framework/test_attachment/` (upload files), `tests/ui/` (tests), root `conftest.py` (browser + `project_owner_login` fixture), `CODING_STANDARDS.md`.
- **Playwright MCP** used to explore pages and verify every locator before it is coded.

### Reliability rules (proven on this app)
- Locators: role/label first; **question-scoped** locators for unlabeled questions (`field_locator`); options picked by `role=option`; never generated ids (`_r_xx_`), MUI classes or hex question ids.
- Synchronisation: wait on API responses (search, save, upload), **milestone stability wait** (sidebar re-renders after Next), upload confirmed by its "Remove <file>" button; no fixed sleeps.
- Every milestone loop step asserts the milestone shows complete before moving on.

## 8. Test data & environments
- Dedicated test accounts per role (buyer + Bloom Ops) in the test environment; credentials via environment variables / secret store (not in code).
- Unique run id in created titles (e.g. `Automation Project <timestamp>`) — titles are not unique in the app and the search returns the newest match.
- API-based cleanup or archiving of created drafts/queries/uploads after runs (data accumulates otherwise).
- Fixed library of upload files (pdf, docx, xlsx, png under 10 MB).
- Dates generated relative to today (`future_date_time`) so deadlines never fall in the past.

## 9. CI/CD & cross-browser
- Pipeline: PR → smoke (Chromium, headless) → merge → nightly full regression (parallel with pytest-xdist) → Allure report + Playwright traces/screenshots on failure → team notification.
- Browser matrix: Chromium (every run), Firefox & WebKit/Edge (nightly), viewport 1280×720 + one laptop size.
- Retries for known-flaky infra only (pytest-rerunfailures), with flaky-test tracking.

## 10. Risks & mitigations

| Risk / finding | Impact | Mitigation |
|---|---|---|
| No `data-testid`s; generated ids/classes | Brittle locators | Role/label + question-scoped locators; **ask dev team to add `data-testid`s** on key controls |
| Questions not linked to their inputs; duplicate labels across sections | Ambiguous matches | Scope by question/section text; verified locator catalogue |
| Sidebar progress re-renders after Next | False "incomplete" reads | Stability wait before reading status (implemented) |
| Answers not autosaved; "leave page?" prompt | Lost data / blocked navigation | Always Next/Save and Exit before navigating; dialog handler |
| Test data accumulates; duplicate titles | Wrong project picked, slow lists | Unique run ids; API cleanup; dedicated test org |
| Multi-role workflow depends on other users' tasks | Long, coupled E2E tests | Per-role fixtures; API to advance state where possible |
| Login form field names vary (Cognito) | Login flakiness | Placeholder-based locators + visible filter; API/session reuse |
| Shared test environment changes | Unstable expectations | Data created per run; assertions on own data only |

## 11. Phased roadmap (indicative, to confirm with client)

| Phase | Scope | Indicative effort |
|---|---|---|
| **0 — Foundation** ✅ | Framework, standards, login fixture, locator catalogue, draft NPR, search, project tasks, milestone loop to Summary, Raise Query | Done |
| **1 — Buyer NPR end-to-end** | Submit Request, all conditional paths (Direct / Mini Competition, ESDA Yes/No, uploads), Specification check after submit | Weeks 1–3 |
| **2 — Multi-role workflow** | Role fixtures, Bloom Ops review tasks (PBP, Procurement Assurance), approvals/rejections, status transitions | Weeks 4–6 |
| **3 — Supporting modules** | Queries lifecycle, Documents & versions, History audit, Projects/Tasks filters, My Org., dashboard KPIs | Weeks 7–8 |
| **4 — Scale & CI** | CI/CD pipeline, cross-browser matrix, API data layer (seed/cleanup), parallel runs, reporting | Weeks 9–10 |

## 12. Current progress (Phase 0)
- `tests/ui/test_login.py` — Project Owner login.
- `tests/ui/NewProjectRequest/test_new_project_request.py` — create draft NPR; search project + read table columns; project status & milestone tasks; open task; **loop that fills and verifies every incomplete milestone up to Summary**.
- `tests/ui/test_query_buyer_bloom_buyer.py` — Raise Query with field checks, save-API status, success toast and list verification.
- Page objects: `login`, `dashboard`, `project`, `new_project_request`, `query`; utils: `date_picker`; locator catalogue for Project Stakeholders, Project Details, Procurement Route (Mini Competition), Compliance.

## 13. Asks from the client
1. Test accounts for every role (buyer roles + Bloom Ops PBP / Procurement Assurance; suppliers later).
2. Agreement on test-data policy: dedicated test org / permission to archive or delete automation data.
3. API access/documentation for seeding and cleanup.
4. `data-testid` attributes on key form controls (low effort, big stability gain).
5. CI platform and notification channel to use.

## 14. Open questions
- What happens after **Submit Request** for each approval path (Approval Required Yes/No) — confirm expected task sequence per role.
- Direct procurement route fields (only Mini Competition explored so far).
- Sourcing / Delivery / Satisfied stages and supplier-side journeys — need data and supplier accounts.
- Invoice flows (no invoices for the test buyer org).

## 15. How to continue after approval
Follow `CODING_STANDARDS.md`; explore each new page with Playwright MCP before coding and add verified locators to `framework/utils/milestone_locators.md`; work phase by phase from section 11.
