const puppeteer = require('puppeteer');
const path = require('path');
const dir = __dirname;
const out = path.resolve(dir, '..', 'niches');
const fs = require('fs');
if (!fs.existsSync(out)) fs.mkdirSync(out, { recursive: true });
const ids = ['ecommerce','medicine','manufacturing','services','realestate','edtech'];
(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.setViewport({ width: 400, height: 400, deviceScaleFactor: 3 });
  await page.goto('file://' + path.resolve(dir, 'niche-icons.html'), { waitUntil: 'networkidle0' });
  for (const id of ids) {
    const el = await page.$('#' + id);
    await el.screenshot({ path: path.resolve(out, id + '.png'), omitBackground: true });
    console.log('icon', id);
  }
  await browser.close();
  console.log('DONE');
})();
