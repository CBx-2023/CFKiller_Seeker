import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=False, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    # We wait 12s so it is loaded and bypassed
    print("Waiting 12 seconds for potential bypass...")
    page.wait_for_timeout(12000)

    print("Title:", page.title())
    print("URL:", page.url)

    # Let's list some top level anchors
    anchors = page.evaluate("""() => {
        const list = Array.from(document.querySelectorAll('a'));
        return list.map(a => ({
            href: a.href,
            text: a.innerText.trim(),
            html: a.outerHTML.substring(0, 200)
        }));
    }""")

    print(f"Total anchors found: {len(anchors)}")
    for idx, a in enumerate(anchors):
        if len(a['text']) > 5:
            print(f"[{idx}] Text: {repr(a['text'])} | Href: {a['href']}")
            
    browser.close()
except Exception as e:
    print(f"Error: {e}")
