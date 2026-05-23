# 🛡️ CFKiller Seeker - Cloudflare Turnstile Bypass & Scraper Research

An advanced research and implementation repository focused on bypassing Cloudflare Turnstile validation challenges and scraping protected web applications using **Playwright** and **CloakBrowser**.

This repository contains both the initial research scripts (used to explore Turnstile behavior inside closed Shadow DOMs) and a fully modularized, production-ready node-based workflow scraper packaged as a command-line tool `cfk`.

---

## 📂 Project Structure

```text
privacy_protector_browser/
├── cfk                        # 🚀 Root CLI Command Launcher (Executable)
│
├── article_scraper/           # 📦 Core Production Scraper Module
│   ├── scraper.py             # Single tool implementing node workflow
│   └── README.md              # Detailed documentation for the scraper module
│
├── flow/                      # 🧪 Workflow Sandbox & Development Logs
│   ├── node_scraper.py        # Headed scraper workflow sandbox
│   ├── test_true_headless.py  # Headless scraper workflow sandbox
│   ├── 目标.md                # Target description file
│   └── 采集数据脚本/          # User-provided IndexedDB JS scraper guidelines
│
├── [Research Scripts]         # 🔍 Diagnostic and exploration scripts
│   ├── natural_click.py       # Natural Bezier curve movement clicks
│   ├── find_shadow_in_frame.py# Shadow DOM tree traversals
│   ├── dump_main_shadow.py    # Main document shadow boundary analyzer
│   ├── poll_all_frames.py     # Multi-frame rendering timeline monitors
│   └── ...                    # Other debugging utilities
│
└── .gitignore                 # Exclusion configuration for logs and build files
```

---

## 💡 The Core Challenge & Solution

Cloudflare Turnstile verification differs significantly from traditional captchas:
1. **Closed Shadow DOM Nesting**: The Turnstile iframe resides inside a closed Shadow DOM on the parent document. Conventional query selectors like `document.querySelectorAll("iframe")` return `0` elements. 
2. **Dynamic Load Rendering**: The Turnstile widget undergoes a 5–10s passive verification loader (spinning state) before transitioning to the interactive checkbox. Clicks dispatched prematurely will fail.
3. **Bot Detection**: Simple programmatic clicks (e.g. `.click()`) are intercepted. The interaction requires natural mouse cursor trajectories and human-like down-to-up delay intervals.

### How this Repository Solves It:
* **Frame Bounding Box Tracking**: Uses Playwright's `frame.frame_element().bounding_box()` to resolve coordinates across closed shadow boundaries.
* **Layout Stabilization**: Implements polling logic that monitors Turnstile dimensions and coordinates until they stabilize.
* **Bezier Curve Mouse Paths**: Generates natural mouse trajectories using quadratic Bezier curves.
* **Human-like Clicking**: Triggers sequential `.mouse.down()` and `.mouse.up()` events with random duration delays (80ms - 150ms).
* **Node Workflow Architecture**: Organizes the scraping execution into distinct step nodes (Launch, Bypass, Scroll, Navigate, Scrape, Group/Save) managed by a runner that handles automatic retries and timing recoveries.
* **On-the-Fly Disk Buffering (O(1) Memory footprint)**: To prevent memory leaks and browser crashes during large scrapes, articles are written directly to disk under a `.tmp/` folder immediately upon scraping. The Playwright page and DOM memory are closed and garbage-collected after each article.
* **Resilience & Resume**: If interrupted, articles already scraped are cached on disk, allowing the scraper to resume and skip already processed articles in subsequent runs.

---

## 🚀 Quick Start

### 1. Set Up Environment
Activate the pre-configured Python virtual environment:
```bash
source .venv/bin/activate
```

Install playwright chromium dependencies:
```bash
playwright install chromium
```

### 2. Run the Production Scraper via CLI
The CLI tool `cfk` is packaged and linked inside `.venv/bin/cfk`. When the virtual environment is active, you can call it directly:

```bash
cfk [section] [options]
```

#### Positional Arguments
* `section`: The target Spot.ph section to scrape.
  * Choices: `eatdrink`, `things-to-do`, `shopping`, `newsfeatures`, `arts-culture`, `entertainment`, or `all` (scrapes all sections sequentially).
  * Default: `all`.

#### Options
* `--all`: Scrape all available articles in the section (ignores `--limit`).
* `--limit LIMIT`: Max articles to scrape per section (ignored if `--all` is set, default: `10`).
* `--headless`: Run browser in headless mode (default: False).
* `--output OUTPUT`: Output base directory (default: `scraped_data`).
* `--delay DELAY`: Delay in seconds between article requests to avoid rate limits (default: `2.0`).
* `--no-screenshots`: Disable capturing full-page screenshots of articles.
* `--no-images`: Disable downloading article images.
* `--scroll-limit SCROLL_LIMIT`: Rounds to scroll to bottom without new links before stopping when `--all` is set (default: `3`).

#### Usage Examples
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

---

## 🔬 Research & Debugging Utilities
If you want to understand how the browser components are resolved, you can explore the research scripts in the root directory:
* **`find_shadow_in_frame.py`**: Prints nested shadow root selectors.
* **`natural_click.py`**: Tests raw Bezier-based mouse coordinate clicks.
* **`poll_all_frames.py`**: Monitors frame creation lifecycle events during Turnstile load.
