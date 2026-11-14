const { chromium } = require('playwright');
(async () => {
  const [url, out, w, h, full] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +w || 1400, height: +h || 900 }, deviceScaleFactor: 1 });
  const errs = []; p.on('pageerror', (e) => errs.push(String(e))); p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto(url, { waitUntil: 'networkidle' }); await p.waitForTimeout(700);
  if (process.env.ACT) await eval('(async()=>{' + process.env.ACT + '})()');
  await p.screenshot({ path: out, fullPage: full === 'full' }); console.log('errors:', errs.length ? errs : 'none'); await b.close();
})();
