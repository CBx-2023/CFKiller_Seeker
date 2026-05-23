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
    
    # Wait for Turnstile frame to appear in page.frames
    frame = None
    for i in range(15):
        turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
        if turnstile_frames:
            frame = turnstile_frames[0]
            print(f"[{i}s] Found Turnstile frame in page.frames: {frame.url}")
            break
        page.wait_for_timeout(1000)

    # Let's perform coordinate clicking by using the frame locator directly, which playwright resolves automatically
    # even if it is cross-origin or in a shadow DOM.
    # Playwright's `frame_locator("...").locator("input[type='checkbox']")` handles locating the elements.
    # We will locate the label `.cb-lb` or checkbox `input[type='checkbox']` and trigger a click.
    page.wait_for_timeout(3000)
    
    try:
        # Resolve frame locator
        fl = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
        
        # Click the label / text element
        checkbox_label = fl.locator(".cb-lb")
        checkbox_box = fl.locator(".cb-i")
        checkbox_input = fl.locator("input[type='checkbox']")
        
        if checkbox_label.count() > 0:
            print("Found .cb-lb label, clicking...")
            checkbox_label.click()
        elif checkbox_box.count() > 0:
            print("Found .cb-i checkbox box, clicking...")
            checkbox_box.click()
        elif checkbox_input.count() > 0:
            print("Found input[type='checkbox'], clicking...")
            checkbox_input.click()
        else:
            print("❌ No locators found inside Turnstile iframe.")
    except Exception as e:
        print(f"❌ Error clicking via frame_locator: {e}")

    # Wait and see if title changes
    print("⏳ Waiting for title to change...")
    for k in range(25):
        title = page.title()
        url = page.url
        print(f"  [{k}s] Title: {title} | URL: {url}")
        if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
            print(f"✅ Bypassed CF! Final Title: {title}")
            break
        page.wait_for_timeout(1000)
            
    screenshot_path = os.path.join(SAVE_DIR, "result_frame_locator_click.png")
    buf = page.screenshot(full_page=False)
    with open(screenshot_path, "wb") as f:
        f.write(buf)
    print(f"📸 Saved final screenshot: {screenshot_path}")
            
    browser.close()
except Exception as e:
    print(f"❌ General Error: {e}")
