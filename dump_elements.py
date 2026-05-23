import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

print("🚀 Starting CloakBrowser to dump iframe elements...")
try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    # Find the challenge frame
    turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
    if not turnstile_frames:
        print("No Turnstile frame found.")
    else:
        frame = turnstile_frames[0]
        print(f"Frame URL: {frame.url}")
        
        # Dump all elements in the frame
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
            
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
