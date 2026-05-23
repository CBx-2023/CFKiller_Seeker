import os
import time
from cloakbrowser import launch

SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
URL = "https://www.spot.ph"
SCREENSHOT_PATH = os.path.join(SAVE_DIR, "result_headed.png")

print("🚀 Starting CloakBrowser in HEADED mode...")
try:
    browser = launch(headless=False, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")

    print(f"📋 Initial Title: {page.title()}")
    print("⏳ Waiting for 15 seconds to let Cloudflare verification solve...")
    
    # Let's poll the title to see if it changes
    for i in range(15):
        title = page.title()
        url = page.url
        print(f"  [{i}s] Title: {title} | URL: {url}")
        if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
            print(f"✅ Bypassed CF! Final Title: {title}")
            break
        page.wait_for_timeout(1000)
    
    page.wait_for_timeout(3000)
    
    # Save screenshot
    buf = page.screenshot(full_page=False)
    with open(SCREENSHOT_PATH, "wb") as f:
        f.write(buf)
    print(f"📸 Screenshot saved to {SCREENSHOT_PATH} ({len(buf)} bytes)")

    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
