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
    # Control point for bezier curve
    cx = x1 + (x2 - x1) * random.uniform(0.3, 0.7) + random.randint(-50, 50)
    cy = y1 + (y2 - y1) * random.uniform(0.3, 0.7) + random.randint(-50, 50)
    
    for i in range(steps + 1):
        t = i / steps
        # Quadratic bezier formula
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
        page.wait_for_timeout(4000) # Wait for widget to load and show "Verify you are human"
        
        frame_element = frame.frame_element()
        if not frame_element:
            print("❌ frame_element is None.")
        else:
            box = frame_element.bounding_box()
            if not box:
                print("❌ Bounding box of frame element is None.")
            else:
                print(f"Frame bounding box: {box}")
                
                # Checkbox center is roughly (x + 30, y + 32)
                target_x = box['x'] + 30
                target_y = box['y'] + 32
                
                # Start mouse from a random position
                start_x = random.randint(100, 500)
                start_y = random.randint(100, 200)
                
                print(f"Moving mouse naturally from ({start_x}, {start_y}) to ({target_x}, {target_y})...")
                page.mouse.move(start_x, start_y)
                page.wait_for_timeout(random.randint(100, 300))
                
                # Generate bezier path points
                points = bezier_curve(start_x, start_y, target_x, target_y, steps=20)
                for pt_x, pt_y in points:
                    page.mouse.move(pt_x, pt_y)
                    page.wait_for_timeout(random.randint(10, 30))
                    
                page.wait_for_timeout(random.randint(200, 500)) # Hover briefly
                
                print("Sending mouse down and up...")
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
            print(f"  [{i}s] Found {anchors_count} links on the page. Title: {page.title()}")
            if anchors_count > 10:
                print("✅ Homepage loaded successfully!")
                homepage_loaded = True
                page.wait_for_timeout(3000) # Wait extra 3s for rendering
                break
            page.wait_for_timeout(1000)

        if not homepage_loaded:
            print("❌ Homepage did not load links in time.")
        else:
            # Let's find all article links on the homepage
            article_links = page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a'));
                return anchors
                    .map(a => ({ href: a.href, text: a.innerText.trim() }))
                    .filter(item => {
                        if (!item.href || !item.href.includes('spot.ph/')) return false;
                        // Spot.ph article links usually have sections like /news-features/, /food-drink/, /shopping-beauty/, etc.
                        // and they end with a post name, not category pages or homepage
                        const path = new URL(item.href).pathname;
                        const segments = path.split('/').filter(Boolean);
                        // Article URLs typically have category/subcategory/slug or category/slug
                        // e.g. /news-features/news-features/109015/nicolas-cage-spider-noir
                        return segments.length >= 2 && !isNaN(parseInt(segments[segments.length - 2]));
                    });
            }""")
            
            # Deduplicate
            unique_links = []
            seen = set()
            for item in article_links:
                if item['href'] not in seen:
                    seen.add(item['href'])
                    unique_links.append(item)
                    
            print(f"Found {len(unique_links)} potential article links on homepage.")
            for idx, item in enumerate(unique_links[:10]):
                print(f"  [{idx}] {item['text']} -> {item['href']}")
                
            if not unique_links:
                print("⚠️ No numeric ID based article links found. Falling back to generic filter...")
                # Let's list some anchors and filter manually
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
                print(f"Total article links after fallback: {len(unique_links)}")
                for idx, item in enumerate(unique_links[:10]):
                    print(f"  [{idx}] {item['text']} -> {item['href']}")

            if not unique_links:
                print("❌ Still no article links found. Saving homepage screenshot.")
                screenshot_path = os.path.join(SAVE_DIR, "homepage_failed_links.png")
                page.screenshot(path=screenshot_path)
            else:
                # Pick the first article link
                target_article = unique_links[0]
                print(f"\n👉 Target Article chosen: {target_article['text']}")
                print(f"📄 Navigating to article page: {target_article['href']} ...")
                
                page.goto(target_article['href'], timeout=60000, wait_until="domcontentloaded")
                
                # Wait for article page content to load
                page.wait_for_timeout(5000)
                print(f"Article page title: {page.title()}")
                
                # Scrape article title, text paragraphs and image URLs
                article_data = page.evaluate("""() => {
                    const title = document.querySelector('h1') ? document.querySelector('h1').innerText.trim() : '';
                    
                    // Paragraph content
                    const paragraphs = Array.from(document.querySelectorAll('p'))
                        .map(p => p.innerText.trim())
                        .filter(txt => txt.length > 30);
                    
                    // Find images
                    const imgs = Array.from(document.querySelectorAll('img'))
                        .map(img => img.src)
                        .filter(src => src && (src.includes('.jpg') || src.includes('.png') || src.includes('.jpeg')) && !src.includes('logo'));
                        
                    return {
                        title: title,
                        paragraphs: paragraphs,
                        images: imgs
                    };
                }""")
                
                print(f"Scraped details:")
                print(f"  Title: {article_data['title']}")
                print(f"  Paragraph count: {len(article_data['paragraphs'])}")
                print(f"  Image count: {len(article_data['images'])}")
                
                # Save scraped text data
                article_json_path = os.path.join(DATA_DIR, "article.json")
                with open(article_json_path, "w", encoding="utf-8") as f:
                    json.dump(article_data, f, ensure_ascii=False, indent=4)
                print(f"💾 Saved article details (JSON) to: {article_json_path}")
                
                # Download images using urllib (unsandboxed)
                downloaded_imgs = []
                for idx, img_url in enumerate(article_data['images'][:3]): # Limit to top 3 images
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
                        
                # Capture full page screenshot of the article page
                screenshot_name = "article_snapshot.png"
                screenshot_path = os.path.join(DATA_DIR, screenshot_name)
                print(f"📸 Capturing article page screenshot to: {screenshot_path} ...")
                
                # Save page screenshot
                buf = page.screenshot(full_page=True)
                with open(screenshot_path, "wb") as f:
                    f.write(buf)
                print(f"✅ Successfully captured article snapshot ({len(buf)} bytes)")
                
                # Copy to top level flow dir
                top_screenshot_path = os.path.join(SAVE_DIR, "article_snapshot.png")
                with open(top_screenshot_path, "wb") as f:
                    f.write(buf)
                print(f"✅ Copied snapshot to top level: {top_screenshot_path}")

    browser.close()
    print("🎉 Scraping complete!")
except Exception as e:
    print(f"❌ General Error: {e}")
