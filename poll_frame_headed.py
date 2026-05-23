import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    # Set headed=True so we run in standard display, which often helps CF Turnstile load normally
    browser = launch(headless=False, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    # Wait for Turnstile frame to load (URL containing challenges.cloudflare.com)
    frame = None
    for i in range(25):
        turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
        if turnstile_frames:
            frame = turnstile_frames[0]
            print(f"[{i}s] Found Turnstile frame: {frame.url}")
            break
        print(f"[{i}s] Checking frames (count={len(page.frames)}): {[f.url for f in page.frames]}")
        page.wait_for_timeout(1000)

    if not frame:
        print("❌ Turnstile frame not found.")
        screenshot_path = os.path.join(SAVE_DIR, "error_no_frame.png")
        buf = page.screenshot(full_page=False)
        with open(screenshot_path, "wb") as f:
            f.write(buf)
        print(f"📸 Saved error screenshot: {screenshot_path}")
    else:
        # Poll body HTML of the Turnstile frame for 25 seconds
        print("Polling Turnstile frame body HTML...")
        for j in range(25):
            try:
                body_html = frame.locator("body").evaluate("el => el.innerHTML")
                inputs = frame.locator("input").count()
                checkboxes = frame.locator("input[type='checkbox']").count()
                cb_lbs = frame.locator(".cb-lb").count()
                cb_is = frame.locator(".cb-i").count()
                
                print(f"  [{j}s] body HTML len: {len(body_html)} | inputs={inputs} | checkboxes={checkboxes} | .cb-lb={cb_lbs} | .cb-i={cb_is}")
                if checkboxes > 0:
                    print(f"    Checkbox HTML: {frame.locator('input[type=\"checkbox\"]').first.evaluate('el => el.outerHTML')}")
                    
                    # Let's perform a click using mouse coordinate relative to the frame bounding box
                    box = frame.locator("input[type='checkbox']").first.bounding_box()
                    if box:
                        print(f"    Clicking checkbox bounding box: {box}")
                        frame.locator("input[type='checkbox']").first.click()
                        break
                    else:
                        print("    Checkbox bounding box is None, attempting standard click...")
                        frame.locator("input[type='checkbox']").first.click()
                        break
            except Exception as e:
                print(f"  [{j}s] Error reading/clicking: {e}")
            page.wait_for_timeout(1000)
            
        print("⏳ Waiting for title to change...")
        for k in range(15):
            title = page.title()
            url = page.url
            print(f"  [{k}s] Title: {title} | URL: {url}")
            if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
                print(f"✅ Bypassed CF! Final Title: {title}")
                break
            page.wait_for_timeout(1000)
            
        screenshot_path = os.path.join(SAVE_DIR, "result_headed_poll.png")
        buf = page.screenshot(full_page=False)
        with open(screenshot_path, "wb") as f:
            f.write(buf)
        print(f"📸 Saved final screenshot: {screenshot_path}")
            
    browser.close()
except Exception as e:
    print(f"❌ General Error: {e}")
