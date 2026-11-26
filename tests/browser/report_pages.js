// BF-D91: the report screens in a real browser (Chromium via Playwright) against
// `trader-bf dashboard --demo`: no horizontal scroll at 360 and 390 px, the report text
// at least 4.5:1 in light and dark, and a daily report opens as a card with JavaScript
// off (plain <details>). argv: base URL, optional folder for screenshots (scale 2,
// 390 px). Prints one JSON line.
const path = require('path');
const pw = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const PAGES = [
  ['home', '/'],
  ['inbox', '/inbox'],
  ['digest', '/digest'],
  ['costs', '/costs'],
  ['health', '/health'],
  ['strategy', '/strategy'],
  ['orders', '/orders'],
  ['highlights', '/research'],
  ['study', '/research/library/research_bw'],
  ['testing', '/research/testing'],
  ['dates', '/research/dates'],
];
const TEXT = '.cmpl,.cmpv b,.cmpn,.gaph span,.gapx span,.luck,.luck b,.bigsub,.kv span,.kv small,.kv b,' +
  '.repline span,.hdo,.hdo>span,.splitk .grow,.rep>.caption,.nrow .sub,.nrow b,.allok,.attn .sub,' +
  '.rep .stats dt,.rep .stats small,.orig>summary,.rtab th,.rtab td,.ylead,.rsure>summary';
(async () => {
  const base = process.argv[2];
  const dir = process.argv[3] || '';
  const browser = await pw.chromium.launch();
  const out = { scroll: [], contrast: [], pages: 0, reportOpens: false, holdingsOpen: false, barsVisible: false, shots: [] };
  for (const width of [360, 390]) {
    for (const scheme of ['light', 'dark']) {
      const ctx = await browser.newContext({ viewport: { width, height: 844 }, deviceScaleFactor: 2, colorScheme: scheme });
      await ctx.addInitScript(() => { try { localStorage.setItem('bw.tour', '1'); } catch (e) {} });
      const page = await ctx.newPage();
      for (const [name, p] of PAGES) {
        await page.goto(base + p);
        await page.waitForTimeout(150);
        if (name === 'inbox') {
          for (const k of ['report', 'approval', 'info']) {
            const el = await page.$('li.msg[data-kind="' + k + '"] > details > summary');
            if (el) await el.click();
          }
          const h = await page.$('li.msg[data-kind="report"] .fold > summary');
          if (h) await h.click();
          await page.waitForTimeout(100);
        }
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
          return { over: document.documentElement.scrollWidth - document.documentElement.clientWidth, bad };
        }, TEXT);
        if (r.over > 0) out.scroll.push(width + ' ' + scheme + ' ' + p + ' +' + r.over);
        out.contrast.push(...r.bad.map(x => width + ' ' + scheme + ' ' + p + ' ' + x));
        out.pages += 1;
        if (name === 'home' && width === 390 && scheme === 'light') {
          out.barsVisible = await page.evaluate(() => {
            const bars = [...document.querySelectorAll('.cmpt i')];
            return bars.length === 2 && bars.every(b => b.getBoundingClientRect().width > 4) &&
              document.querySelector('.gapsvg').getBoundingClientRect().height > 30;
          });
        }
        if (dir && width === 390) {
          const f = path.join(dir, name + '_' + scheme + '.png');
          await page.screenshot({ path: f, fullPage: true });
          out.shots.push(f);
        }
      }
      await ctx.close();
    }
  }
  // no JavaScript: a daily report is a plain <details> and still opens as a card
  const nojs = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false });
  const page = await nojs.newPage();
  await page.goto(base + '/inbox');
  await page.click('li.msg[data-kind="report"] > details > summary');
  out.reportOpens = await page.$eval('li.msg[data-kind="report"] .rep .bignum', el => el.getBoundingClientRect().height > 20);
  // bring the fold-out clear of the fixed tab bar first, as a thumb would
  await page.$eval('li.msg[data-kind="report"] .fold > summary', el => el.scrollIntoView({ block: 'center' }));
  await page.click('li.msg[data-kind="report"] .fold > summary');
  out.holdingsOpen = await page.$eval('li.msg[data-kind="report"] .fold .rtab', el => el.getBoundingClientRect().height > 40);
  await browser.close();
  console.log(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
