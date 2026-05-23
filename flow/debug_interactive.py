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
    
    # Wait for Turnstile frame
    frame = None
    for i in range(15):
        turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
        if turnstile_frames:
            frame = turnstile_frames[0]
            print(f"Found Turnstile frame at {i}s")
            break
        page.wait_for_timeout(1000)
        
    if not frame:
        print("❌ Turnstile frame not found.")
    else:
        # Every second, print details and take a screenshot
        for j in range(15):
            box = frame.frame_element().bounding_box() if frame.frame_element() else None
            # Read text via evaluate if possible
            try:
                text = frame.locator("body").evaluate("el => el.innerText").strip().replace('\n', ' ')
            except Exception as e:
                text = f"Error: {e}"
                
            print(f"[{j}s] Bounding Box: {box} | Text: {repr(text)}")
            
            # Save screenshot of each second
            screenshot_path = os.path.join(SAVE_DIR, f"state_{j}.png")
            page.screenshot(path=screenshot_path)
            
    browser.close()
except Exception as e:
    print(f"Error: {e}")
