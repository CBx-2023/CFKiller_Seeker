import os
import time
import random
from cloakbrowser import launch

URL = "https://www.spot.ph"
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

def bezier_curve(x1, y1, x2, y2, steps=15):
    """Generate a simple bezier curve for human-like mouse movement"""
    points = []
    cx = x1 + (x2 - x1) * random.uniform(0.3, 0.7) + random.randint(-50, 50)
    cy = y1 + (y2 - y1) * random.uniform(0.3, 0.7) + random.randint(-50, 50)
    
    for i in range(steps + 1):
        t = i / steps
        x = (1-t)**2 * x1 + 2*(1-t)*t * cx + t**2 * x2
        y = (1-t)**2 * y1 + 2*(1-t)*t * cy + t**2 * y2
        points.append((x, y))
    return points

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
        print("❌ Turnstile frame not found.")
    else:
        # Wait for frame element's bounding box to be stable
        print("Waiting for Turnstile frame layout to stabilize...")
        last_box = None
        for i in range(10):
            frame_element = frame.frame_element()
            if frame_element:
                box = frame_element.bounding_box()
                if box:
                    print(f"  [{i}s] Bounding box: {box}")
                    if last_box and box['x'] == last_box['x'] and box['y'] == last_box['y']:
                        print("✅ Layout stabilized!")
                        break
                    last_box = box
            page.wait_for_timeout(1000)
            
        # Wait additional 8 seconds for "Verifying..." -> Checkbox transition
        print("⏳ Waiting 8s for Turnstile checkbox to render...")
        page.wait_for_timeout(8000)
        
        # Get final stable bounding box
        frame_element = frame.frame_element()
        box = frame_element.bounding_box() if frame_element else None
        if not box:
            print("❌ Stable bounding box not found.")
        else:
            target_x = box['x'] + 30
            target_y = box['y'] + 32
            
            start_x = random.randint(100, 500)
            start_y = random.randint(100, 200)
            
            print(f"Moving mouse naturally to target ({target_x}, {target_y})...")
            page.mouse.move(start_x, start_y)
            page.wait_for_timeout(random.randint(100, 300))
            
            points = bezier_curve(start_x, start_y, target_x, target_y, steps=20)
            for pt_x, pt_y in points:
                page.mouse.move(pt_x, pt_y)
                page.wait_for_timeout(random.randint(10, 30))
                
            page.wait_for_timeout(random.randint(200, 500))
            page.mouse.down()
            page.wait_for_timeout(random.randint(80, 150))
            page.mouse.up()
            
            # Wait and see if title changes
            print("⏳ Waiting for title to change...")
            bypassed = False
            for k in range(25):
                title = page.title()
                url = page.url
                print(f"  [{k}s] Title: {title} | URL: {url}")
                if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
                    print(f"✅ Bypassed CF! Final Title: {title}")
                    bypassed = True
                    break
                page.wait_for_timeout(1000)
                
            if bypassed:
                print("⏳ Waiting 8s for homepage to fully load and render...")
                page.wait_for_timeout(8000)
                
    screenshot_path = os.path.join(SAVE_DIR, "stable_click_result.png")
    page.screenshot(path=screenshot_path)
    print(f"📸 Saved final screenshot to: {screenshot_path}")

    browser.close()
except Exception as e:
    print(f"Error: {e}")
