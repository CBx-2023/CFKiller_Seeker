import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    browser = launch(headless=False, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    print("Waiting 15 seconds...")
    page.wait_for_timeout(15000)
    
    screenshot_path = os.path.join(SAVE_DIR, "current_state.png")
    buf = page.screenshot(full_page=False)
    with open(screenshot_path, "wb") as f:
        f.write(buf)
    print(f"📸 Screenshot saved to {screenshot_path} ({len(buf)} bytes)")

    browser.close()
except Exception as e:
    print(f"Error: {e}")
