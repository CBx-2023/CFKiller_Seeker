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
            print(f"[{i}s] Found Turnstile frame in page.frames: {frame.url}")
            break
        page.wait_for_timeout(1000)

    # Let's locate the iframe element from the parent document using evaluates or other selectors.
    # Note: Cloudflare might embed the iframe inside a shadow root, or it might be directly in a div.
    # Let's write a JS snippet to find the absolute page coordinates of any iframe with src containing challenges.cloudflare.com
    page.wait_for_timeout(3000)
    
    coords = page.evaluate("""() => {
        const findCoords = (root) => {
            const iframes = Array.from(root.querySelectorAll('iframe'));
            for (let iframe of iframes) {
                if (iframe.src.includes('challenges.cloudflare.com')) {
                    const rect = iframe.getBoundingClientRect();
                    return {
                        x: rect.left + window.scrollX,
                        y: rect.top + window.scrollY,
                        width: rect.width,
                        height: rect.height
                    };
                }
            }
            // Traverse shadow root
            const all = Array.from(root.querySelectorAll('*'));
            for (let el of all) {
                if (el.shadowRoot) {
                    const res = findCoords(el.shadowRoot);
                    if (res) return res;
                }
            }
            return null;
        };
        return findCoords(document.body);
    }""")
    
    if not coords:
        print("❌ Could not find challenges.cloudflare.com iframe via document.querySelectorAll.")
        # Let's list all iframes rects
        all_rects = page.evaluate("""() => {
            const getRects = (root) => {
                let rects = [];
                const iframes = Array.from(root.querySelectorAll('iframe'));
                for (let iframe of iframes) {
                    const rect = iframe.getBoundingClientRect();
                    rects.push({
                        src: iframe.src,
                        x: rect.left,
                        y: rect.top,
                        w: rect.width,
                        h: rect.height
                    });
                }
                const all = Array.from(root.querySelectorAll('*'));
                for (let el of all) {
                    if (el.shadowRoot) {
                        rects = rects.concat(getRects(el.shadowRoot));
                    }
                }
                return rects;
            };
            return getRects(document.body);
        }""")
        print(f"All found iframes rects: {all_rects}")
    else:
        print(f"Found Turnstile iframe coordinates: {coords}")
        click_x = coords['x'] + 30
        click_y = coords['y'] + 32
        print(f"Clicking at coordinates: X={click_x}, Y={click_y}...")
        page.mouse.click(click_x, click_y)

        # Wait and see if title changes
        print("⏳ Waiting for title to change...")
        for k in range(25):
            title = page.title()
            url = page.url
            print(f"  [{k}s] Title: {title} | URL: {url}")
            if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
                print(f"✅ Bypassed CF! Final Title: {title}")
                break
            page.wait_for_timeout(1000)
            
    screenshot_path = os.path.join(SAVE_DIR, "result_coordinate_dom.png")
    buf = page.screenshot(full_page=False)
    with open(screenshot_path, "wb") as f:
        f.write(buf)
    print(f"📸 Saved final screenshot: {screenshot_path}")
            
    browser.close()
except Exception as e:
    print(f"❌ General Error: {e}")
