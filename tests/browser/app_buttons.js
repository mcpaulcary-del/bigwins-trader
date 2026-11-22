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
  console.log(JSON.stringify(out));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
