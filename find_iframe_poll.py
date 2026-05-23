import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    # We look for all iframes in the document using standard frame_locator or locator.
    # Note: `challenges.cloudflare.com` is where Turnstile checkbox is loaded.
    # Let's poll for 15s until an iframe src containing challenges.cloudflare.com appears in the page.
    iframe_found = False
    for i in range(15):
        iframe_count = page.locator("iframe").count()
        print(f"[{i}s] Found {iframe_count} iframes in page:")
        for idx in range(iframe_count):
            iframe_src = page.locator("iframe").nth(idx).evaluate("el => el.src")
            iframe_id = page.locator("iframe").nth(idx).evaluate("el => el.id")
            print(f"  - [{idx}] id='{iframe_id}' | src: {iframe_src}")
            if "challenges.cloudflare.com" in iframe_src:
                iframe_found = True
        if iframe_found:
            break
        page.wait_for_timeout(1000)
        
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
