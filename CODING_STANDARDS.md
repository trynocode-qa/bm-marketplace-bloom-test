# Coding Standards — Bloom Marketplace Automation

Stack: **Playwright (sync API) + Python + Pytest**, Page Object Model.
Reference samples: `framework/pages/login.py`, `tests/ui/test_login.py`, `conftest.py`.
All new code must follow these rules strictly. When something is not covered here, copy the pattern from the reference samples.

## 1. Project layout

| What | Where | File naming |
|---|---|---|
| Page objects | `framework/pages/` | `<page_name>.py` (e.g. `login.py`, `dashboard.py`) — no `_page` suffix |
| Test data | `framework/data/test_data.py` | one shared module |
| Reusable UI helpers | `framework/utils/` | `<widget>.py` (e.g. `date_picker.py`) — plain functions taking `page` first; page objects call them |
| UI tests | `tests/ui/` | `test_<feature>.py` |
| Fixtures | root `conftest.py` | — |

## 2. Page objects

```python
from playwright.sync_api import Page

class LoginPage:
    def __init__(self,page):
        self.page = page
        self.email_locator = page.get_by_role("textbox", name="name@host.com")
        self.password_locator = page.get_by_role("textbox", name="Password")
        self.sign_in_locator = page.get_by_role("button", name="submit")

    def buyer_login(self,email,password):
        self.email_locator.filter(visible=True).fill(email)
        self.password_locator.filter(visible=True).fill(password)
        self.sign_in_locator.filter(visible=True).click()
```

Rules:
- Class name: `<Name>Page` in PascalCase. Plain class — **no base class / inheritance**.
- Constructor takes `page` and stores it as `self.page`.
- **All locators are defined in `__init__`** as instance attributes — never build locators inside action methods.
- Locator attribute names: snake_case ending in **`_locator`** (e.g. `email_locator`, `sign_in_locator`).
- Locator strategy: **`page.get_by_role(role, name=...)`** first. Use other `get_by_*` only when no role/name exists. No CSS/XPath unless there is no alternative.
- Action methods: snake_case, named after the **business action** from the user's point of view (e.g. `buyer_login`, not `fill_form`).
- Action methods take plain values (strings) as parameters — never test-data dicts.
- Interact via `.filter(visible=True)` before `fill()` / `click()` where the page can render duplicate hidden elements (e.g. the Cognito login page).
- **No assertions** inside page objects; no return values unless a test needs one.

## 3. Test data

```python
project_owner_credential = {
    'email':'...',
    'password':'...'
}
```

- Module-level dicts in `framework/data/test_data.py`.
- Naming: `<role>_credential` for logins (e.g. `project_owner_credential`); snake_case for everything else.
- Keys use single quotes.

## 4. Fixtures (`conftest.py`)

- Defined in the **root `conftest.py`** with `@pytest.fixture`.
- Always use **`yield`** (not `return`) to hand the page to the test; put cleanup after the `yield`.
- Browser is opened with `sync_playwright()` in `open_browser_test_environment`.
- Fixtures build on each other (e.g. `project_owner_login` uses `open_browser_test_environment`) and reuse page objects + test data instead of duplicating steps.
- Fixture names describe the state they provide: `open_browser_test_environment`, `project_owner_login`.

## 5. Tests

```python
from framework.pages.login import LoginPage
from framework.data.test_data import project_owner_credential

def test_successful_login(open_browser_test_environment):
    page = open_browser_test_environment
    buyer_login = LoginPage(page)
    buyer_login.buyer_login(project_owner_credential['email'],project_owner_credential['password'])
```

Rules:
- **Function-based tests** — no test classes.
- Name: `test_<expected_behaviour>` (e.g. `test_successful_login`).
- Import page objects and test data with full module paths: `from framework.pages.<module> import <Class>`, `from framework.data.test_data import <name>`.
- First line of the test assigns the fixture to a local `page` variable: `page = <fixture_name>`.
- Instantiate page objects inside the test, in a snake_case variable named after its purpose.
- Read test data via dict keys: `project_owner_credential['email']`.
- Assertions use Playwright `expect` (`from playwright.sync_api import expect`).
- Do not leave `page.pause()` in committed tests (debug only).
