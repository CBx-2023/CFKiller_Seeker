import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(10000)

    # Let's count different tags that can host frames or elements
    for tag in ["iframe", "frame", "object", "embed", "portal", "div", "span"]:
        count = page.locator(tag).count()
        print(f"Tag '{tag}': count={count}")
        if count > 0 and tag not in ["div", "span"]:
            for idx in range(min(count, 5)):
                try:
                    html = page.locator(tag).nth(idx).evaluate("el => el.outerHTML")
                    print(f"  - [{idx}] HTML: {html[:300]}")
                except Exception as e:
                    print(f"  - [{idx}] Error: {e}")
                    
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
