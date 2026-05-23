import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

print("🚀 Starting CloakBrowser in HEADED mode to perform click...")
try:
    browser = launch(headless=False, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    # Wait for Turnstile frame to appear
    frame = None
    for i in range(15):
        turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
        if turnstile_frames:
            frame = turnstile_frames[0]
            print(f"Found Turnstile frame: {frame.url}")
            break
        page.wait_for_timeout(1000)

    if not frame:
        print("❌ Turnstile frame not found.")
    else:
        # Give it a second to load elements inside the iframe
        page.wait_for_timeout(3000)
        
        # Click the checkbox inside the iframe
        print("Clicking checkbox inside Turnstile frame...")
        # Since it is a shadow DOM or standard iframe, let's locate the checkbox
        # The HTML shows a label with class "cb-lb" containing the input.
        # Let's try locating the checkbox directly or by clicking the label/body/wrapper
        try:
            checkbox = frame.locator("input[type='checkbox']")
            if checkbox.count() > 0:
                print("Found checkbox locator, clicking...")
                checkbox.click()
            else:
                # Try clicking by the visible box container
                box = frame.locator(".cb-i")
                if box.count() > 0:
                    print("Found .cb-i locator, clicking...")
                    box.click()
                else:
                    # Let's click the label container
                    lbl = frame.locator(".cb-lb")
                    if lbl.count() > 0:
                        print("Found .cb-lb locator, clicking...")
                        lbl.click()
                    else:
                        print("Locators not found, clicking center of frame...")
                        # Get bounding box of the iframe
                        iframe_el = page.locator("iframe[src*='challenges.cloudflare.com']").first
                        box = iframe_el.bounding_box()
                        if box:
                            page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
        except Exception as e:
            print(f"Error during click: {e}")

        # Now wait and see if title changes
        print("⏳ Waiting for title to change...")
        for i in range(20):
            title = page.title()
            url = page.url
            print(f"  [{i}s] Title: {title} | URL: {url}")
            if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
                print(f"✅ Bypassed CF! Final Title: {title}")
                break
            page.wait_for_timeout(1000)

    page.wait_for_timeout(3000)
    screenshot_path = os.path.join(SAVE_DIR, "result_clicked.png")
    buf = page.screenshot(full_page=False)
    with open(screenshot_path, "wb") as f:
        f.write(buf)
    print(f"📸 Screenshot saved: {screenshot_path}")

    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
