import sys
import time
import re
from pathlib import Path

from playwright.sync_api import sync_playwright


# ============================================================
# CONFIGURATION
# ============================================================

JIRA_URL = "https://selector.atlassian.net"

# Persistent browser profile.
# This keeps Jira + S2AP login sessions.
PROFILE_DIR = Path(
    "playwright/automation-profile"
)

CHECK_INTERVAL = 30

ISSUE_PATTERN = re.compile(
    r"\b[A-Z][A-Z0-9]+-\d+\b"
)


# ============================================================
# JIRA
# ============================================================

def open_jira(page, ticket):

    url = f"{JIRA_URL}/browse/{ticket}"

    print(f"\nOpening Jira ticket: {ticket}")

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(3000)


def check_jira_login(page):

    current_url = page.url.lower()

    if "id.atlassian.com/login" in current_url:

        print("\nERROR: Jira login is required.")

        print(
            f"Current page: {page.url}"
        )

        return False

    return True


def get_subtasks(page, parent_ticket):

    print("\n========================================")
    print("FINDING JIRA SUBTASKS")
    print("========================================")

    open_jira(
        page,
        parent_ticket
    )

    if not check_jira_login(page):
        return []

    tickets = []

    issue_links = page.locator(
        'a[href*="/browse/"]'
    )

    count = issue_links.count()

    for i in range(count):

        try:

            href = issue_links.nth(i).get_attribute(
                "href"
            )

            if not href:
                continue

            match = ISSUE_PATTERN.search(
                href
            )

            if not match:
                continue

            ticket = match.group(0)

            if ticket == parent_ticket:
                continue

            if ticket not in tickets:
                tickets.append(ticket)

        except Exception:
            continue

    print("\nJira tickets found:")

    for ticket in tickets:
        print(
            f"  {ticket}"
        )

    if not tickets:

        print(
            "ERROR: No Jira tickets were found."
        )

    return tickets


def get_ticket_status(page, ticket):

    print(
        f"\nChecking status of {ticket}..."
    )

    open_jira(
        page,
        ticket
    )

    if not check_jira_login(page):
        return None

    selectors = [
        '[data-testid*="issue.views.issue-base.foundation.status"]',
        '[data-testid*="status"]',
        '[aria-label*="status" i]',
        'button[data-testid*="status"]',
    ]

    for selector in selectors:

        try:

            locator = page.locator(
                selector
            )

            for i in range(
                min(locator.count(), 5)
            ):

                text = locator.nth(i).inner_text(
                    timeout=2000
                ).strip()

                if text:

                    print(
                        f"{ticket} status: {text}"
                    )

                    return text

        except Exception:
            pass

    # Fallback to page text.

    try:

        body = page.locator(
            "body"
        ).inner_text()

        statuses = [
            "Done",
            "In Progress",
            "New",
            "To Do",
            "Open",
            "Blocked",
            "Closed",
        ]

        for status in statuses:

            if re.search(
                rf"\b{re.escape(status)}\b",
                body,
                re.IGNORECASE
            ):

                print(
                    f"{ticket} status: {status}"
                )

                return status

    except Exception:
        pass

    print(
        f"WARNING: Could not determine status of {ticket}"
    )

    return None


# ============================================================
# FIRST 3 TICKETS
# ============================================================

def check_first_three(page, subtasks):

    print("\n========================================")
    print("CHECKING FIRST 3 TICKETS")
    print("========================================")

    for i in range(3):

        ticket = subtasks[i]

        status = get_ticket_status(
            page,
            ticket
        )

        if not status:

            print(
                f"ERROR: Could not determine status of {ticket}"
            )

            return False

        if status.lower() != "done":

            print(
                f"STOP: {ticket} is not Done."
            )

            print(
                f"Current status: {status}"
            )

            return False

        print(
            f"PASS: {ticket} is Done."
        )

    return True


# ============================================================
# TICKET 4
# ============================================================

def wait_for_ticket_four(page, subtasks):

    ticket = subtasks[3]

    print("\n========================================")
    print("WAITING FOR TICKET 4")
    print("========================================")

    while True:

        status = get_ticket_status(
            page,
            ticket
        )

        if status and status.lower() == "done":

            print(
                f"PASS: {ticket} is Done."
            )

            return True

        print(
            f"{ticket} is currently: {status}"
        )

        print(
            f"Waiting {CHECK_INTERVAL} seconds..."
        )

        time.sleep(
            CHECK_INTERVAL
        )


# ============================================================
# ASSIGN TICKET 5 TO MYSELF
# ============================================================

def assign_ticket_five_to_me(page, ticket):

    print("\n========================================")
    print("ASSIGNING TICKET 5 TO MYSELF")
    print("========================================")

    open_jira(
        page,
        ticket
    )

    if not check_jira_login(page):
        return False

    page.wait_for_timeout(2000)

    selectors = [
        'text="Assign to me"',
        'button:has-text("Assign to me")',
        '[role="button"]:has-text("Assign to me")',
        '[data-testid*="assign"]:has-text("Assign to me")',
    ]

    for selector in selectors:

        try:

            locator = page.locator(
                selector
            )

            for i in range(
                locator.count()
            ):

                element = locator.nth(i)

                if not element.is_visible():
                    continue

                print(
                    "Found 'Assign to me'."
                )

                print(
                    "Clicking 'Assign to me'..."
                )

                element.click()

                page.wait_for_timeout(
                    3000
                )

                print(
                    "PASS: Ticket 5 assigned to me."
                )

                return True

        except Exception:
            continue

    print(
        "WARNING: 'Assign to me' was not found."
    )

    return False


# ============================================================
# FIND S2AP URL FROM TICKET 5
# ============================================================

def get_s2ap_url_from_ticket(page, ticket):

    print("\n========================================")
    print("FINDING S2AP URL FROM TICKET 5")
    print("========================================")

    open_jira(
        page,
        ticket
    )

    if not check_jira_login(page):
        return None

    page.wait_for_timeout(
        2000
    )

    links = page.locator(
        "a[href]"
    )

    for i in range(
        links.count()
    ):

        try:

            href = links.nth(i).get_attribute(
                "href"
            )

            if not href:
                continue

            lower = href.lower()

            if "selector.ai" not in lower:
                continue

            if "s2m.selector.ai" in lower:
                continue

            if "selector.atlassian.net" in lower:
                continue

            if href.startswith("http"):

                print(
                    f"S2AP URL found: {href}"
                )

                return href.rstrip("/")

        except Exception:
            continue

    # Fallback: search page text.

    try:

        body = page.locator(
            "body"
        ).inner_text()

        urls = re.findall(
            r'https?://[^\s<>"\']+',
            body
        )

        for url in urls:

            url = url.rstrip(
                ".,);]"
            )

            lower = url.lower()

            if "selector.ai" not in lower:
                continue

            if "s2m.selector.ai" in lower:
                continue

            if "selector.atlassian.net" in lower:
                continue

            print(
                f"S2AP URL found in ticket text: {url}"
            )

            return url.rstrip("/")

    except Exception:
        pass

    print(
        "ERROR: S2AP URL was not found in Ticket 5."
    )

    return None


# ============================================================
# OPEN S2AP
# ============================================================

def open_s2ap(page, s2ap_url):

    print("\n========================================")
    print("OPENING S2AP")
    print("========================================")

    print(
        f"S2AP URL: {s2ap_url}"
    )

    page.goto(
        s2ap_url,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(
        5000
    )

    print(
        f"Current page: {page.url}"
    )

    # Detect S2AP login redirect.

    if (
        "/realms/" in page.url.lower()
        or "openid-connect" in page.url.lower()
        or "/login" in page.url.lower()
    ):

        print(
            "\nERROR: S2AP login is required."
        )

        print(
            "The persistent browser profile does not currently "
            "have a valid S2AP session."
        )

        return False

    return True


# ============================================================
# SET TIME RANGE
# ============================================================

def set_time_range_to_two_days(page):

    print("\n========================================")
    print("SETTING TIME RANGE")
    print("========================================")

    current_options = [
        "Last 30 minutes",
        "Last 1 hour",
        "Last 6 hours",
        "Last 12 hours",
        "Last 24 hours",
        "Last 7 days",
    ]

    time_button = None

    for option in current_options:

        selectors = [
            f'button:has-text("{option}")',
            f'[role="button"]:has-text("{option}")',
        ]

        for selector in selectors:

            try:

                locator = page.locator(
                    selector
                )

                for i in range(
                    locator.count()
                ):

                    element = locator.nth(i)

                    if element.is_visible():

                        time_button = element
                        break

                if time_button:
                    break

            except Exception:
                pass

        if time_button:
            break

    if not time_button:

        print(
            "WARNING: Time range button was not found."
        )

        return False

    try:

        print(
            "Opening time range selector..."
        )

        time_button.click()

        page.wait_for_timeout(
            1000
        )

    except Exception as e:

        print(
            f"WARNING: Could not open time range selector: {e}"
        )

        return False

    selectors = [
        'text="Last 2 days"',
        '[role="option"]:has-text("Last 2 days")',
        '[role="menuitem"]:has-text("Last 2 days")',
        'button:has-text("Last 2 days")',
    ]

    for selector in selectors:

        try:

            locator = page.locator(
                selector
            )

            for i in range(
                locator.count()
            ):

                element = locator.nth(i)

                if element.is_visible():

                    element.click()

                    page.wait_for_timeout(
                        5000
                    )

                    print(
                        "PASS: Time range set to Last 2 days."
                    )

                    return True

        except Exception:
            continue

    print(
        "WARNING: 'Last 2 days' option was not found."
    )

    return False


# ============================================================
# SCROLL ENTIRE DASHBOARD
# ============================================================

def scroll_entire_dashboard(page):

    print("\n========================================")
    print("SCROLLING THROUGH ENTIRE DASHBOARD")
    print("========================================")

    previous_height = 0

    for i in range(40):

        page.mouse.wheel(
            0,
            1200
        )

        page.wait_for_timeout(
            800
        )

        try:

            current_height = page.evaluate(
                """
                () => Math.max(
                    document.body.scrollHeight,
                    document.documentElement.scrollHeight
                )
                """
            )

        except Exception:

            current_height = previous_height

        print(
            f"Scroll {i + 1}: page height = {current_height}"
        )

        if current_height == previous_height:

            page.wait_for_timeout(
                1500
            )

            try:

                new_height = page.evaluate(
                    """
                    () => Math.max(
                        document.body.scrollHeight,
                        document.documentElement.scrollHeight
                    )
                    """
                )

            except Exception:

                new_height = current_height

            if new_height == current_height:

                break

            current_height = new_height

        previous_height = current_height

    page.evaluate(
        "window.scrollTo(0, 0)"
    )

    page.wait_for_timeout(
        1000
    )

    print(
        "PASS: Entire dashboard was scrolled."
    )


# ============================================================
# WIDGETS
# ============================================================

def get_widget_containers(page):

    selectors = [
        '[data-testid*="widget"]',
        '[data-testid*="Widget"]',
        '[class*="widget"]',
        '[class*="Widget"]',
    ]

    widgets = []

    for selector in selectors:

        try:

            locator = page.locator(
                selector
            )

            for i in range(
                locator.count()
            ):

                element = locator.nth(i)

                try:

                    if element.is_visible():

                        widgets.append(
                            element
                        )

                except Exception:
                    continue

        except Exception:
            continue

    # Remove duplicates.

    unique_widgets = []

    seen = set()

    for widget in widgets:

        try:

            box = widget.bounding_box()

            text = widget.inner_text(
                timeout=1000
            ).strip()

            key = (
                str(box),
                text[:300]
            )

            if key in seen:
                continue

            seen.add(key)

            unique_widgets.append(
                widget
            )

        except Exception:
            continue

    return unique_widgets


def extract_widget_name(widget):

    selectors = [
        '[data-testid*="title"]',
        '[data-testid*="Title"]',
        '[class*="title"]',
        '[class*="Title"]',
        "h1",
        "h2",
        "h3",
        "h4",
    ]

    for selector in selectors:

        try:

            locator = widget.locator(
                selector
            )

            for i in range(
                locator.count()
            ):

                text = locator.nth(i).inner_text(
                    timeout=1000
                ).strip()

                if text and len(text) < 200:

                    return text

        except Exception:
            continue

    try:

        text = widget.inner_text(
            timeout=1000
        ).strip()

        lines = [
            x.strip()
            for x in text.splitlines()
            if x.strip()
        ]

        if lines:

            return lines[0]

    except Exception:
        pass

    return "Unknown Widget"


# ============================================================
# HOME DASHBOARD VALIDATION
# ============================================================

def validate_home_dashboard(page):

    print("\n========================================")
    print("VALIDATING HOME DASHBOARD")
    print("========================================")

    # --------------------------------------------------------
    # TIME RANGE
    # --------------------------------------------------------

    set_time_range_to_two_days(
        page
    )

    print(
        "\nWaiting for Home Dashboard widgets..."
    )

    page.wait_for_timeout(
        10000
    )

    # --------------------------------------------------------
    # SCROLL ENTIRE DASHBOARD
    # --------------------------------------------------------

    scroll_entire_dashboard(
        page
    )

    # --------------------------------------------------------
    # FIND WIDGETS
    # --------------------------------------------------------

    widgets = get_widget_containers(
        page
    )

    print(
        f"\nWidgets detected: {len(widgets)}"
    )

    if not widgets:

        print(
            "FAIL: No dashboard widgets were detected."
        )

        return False

    error_patterns = [
        "Error loading",
        "Failed to load",
        "Unable to load",
        "Something went wrong",
        "Internal Server Error",
        "Service unavailable",
        "Request failed",
        "Failed to fetch",
        "Error occurred",
        "Could not load",
    ]

    loading_patterns = [
        "Loading...",
        "Loading…",
        "Please wait",
        "Fetching...",
        "Fetching…",
    ]

    failures = []

    for index, widget in enumerate(
        widgets,
        start=1
    ):

        name = extract_widget_name(
            widget
        )

        try:

            text = widget.inner_text(
                timeout=3000
            ).strip()

        except Exception:

            text = ""

        problem = None

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        if not name:

            problem = (
                "Widget name could not be identified."
            )

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        if not problem:

            for error in error_patterns:

                if re.search(
                    re.escape(error),
                    text,
                    re.IGNORECASE
                ):

                    problem = (
                        f"Widget displays error: {error}"
                    )

                    break

        # ----------------------------------------------------
        # LOADING
        # ----------------------------------------------------

        if not problem:

            for loading in loading_patterns:

                if re.search(
                    re.escape(loading),
                    text,
                    re.IGNORECASE
                ):

                    problem = (
                        f"Widget still loading: {loading}"
                    )

                    break

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        if problem:

            print(
                f"FAIL - {name}: {problem}"
            )

            failures.append(
                (
                    name,
                    problem
                )
            )

        else:

            print(
                f"PASS - {name}"
            )

    print("\n========================================")
    print("HOME DASHBOARD RESULT")
    print("========================================")

    print(
        f"Widgets checked: {len(widgets)}"
    )

    print(
        f"Widgets failed: {len(failures)}"
    )

    if failures:

        print(
            "\nProblems found:"
        )

        for name, problem in failures:

            print(
                f"- {name}: {problem}"
            )

        return False

    print(
        "\nPASS: Home Dashboard loaded without widget errors."
    )

    print(
        "Down/Violation widget values are not evaluated."
    )

    return True


# ============================================================
# FIND S2OPS
# ============================================================

def find_and_open_s2ops(page):

    print("\n========================================")
    print("FINDING S2OPS DASHBOARD")
    print("========================================")

    selectors = [
        'text="S2Ops"',
        '[role="menuitem"]:has-text("S2Ops")',
        '[role="option"]:has-text("S2Ops")',
        'a:has-text("S2Ops")',
        'button:has-text("S2Ops")',
    ]

    # Try directly.

    for selector in selectors:

        try:

            locator = page.locator(
                selector
            )

            for i in range(
                locator.count()
            ):

                element = locator.nth(i)

                if not element.is_visible():
                    continue

                print(
                    "S2Ops found. Opening..."
                )

                element.click()

                page.wait_for_timeout(
                    5000
                )

                print(
                    f"S2Ops page: {page.url}"
                )

                return True

        except Exception:
            continue

    # Try Dashboards menu.

    dashboard_selectors = [
        'text="Dashboards"',
        '[role="button"]:has-text("Dashboards")',
        'button:has-text("Dashboards")',
    ]

    for selector in dashboard_selectors:

        try:

            locator = page.locator(
                selector
            )

            for i in range(
                locator.count()
            ):

                element = locator.nth(i)

                if not element.is_visible():
                    continue

                print(
                    "Opening Dashboards menu..."
                )

                element.click()

                page.wait_for_timeout(
                    1500
                )

                s2ops = page.locator(
                    'text="S2Ops"'
                )

                for j in range(
                    s2ops.count()
                ):

                    item = s2ops.nth(j)

                    if item.is_visible():

                        print(
                            "S2Ops found in menu."
                        )

                        item.click()

                        page.wait_for_timeout(
                            5000
                        )

                        print(
                            f"S2Ops page: {page.url}"
                        )

                        return True

        except Exception:
            continue

    print(
        "ERROR: S2Ops dashboard could not be found."
    )

    return False


# ============================================================
# S2OPS ENGINE VALIDATION
# ============================================================

def validate_s2ops_engines(page):

    print("\n========================================")
    print("VALIDATING S2OPS ENGINES")
    print("========================================")

    page.wait_for_timeout(
        5000
    )

    scroll_entire_dashboard(
        page
    )

    red_found = []
    grey_found = []

    # --------------------------------------------------------
    # RED INDICATORS
    # --------------------------------------------------------

    red_selectors = [
        '[style*="red"]',
        '[style*="rgb(255"]',
        '[class*="red"]',
        '[class*="Red"]',
        '[class*="error"]',
        '[class*="Error"]',
        '[class*="danger"]',
        '[class*="Danger"]',
    ]

    for selector in red_selectors:

        try:

            locator = page.locator(
                selector
            )

            for i in range(
                locator.count()
            ):

                element = locator.nth(i)

                if not element.is_visible():
                    continue

                try:

                    text = element.inner_text(
                        timeout=1000
                    ).strip()

                except Exception:

                    text = ""

                if text:

                    red_found.append(
                        text[:200]
                    )

        except Exception:
            continue

    # --------------------------------------------------------
    # GREY INDICATORS
    # --------------------------------------------------------

    grey_selectors = [
        '[style*="gray"]',
        '[style*="grey"]',
        '[class*="gray"]',
        '[class*="Gray"]',
        '[class*="grey"]',
        '[class*="Grey"]',
        '[class*="disabled"]',
        '[class*="Disabled"]',
    ]

    for selector in grey_selectors:

        try:

            locator = page.locator(
                selector
            )

            for i in range(
                locator.count()
            ):

                element = locator.nth(i)

                if not element.is_visible():
                    continue

                try:

                    text = element.inner_text(
                        timeout=1000
                    ).strip()

                except Exception:

                    text = ""

                if text:

                    grey_found.append(
                        text[:200]
                    )

        except Exception:
            continue

    red_found = list(
        dict.fromkeys(red_found)
    )

    grey_found = list(
        dict.fromkeys(grey_found)
    )

    print(
        f"Potential red indicators: {len(red_found)}"
    )

    print(
        f"Potential grey indicators: {len(grey_found)}"
    )

    if red_found:

        print(
            "\nRED ENGINE / ERROR INDICATORS:"
        )

        for item in red_found:

            print(
                f"- {item}"
            )

    if grey_found:

        print(
            "\nGREY ENGINE / DISABLED INDICATORS:"
        )

        for item in grey_found:

            print(
                f"- {item}"
            )

    if red_found or grey_found:

        print(
            "\nFAIL: Red or grey engine indicators detected."
        )

        return False

    print(
        "\nPASS: No red or grey engine indicators detected."
    )

    return True


# ============================================================
# TICKET 5
# ============================================================

def process_ticket_five(page, ticket):

    print("\n========================================")
    print("PROCESSING TICKET 5")
    print("========================================")

    # --------------------------------------------------------
    # ASSIGN TO ME
    # --------------------------------------------------------

    assign_result = assign_ticket_five_to_me(
        page,
        ticket
    )

    if not assign_result:

        print(
            "\nWARNING: Could not assign Ticket 5 to me."
        )

        print(
            "Continuing with validation..."
        )

    # --------------------------------------------------------
    # S2AP URL
    # --------------------------------------------------------

    s2ap_url = get_s2ap_url_from_ticket(
        page,
        ticket
    )

    if not s2ap_url:

        return False

    # --------------------------------------------------------
    # OPEN S2AP
    # --------------------------------------------------------

    if not open_s2ap(
        page,
        s2ap_url
    ):

        print(
            "\nS2AP login is required."
        )

        print(
            "Please run login.py once to create/update "
            "the persistent browser profile."
        )

        return False

    # --------------------------------------------------------
    # HOME DASHBOARD
    # --------------------------------------------------------

    home_result = validate_home_dashboard(
        page
    )

    if not home_result:

        print(
            "\nHOME DASHBOARD FAILED."
        )

        return False

    print(
        "\nHOME DASHBOARD PASSED."
    )

    # --------------------------------------------------------
    # S2OPS
    # --------------------------------------------------------

    if not find_and_open_s2ops(
        page
    ):

        return False

    s2ops_result = validate_s2ops_engines(
        page
    )

    if not s2ops_result:

        print(
            "\nS2OPS ENGINE VALIDATION FAILED."
        )

        return False

    print(
        "\nS2OPS ENGINE VALIDATION PASSED."
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) < 2:

        print(
            "\nUsage:"
        )

        print(
            "python main.py OPS-13641"
        )

        sys.exit(1)

    parent_ticket = sys.argv[1].strip()

    print("\n========================================")
    print("S2AP UPGRADE VALIDATOR")
    print("========================================")

    print(
        f"Parent Jira ticket: {parent_ticket}"
    )

    # --------------------------------------------------------
    # Persistent profile
    # --------------------------------------------------------

    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with sync_playwright() as p:

        print(
            "\nOpening persistent browser profile..."
        )

        context = p.chromium.launch_persistent_context(
            user_data_dir=str(
                PROFILE_DIR
            ),
            headless=False
        )

        if context.pages:

            page = context.pages[0]

        else:

            page = context.new_page()

        # ----------------------------------------------------
        # FIND SUBTASKS
        # ----------------------------------------------------

        subtasks = get_subtasks(
            page,
            parent_ticket
        )

        if len(subtasks) < 5:

            print(
                "\nERROR: At least 5 Jira tickets were expected."
            )

            context.close()

            sys.exit(1)

        print(
            f"\nTotal Jira tickets found: {len(subtasks)}"
        )

        # ----------------------------------------------------
        # FIRST 3
        # ----------------------------------------------------

        if not check_first_three(
            page,
            subtasks
        ):

            print(
                "\nVALIDATION STOPPED."
            )

            context.close()

            sys.exit(1)

        # ----------------------------------------------------
        # TICKET 4
        # ----------------------------------------------------

        if not wait_for_ticket_four(
            page,
            subtasks
        ):

            print(
                "\nVALIDATION STOPPED."
            )

            context.close()

            sys.exit(1)

        # ----------------------------------------------------
        # TICKET 5
        # ----------------------------------------------------

        ticket_five = subtasks[4]

        print(
            f"\nTicket 5: {ticket_five}"
        )

        result = process_ticket_five(
            page,
            ticket_five
        )

        # ----------------------------------------------------
        # FINAL
        # ----------------------------------------------------

        print("\n========================================")
        print("FINAL RESULT")
        print("========================================")

        if result:

            print(
                "ALL GOOD"
            )

            print(
                "Home Dashboard and S2Ops validation passed."
            )

        else:

            print(
                "VALIDATION FAILED"
            )

            print(
                "Check the errors reported above."
            )

        input(
            "\nPress ENTER to close the browser..."
        )

        context.close()


if __name__ == "__main__":

    main()