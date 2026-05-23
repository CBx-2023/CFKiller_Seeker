import os
import time
import random
import json
import urllib.request
from cloakbrowser import launch

URL = "https://www.spot.ph"
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SAVE_DIR, "scraped_article")
os.makedirs(DATA_DIR, exist_ok=True)

def bezier_curve(x1, y1, x2, y2, steps=15):
    """Generate a simple bezier curve for human-like mouse movement"""
    points = []
    cx = x1 + (x2 - x1) * random.uniform(0.3, 0.7) + random.randint(-50, 50)
    cy = y1 + (y2 - y1) * random.uniform(0.3, 0.7) + random.randint(-50, 50)
    
    for i in range(steps + 1):
        t = i / steps
        x = (1-t)**2 * x1 + 2*(1-t)*t * cx + t**2 * x2
        y = (1-t)**2 * y1 + 2*(1-t)*t * cy + t**2 * y2
        points.append((x, y))
    return points

try:
    browser = launch(headless=False, humanize=True)
    page = browser.new_page()

    print(f"📄 Navigating to {URL} ...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    
    # Wait for Turnstile frame to appear in page.frames
    frame = None
    for i in range(15):
        turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
        if turnstile_frames:
            frame = turnstile_frames[0]
            print(f"[{i}s] Found Turnstile frame: {frame.url}")
            break
        page.wait_for_timeout(1000)

    bypassed = False
    if not frame:
        print("⚠️ Turnstile frame not found. Checking if already bypassed...")
        title = page.title()
        if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
            bypassed = True
    else:
        # Wait for frame element's bounding box to be stable
        print("Waiting for Turnstile frame layout to stabilize...")
        last_box = None
        for i in range(10):
            frame_element = frame.frame_element()
            if frame_element:
                box = frame_element.bounding_box()
                if box:
                    print(f"  [{i}s] Bounding box: {box}")
                    if last_box and box['x'] == last_box['x'] and box['y'] == last_box['y']:
                        print("✅ Layout stabilized!")
                        break
                    last_box = box
            page.wait_for_timeout(1000)
            
        # Wait additional 8 seconds for "Verifying..." -> Checkbox transition
        print("⏳ Waiting 8s for Turnstile checkbox to render...")
        page.wait_for_timeout(8000)
        
        # Get final stable bounding box
        frame_element = frame.frame_element()
        box = frame_element.bounding_box() if frame_element else None
        if not box:
            print("❌ Stable bounding box not found.")
        else:
            target_x = box['x'] + 30
            target_y = box['y'] + 32
            
            start_x = random.randint(100, 500)
            start_y = random.randint(100, 200)
            
            print(f"Moving mouse naturally from ({start_x}, {start_y}) to ({target_x}, {target_y})...")
            page.mouse.move(start_x, start_y)
            page.wait_for_timeout(random.randint(100, 300))
            
            points = bezier_curve(start_x, start_y, target_x, target_y, steps=20)
            for pt_x, pt_y in points:
                page.mouse.move(pt_x, pt_y)
                page.wait_for_timeout(random.randint(10, 30))
                
            page.wait_for_timeout(random.randint(200, 500))
            page.mouse.down()
            page.wait_for_timeout(random.randint(80, 150))
            page.mouse.up()
            
            # Wait and see if title changes
            print("⏳ Waiting for title to change...")
            for k in range(25):
                title = page.title()
                url = page.url
                print(f"  [{k}s] Title: {title} | URL: {url}")
                if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
                    print(f"✅ Bypassed CF! Final Title: {title}")
                    bypassed = True
                    break
                page.wait_for_timeout(1000)

    if bypassed:
        # Wait for the homepage to load anchors
        print("⏳ Waiting for homepage content to load...")
        homepage_loaded = False
        for i in range(20):
            anchors_count = page.locator("a").count()
            print(f"  Homepage check [{i}s]: Found {anchors_count} links. Title: {page.title()}")
            if anchors_count > 10:
                print("✅ Homepage loaded successfully!")
                homepage_loaded = True
                page.wait_for_timeout(5000) # Wait 5s for full homepage rendering
                break
            page.wait_for_timeout(1000)

        if not homepage_loaded:
            print("❌ Homepage content did not load in time.")
        else:
            # Find article links on the homepage
            article_links = page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a'));
                return anchors
                    .map(a => ({ href: a.href, text: a.innerText.trim() }))
                    .filter(item => {
                        if (!item.href || !item.href.includes('spot.ph/')) return false;
                        const path = new URL(item.href).pathname;
                        const segments = path.split('/').filter(Boolean);
                        // Spot.ph article links usually contain a numeric ID segment and a slug
                        return segments.length >= 2 && !isNaN(parseInt(segments[segments.length - 2]));
                    });
            }""")
            
            unique_links = []
            seen = set()
            for item in article_links:
                if item['href'] not in seen:
                    seen.add(item['href'])
                    unique_links.append(item)
                    
            if not unique_links:
                print("⚠️ No numeric ID based article links found. Trying generic filter...")
                fallback_links = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('a'))
                        .map(a => ({ href: a.href, text: a.innerText.trim() }))
                        .filter(item => {
                            if (!item.text || item.text.length < 15) return false;
                            const path = new URL(item.href).pathname;
                            const segments = path.split('/').filter(Boolean);
                            return segments.length >= 2 && 
                                   !item.href.includes('/category/') && 
                                   !item.href.includes('/tag/');
                        });
                }""")
                for item in fallback_links:
                    if item['href'] not in seen:
                        seen.add(item['href'])
                        unique_links.append(item)

            print(f"Total articles found on homepage: {len(unique_links)}")
            if not unique_links:
                print("❌ No article links could be found on the homepage.")
            else:
                # Pick the first descriptive article
                target_article = unique_links[0]
                print(f"\n👉 Target Article chosen: {target_article['text']}")
                print(f"📄 Navigating to article page: {target_article['href']} ...")
                
                page.goto(target_article['href'], timeout=60000, wait_until="domcontentloaded")
                
                # Wait for article page content to load
                print("⏳ Waiting for article page to load and render content...")
                page.wait_for_timeout(8000)
                print(f"Article page title: {page.title()}")
                
                # Scrape content: title, body paragraphs, and image links
                article_data = page.evaluate("""() => {
                    const title = document.querySelector('h1') ? document.querySelector('h1').innerText.trim() : '';
                    
                    // Spot.ph body text paragraphs
                    const paragraphs = Array.from(document.querySelectorAll('p'))
                        .map(p => p.innerText.trim())
                        .filter(txt => txt.length > 30);
                    
                    // Find all main article image elements
                    const imgs = Array.from(document.querySelectorAll('img'))
                        .map(img => img.src)
                        .filter(src => src && (src.includes('.jpg') || src.includes('.png') || src.includes('.jpeg')) && !src.includes('logo'));
                        
                    return {
                        title: title,
                        paragraphs: paragraphs,
                        images: imgs
                    };
                }""")
                
                print("\n📊 Scraped Data Summary:")
                print(f"  Title: {article_data['title']}")
                print(f"  Paragraph count: {len(article_data['paragraphs'])}")
                print(f"  Images count: {len(article_data['images'])}")
                
                # Save scraped details to json file
                article_json_path = os.path.join(DATA_DIR, "article.json")
                with open(article_json_path, "w", encoding="utf-8") as f:
                    json.dump(article_data, f, ensure_ascii=False, indent=4)
                print(f"💾 Saved scraped metadata (JSON) to: {article_json_path}")
                
                # Download top 3 images
                downloaded_imgs = []
                for idx, img_url in enumerate(article_data['images'][:3]):
                    try:
                        img_name = f"image_{idx}.jpg"
                        img_path = os.path.join(DATA_DIR, img_name)
                        print(f"📥 Downloading image {idx}: {img_url} ...")
                        
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Referer': target_article['href']
                        }
                        req = urllib.request.Request(img_url, headers=headers)
                        with urllib.request.urlopen(req, timeout=15) as response:
                            with open(img_path, 'wb') as out_file:
                                out_file.write(response.read())
                        print(f"   Saved image: {img_path}")
                        downloaded_imgs.append(img_path)
                    except Exception as e:
                        print(f"   ⚠️ Error downloading image {idx}: {e}")
                        
                # Capture full-page screenshot of the article page
                screenshot_name = "article_snapshot.png"
                screenshot_path = os.path.join(DATA_DIR, screenshot_name)
                print(f"📸 Capturing full-page article page screenshot to: {screenshot_path} ...")
                
                buf = page.screenshot(full_page=True)
                with open(screenshot_path, "wb") as f:
                    f.write(buf)
                print(f"✅ Successfully captured article snapshot ({len(buf)} bytes)")
                
                # Copy screenshot to the top level flow dir
                top_screenshot_path = os.path.join(SAVE_DIR, "article_snapshot.png")
                with open(top_screenshot_path, "wb") as f:
                    f.write(buf)
                print(f"✅ Copied snapshot to: {top_screenshot_path}")

    browser.close()
    print("🎉 Scraping complete!")
except Exception as e:
    print(f"❌ General Error: {e}")
