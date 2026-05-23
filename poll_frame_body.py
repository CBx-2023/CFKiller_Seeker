import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    # Poll for Turnstile frame
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
        # Poll body HTML of the Turnstile frame for 20 seconds
        print("Polling Turnstile frame body HTML...")
        for j in range(20):
            try:
                body_html = frame.locator("body").evaluate("el => el.innerHTML")
                inputs = frame.locator("input").count()
                checkboxes = frame.locator("input[type='checkbox']").count()
                cb_lbs = frame.locator(".cb-lb").count()
                cb_is = frame.locator(".cb-i").count()
                
                print(f"  [{j}s] body HTML len: {len(body_html)} | inputs={inputs} | checkboxes={checkboxes} | .cb-lb={cb_lbs} | .cb-i={cb_is}")
                if len(body_html) > 0:
                    print(f"    Body HTML: {body_html[:500]}")
                    # If we found input or checkboxes, let's print their HTML
                    if checkboxes > 0:
                        print(f"    Checkbox HTML: {frame.locator('input[type=\"checkbox\"]').first.evaluate('el => el.outerHTML')}")
                        break
            except Exception as e:
                print(f"  [{j}s] Error reading body: {e}")
            page.wait_for_timeout(1000)
            
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
