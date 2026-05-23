import os
import sys
import time
import random
import json
import urllib.request
import argparse
import shutil
import re
from urllib.parse import urlparse
from cloakbrowser import launch

# ── TARGET SPOT.PH SECTIONS CONFIGURATION ─────────────────────────────────────
SECTIONS = {
    "eatdrink": {
        "name": "Eat + Drink",
        "url": "https://www.spot.ph/eatdrink"
    },
    "things-to-do": {
        "name": "Things To Do",
        "url": "https://www.spot.ph/things-to-do"
    },
    "shopping": {
        "name": "Shopping + Services",
        "url": "https://www.spot.ph/shopping"
    },
    "newsfeatures": {
        "name": "News + Explainer",
        "url": "https://www.spot.ph/newsfeatures"
    },
    "arts-culture": {
        "name": "Latest: Arts + Culture",
        "url": "https://www.spot.ph/arts-culture"
    },
    "entertainment": {
        "name": "Entertainment",
        "url": "https://www.spot.ph/entertainment"
    }
}


class WorkflowContext:
    """Shared state context between different workflow nodes"""
    def __init__(self, section_key, section_url, output_dir, limit, all_articles, delay, save_screenshots, save_images, scroll_limit):
        self.section_key = section_key
        self.section_url = section_url
        self.output_dir = os.path.abspath(output_dir)
        self.limit = limit
        self.all_articles = all_articles
        self.delay = delay
        self.save_screenshots = save_screenshots
        self.save_images = save_images
        self.scroll_limit = scroll_limit
        
        # Internals
        self.browser = None
        self.playwright_context = None
        self.page = None
        
        # Extracted article list: list of dicts with {"title": ..., "url": ...}
        self.article_links = []
        
        # Directories
        self.section_dir = os.path.join(self.output_dir, self.section_key)
        self.tmp_dir = os.path.join(self.output_dir, ".tmp", self.section_key)
        
        os.makedirs(self.section_dir, exist_ok=True)
        os.makedirs(self.tmp_dir, exist_ok=True)
        
    def cleanup(self):
        if self.browser:
            try:
                if self.playwright_context:
                    self.playwright_context.close()
                self.browser.close()
                print("🔒 Browser closed.")
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")
            self.browser = None
            self.playwright_context = None
            self.page = None


class Node:
    """Base class for a Workflow Node"""
    def __init__(self, name, max_retries=3, retry_delay=2):
        self.name = name
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def execute(self, context: WorkflowContext) -> bool:
        raise NotImplementedError


def bezier_curve(x1, y1, x2, y2, steps=15):
    """Helper to generate quadratic bezier curves simulating natural mouse paths"""
    points = []
    cx = x1 + (x2 - x1) * random.uniform(0.3, 0.7) + random.randint(-50, 50)
    cy = y1 + (y2 - y1) * random.uniform(0.3, 0.7) + random.randint(-50, 50)
    
    for i in range(steps + 1):
        t = i / steps
        x = (1-t)**2 * x1 + 2*(1-t)*t * cx + t**2 * x2
        y = (1-t)**2 * y1 + 2*(1-t)*t * cy + t**2 * y2
        points.append((x, y))
    return points


def parse_section_and_subsection(url, main_section_key):
    """Parses URL to find main section and subsection keys"""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    segments = [seg for seg in path.split("/") if seg]
    
    if len(segments) >= 3:
        if segments[0] == main_section_key:
            return segments[0], segments[1]
            
    return main_section_key, None


# ── WORKFLOW NODES IMPLEMENTATION ───────────────────────────────────────────

class LaunchBrowserNode(Node):
    """Node responsible for launching CloakBrowser and opening the initial URL"""
    def __init__(self, headless=False):
        super().__init__("Launch Browser", max_retries=3, retry_delay=3)
        self.headless = headless

    def execute(self, context: WorkflowContext) -> bool:
        if context.browser:
            context.cleanup()
            
        print(f"🚀 Launching CloakBrowser (headless={self.headless})...")
        context.browser = launch(headless=self.headless, humanize=True)
        context.playwright_context = context.browser.new_context()
        context.page = context.playwright_context.new_page()
        
        print(f"Navigating to {context.section_url}...")
        context.page.goto(context.section_url, timeout=60000, wait_until="domcontentloaded")
        return True


class BypassCloudflareNode(Node):
    """Node responsible for detecting and solving Cloudflare Turnstile challenge"""
    def __init__(self):
        super().__init__("Bypass Cloudflare", max_retries=3, retry_delay=4)

    def execute(self, context: WorkflowContext) -> bool:
        page = context.page
        if not page:
            raise ValueError("Browser page not initialized. Run LaunchBrowserNode first.")

        # Ensure page is loaded or reloaded if we are retrying
        title = page.title()
        if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
            print("✅ Already bypassed Cloudflare. Skipping bypass logic.")
            return True

        # Wait for Turnstile frame
        frame = None
        for i in range(15):
            turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
            if turnstile_frames:
                frame = turnstile_frames[0]
                print(f"  Found Turnstile frame: {frame.url}")
                break
            page.wait_for_timeout(1000)

        if not frame:
            print("  ⚠️ Turnstile frame not found. Reloading page...")
            page.reload(wait_until="domcontentloaded")
            return False

        # Stabilize Turnstile frame bounding box
        print("  Stabilizing Turnstile layout...")
        last_box = None
        stabilized = False
        for i in range(10):
            frame_element = frame.frame_element()
            if frame_element:
                box = frame_element.bounding_box()
                if box:
                    if last_box and box['x'] == last_box['x'] and box['y'] == last_box['y']:
                        stabilized = True
                        break
                    last_box = box
            page.wait_for_timeout(1000)

        if not stabilized or not last_box:
            print("  ⚠️ Turnstile frame failed to stabilize.")
            return False

        # Wait for transition from loading to checkbox
        print("  ⏳ Waiting 8s for checkbox transition...")
        page.wait_for_timeout(8000)

        # Coordinate click with Bezier mouse movement
        target_x = last_box['x'] + 30
        target_y = last_box['y'] + 32
        
        start_x = random.randint(100, 500)
        start_y = random.randint(100, 200)
        
        print(f"  鼠标 🖱️ 自然移动到坐标 ({target_x}, {target_y})...")
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
        print("  Click registered.")

        # Wait and verify title changes
        print("  ⏳ Checking if bypass succeeded...")
        for k in range(25):
            title = page.title()
            if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
                print(f"  ✅ Cloudflare Turnstile Bypassed! Title: {title}")
                return True
            page.wait_for_timeout(1000)

        print("  ❌ Verification timed out.")
        return False


class ScrollSectionNode(Node):
    """Simulates scrolling to load lazy-loaded elements on the category page"""
    def __init__(self):
        super().__init__("Scroll Section Page", max_retries=2, retry_delay=3)

    def execute(self, context: WorkflowContext) -> bool:
        page = context.page
        
        print("⏳ Waiting for page to load and stabilize...")
        try:
            page.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception as e:
            print(f"  ⚠️ Wait for domcontentloaded timed out: {e}")
            
        print("⏳ Waiting for article cards to appear on page...")
        cards_found = False
        for i in range(15):
            try:
                count = page.locator(".article-card").count()
                if count > 0:
                    print(f"  ✅ Found {count} article cards initially.")
                    cards_found = True
                    break
            except Exception as e:
                pass
            page.wait_for_timeout(1000)
            
        if not cards_found:
            print("  ❌ No article cards found on the page.")
            return False
            
        print("📜 Starting scrolling simulation to load articles...")
        prev_links_count = 0
        stable_rounds = 0
        
        while True:
            # Extract unique links currently in view
            current_links = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('.article-card a'))
                    .map(a => a.href)
                    .filter(href => href && href.includes('spot.ph/'));
            }""")
            unique_links = list(set(current_links))
            links_count = len(unique_links)
            
            print(f"  Loaded {links_count} article links on category page.")
            
            # Stop early if we are not fetching all and we've already satisfied our limit
            if not context.all_articles and links_count >= context.limit:
                print(f"  ✅ Target limit of {context.limit} links satisfied. Stopping scroll.")
                break
                
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            
            # Re-evaluate count
            next_links = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('.article-card a'))
                    .map(a => a.href)
                    .filter(href => href && href.includes('spot.ph/'));
            }""")
            next_unique = list(set(next_links))
            next_count = len(next_unique)
            
            if next_count == prev_links_count:
                stable_rounds += 1
                print(f"  ⚠️ No new article links loaded (round {stable_rounds}/{context.scroll_limit}).")
                if stable_rounds >= context.scroll_limit:
                    print(f"  ✅ Reached bottom (no new links for {context.scroll_limit} consecutive rounds). Stopping scroll.")
                    break
            else:
                stable_rounds = 0
                prev_links_count = next_count
                
        return True


class ExtractArticleLinksNode(Node):
    """Extracts all article card items from the section page"""
    def __init__(self):
        super().__init__("Extract Article Links", max_retries=2, retry_delay=2)

    def execute(self, context: WorkflowContext) -> bool:
        page = context.page
        
        articles = page.evaluate("""() => {
            const cards = Array.from(document.querySelectorAll('.article-card'));
            return cards.map(card => {
                const a = card.querySelector('a');
                const titleEl = card.querySelector('h2, h3, h4');
                return {
                    title: titleEl ? titleEl.innerText.trim() : '',
                    url: a ? a.href : ''
                };
            }).filter(item => item.url && item.url.includes('spot.ph/'));
        }""")
        
        # Remove duplicates preserving order
        unique_articles = []
        seen_urls = set()
        for art in articles:
            if art['url'] not in seen_urls:
                seen_urls.add(art['url'])
                unique_articles.append(art)
                
        if not unique_articles:
            print("  ❌ No article links could be extracted from page.")
            return False
            
        # Truncate to limit if not fetching all
        if not context.all_articles and len(unique_articles) > context.limit:
            unique_articles = unique_articles[:context.limit]
            
        context.article_links = unique_articles
        print(f"  ✅ Extracted {len(unique_articles)} article links to scrape.")
        return True


class ScrapeArticlesNode(Node):
    """Scrapes individual articles sequentially and buffers results to disk (O(1) memory)"""
    def __init__(self):
        super().__init__("Scrape Articles", max_retries=1, retry_delay=1)

    def execute(self, context: WorkflowContext) -> bool:
        # Close the category list page to free memory
        if context.page:
            try:
                context.page.close()
            except:
                pass
            context.page = None
            
        total_articles = len(context.article_links)
        print(f"🎬 Commencing scraping of {total_articles} articles with O(1) memory buffering...")
        
        for idx, item in enumerate(context.article_links, 1):
            url = item['url']
            title_preview = item['title'][:40]
            print(f"\n  📝 [{idx}/{total_articles}] Scrape: {title_preview}...")
            
            # Check if this article was already scraped in a previous run (resume support)
            tmp_json_path = os.path.join(context.tmp_dir, f"{idx}.json")
            if os.path.exists(tmp_json_path):
                print(f"    ✓ Found cached data at: {tmp_json_path}. Skipping.")
                continue
            
            # Open dynamic page and scrape
            article_page = None
            try:
                article_page = context.playwright_context.new_page()
                article_page.goto(url, timeout=60000, wait_until="domcontentloaded")
                article_page.wait_for_timeout(2000)
                
                # Check for Turnstile on subpage
                title = article_page.title()
                if "just a moment" in title.lower() or "security check" in title.lower() or "performing security verification" in title.lower():
                    print("    ⚠️ Cloudflare Turnstile triggered on article page. Bypassing...")
                    bypass_success = self._bypass_on_page(article_page)
                    if not bypass_success:
                        print("    ❌ Failed to bypass Turnstile on article page.")
                        err_data = {"index": idx, "url": url, "error": "Cloudflare Turnstile bypass failed on article page."}
                        with open(tmp_json_path, "w", encoding="utf-8") as f:
                            json.dump(err_data, f, ensure_ascii=False, indent=4)
                        continue
                        
                # Scrape article contents
                article_data = article_page.evaluate("""() => {
                    const h1 = document.querySelector('h1');
                    const title = h1 ? h1.innerText.trim() : '';
                    
                    const authorEl = document.querySelector('.author, [class*="author"]');
                    const author = authorEl ? authorEl.innerText.trim() : '';
                    
                    const images = [];
                    document.querySelectorAll('img').forEach(img => {
                        const src = img.src || img.getAttribute('data-src') || '';
                        if (src && src.includes('spot.ph') && !src.includes('logo') && !src.includes('icon') && !src.includes('favicon') && !src.includes('ad-')) {
                            if (!images.includes(src)) images.push(src);
                        }
                    });
                    
                    const paragraphs = [];
                    document.querySelectorAll('p').forEach(p => {
                        const t = p.innerText.trim();
                        if (t.length > 20 && !t.includes('cookie') && !t.includes('Subscribe') && !t.includes('Sign up')) {
                            paragraphs.push(t);
                        }
                    });
                    
                    return {
                        title: title,
                        author: author,
                        images: images,
                        paragraphs: paragraphs
                    };
                }""")
                
                # Parse date
                html = article_page.content()
                date_str = ""
                dm = re.search(r'Published on ([A-Z][a-z]+ \d+, \d{4})', html)
                if dm:
                    date_str = dm.group(1)
                    
                if not article_data['title']:
                    article_data['title'] = item['title']
                    
                result = {
                    "index": idx,
                    "title": article_data['title'],
                    "url": url,
                    "date": date_str,
                    "author": article_data['author'],
                    "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "images": article_data['images'],
                    "imageCount": len(article_data['images']),
                    "content": "\n\n".join(article_data['paragraphs']),
                    "paragraphs": len(article_data['paragraphs'])
                }
                
                # Handle Screenshot Capturing
                if context.save_screenshots:
                    article_screenshot_path = os.path.join(context.tmp_dir, f"screenshot_{idx}.png")
                    try:
                        article_page.screenshot(path=article_screenshot_path, full_page=True, timeout=20000)
                        result["screenshot"] = article_screenshot_path
                    except Exception as screenshot_err:
                        print(f"    ⚠️ Screenshot failed: {screenshot_err}")
                        result["screenshot_error"] = str(screenshot_err)
                        
                # Handle Image Downloads
                if context.save_images and article_data['images']:
                    downloaded = []
                    img_subdir = os.path.join(context.tmp_dir, f"images_{idx}")
                    os.makedirs(img_subdir, exist_ok=True)
                    
                    for img_idx, img_url in enumerate(article_data['images'][:3]):
                        try:
                            img_name = f"image_{img_idx}.jpg"
                            img_path = os.path.join(img_subdir, img_name)
                            
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                'Referer': url
                            }
                            req = urllib.request.Request(img_url, headers=headers)
                            with urllib.request.urlopen(req, timeout=10) as response:
                                with open(img_path, 'wb') as out_file:
                                    out_file.write(response.read())
                            downloaded.append(img_path)
                        except Exception as img_err:
                            print(f"      ⚠️ Failed to download image {img_idx}: {img_err}")
                    result["downloaded_images"] = downloaded
                    
                # Save single article buffer to disk immediately
                with open(tmp_json_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
                print(f"    ✓ Success: {len(article_data['paragraphs'])}p, {len(article_data['images'])}img saved.")
                
            except Exception as e:
                print(f"    ❌ Error processing article: {e}")
                err_data = {"index": idx, "url": url, "error": str(e)}
                with open(tmp_json_path, "w", encoding="utf-8") as f:
                    json.dump(err_data, f, ensure_ascii=False, indent=4)
                    
            finally:
                # GC and free page memory O(1)
                if article_page:
                    try:
                        article_page.close()
                    except:
                        pass
                    article_page = None
                time.sleep(context.delay)
                
        return True

    def _bypass_on_page(self, page) -> bool:
        frame = None
        for i in range(10):
            turnstile_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
            if turnstile_frames:
                frame = turnstile_frames[0]
                break
            page.wait_for_timeout(1000)
        if not frame:
            return False
            
        last_box = None
        stabilized = False
        for i in range(10):
            frame_element = frame.frame_element()
            if frame_element:
                box = frame_element.bounding_box()
                if box:
                    if last_box and box['x'] == last_box['x'] and box['y'] == last_box['y']:
                        stabilized = True
                        break
                    last_box = box
            page.wait_for_timeout(1000)
        if not stabilized or not last_box:
            return False
            
        page.wait_for_timeout(4000)
        
        target_x = last_box['x'] + 30
        target_y = last_box['y'] + 32
        start_x = random.randint(100, 500)
        start_y = random.randint(100, 200)
        
        page.mouse.move(start_x, start_y)
        page.wait_for_timeout(random.randint(100, 200))
        points = bezier_curve(start_x, start_y, target_x, target_y, steps=15)
        for pt_x, pt_y in points:
            page.mouse.move(pt_x, pt_y)
            page.wait_for_timeout(random.randint(10, 20))
        page.wait_for_timeout(200)
        page.mouse.down()
        page.wait_for_timeout(random.randint(80, 120))
        page.mouse.up()
        
        for k in range(15):
            title = page.title()
            if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
                return True
            page.wait_for_timeout(1000)
        return False


class SaveDataNode(Node):
    """Reads disk-buffered JSONs, groups by subsection, compiles to final outputs, and cleans up"""
    def __init__(self):
        super().__init__("Save and Group Data", max_retries=1, retry_delay=1)

    def execute(self, context: WorkflowContext) -> bool:
        print("📦 Processing and compiling scraped articles...")
        
        # Load all temporary article files
        articles = []
        if not os.path.exists(context.tmp_dir):
            print("  ❌ No temporary directory found.")
            return False
            
        files = sorted(os.listdir(context.tmp_dir), key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 99999)
        for f in files:
            if f.endswith('.json'):
                file_path = os.path.join(context.tmp_dir, f)
                try:
                    with open(file_path, 'r', encoding='utf-8') as fh:
                        art = json.load(fh)
                        articles.append(art)
                except Exception as e:
                    print(f"  ⚠️ Error loading temp file {f}: {e}")
                    
        if not articles:
            print("  ❌ No articles were scraped successfully.")
            return False
            
        # Group articles by subsection
        grouped = {}
        for art in articles:
            _, sub = parse_section_and_subsection(art['url'], context.section_key)
            key = sub if sub else "others"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(art)
            
        # If there are multiple subsections, or only one subsection which is NOT "others"
        has_subsections = len(grouped) > 1 or "others" not in grouped
        
        dest_base_dir = context.output_dir
        if has_subsections:
            section_dest_dir = os.path.join(dest_base_dir, context.section_key)
            os.makedirs(section_dest_dir, exist_ok=True)
        else:
            section_dest_dir = dest_base_dir
            
        for sub_key, sub_articles in grouped.items():
            success_count = sum(1 for a in sub_articles if "error" not in a)
            fail_count = sum(1 for a in sub_articles if "error" in a)
            
            source_url = context.section_url
            if sub_key != "others" and has_subsections:
                source_url = f"{context.section_url}/{sub_key}"
                
            # Copy screenshots and images to final location
            for art in sub_articles:
                # Handle Screenshot Copy
                if "screenshot" in art and os.path.exists(art['screenshot']):
                    ss_folder = os.path.join(dest_base_dir, context.section_key, "screenshots")
                    os.makedirs(ss_folder, exist_ok=True)
                    new_ss_path = os.path.join(ss_folder, f"article_{art['index']}.png")
                    try:
                        shutil.copy2(art['screenshot'], new_ss_path)
                        art['screenshot'] = os.path.relpath(new_ss_path, dest_base_dir)
                    except Exception as cp_err:
                        print(f"    ⚠️ Failed to copy screenshot: {cp_err}")
                        
                # Handle Images Copy
                if "downloaded_images" in art and art['downloaded_images']:
                    img_folder = os.path.join(dest_base_dir, context.section_key, "images", f"article_{art['index']}")
                    os.makedirs(img_folder, exist_ok=True)
                    new_img_paths = []
                    for local_img_path in art['downloaded_images']:
                        if os.path.exists(local_img_path):
                            img_filename = os.path.basename(local_img_path)
                            new_img_path = os.path.join(img_folder, img_filename)
                            try:
                                shutil.copy2(local_img_path, new_img_path)
                                new_img_paths.append(os.path.relpath(new_img_path, dest_base_dir))
                            except Exception as cp_err:
                                print(f"    ⚠️ Failed to copy image: {cp_err}")
                    art['downloaded_images'] = new_img_paths
                    
            output_data = {
                "source": source_url,
                "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total": len(sub_articles),
                "success": success_count,
                "failed": fail_count,
                "articles": sub_articles
            }
            
            if has_subsections:
                dest_json_path = os.path.join(dest_base_dir, context.section_key, f"{sub_key}.json")
            else:
                dest_json_path = os.path.join(dest_base_dir, f"{context.section_key}.json")
                
            with open(dest_json_path, 'w', encoding='utf-8') as out_f:
                json.dump(output_data, out_f, ensure_ascii=False, indent=4)
                
            print(f"  💾 Saved grouped articles to: {dest_json_path} (count={len(sub_articles)})")
            
        # Cleanup temporary files
        try:
            shutil.rmtree(context.tmp_dir)
            parent_tmp = os.path.dirname(context.tmp_dir)
            if os.path.exists(parent_tmp) and not os.listdir(parent_tmp):
                os.rmdir(parent_tmp)
            print("  🧹 Cleaned up temporary directory.")
        except Exception as clean_err:
            print(f"  ⚠️ Error cleaning up temp dir: {clean_err}")
            
        return True


# ── WORKFLOW ENGINE ──────────────────────────────────────────────────────────

class WorkflowRunner:
    """Engine that executes sequential workflow nodes with built-in retry-on-failure logic"""
    def __init__(self, context: WorkflowContext):
        self.context = context
        self.nodes = []

    def add_node(self, node: Node):
        self.nodes.append(node)

    def run(self) -> bool:
        print("\n🏁 Starting Node-Based Scraper Workflow...")
        for node in self.nodes:
            print(f"\n" + "="*60)
            print(f"🎬 Running Node: {node.name}")
            print("="*60)
            
            success = False
            for attempt in range(1, node.max_retries + 1):
                print(f"  [Attempt {attempt}/{node.max_retries}] Executing node tasks...")
                try:
                    res = node.execute(self.context)
                    if res:
                        success = True
                        break
                    else:
                        print(f"  ⚠️ Node returned failure status.")
                except Exception as e:
                    print(f"  ❌ Node execution failed with error: {e}")
                
                if attempt < node.max_retries:
                    print(f"  ⏳ Waiting {node.retry_delay}s before retrying...")
                    time.sleep(node.retry_delay)
                    
            if not success:
                print(f"\n💀 Node '{node.name}' failed after {node.max_retries} attempts.")
                print("🚫 Aborting workflow execution.")
                return False
                
        print("\n" + "="*60)
        print("🎉 Workflow completed successfully!")
        print("="*60)
        return True


# ── CLI MAIN ENTRY ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CFK (Cloudflare-Turnstile Bypassing Scraper)")
    parser.add_argument("section", nargs="?", default="all", choices=list(SECTIONS.keys()) + ["all"],
                        help="Target section to scrape (choices: %(choices)s, default: all)")
    parser.add_argument("--limit", type=int, default=10, help="Max articles to scrape per section (ignored if --all is set, default: 10)")
    parser.add_argument("--all", action="store_true", help="Scrape all available articles in the section (ignores --limit)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (default: False)")
    parser.add_argument("--output", type=str, default="scraped_data", help="Output base directory (default: scraped_data)")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay in seconds between article requests (default: 2.0)")
    parser.add_argument("--no-screenshots", action="store_true", help="Disable article full-page screenshot capturing")
    parser.add_argument("--no-images", action="store_true", help="Disable downloading article images")
    parser.add_argument("--scroll-limit", type=int, default=3, help="Rounds to scroll without new links before stopping when --all is set (default: 3)")
    
    args = parser.parse_args()
    
    if args.section == "all":
        target_keys = list(SECTIONS.keys())
    else:
        target_keys = [args.section]
        
    for key in target_keys:
        print(f"\n============================================================")
        print(f"🌟 Starting Scraper for Section: {SECTIONS[key]['name']}")
        print(f"============================================================")
        
        context = WorkflowContext(
            section_key=key,
            section_url=SECTIONS[key]['url'],
            output_dir=args.output,
            limit=0 if args.all else args.limit,
            all_articles=args.all,
            delay=args.delay,
            save_screenshots=not args.no_screenshots,
            save_images=not args.no_images,
            scroll_limit=args.scroll_limit
        )
        
        runner = WorkflowRunner(context)
        runner.add_node(LaunchBrowserNode(headless=args.headless))
        runner.add_node(BypassCloudflareNode())
        runner.add_node(ScrollSectionNode())
        runner.add_node(ExtractArticleLinksNode())
        runner.add_node(ScrapeArticlesNode())
        runner.add_node(SaveDataNode())
        
        try:
            success = runner.run()
            if not success:
                print(f"❌ Scraper for section {key} failed.")
        finally:
            context.cleanup()


if __name__ == "__main__":
    main()
