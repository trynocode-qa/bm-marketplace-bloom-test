from datetime import datetime
from playwright.sync_api import expect
from framework.pages.query import Query
from framework.data.query_data import raise_query_data

def test_buyer_create_query(project_owner_login):
    page = project_owner_login
    buyer_query = Query(page)
    # Unique title per run so the new query can be found in the list without clashing with older runs.
    query_title = f"{raise_query_data['query_title']} {datetime.now().strftime('%d%m%Y%H%M%S')}"

    get_default_page = buyer_query.navigate_to_the_task_menu()
    assert get_default_page == 'New Project Request', f"Default Page Tab Mismatch {get_default_page}"

    buyer_query.move_to_query_tab()
    expect(buyer_query.query_tab_locator, "Queries tab is not selected").to_have_attribute("aria-selected", "true")

    buyer_query.open_query_pop_up()
    expect(buyer_query.raise_query_heading_locator, "Raise Query pop-up did not open").to_be_visible()

    buyer_query.raise_query(query_title,
                            raise_query_data['project_name'],
                            raise_query_data['query_description'],
                            raise_query_data['deadline'],
                            raise_query_data['related_task'],
                            raise_query_data['query_responder'])
    expect(buyer_query.query_title_locator).to_have_value(query_title)
    expect(buyer_query.search_project_locator).to_have_value(raise_query_data['project_name'])
    expect(buyer_query.query_description_locator).to_have_value(raise_query_data['query_description'])
    expect(buyer_query.deadline_locator).to_have_value(raise_query_data['deadline'])
    expect(buyer_query.related_task_locator).to_have_text(raise_query_data['related_task'])
    expect(buyer_query.query_responder_locator).to_have_text(raise_query_data['query_responder'])

    status = buyer_query.submit_query()
    assert status == 200, f"Save Query API failed with status {status}"
    expect(buyer_query.toast_locator, "Success message not displayed").to_contain_text(raise_query_data['success_message'])
    expect(buyer_query.raise_query_dialog_locator, "Raise Query pop-up did not close after submit").to_be_hidden()

    query_row = buyer_query.get_query_row(query_title)
    expect(query_row, f"Query '{query_title}' not found in Queries list").to_be_visible()
    expect(query_row).to_contain_text(raise_query_data['project_name'])
    expect(query_row).to_contain_text(raise_query_data['related_task'])
    expect(query_row).to_contain_text(raise_query_data['query_status'])
