# 🛡️ CFKiller Seeker - Cloudflare Turnstile Bypass & Scraper Research

An advanced research and implementation repository focused on bypassing Cloudflare Turnstile validation challenges and scraping protected web applications using **Playwright** and **CloakBrowser**.

This repository contains both the initial research scripts (used to explore Turnstile behavior inside closed Shadow DOMs) and a fully modularized, production-ready node-based workflow scraper.

---

## 📂 Project Structure

```text
privacy_protector_browser/
├── article_scraper/           # 🚀 Unified Production-ready Tool
│   ├── scraper.py             # Single tool supporting headed & headless modes
│   └── README.md              # Documentation for the scraper module
│
├── flow/                      # 🧪 Workflow Sandbox & Development Logs
│   ├── node_scraper.py        # Headed scraper workflow sandbox
│   ├── test_true_headless.py  # Headless scraper workflow sandbox
│   └── scraped_article/       # Output directories for development runs
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
* **Node Workflow Architecture**: Organizes the scraping execution into distinct step nodes (Launch, Bypass, Navigate, Scrape, Screenshot) managed by a runner that handles automatic retries and timing recoveries.

---

## 🛠️ Quick Start

### 1. Set Up Environment
Activate the pre-configured Python virtual environment:
```bash
source .venv/bin/activate
```

Install playwright chromium dependencies:
```bash
playwright install chromium
```

### 2. Run the Production Scraper
Navigate to the production directory:
```bash
cd article_scraper
```

* **Headed Mode (Visible browser window)**:
  ```bash
  python scraper.py
  ```
* **Headless Mode (Server CLI-only execution)**:
  ```bash
  python scraper.py --headless
  ```

Outputs will be saved in `article_scraper/scraped_data/`.

---

## 🔬 Research & Debugging Utilities
If you want to understand how the browser components are resolved, you can explore the research scripts in the root directory:
* **`find_shadow_in_frame.py`**: Prints nested shadow root selectors.
* **`natural_click.py`**: Tests raw Bezier-based mouse coordinate clicks.
* **`poll_all_frames.py`**: Monitors frame creation lifecycle events during Turnstile load.
