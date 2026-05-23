import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

print("🚀 Starting CloakBrowser to find Turnstile frame and dump elements...")
try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    # Poll for Turnstile frame
    frame = None
    for i in range(10):
        print(f"[{i}s] Checking frames...")
        for f in page.frames:
            print(f"  - Frame URL: {f.url}")
        turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
        if turnstile_frames:
            frame = turnstile_frames[0]
            print(f"Found Turnstile frame at {frame.url}!")
            break
        page.wait_for_timeout(1000)

    if not frame:
        print("❌ Turnstile frame not found after 10s.")
    else:
        # Wait a bit for the Turnstile iframe content to load
        page.wait_for_timeout(2000)
        print("Dumping elements inside Turnstile frame:")
        try:
            elements_info = frame.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('*'));
                return els.map(el => {
                    return {
                        tagName: el.tagName,
                        id: el.id,
                        className: el.className,
                        innerText: el.innerText,
                        outerHTML: el.outerHTML.substring(0, 300)
                    };
                });
            }""")
            
            print(f"Found {len(elements_info)} elements:")
            for idx, info in enumerate(elements_info):
                print(f"[{idx}] {info['tagName']} (id='{info['id']}', class='{info['className']}')")
                print(f"    HTML: {info['outerHTML']}")
                print(f"    Text: {repr(info['innerText'])}")
                print("-" * 50)
        except Exception as e:
            print(f"❌ Error evaluating inside frame: {e}")
            
    browser.close()
except Exception as e:
    print(f"❌ General Error: {e}")
