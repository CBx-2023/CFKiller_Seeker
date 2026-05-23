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
    
    # Poll all frames every second for 25 seconds
    for i in range(25):
        print(f"\n--- [{i}s] Total Frames: {len(page.frames)} ---")
        for idx, f in enumerate(page.frames):
            parent_url = f.parent_frame.url if f.parent_frame else "None (Main)"
            try:
                # Let's count some elements in this frame
                inputs = f.locator("input").count()
                divs = f.locator("div").count()
                checkboxes = f.locator("input[type='checkbox']").count()
                print(f"  Frame {idx}: URL={f.url}")
                print(f"    Parent: {parent_url}")
                print(f"    Name: {f.name}")
                print(f"    Elements: inputs={inputs}, checkboxes={checkboxes}, divs={divs}")
                
                # If checkboxes > 0, let's print checkbox outerHTML
                if checkboxes > 0:
                    html = f.locator("input[type='checkbox']").first.evaluate("el => el.outerHTML")
                    print(f"    👉 FOUND CHECKBOX: {html}")
            except Exception as e:
                print(f"  Frame {idx}: URL={f.url} | Error: {e}")
        page.wait_for_timeout(1000)
        
    screenshot_path = os.path.join(SAVE_DIR, "result_poll_all_frames.png")
    buf = page.screenshot(full_page=False)
    with open(screenshot_path, "wb") as f:
        f.write(buf)
    print(f"📸 Saved final screenshot: {screenshot_path}")
            
    browser.close()
except Exception as e:
    print(f"❌ General Error: {e}")
