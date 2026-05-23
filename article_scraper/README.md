# 🕷️ Cloudflare-Turnstile Bypassing Node-Based Scraper

A robust, modular Web Scraper built to bypass Cloudflare Turnstile challenges and scrape complete articles (including text contents, metadata, images, and full-page screenshots) in both **headed** (`headless=False`) and **headless** (`headless=True`) modes.

---

## 🏗️ Architecture Design

The scraper is designed using a **Node-Based Step Architecture** (inspired by projects like `GuJumpgate`). 

Each step in the crawling process is encapsulated in a discrete `Node` class. The steps are managed by a centralized `WorkflowRunner` engine that executes them sequentially, passing a shared `WorkflowContext`.

### Features
* **Node Autonomy**: Nodes only worry about their specific task (e.g., bypassing Cloudflare, downloading images).
* **Automatic Retry & Recovery**: If a node fails (due to transient network timeouts, rendering lags, or Turnstile timing shifts), the `WorkflowRunner` automatically retries execution up to `max_retries` with a `retry_delay` before aborting.
* **State Preservation**: The `WorkflowContext` carries state (like page references, target URLs, and scraped text data) across nodes.

---

## 📋 Scraper Workflow Steps

The workflow executes 8 distinct nodes in sequence:

1. **Launch Browser**: Launches the `CloakBrowser` instance (with Stealth and Humanize modules) and navigates to the target site.
2. **Bypass Cloudflare**: Detects the Turnstile iframe hidden in the closed Shadow DOM, waits for its layout coordinates to stabilize, waits for the checkbox transition, moves the mouse along a natural quadratic **Bezier path**, and clicks the checkbox with human-like duration.
3. **Load Homepage**: Confirms the site's main content is fully loaded and links are ready.
4. **Extract Article Links**: Extracts unique article URLs from the homepage.
5. **Navigate To Article**: Navigates to the selected target article page.
6. **Scrape Content**: Extracts the article title, body paragraphs, and image source URLs, saving them as a structured JSON file.
7. **Download Images**: Downloads the top three images of the article to the output directory.
8. **Capture Snapshot**: Takes a full-height high-resolution PNG screenshot of the final scraped page.

---

## 🛠️ Prerequisites & Setup

### 1. Python Environment
This project runs on Python 3.8+.
Ensure you have the virtual environment activated:
```bash
source .venv/bin/activate
```

### 2. Dependencies
Ensure you have `playwright` and `cloakbrowser` installed. (If you initialized the parent workspace using `uv`, they are already present in the virtual environment).

To initialize or check Playwright browser binaries:
```bash
playwright install chromium
```

---

## 🚀 Running the Scraper

The scraper script `scraper.py` is configured with argparse to allow customization:

### 1. Headed Mode (False mode)
Runs with a visible browser window. This is useful for debugging and visual monitoring:
```bash
python scraper.py --headless
# or simply
python scraper.py
```
*(By default, `--headless` is False if omitted, triggering headed mode).*

### 2. Headless Mode (True mode)
Runs in pure headless mode. This is designed for headless servers (e.g., CLI-only Linux machines) without needing virtual framebuffers (like Xvfb):
```bash
python scraper.py --headless
```

### 3. Customized Arguments
You can specify a different target URL or output folder:
```bash
python scraper.py --headless --url "https://www.spot.ph" --output "my_scraped_article"
```

---

## 📂 Output Structure

All outputs are saved to the specified `--output` directory (defaulting to `scraped_data/`):
```text
scraped_data/
├── article.json             # Scraped Title, paragraph text list, and image URLs
├── article_snapshot.png     # Full-page high-resolution screenshot
├── image_0.jpg              # Downloaded top image 1
├── image_1.jpg              # Downloaded top image 2
└── image_2.jpg              # Downloaded top image 3
```
