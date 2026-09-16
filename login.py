from pathlib import Path
from playwright.sync_api import sync_playwright


# ============================================================
# CONFIGURATION
# ============================================================

JIRA_URL = "https://selector.atlassian.net/browse/OPS-13641"

S2AP_URL = "https://nghs-staging.selector.ai"

PROFILE_DIR = Path(
    "playwright/automation-profile"
)


# ============================================================
# LOGIN
# ============================================================

with sync_playwright() as p:

    print("\n========================================")
    print("STARTING PERSISTENT BROWSER")
    print("========================================")

    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False
    )

    page = browser.pages[0] if browser.pages else browser.new_page()

    # ========================================================
    # JIRA
    # ========================================================

    print("\n========================================")
    print("JIRA")
    print("========================================")

    page.goto(
        JIRA_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(5000)

    print("\nCurrent Jira page:")
    print(page.url)

    print("\nIf Jira asks you to login:")
    print("Complete the Google / Selector SSO login.")

    input(
        "\nPress ENTER after Jira is visible..."
    )

    print("\nJira page:")
    print(page.url)

    # ========================================================
    # S2AP
    # ========================================================

    print("\n========================================")
    print("S2AP")
    print("========================================")

    page.goto(
        S2AP_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(5000)

    print("\nCurrent S2AP page:")
    print(page.url)

    print("\nIf S2AP asks you to login:")
    print("Complete the S2AP / Selector SSO login.")

    print(
        "\nIMPORTANT:"
    )

    print(
        "Wait until you can actually see the S2AP dashboard."
    )

    input(
        "\nPress ENTER after the S2AP dashboard is visible..."
    )

    print("\nS2AP page:")
    print(page.url)

    # ========================================================
    # DONE
    # ========================================================

    print("\n========================================")
    print("LOGIN PROFILE SAVED")
    print("========================================")

    print(
        "Browser profile:"
    )

    print(
        PROFILE_DIR.resolve()
    )

    print(
        "\nYou can now close this browser."
    )

    print(
        "The login session will remain in this profile."
    )

    input(
        "\nPress ENTER to close..."
    )

    browser.close()