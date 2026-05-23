import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

print("🚀 Starting CloakBrowser to dump iframe info...")
try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    print(f"📋 Current Title: {page.title()}")
    print("Listing all frames:")
    for frame in page.frames:
        print(f"  - Name: {frame.name} | URL: {frame.url}")

    # Check challenges.cloudflare.com specifically
    turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
    print(f"Found {len(turnstile_frames)} Turnstile frames:")
    for i, frame in enumerate(turnstile_frames):
        print(f"Frame {i}:")
        content = frame.content_body() if hasattr(frame, 'content_body') else None
        # We can query selectors inside the frame
        try:
            html = frame.content()
            print(f"  Content length: {len(html)}")
            # Let's search for checkbox or input
            checkboxes = frame.locator("input[type='checkbox']").count()
            cb_lbs = frame.locator(".cb-lb").count()
            elements = frame.locator("*").count()
            print(f"  Elements: {elements}, checkboxes: {checkboxes}, .cb-lb count: {cb_lbs}")
            
            # Print some outer HTML of likely elements
            for sel in ["input[type='checkbox']", ".cb-lb", "span", "div"]:
                try:
                    loc = frame.locator(sel)
                    if loc.count() > 0:
                        print(f"  Matches for '{sel}': {loc.count()}")
                        for idx in range(min(loc.count(), 3)):
                            print(f"    [{idx}] text: {loc.nth(idx).inner_text()} | html: {loc.nth(idx).evaluate('el => el.outerHTML')}")
                except Exception as e:
                    print(f"    Error querying '{sel}': {e}")
        except Exception as e:
            print(f"  Error reading frame {i}: {e}")

    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
