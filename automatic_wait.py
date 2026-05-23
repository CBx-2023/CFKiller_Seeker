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
    
    # Let's poll for 30s to see if the Turnstile challenge automatically goes through
    # when we do NOT touch anything (since Turnstile is designed to be non-interactive/managed
    # and has a passive verification check, let's observe if it automatically finishes).
    print("⏳ Waiting for Turnstile to automatically verify (passive challenge)...")
    for k in range(30):
        title = page.title()
        url = page.url
        
        # Let's inspect what Turnstile status text is visible (e.g. "Verifying...", "Verify you are human", etc.)
        turnstile_frame = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
        status_text = "No Turnstile Frame"
        if turnstile_frame:
            try:
                # Read inner text of frame body
                status_text = turnstile_frame[0].locator("body").evaluate("el => el.innerText")
                status_text = status_text.strip().replace('\n', ' | ')
            except Exception as e:
                status_text = f"Error reading: {e}"
                
        print(f"  [{k}s] Title: {title} | Frame Status: {status_text}")
        
        if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
            print(f"✅ Bypassed CF! Final Title: {title}")
            break
        page.wait_for_timeout(1000)
            
    screenshot_path = os.path.join(SAVE_DIR, "result_automatic_wait.png")
    buf = page.screenshot(full_page=False)
    with open(screenshot_path, "wb") as f:
        f.write(buf)
    print(f"📸 Saved final screenshot: {screenshot_path}")
            
    browser.close()
except Exception as e:
    print(f"❌ General Error: {e}")
