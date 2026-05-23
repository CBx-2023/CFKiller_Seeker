import os
import time
import random
import math
from cloakbrowser import launch

URL = "https://www.spot.ph"
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

def bezier_curve(x1, y1, x2, y2, steps=15):
    """Generate a simple bezier curve for human-like mouse movement"""
    points = []
    # Control point for bezier curve
    cx = x1 + (x2 - x1) * random.uniform(0.3, 0.7) + random.randint(-50, 50)
    cy = y1 + (y2 - y1) * random.uniform(0.3, 0.7) + random.randint(-50, 50)
    
    for i in range(steps + 1):
        t = i / steps
        # Quadratic bezier formula
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
        page.wait_for_timeout(4000) # Wait for widget to load and show "Verify you are human"
        
        frame_element = frame.frame_element()
        if not frame_element:
            print("❌ frame_element is None.")
        else:
            box = frame_element.bounding_box()
            if not box:
                print("❌ Bounding box of frame element is None.")
            else:
                print(f"Frame bounding box: {box}")
                
                # Checkbox center is roughly (x + 30, y + 32)
                target_x = box['x'] + 30
                target_y = box['y'] + 32
                
                # Start mouse from a random position
                start_x = random.randint(100, 500)
                start_y = random.randint(100, 200)
                
                print(f"Moving mouse naturally from ({start_x}, {start_y}) to ({target_x}, {target_y})...")
                page.mouse.move(start_x, start_y)
                page.wait_for_timeout(random.randint(100, 300))
                
                # Generate bezier path points
                points = bezier_curve(start_x, start_y, target_x, target_y, steps=20)
                for pt_x, pt_y in points:
                    page.mouse.move(pt_x, pt_y)
                    # Add tiny human-like variation in sleep
                    page.wait_for_timeout(random.randint(10, 30))
                    
                page.wait_for_timeout(random.randint(200, 500)) # Hover briefly
                
                print("Sending mouse down and up...")
                page.mouse.down()
                page.wait_for_timeout(random.randint(80, 150)) # Human-like click duration
                page.mouse.up()
                
                # Wait and see if title changes
                print("⏳ Waiting for title to change...")
                for k in range(25):
                    title = page.title()
                    url = page.url
                    print(f"  [{k}s] Title: {title} | URL: {url}")
                    if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
                        print(f"✅ Bypassed CF! Final Title: {title}")
                        print("⏳ Waiting 8s for the website to fully load and render...")
                        page.wait_for_timeout(8000)
                        break
                    page.wait_for_timeout(1000)

    screenshot_path = os.path.join(SAVE_DIR, "result_natural_click.png")
    buf = page.screenshot(full_page=False)
    with open(screenshot_path, "wb") as f:
        f.write(buf)
    print(f"📸 Saved final screenshot: {screenshot_path}")
            
    browser.close()
except Exception as e:
    print(f"❌ General Error: {e}")
