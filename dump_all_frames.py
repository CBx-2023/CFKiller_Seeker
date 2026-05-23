import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    print(f"📋 Current Title: {page.title()}")
    print(f"Total frames: {len(page.frames)}")
    
    for idx, f in enumerate(page.frames):
        parent_url = f.parent_frame.url if f.parent_frame else "None (Main)"
        print(f"Frame {idx}:")
        print(f"  URL: {f.url}")
        print(f"  Parent: {parent_url}")
        print(f"  Name: {f.name}")
        
        # Check elements in this frame
        try:
            input_count = f.locator("input").count()
            checkbox_count = f.locator("input[type='checkbox']").count()
            div_count = f.locator("div").count()
            iframe_count = f.locator("iframe").count()
            print(f"  Locators inside frame: inputs={input_count}, checkboxes={checkbox_count}, divs={div_count}, iframes={iframe_count}")
            
            # Print outer HTML of frame body
            body_html = f.locator("body").evaluate("el => el.innerHTML")
            print(f"  Body HTML length: {len(body_html)}")
            if len(body_html) > 0:
                print(f"  Body HTML snippet: {body_html[:300]}")
        except Exception as e:
            print(f"  Error reading frame: {e}")
        print("-" * 60)
        
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
