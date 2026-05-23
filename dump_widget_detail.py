import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(10000)

    # Dump the exact outerHTML of `#GZIfP3`
    outer_html = page.locator("#GZIfP3").evaluate("el => el.outerHTML")
    print("Outer HTML of #GZIfP3:")
    print(outer_html)
    
    # Check if there is any shadow root under #GZIfP3 or its children
    shadow_info = page.evaluate("""() => {
        const getShadows = (el, path) => {
            let res = [];
            if (el.shadowRoot) {
                res.push({
                    path: path + ' -> #shadow-root',
                    innerHTML: el.shadowRoot.innerHTML
                });
                res = res.concat(getShadows(el.shadowRoot, path + ' -> #shadow-root'));
            }
            for (let child of el.children || []) {
                let name = child.tagName;
                if (child.id) name += '#' + child.id;
                res = res.concat(getShadows(child, path + ' -> ' + name));
            }
            return res;
        };
        const root = document.querySelector('#GZIfP3');
        return root ? getShadows(root, '#GZIfP3') : 'Not found';
    }""")
    print("Shadow roots under #GZIfP3:")
    print(shadow_info)

    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
