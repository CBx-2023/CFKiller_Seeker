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

    # Recursively find all elements, traversing shadow roots
    res = page.evaluate("""() => {
        const findIframes = (root) => {
            let found = [];
            const walk = (node) => {
                if (!node) return;
                if (node.tagName === 'IFRAME') {
                    found.push({
                        id: node.id,
                        name: node.name,
                        src: node.src,
                        outerHTML: node.outerHTML.substring(0, 300)
                    });
                }
                // Traverse shadow root if exists
                if (node.shadowRoot) {
                    walk(node.shadowRoot);
                }
                // Traverse children
                if (node.children) {
                    for (let child of node.children) {
                        walk(child);
                    }
                }
            };
            walk(root);
            return found;
        };
        return findIframes(document.body);
    }""")
    
    print(f"Traversing Shadow DOM found {len(res)} iframes:")
    for idx, r in enumerate(res):
        print(f"[{idx}] id='{r['id']}', name='{r['name']}', src='{r['src']}'")
        print(f"    HTML: {r['outerHTML']}")
        
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
