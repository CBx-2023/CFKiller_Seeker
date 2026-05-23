import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(10000) # Wait 10s for Turnstile to fully load

    # Walk the entire main page DOM, including shadow roots, and find any visible text or inputs
    elements = page.evaluate("""() => {
        let found = [];
        const walk = (node, path) => {
            if (!node) return;
            
            let nodeDesc = node.tagName || node.nodeName;
            if (node.id) nodeDesc += '#' + node.id;
            if (node.className) nodeDesc += '.' + node.className.replace(/\\s+/g, '.');
            
            // Check if it's an iframe, input, or has innerText
            const hasText = node.innerText && node.innerText.trim().length > 0;
            const isIframe = node.tagName === 'IFRAME';
            const isInput = node.tagName === 'INPUT';
            
            if (isIframe || isInput || hasText) {
                found.push({
                    path: path + ' -> ' + nodeDesc,
                    tagName: node.tagName,
                    id: node.id,
                    className: node.className,
                    innerText: isIframe ? '' : (node.innerText ? node.innerText.substring(0, 100) : ''),
                    src: node.src || ''
                });
            }
            
            // Traverse shadow root
            if (node.shadowRoot) {
                walk(node.shadowRoot, path + ' -> ' + nodeDesc + ' -> #shadow-root');
            }
            
            // Traverse children
            if (node.childNodes) {
                for (let child of node.childNodes) {
                    walk(child, path + ' -> ' + nodeDesc);
                }
            }
        };
        walk(document.documentElement, 'HTML');
        return found;
    }""")
    
    print(f"Found {len(elements)} interesting elements in main page:")
    for idx, el in enumerate(elements):
        print(f"[{idx}] Path: {el['path']}")
        print(f"    Tag: {el['tagName']} | ID: {el['id']} | Class: {el['className']}")
        if el['src']:
            print(f"    Src: {el['src']}")
        if el['innerText']:
            print(f"    Text: {repr(el['innerText'])}")
        print("-" * 60)
        
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
