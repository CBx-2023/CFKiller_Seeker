import os
import time
from cloakbrowser import launch

URL = "https://www.spot.ph"

try:
    browser = launch(headless=True, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    # Wait for Turnstile frame to appear in page.frames
    frame = None
    for i in range(15):
        turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
        if turnstile_frames:
            frame = turnstile_frames[0]
            print(f"Found Turnstile frame: {frame.url}")
            break
        page.wait_for_timeout(1000)

    if not frame:
        print("❌ Turnstile frame not found.")
    else:
        frame_element = frame.frame_element()
        if not frame_element:
            print("❌ frame_element is None.")
        else:
            # Let's inspect the frame element inside the parent document context!
            info = page.evaluate("""(el) => {
                const getPath = (node) => {
                    let path = [];
                    while (node) {
                        let name = node.tagName || node.nodeName;
                        if (node.id) name += '#' + node.id;
                        if (node.className) name += '.' + node.className.replace(/\\s+/g, '.');
                        path.unshift(name);
                        node = node.parentNode || node.host; // Traverse up parent or shadow host
                    }
                    return path.join(' -> ');
                };
                return {
                    tagName: el.tagName,
                    id: el.id,
                    className: el.className,
                    src: el.src || '',
                    parentTag: el.parentElement ? el.parentElement.tagName : 'None',
                    path: getPath(el),
                    outerHTML: el.outerHTML.substring(0, 500)
                };
            }""", frame_element)
            
            print("Frame Element Info:")
            for k, v in info.items():
                print(f"  {k}: {v}")
                
    browser.close()
except Exception as e:
    print(f"❌ Error: {e}")
