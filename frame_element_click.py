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
            print(f"[{i}s] Found Turnstile frame: {frame.url}")
            break
        page.wait_for_timeout(1000)

    if not frame:
        print("❌ Turnstile frame not found in page.frames.")
    else:
        # Give it a few seconds to load the checkbox
        page.wait_for_timeout(5000)
        
        # Get the owner element of the frame
        frame_element = frame.frame_element()
        if not frame_element:
            print("❌ frame.frame_element() returned None.")
        else:
            print("Found frame element!")
            box = frame_element.bounding_box()
            if not box:
                print("❌ Bounding box of frame element is None.")
            else:
                print(f"Frame bounding box: {box}")
                # Click the checkbox center (X = x + 30, Y = y + 32)
                click_x = box['x'] + 30
                click_y = box['y'] + 32
                print(f"Clicking at coordinates: X={click_x}, Y={click_y}...")
                page.mouse.click(click_x, click_y)
                
                # Let's wait and see if the verification completes
                print("⏳ Waiting for title to change...")
                for k in range(25):
                    title = page.title()
                    url = page.url
                    print(f"  [{k}s] Title: {title} | URL: {url}")
                    if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
                        print(f"✅ Bypassed CF! Final Title: {title}")
                        break
                    page.wait_for_timeout(1000)

    screenshot_path = os.path.join(SAVE_DIR, "result_frame_element_click.png")
    buf = page.screenshot(full_page=False)
    with open(screenshot_path, "wb") as f:
        f.write(buf)
    print(f"📸 Saved final screenshot: {screenshot_path}")
            
    browser.close()
except Exception as e:
    print(f"❌ General Error: {e}")
