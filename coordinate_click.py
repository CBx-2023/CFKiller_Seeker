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
    
    # Wait for Turnstile frame to appear
    frame = None
    for i in range(15):
        turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
        if turnstile_frames:
            frame = turnstile_frames[0]
            print(f"[{i}s] Found Turnstile frame: {frame.url}")
            break
        page.wait_for_timeout(1000)

    if not frame:
        print("❌ Turnstile frame not found.")
    else:
        # Instead of reading the DOM inside the cross-origin iframe (which might be blocked or empty due to timing/cors),
        # let's find the position of the iframe element on the main page, and send a click to its exact center!
        page.wait_for_timeout(3000)
        
        iframe_selector = "iframe[src*='challenges.cloudflare.com']"
        iframe_loc = page.locator(iframe_selector).first
        
        box = iframe_loc.bounding_box()
        if box:
            print(f"Found iframe bounding box: {box}")
            # The Turnstile checkbox is typically near the left-middle.
            # In a standard widget size of ~300x65, the checkbox center is roughly at:
            # X = x + 30, Y = y + 32
            click_x = box['x'] + 30
            click_y = box['y'] + 32
            print(f"Clicking at coordinates: X={click_x}, Y={click_y}...")
            page.mouse.click(click_x, click_y)
        else:
            print("❌ Iframe bounding box is None. Cannot click by coordinates.")

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
            
        screenshot_path = os.path.join(SAVE_DIR, "result_coordinate_click.png")
        buf = page.screenshot(full_page=False)
        with open(screenshot_path, "wb") as f:
            f.write(buf)
        print(f"📸 Saved final screenshot: {screenshot_path}")
            
    browser.close()
except Exception as e:
    print(f"❌ General Error: {e}")
