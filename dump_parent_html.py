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

    # Let's find all iframes in the document using js
    iframes_info = page.evaluate("""() => {
        const iframes = Array.from(document.querySelectorAll('iframe'));
        return iframes.map(iframe => {
            return {
                id: iframe.id,
                name: iframe.name,
                src: iframe.src,
                className: iframe.className,
                outerHTML: iframe.outerHTML.substring(0, 300)
            };
        });
    }""")
    
    print(f"Found {len(iframes_info)} iframe elements in the main document:")
    for idx, info in enumerate(iframes_info):
        print(f"[{idx}] id='{info['id']}', name='{info['name']}', src='{info['src']}', class='{info['className']}'")
        print(f"    HTML: {info['outerHTML']}")
        print("-" * 50)
        
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
