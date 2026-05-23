"""
CloakBrowser — Cloudflare 验证通过测试
尝试多种策略绕过 Cloudflare 安全验证
"""
from cloakbrowser import launch
import os
import time

SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
URL = "https://www.spot.ph"


def is_cf_challenge(page):
    """检测是否仍在 Cloudflare 挑战页面"""
    title = page.title().lower()
    cf_keywords = ["just a moment", "attention required", "checking your browser",
                    "security check", "performing security verification"]
    return any(kw in title for kw in cf_keywords)


def wait_for_cf_pass(page, timeout=30):
    """等待 Cloudflare 验证通过，最多等待 timeout 秒"""
    print(f"  ⏳ 等待 Cloudflare 验证（最多 {timeout}s）...")
    start = time.time()
    while time.time() - start < timeout:
        if not is_cf_challenge(page):
            elapsed = round(time.time() - start, 1)
            print(f"  ✅ Cloudflare 验证通过！耗时 {elapsed}s")
            return True
        # 检查是否有 Turnstile checkbox 需要点击
        try:
            turnstile = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
            checkbox = turnstile.locator("input[type='checkbox'], .cb-lb")
            if checkbox.count() > 0 and checkbox.first.is_visible():
                print("  🖱️ 检测到 Turnstile checkbox，正在点击...")
                checkbox.first.click()
        except Exception:
            pass
        page.wait_for_timeout(1000)
    print(f"  ❌ 等待超时 ({timeout}s)")
    return False


def take_screenshot(page, name):
    """截图并保存"""
    path = os.path.join(SAVE_DIR, name)
    buf = page.screenshot(full_page=False)
    with open(path, "wb") as f:
        f.write(buf)
    print(f"  📸 截图: {name} ({len(buf)} bytes)")
    return path


def test_strategy(name, **launch_kwargs):
    """用指定策略测试"""
    print(f"\n{'='*60}")
    print(f"🧪 策略: {name}")
    print(f"{'='*60}")
    print(f"  参数: {launch_kwargs}")

    try:
        browser = launch(**launch_kwargs)
        page = browser.new_page()

        print(f"  📄 正在打开 {URL} ...")
        page.goto(URL, timeout=30000, wait_until="domcontentloaded")

        # 第一次截图（可能是 CF 挑战页）
        title_before = page.title()
        print(f"  📋 初始标题: {title_before}")

        if is_cf_challenge(page):
            take_screenshot(page, f"cf_challenge_{name}.png")
            passed = wait_for_cf_pass(page, timeout=30)
        else:
            passed = True

        # 最终结果
        page.wait_for_timeout(2000)
        title_after = page.title()
        url_after = page.url
        print(f"  📋 最终标题: {title_after}")
        print(f"  📍 最终 URL: {url_after}")

        take_screenshot(page, f"result_{name}.png")

        if not is_cf_challenge(page):
            print(f"  🎉 结果: ✅ 通过！")
            result = True
        else:
            print(f"  💀 结果: ❌ 未通过")
            result = False

        browser.close()
        return result

    except Exception as e:
        print(f"  ⚠️ 异常: {e}")
        try:
            browser.close()
        except:
            pass
        return False


# ── 逐个测试不同策略 ──────────────────────────────

results = {}

# 策略 1: humanize 模式（人类行为模拟）
results["humanize"] = test_strategy(
    "humanize",
    headless=True,
    humanize=True,
)

# 策略 2: humanize + careful 预设
results["humanize_careful"] = test_strategy(
    "humanize_careful",
    headless=True,
    humanize=True,
    human_preset="careful",
)

# 策略 3: 带有额外 stealth 参数
results["stealth_args"] = test_strategy(
    "stealth_args",
    headless=True,
    humanize=True,
    args=["--disable-blink-features=AutomationControlled"],
)

# ── 汇总结果 ──────────────────────────────────────

print(f"\n{'='*60}")
print("📊 测试结果汇总")
print(f"{'='*60}")
for name, passed in results.items():
    status = "✅ 通过" if passed else "❌ 未通过"
    print(f"  {name:25s} → {status}")
print(f"{'='*60}")
