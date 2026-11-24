// BF-D89: the research pages in a real browser (Chromium via Playwright) against
// `trader-bf dashboard --demo`: no horizontal scroll at the given phone width, every
// chip's text at least 4.5:1 in light and dark, and a "Why" opens with JavaScript off.
// argv: base URL, width (default 360), optional folder for screenshots (scale 2).
// Prints one JSON line.
const path = require('path');
const pw = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const SHOTS = [
  ['home', '/'],
  ['highlights', '/research'],
  ['library', '/research/library'],
  ['study', '/research/library/research_bw', '.rsure > summary'],
  ['testing', '/research/testing'],
  ['dates', '/research/dates'],
  ['glossary', '/research/glossary'],
];
(async () => {
  const base = process.argv[2];
  const width = Number(process.argv[3] || 360);
  const dir = process.argv[4] || '';
  const browser = await pw.chromium.launch();
  const out = { scroll: [], contrast: [], chips: 0, whyOpens: false, shots: [] };
  for (const scheme of ['light', 'dark']) {
    const ctx = await browser.newContext({ viewport: { width, height: 844 }, deviceScaleFactor: 2, colorScheme: scheme });
    await ctx.addInitScript(() => { try { localStorage.setItem('bw.tour', '1'); } catch (e) {} });
    const page = await ctx.newPage();
    for (const [name, p, open] of SHOTS) {
      await page.goto(base + p);
      await page.waitForTimeout(200);
      if (open) await page.click(open);
      const r = await page.evaluate(() => {
        function rgb(c) { const m = c.match(/[\d.]+/g); return m ? m.slice(0, 4).map(Number) : [0, 0, 0, 0]; }
        function lum(c) { const a = c.slice(0, 3).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]; }
        function bg(el) { while (el) { const c = rgb(getComputedStyle(el).backgroundColor); if (!(c.length === 4 && c[3] < 0.9)) return c; el = el.parentElement; } return rgb(getComputedStyle(document.body).backgroundColor); }
        const bad = [];
        const chips = document.querySelectorAll('.rchip');
        for (const el of chips) {
          const f = lum(rgb(getComputedStyle(el).color)), b = lum(bg(el));
          const ratio = (Math.max(f, b) + 0.05) / (Math.min(f, b) + 0.05);
          if (ratio < 4.5) bad.push(el.className + ' ' + ratio.toFixed(2));
        }
        return { over: document.documentElement.scrollWidth - document.documentElement.clientWidth, bad, n: chips.length };
      });
      if (r.over > 0) out.scroll.push(scheme + ' ' + p + ' +' + r.over);
      out.contrast.push(...r.bad.map(x => scheme + ' ' + p + ' ' + x));
      out.chips += r.n;
      if (dir) {
        const f = path.join(dir, `${name}_${scheme}.png`);
        await page.screenshot({ path: f, fullPage: true });
        out.shots.push(f);
      }
    }
    await ctx.close();
  }
  // no JavaScript: a highlight's "Why" is a plain <details> and still opens
  const nojs = await browser.newContext({ viewport: { width, height: 844 }, javaScriptEnabled: false });
  const page = await nojs.newPage();
  await page.goto(base + '/research');
  await page.click('details.why > summary');
  out.whyOpens = await page.$eval('details.why', d => d.open);
  await browser.close();
  console.log(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
