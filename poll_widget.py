import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    # Wait for the widget wrapper div to be rendered
    page.wait_for_selector("#GZIfP3", timeout=15000)
    print("Found #GZIfP3 wrapper div!")
    
    # Let's inspect its inner HTML and look for any iframe dynamically appended inside it
    # We poll for 10 seconds checking if #GZIfP3 gets new child elements (like shadow roots or dynamically inserted iframes)
    for i in range(10):
        wrapper_html = page.locator("#GZIfP3").evaluate("el => el.innerHTML")
        child_count = page.locator("#GZIfP3 > *").count()
        print(f"[{i}s] Wrapper innerHTML length: {len(wrapper_html)} | child count: {child_count}")
        if len(wrapper_html) > 200:
            print("Wrapper innerHTML snippet:")
            print(wrapper_html)
            break
        page.wait_for_timeout(1000)
        
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
