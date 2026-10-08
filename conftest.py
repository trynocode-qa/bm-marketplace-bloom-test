import os
import re
import allure
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load local settings/credentials from the git-ignored .env before test data is imported.
# In CI the same variables come from GitHub secrets; .env does not exist there and existing variables are not overridden.
load_dotenv(Path(__file__).resolve().parent / ".env")

from  playwright.sync_api import sync_playwright, expect
from framework.pages.login import LoginPage
from framework.data.test_data import project_owner_credential

FAILURE_ARTIFACTS_DIR = Path(__file__).resolve().parent / "test-results"
BASE_URL = os.getenv("BASE_URL", "https://test.bloom.engineering")
# Visible browser locally by default; CI sets HEADLESS=true (runners have no display).
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Keep each phase's result on the test item (fixtures read it in teardown) and, when the test body fails,
    # attach a full-page screenshot and the page URL to the Allure report while the browser is still open.
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)
    if report.when == "call" and report.failed:
        page = item.funcargs.get("project_owner_login") or item.funcargs.get("open_browser_test_environment")
        if page is not None and not page.is_closed():
            try:
                allure.attach(page.screenshot(full_page=True), name="Screenshot on failure", attachment_type=allure.attachment_type.PNG)
                allure.attach(page.url, name="Page URL on failure", attachment_type=allure.attachment_type.TEXT)
            except Exception as error:  # never let reporting hide the real failure
                print(f"Could not capture failure screenshot: {error}")


@pytest.fixture
def open_browser_test_environment(request):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        # Record a Playwright trace (screenshots + DOM snapshots); it is kept and attached to Allure only on failure.
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.goto(BASE_URL)
        yield page
        failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
        if failed:
            FAILURE_ARTIFACTS_DIR.mkdir(exist_ok=True)
            trace_path = FAILURE_ARTIFACTS_DIR / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', request.node.name)}-trace.zip"
            context.tracing.stop(path=str(trace_path))
            allure.attach.file(str(trace_path), name="Playwright trace (open with: playwright show-trace)", extension="zip")
        else:
            context.tracing.stop()
        page.close()
        context.close()
        browser.close()


@pytest.fixture
def project_owner_login(open_browser_test_environment):
    """Logs in as Project Owner and yields the page on the dashboard."""
    page = open_browser_test_environment
    if not project_owner_credential['email'] or not project_owner_credential['password']:
        pytest.fail("Project Owner credentials are empty - check framework/data/test_data.py or BLOOM_PO_EMAIL / BLOOM_PO_PASSWORD overrides")
    login = LoginPage(page)
    login.buyer_login(project_owner_credential['email'], project_owner_credential['password'])
    # Dashboard is loaded once the profile menu appears after the Cognito redirect.
    expect(page.get_by_role("button", name="Open profile menu")).to_be_visible(timeout=30000)
    yield page
