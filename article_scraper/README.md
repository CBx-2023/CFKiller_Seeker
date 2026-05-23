# 🕷️ CFK: Cloudflare-Turnstile Bypassing Node-Based Scraper

A robust, modular Web Scraper and CLI tool built to bypass Cloudflare Turnstile challenges and scrape complete articles (including text contents, metadata, images, and full-page screenshots) in both **headed** (`headless=False`) and **headless** (`headless=True`) modes across all Spot.ph sections.

---

## 🏗️ Architecture Design

The scraper is designed using a **Node-Based Step Architecture** (inspired by projects like `GuJumpgate`). 

Each step in the crawling process is encapsulated in a discrete `Node` class. The steps are managed by a centralized `WorkflowRunner` engine that executes them sequentially, passing a shared `WorkflowContext`.

### Key Features
* **Node Autonomy**: Nodes only worry about their specific task (e.g., bypassing Cloudflare, downloading images).
* **Automatic Retry & Recovery**: If a node fails (due to transient network timeouts, rendering lags, or Turnstile timing shifts), the `WorkflowRunner` automatically retries execution up to `max_retries` with a `retry_delay` before aborting.
* **On-the-Fly Disk Buffering (O(1) Memory footprint)**: To prevent memory leaks and browser crashes during large scrapes, articles are written directly to disk under a `.tmp/` folder immediately upon scraping. The Playwright page and DOM memory are closed and garbage-collected after each article.
* **Resilience & Resume**: If interrupted, articles already scraped are cached on disk, allowing the scraper to resume and skip already processed articles in subsequent runs.

---

## 📋 Scraper Workflow Steps

The workflow executes 6 distinct nodes in sequence:

1. **Launch Browser**: Launches the `CloakBrowser` instance (with Stealth and Humanize modules) and initializes a unified `BrowserContext`.
2. **Bypass Cloudflare**: Detects the Turnstile iframe hidden in the closed Shadow DOM on the section home page, waits for its layout coordinates to stabilize, waits for the checkbox transition, moves the mouse along a natural quadratic **Bezier path**, and clicks the checkbox with human-like duration.
3. **Scroll Section Page**: Simulates page scrolling to load lazy-loaded content.
   * If `--all` is set: Scrolls to the bottom, waits for content to load, and compares article counts. If no new article links are found after scrolling **3 consecutive times**, scrolling stops.
   * If `--all` is not set: Stops scrolling as soon as the loaded article link count satisfies the `--limit`.
4. **Extract Article Links**: Extracts unique article URLs and titles from the page.
5. **Scrape Articles**: Navigates to each article page within the same `BrowserContext` (reusing cookies to bypass Turnstile without re-triggering), extracts contents, downloads up to 3 images, takes full-page screenshots, and buffers data to disk.
6. **Save and Group Data**: Compiles temporary buffers, groups articles by their subsection, moves screenshots/images to their final location, outputs structured JSONs, and cleans up the temporary directory.

---

## 🛠️ Prerequisites & Setup

### 1. Python Environment
This project runs on Python 3.8+.
Ensure you have the virtual environment activated:
```bash
source .venv/bin/activate
```

### 2. Dependencies
Ensure you have `playwright` and `cloakbrowser` installed.

To initialize or check Playwright browser binaries:
```bash
playwright install chromium
```

---

## 🚀 Running the Scraper via CLI

The CLI tool `cfk` is packaged and linked inside `.venv/bin/cfk`. When the virtual environment is active, you can call it directly:

```bash
cfk [section] [options]
```

### 1. Positional Arguments
* `section`: The target Spot.ph section to scrape.
  * Choices: `eatdrink`, `things-to-do`, `shopping`, `newsfeatures`, `arts-culture`, `entertainment`, or `all` (scrapes all sections sequentially).
  * Default: `all`.

### 2. Options
* `--all`: Scrape all available articles in the section (ignores `--limit`).
* `--limit LIMIT`: Max articles to scrape per section (ignored if `--all` is set, default: `10`).
* `--headless`: Run browser in headless mode (default: False).
* `--output OUTPUT`: Output base directory (default: `scraped_data`).
* `--delay DELAY`: Delay in seconds between article requests to avoid rate limits (default: `2.0`).
* `--no-screenshots`: Disable capturing full-page screenshots of articles.
* `--no-images`: Disable downloading article images.
* `--scroll-limit SCROLL_LIMIT`: Rounds to scroll to bottom without new links before stopping when `--all` is set (default: `3`).

### 3. Usage Examples
* **Scrape 5 articles from Eat + Drink in headed mode**:
  ```bash
  cfk eatdrink --limit 5
  ```
* **Scrape all articles from News + Explainer in headless mode (no screenshots)**:
  ```bash
  cfk newsfeatures --all --headless --no-screenshots
  ```
* **Scrape everything across all sections (default configuration)**:
  ```bash
  cfk
  ```

---

## 📂 Output Structure

All outputs are saved to the specified `--output` directory (defaulting to `scraped_data/`).

According to the grouping rules, articles are grouped by their subsections:
* If a section contains subsections (e.g. `eatdrink/the-latest-eat-drink`):
  A folder named after the section is created, containing a JSON file for each subsection:
  ```text
  scraped_data/
  └── eatdrink/
      ├── the-latest-eat-drink.json  # Sub-category articles JSON
      ├── special-features.json      # Another sub-category JSON
      ├── screenshots/               # High-resolution full-page screenshots
      │   ├── article_1.png
      │   └── article_2.png
      └── images/                    # Downloaded top images
          ├── article_1/
          │   ├── image_0.jpg
          │   └── image_1.jpg
          └── article_2/
              └── image_0.jpg
  ```
* If a section has no subsections, it is saved directly to the root of the output directory as `{section_name}.json`.
* If an article in a subsection-grouped section has no subcategory, it is saved under `{section_name}/others.json`.
* All file paths for images and screenshots inside the output JSON are stored relative to the output root, ensuring the data folder is completely portable.
