import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    # Print top-level body html of the main frame
    html = page.locator("body").evaluate("el => el.innerHTML")
    print(f"Main Frame Body HTML (length={len(html)}):")
    print(html)
        
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
