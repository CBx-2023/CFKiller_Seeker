// ============================================================
// SPOT.ph Eat + Drink 流式抓取 v6
// IndexedDB 中转，逐条写入，最后一次性下载
// 在 https://www.spot.ph/eatdrink 控制台执行
// ============================================================

(async function() {
  const delay = ms => new Promise(r => setTimeout(r, ms));

  // ============ IndexedDB 初始化 ============
  function openDB() {
    return new Promise((resolve, reject) => {
      let req = indexedDB.open('SpotPHScraper', 1);
      req.onupgradeneeded = e => {
        let db = e.target.result;
        if (!db.objectStoreNames.contains('articles')) {
          db.createObjectStore('articles', { keyPath: 'index' });
        }
      };
      req.onsuccess = e => resolve(e.target.result);
      req.onerror = e => reject(e.target.error);
    });
  }

  async function dbPut(db, article) {
    return new Promise((resolve, reject) => {
      let tx = db.transaction('articles', 'readwrite');
      tx.objectStore('articles').put(article);
      tx.oncomplete = resolve;
      tx.onerror = e => reject(e.target.error);
    });
  }

  async function dbGetAll(db) {
    return new Promise((resolve, reject) => {
      let tx = db.transaction('articles', 'readonly');
      let req = tx.objectStore('articles').getAll();
      req.onsuccess = e => resolve(e.target.result);
      req.onerror = e => reject(e.target.error);
    });
  }

  async function dbCount(db) {
    return new Promise((resolve, reject) => {
      let tx = db.transaction('articles', 'readonly');
      let req = tx.objectStore('articles').count();
      req.onsuccess = e => resolve(e.target.result);
      req.onerror = e => reject(e.target.error);
    });
  }

  function dbClear(db) {
    return new Promise((resolve, reject) => {
      let tx = db.transaction('articles', 'readwrite');
      tx.objectStore('articles').clear();
      tx.oncomplete = resolve;
      tx.onerror = e => reject(e.target.error);
    });
  }

  // ============ 初始化 ============
  let db = await openDB();
  await dbClear(db); // 清空上次残留
  console.log('[IndexedDB 就绪]');

  // ============ 状态 ============
  let seen = new Set();
  let ok = 0, fail = 0, idx = 0;

  // ============ 写入单篇到 IndexedDB ============
  async function saveArticle(article) {
    await dbPut(db, article);
    if (article.error) fail++; else ok++;
  }

  // ============ 抓取单篇 ============
  async function fetchArticle(url, index) {
    if (seen.has(url)) return null;
    seen.add(url);

    try {
      let resp = await fetch(url);
      let html = await resp.text();
      let parser = new DOMParser();
      let doc = parser.parseFromString(html, 'text/html');

      let title = doc.querySelector('h1')?.innerText?.trim() || '';
      let date = '';
      let dm = html.match(/Published on ([A-Z][a-z]+ \d+, \d{4})/);
      if (dm) date = dm[1];
      let author = doc.querySelector('.author,[class*="author"]')?.innerText?.trim() || '';

      let images = [];
      doc.querySelectorAll('img').forEach(img => {
        let src = img.src || img.getAttribute('data-src') || '';
        if (src && src.includes('spot.ph') && !src.includes('logo') && !src.includes('icon') && !src.includes('favicon') && !src.includes('ad-')) {
          if (!images.includes(src)) images.push(src);
        }
      });

      let paragraphs = [];
      doc.querySelectorAll('p').forEach(p => {
        let t = p.innerText.trim();
        if (t.length > 20 && !t.includes('cookie') && !t.includes('Subscribe') && !t.includes('Sign up')) {
          paragraphs.push(t);
        }
      });

      let article = {
        index, title, url, date, author,
        scraped_at: new Date().toISOString(),
        images, imageCount: images.length,
        content: paragraphs.join('\n\n'), paragraphs: paragraphs.length
      };

      await saveArticle(article);
      html = doc = resp = null; // 释放
      return article;

    } catch (e) {
      let f = { index, url, error: e.message };
      await saveArticle(f);
      return f;
    }
  }

  // ============ 提取新链接 ============
  function extractNewLinks() {
    let out = [];
    document.querySelectorAll('.article-card').forEach(el => {
      let a = el.querySelector('a'), t = el.querySelector('h2,h3,h4');
      if (a && t) {
        let u = a.href, x = t.innerText.trim();
        if (u && x && !seen.has(u)) out.push({ title: x, url: u });
      }
    });
    return out;
  }

  // ============ 主循环 ============
  console.log('=== 边滚动边抓取，写入 IndexedDB ===');

  let prevCount = 0, stableRounds = 0;

  while (stableRounds < 5) {
    let newLinks = extractNewLinks();
    for (let item of newLinks) {
      idx++;
      console.log(`[${idx}] ${item.title.substring(0, 50)}`);
      let r = await fetchArticle(item.url, idx);
      if (r && !r.error) console.log(`    ✓ ${r.paragraphs}p ${r.imageCount}img`);
      else if (r?.error) console.log(`    ✗ ${r.error}`);
      await delay(600);
    }

    window.scrollTo(0, document.body.scrollHeight);
    await delay(2000);

    let cc = document.querySelectorAll('.article-card').length;
    if (cc === prevCount) stableRounds++;
    else { stableRounds = 0; prevCount = cc; console.log(`\n[滚动] ${cc} 篇\n`); }
  }

  // 补抓
  console.log('\n[检查遗漏...]');
  let rem = extractNewLinks();
  for (let item of rem) {
    idx++;
    await fetchArticle(item.url, idx);
    await delay(600);
  }

  // ============ 从 IndexedDB 导出并下载 ============
  console.log('\n[导出下载...]');
  let all = await dbGetAll(db);
  all.sort((a, b) => a.index - b.index);

  let output = {
    source: 'https://www.spot.ph/eatdrink',
    scraped_at: new Date().toISOString(),
    total: all.length,
    success: ok,
    failed: fail,
    articles: all
  };

  let blob = new Blob([JSON.stringify(output, null, 2)], { type: 'application/json' });
  let url = URL.createObjectURL(blob);
  let a = document.createElement('a');
  a.href = url;
  a.download = 'spotph_eatdrink_' + new Date().toISOString().slice(0, 10) + '.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  // 清理 IndexedDB
  await dbClear(db);
  db.close();

  console.log('\n========================================');
  console.log('       完成！文件已下载');
  console.log('========================================');
  console.log(`  文件: ${a.download}`);
  console.log(`  成功: ${ok}  失败: ${fail}`);
  console.log('  IndexedDB 已清理');
  console.log('========================================');
})();
