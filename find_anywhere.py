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

    # Let's search all nodes starting from document.documentElement
    res = page.evaluate("""() => {
        let found = [];
        const walk = (node, path) => {
            if (!node) return;
            
            // Check if node is an iframe
            if (node.tagName === 'IFRAME') {
                found.push({
                    path: path,
                    id: node.id,
                    name: node.name,
                    src: node.src,
                    outerHTML: node.outerHTML.substring(0, 300)
                });
            }
            
            // Traverse shadow root
            if (node.shadowRoot) {
                walk(node.shadowRoot, path + ' -> #shadow-root');
            }
            
            // Traverse children
            if (node.childNodes) {
                for (let i = 0; i < node.childNodes.length; i++) {
                    const child = node.childNodes[i];
                    let childName = child.tagName || child.nodeName;
                    if (child.id) childName += '#' + child.id;
                    walk(child, path + ' -> ' + childName);
                }
            }
        };
        walk(document.documentElement, 'HTML');
        return found;
    }""")
    
    print(f"Found {len(res)} iframes:")
    for idx, r in enumerate(res):
        print(f"[{idx}] Path: {r['path']}")
        print(f"    id='{r['id']}', name='{r['name']}', src='{r['src']}'")
        print(f"    HTML: {r['outerHTML']}")
        
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
