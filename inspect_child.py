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

    # Dump the inner content of the single child inside #GZIfP3
    child_info = page.evaluate("""() => {
        const wrapper = document.querySelector('#GZIfP3');
        if (!wrapper) return 'Wrapper #GZIfP3 not found';
        const children = Array.from(wrapper.children);
        return children.map((child, idx) => {
            let info = `Child ${idx}: tagName=${child.tagName}, id='${child.id}', class='${child.className}'`;
            info += `\\n  outerHTML: ${child.outerHTML.substring(0, 300)}`;
            // Check for shadow root
            if (child.shadowRoot) {
                info += `\\n  shadowRoot detected! innerHTML: ${child.shadowRoot.innerHTML}`;
            }
            return info;
        }).join('\\n\\n');
    }""")
    
    print(child_info)
        
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
