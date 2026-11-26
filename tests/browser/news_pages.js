// BF-D92: the News tab in a real browser (Chromium via Playwright) against
// `trader-bf dashboard --demo`: six tabs still fit at 360 and 390 px (one row, every tap
// target at least 44 px, no label cut), no horizontal scroll, the News text at least
// 4.5:1 in light and dark, the unread dot shows until News is opened, a stored PDF
// opens, and the page reads the same with JavaScript off. argv: base URL, optional
// folder for screenshots (scale 2, 390 px). Prints one JSON line.
const path = require('path');
const pw = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const PAGES = [['home', '/'], ['news', '/news'], ['news_ps', '/news?f=ps'], ['holdings', '/holdings'], ['inbox', '/inbox']];
const TEXT = '.newshead .verdict,.newshead .bigsub,.mkt .mk1,.mkt .mk1>span,.mkt .sub,.luck span,.moves .nrow b,' +
  '.moves .nrow .sub,.nmv span,.ncode,.nws .nwho,.nws .sub,.nws div,.nws .pill,.pdfl,.newsfeed .day,' +
  '.newsfeed .chip,.news .caption,.news .allok span,.tabs .tab span';
(async () => {
  const base = process.argv[2];
  const dir = process.argv[3] || '';
  const browser = await pw.chromium.launch();
  const out = { scroll: [], contrast: [], tabs: [], pages: 0, dotBefore: null, dotOnNews: null, dotAfter: null,
    pdf: '', pdfLinks: 0, rows: 0, nojsRows: 0, nojsLabel: false, shots: [] };
  for (const width of [360, 390]) {
    for (const scheme of ['light', 'dark']) {
      const ctx = await browser.newContext({ viewport: { width, height: 844 }, deviceScaleFactor: 2, colorScheme: scheme });
      await ctx.addInitScript(() => { try { localStorage.setItem('bw.tour', '1'); } catch (e) {} });
      const page = await ctx.newPage();
      for (const [name, p] of PAGES) {
        await page.goto(base + p);
        await page.waitForTimeout(150);
        const r = await page.evaluate((sel) => {
          function rgb(c) { const m = c.match(/[\d.]+/g); return m ? m.slice(0, 4).map(Number) : [0, 0, 0, 0]; }
          function lum(c) { const a = c.slice(0, 3).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]; }
          function bg(el) { while (el) { const c = rgb(getComputedStyle(el).backgroundColor); if (!(c.length === 4 && c[3] < 0.9)) return c; el = el.parentElement; } return rgb(getComputedStyle(document.body).backgroundColor); }
          const bad = [];
          for (const el of document.querySelectorAll(sel)) {
            if (!el.offsetParent || !el.textContent.trim()) continue;
            const f = lum(rgb(getComputedStyle(el).color)), b = lum(bg(el));
            const ratio = (Math.max(f, b) + 0.05) / (Math.min(f, b) + 0.05);
            if (ratio < 4.5) bad.push(el.className + ' "' + el.textContent.trim().slice(0, 24) + '" ' + ratio.toFixed(2));
          }
          const tabs = [...document.querySelectorAll('.tabs .tab')].map(a => {
            const b = a.getBoundingClientRect(), s = a.querySelector('span');
            return { k: a.dataset.tab, w: b.width, h: b.height, top: Math.round(b.top), left: b.left, right: b.right,
              cut: s.scrollWidth > s.clientWidth + 0.5 };
          });
          return { over: document.documentElement.scrollWidth - document.documentElement.clientWidth, bad, tabs, vw: innerWidth };
        }, TEXT);
        if (r.over > 0) out.scroll.push(width + ' ' + scheme + ' ' + p + ' +' + r.over);
        out.contrast.push(...r.bad.map(x => width + ' ' + scheme + ' ' + p + ' ' + x));
        const t = r.tabs, where = width + ' ' + scheme + ' ' + p + ' ';
        if (t.map(x => x.k).join() !== 'home,holdings,news,orders,inbox,server') out.tabs.push(where + 'tabs ' + t.map(x => x.k).join());
        for (const x of t) {
          if (x.w < 44 || x.h < 44) out.tabs.push(where + x.k + ' target ' + x.w.toFixed(0) + 'x' + x.h.toFixed(0));
          if (x.cut) out.tabs.push(where + x.k + ' label cut');
          if (x.top !== t[0].top) out.tabs.push(where + x.k + ' wrapped');
          if (x.left < -0.5 || x.right > r.vw + 0.5) out.tabs.push(where + x.k + ' off screen');
        }
        out.pages += 1;
        if (dir && width === 390 && name.startsWith('news')) {
          const f = path.join(dir, name + '_' + scheme + '.png');
          await page.screenshot({ path: f, fullPage: true });
          out.shots.push(f);
        }
        if (dir && width === 390 && name === 'home') {
          const f = path.join(dir, scheme === 'light' ? 'after_home_tabbar.png' : 'after_dark_home_tabbar.png');
          await page.screenshot({ path: f });
          out.shots.push(f);
        }
      }
      await ctx.close();
    }
  }
  // the unread dot: shown on Home until News has been opened, then gone
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await ctx.addInitScript(() => { try { localStorage.setItem('bw.tour', '1'); } catch (e) {} });
  const page = await ctx.newPage();
  const dot = () => page.$eval('.tab[data-tab=news] .dot', d => !d.hidden && d.getBoundingClientRect().width > 4);
  await page.goto(base + '/');
  await page.waitForTimeout(200);
  out.dotBefore = await dot();
  await page.click('.tab[data-tab=news]');
  await page.waitForSelector('.newshead');
  await page.waitForTimeout(200);
  out.dotOnNews = await dot();
  out.rows = await page.$$eval('.nws', els => els.length);
  out.pdfLinks = await page.$$eval('.pdfl', els => els.length);
  const href = await page.$eval('.pdfl', a => a.getAttribute('href'));
  const resp = await ctx.request.get(base + href);
  out.pdf = resp.status() + ' ' + resp.headers()['content-type'] + ' ' + (await resp.body()).slice(0, 5).toString();
  await page.goto(base + '/');
  await page.waitForTimeout(200);
  out.dotAfter = await dot();
  await ctx.close();
  // no JavaScript: the same feed, and the information-only label
  const nojs = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false });
  const p2 = await nojs.newPage();
  await p2.goto(base + '/news');
  out.nojsRows = await p2.$$eval('.nws', els => els.length);
  out.nojsLabel = (await p2.textContent('.newshead')).includes('Information only, not a trading signal');
  await browser.close();
  console.log(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
