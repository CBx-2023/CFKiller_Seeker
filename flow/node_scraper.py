import os
import time
import random
import json
import urllib.request
import math
from cloakbrowser import launch

URL = "https://www.spot.ph"
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SAVE_DIR, "scraped_article")
os.makedirs(DATA_DIR, exist_ok=True)

class WorkflowContext:
    """Shared state context between different workflow nodes"""
    def __init__(self):
        self.browser = None
        self.page = None
        self.bypassed = False
        self.homepage_loaded = False
        self.article_links = []
        self.target_article = None
        self.scraped_data = None
        self.downloaded_images = []
        self.snapshot_path = None

    def cleanup(self):
        """Ensure browser resources are cleaned up"""
        if self.browser:
            try:
                self.browser.close()
                print("🔒 Browser closed successfully.")
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")
            self.browser = None
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


# ── WORKFLOW NODES IMPLEMENTATION ───────────────────────────────────────────

class LaunchBrowserNode(Node):
    """Node responsible for launching CloakBrowser and opening the initial URL"""
    def __init__(self):
        super().__init__("Launch Browser", max_retries=3, retry_delay=3)

    def execute(self, context: WorkflowContext) -> bool:
        if context.browser:
            context.cleanup()
            
        print(f"🚀 Launching CloakBrowser and navigating to {URL}...")
        context.browser = launch(headless=False, humanize=True)
        context.page = context.browser.new_page()
        
        # Initial navigation
        context.page.goto(URL, timeout=60000, wait_until="domcontentloaded")
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
        for i in range(10):
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
        
        print(f"  🖱️ Moving mouse naturally to ({target_x}, {target_y})...")
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
        for k in range(20):
            title = page.title()
            if "just a moment" not in title.lower() and "security check" not in title.lower() and "performing security verification" not in title.lower():
                print(f"  ✅ Cloudflare Turnstile Bypassed! Title: {title}")
                return True
            page.wait_for_timeout(1000)

        print("  ❌ Verification timed out.")
        return False


class LoadHomepageNode(Node):
    """Node that waits for the homepage contents to be rendered"""
    def __init__(self):
        super().__init__("Load Homepage", max_retries=3, retry_delay=2)

    def execute(self, context: WorkflowContext) -> bool:
        page = context.page
        print("⏳ Waiting for homepage content links to load...")
        for i in range(15):
            anchors_count = page.locator("a").count()
            if anchors_count > 10:
                print(f"  ✅ Homepage loaded! Found {anchors_count} links.")
                page.wait_for_timeout(3000) # extra wait for full rendering
                return True
            page.wait_for_timeout(1000)
        
        print("  ❌ Homepage content failed to load.")
        return False


class ExtractArticleLinksNode(Node):
    """Node that extracts article links from the homepage"""
    def __init__(self):
        super().__init__("Extract Article Links", max_retries=2, retry_delay=1)

    def execute(self, context: WorkflowContext) -> bool:
        page = context.page
        article_links = page.evaluate("""() => {
            const anchors = Array.from(document.querySelectorAll('a'));
            return anchors
                .map(a => ({ href: a.href, text: a.innerText.trim() }))
                .filter(item => {
                    if (!item.href || !item.href.includes('spot.ph/')) return false;
                    const path = new URL(item.href).pathname;
                    const segments = path.split('/').filter(Boolean);
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
            print("  ⚠️ No ID-based articles. Trying fallback filter...")
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

        if not unique_links:
            print("  ❌ No article links found.")
            return False
            
        context.article_links = unique_links
        context.target_article = unique_links[0]
        print(f"  ✅ Extracted {len(unique_links)} article links. Chosen target: {context.target_article['text']}")
        return True


class NavigateToArticleNode(Node):
    """Node that navigates to the chosen article URL"""
    def __init__(self):
        super().__init__("Navigate To Article", max_retries=3, retry_delay=3)

    def execute(self, context: WorkflowContext) -> bool:
        page = context.page
        target = context.target_article
        if not target:
            raise ValueError("No target article chosen. Run ExtractArticleLinksNode first.")
            
        print(f"📄 Navigating to: {target['href']} ...")
        page.goto(target['href'], timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(8000) # wait for render
        print(f"  ✅ Navigated. Article page title: {page.title()}")
        return True


class ScrapeArticleContentNode(Node):
    """Node that scrapes article text contents and metadata"""
    def __init__(self):
        super().__init__("Scrape Content", max_retries=2, retry_delay=2)

    def execute(self, context: WorkflowContext) -> bool:
        page = context.page
        
        article_data = page.evaluate("""() => {
            const title = document.querySelector('h1') ? document.querySelector('h1').innerText.trim() : '';
            const paragraphs = Array.from(document.querySelectorAll('p'))
                .map(p => p.innerText.trim())
                .filter(txt => txt.length > 30);
            const imgs = Array.from(document.querySelectorAll('img'))
                .map(img => img.src)
                .filter(src => src && (src.includes('.jpg') || src.includes('.png') || src.includes('.jpeg')) && !src.includes('logo'));
                
            return {
                title: title,
                paragraphs: paragraphs,
                images: imgs
            };
        }""")
        
        if not article_data['title'] or not article_data['paragraphs']:
            print("  ❌ Scraped content is empty (missing title or body paragraphs).")
            return False
            
        context.scraped_data = article_data
        
        # Save details to json file
        article_json_path = os.path.join(DATA_DIR, "article.json")
        with open(article_json_path, "w", encoding="utf-8") as f:
            json.dump(article_data, f, ensure_ascii=False, indent=4)
            
        print(f"  ✅ Scraped successfully! Title: {article_data['title']}")
        print(f"  💾 Saved JSON details to: {article_json_path}")
        return True


class DownloadImagesNode(Node):
    """Node that downloads images associated with the article"""
    def __init__(self):
        super().__init__("Download Images", max_retries=2, retry_delay=2)

    def execute(self, context: WorkflowContext) -> bool:
        data = context.scraped_data
        target = context.target_article
        if not data:
            raise ValueError("No scraped data available. Run ScrapeArticleContentNode first.")
            
        print(f"📥 Downloading top images (count={len(data['images'])})...")
        downloaded = []
        for idx, img_url in enumerate(data['images'][:3]):
            try:
                img_name = f"image_{idx}.jpg"
                img_path = os.path.join(DATA_DIR, img_name)
                print(f"  Downloading image {idx}: {img_url} ...")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': target['href']
                }
                req = urllib.request.Request(img_url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response:
                    with open(img_path, 'wb') as out_file:
                        out_file.write(response.read())
                print(f"    Saved image: {img_path}")
                downloaded.append(img_path)
            except Exception as e:
                print(f"    ⚠️ Error downloading image {idx}: {e}")
                
        context.downloaded_images = downloaded
        return True


class CaptureSnapshotNode(Node):
    """Node that captures full page snapshot of the article page"""
    def __init__(self):
        super().__init__("Capture Snapshot", max_retries=2, retry_delay=2)

    def execute(self, context: WorkflowContext) -> bool:
        page = context.page
        snapshot_path = os.path.join(DATA_DIR, "article_snapshot.png")
        print(f"📸 Capturing full-page snapshot to: {snapshot_path}...")
        
        buf = page.screenshot(full_page=True)
        with open(snapshot_path, "wb") as f:
            f.write(buf)
            
        # Copy to top level flow dir
        top_screenshot_path = os.path.join(SAVE_DIR, "article_snapshot.png")
        with open(top_screenshot_path, "wb") as f:
            f.write(buf)
            
        context.snapshot_path = snapshot_path
        print(f"  ✅ Saved snapshot ({len(buf)} bytes) to: {top_screenshot_path}")
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
                
                # If attempt failed, wait and retry
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


# ── MAIN EXECUTION ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    context = WorkflowContext()
    runner = WorkflowRunner(context)
    
    # Register workflow nodes sequentially
    runner.add_node(LaunchBrowserNode())
    runner.add_node(BypassCloudflareNode())
    runner.add_node(LoadHomepageNode())
    runner.add_node(ExtractArticleLinksNode())
    runner.add_node(NavigateToArticleNode())
    runner.add_node(ScrapeArticleContentNode())
    runner.add_node(DownloadImagesNode())
    runner.add_node(CaptureSnapshotNode())
    
    try:
        success = runner.run()
        if not success:
            exit(1)
    finally:
        context.cleanup()
