import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    # Wait for Turnstile frame to load (URL containing challenges.cloudflare.com)
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
        # Let's wait a few seconds for the frame contents to load/render
        page.wait_for_timeout(5000)
        
        # Traverse the frame's DOM, including shadow roots of all elements inside it!
        shadow_elements = frame.evaluate("""() => {
            let found = [];
            const walk = (node, path) => {
                if (!node) return;
                
                let nodeDesc = node.tagName || node.nodeName;
                if (node.id) nodeDesc += '#' + node.id;
                if (node.className) nodeDesc += '.' + node.className.replace(/\\s+/g, '.');
                
                // Collect info
                found.push({
                    path: path + ' -> ' + nodeDesc,
                    tagName: node.tagName,
                    id: node.id,
                    className: node.className,
                    innerText: node.innerText,
                    outerHTML: node.outerHTML ? node.outerHTML.substring(0, 300) : ''
                });
                
                // Traverse shadow root
                if (node.shadowRoot) {
                    walk(node.shadowRoot, path + ' -> ' + nodeDesc + ' -> #shadow-root');
                }
                
                // Traverse child nodes
                if (node.childNodes) {
                    for (let i = 0; i < node.childNodes.length; i++) {
                        walk(node.childNodes[i], path + ' -> ' + nodeDesc);
                    }
                }
            };
            walk(document.documentElement, 'HTML');
            return found;
        }""")
        
        print(f"Found {len(shadow_elements)} elements inside Turnstile frame:")
        for idx, el in enumerate(shadow_elements):
            if el['tagName'] in ['STYLE', 'SCRIPT', 'META', 'LINK', 'HEAD']:
                continue
            # If the element has outerHTML or text or a checkbox
            print(f"[{idx}] Path: {el['path']}")
            print(f"    HTML: {el['outerHTML']}")
            print(f"    Text: {repr(el['innerText'])}")
            print("-" * 60)
            
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
