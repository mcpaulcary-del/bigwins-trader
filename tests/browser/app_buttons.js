// BF-D55: a real browser (Chromium via Playwright) clicks the app's buttons against
// `trader-bf dashboard --demo` (signed forwarding and the CSRF / Origin checks as in
// production; the demo's actions are simulated). Prints one JSON line per step.
const path = require('path');
const pw = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const base = process.argv[2];
  const browser = await pw.chromium.launch();
  const page = await browser.newPage();
  const posts = [];
  page.on('request', r => { if (r.method() === 'POST') posts.push({url: r.url(), origin: r.headers()['origin'] || null, site: r.headers()['sec-fetch-site'] || null}); });
  const out = {};
  const text = async () => (await page.innerText('main')).replace(/\s+/g, ' ').slice(0, 300);
  await page.goto(base + '/act');
  await page.click('button.warnb');            // Pause: one tap
  await page.waitForLoadState();
  out.pause = await text();
  await page.goto(base + '/act/confirm?a=ki');
  await page.click('button.danger');           // Kill -> Yes
  await page.waitForLoadState();
  out.kill = await text();
  await page.goto(base + '/');
  await page.click('a.btn:has-text("Approve all")');
  await page.waitForLoadState();
  out.confirm = await text();
  await page.fill('#code', '123456');
  await page.click('form button.btn');         // Approve all N orders
  await page.waitForLoadState();
  out.approve = await text();
  out.posts = posts;
  // BF-D62: the chart read-out on hover / drag
  await page.goto(base + '/');
  await page.waitForTimeout(400);
  const svg = await page.$('[data-chart] svg');
  await svg.scrollIntoViewIfNeeded();
  const bb = await svg.boundingBox();
  await page.mouse.move(bb.x + bb.width * 0.6, bb.y + bb.height / 2);
  await page.waitForTimeout(200);
  out.tooltip = await page.evaluate(() => { const t = document.querySelector('.ctip.on'); return t ? t.innerText : null; });
  await page.click('[data-range="31"]');
  await page.waitForTimeout(500);
  out.range = await page.getAttribute('[data-range="31"]', 'aria-pressed');
  // tab switching without a page load, and the holdings' interactions
  await page.click('.tab[data-tab="holdings"]');
  await page.waitForFunction(() => document.body.dataset.tab === 'holdings' && location.pathname === '/holdings');
  out.tab = await page.evaluate(() => [document.body.dataset.tab, location.pathname, document.querySelector('.tab.on').dataset.tab]);
  await page.click('[data-sort="name"]');
  out.sorted = await page.evaluate(() => { const c = Array.from(document.querySelectorAll('#hlist li[data-code]')).map(l => l.dataset.code); return c.join(',') === c.slice().sort().join(','); });
  await page.dispatchEvent('.ds[data-code]', 'click');  // (a tap lands on the ring, not its hole)
  out.donut = await page.evaluate(() => document.querySelectorAll('#hlist li.hl').length);
  // accessibility: names and contrast (light and dark)
  const a11y = [];
  for (const scheme of ['light', 'dark']) {
    await page.emulateMedia({ colorScheme: scheme });
    for (const p of ['/', '/holdings', '/orders', '/inbox', '/server', '/act']) {
      await page.goto(base + p);
      await page.waitForTimeout(150);
      const bad = await page.evaluate(() => {
        const out = [];
        for (const el of document.querySelectorAll('a,button,input,select')) {
          if (el.type === 'hidden') continue;
          const name = (el.getAttribute('aria-label') || el.innerText || el.value || el.placeholder || (el.labels && el.labels[0] && el.labels[0].innerText) || '').trim();
          if (!name) out.push('no name: ' + el.outerHTML.slice(0, 80));
        }
        for (const s of document.querySelectorAll('svg[role=img]')) if (!s.getAttribute('aria-label')) out.push('svg without label');
        function rgb(c) { const m = c.match(/[\d.]+/g); return m ? m.slice(0, 4).map(Number) : [0, 0, 0, 0]; }
        function lum(c) { const a = c.slice(0, 3).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]; }
        function bg(el) { while (el) { const c = rgb(getComputedStyle(el).backgroundColor); if (c.length < 4 || c[3] > 0.9) { if (!(c.length === 4 && c[3] === 0)) return c; } el = el.parentElement; } return rgb(getComputedStyle(document.body).backgroundColor); }
        for (const sel of ['body', 'h1', 'h2', '.muted', '.sub', '.tab', '.tab.on', '.btn', '.btn.sec', '.btn.danger', '.chip', '.pill', '.up', '.down', '.note', '.tl', '.badge']) {
          const el = document.querySelector('main ' + sel) || document.querySelector(sel);
          if (!el || !el.offsetParent && sel !== 'body') continue;
          const f = rgb(getComputedStyle(el).color), b = bg(el);
          const l1 = lum(f), l2 = lum(b), r = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
          if (r < 4.5) out.push(sel + ' contrast ' + r.toFixed(2));
        }
        return out;
      });
      for (const b of bad) a11y.push(scheme + ' ' + p + ': ' + b);
    }
  }
  out.a11y = a11y;
  console.log(JSON.stringify(out));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
