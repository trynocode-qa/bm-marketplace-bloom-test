from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DATE_TIME_FORMAT = "%d/%m/%Y %I:%M %p"
# The app displays saved dates in UK time: GMT in winter, BST (GMT+1) in summer.
APP_DISPLAY_TIMEZONE = "Europe/London"

def to_app_display_time(date_time,entered_timezone=None):
    """
    Converts a date-time typed into a picker to the value the app shows afterwards (e.g. on the Summary page).
    date_time        : 'DD/MM/YYYY hh:mm AM' as entered, e.g. '01/12/2026 04:30 AM'
    entered_timezone : IANA name of the browser's timezone (e.g. 'Asia/Kolkata'). Default = this machine's timezone,
                       which is what the browser uses unless the test sets timezone_id.
    Example (IST machine): '01/12/2026 04:30 AM' -> '30/11/2026 11:00 PM' (GMT), '01/07/2026 04:30 AM' -> '01/07/2026 12:00 AM' (BST)
    """
    entered = datetime.strptime(date_time, DATE_TIME_FORMAT)
    entered = entered.replace(tzinfo=ZoneInfo(entered_timezone)) if entered_timezone else entered.astimezone()
    return entered.astimezone(ZoneInfo(APP_DISPLAY_TIMEZONE)).strftime(DATE_TIME_FORMAT)

def future_date_time(days):
    """Returns a date-time string 'DD/MM/YYYY hh:mm AM' that is `days` from now (deadlines must be in the future)."""
    return (datetime.now() + timedelta(days=days)).strftime(DATE_TIME_FORMAT)

def select_date_time(page,input_id,date_time):
    """
    Fills an MUI date-time picker (Day / Month / Year / Hours / Minutes / Meridiem sections).
    input_id  : id of the picker's hidden input, e.g. 'query-deadline'
    date_time : 'DD/MM/YYYY hh:mm AM' string, e.g. '15/10/2026 02:30 PM'
    Typing into the Day section auto-advances through all sections.
    """
    value = datetime.strptime(date_time, DATE_TIME_FORMAT)
    date_picker = page.get_by_role("group").filter(has=page.locator(f"#{input_id}"))
    date_picker.get_by_role("spinbutton", name="Day").press_sequentially(value.strftime("%d%m%Y%I%M") + value.strftime("%p")[0])
