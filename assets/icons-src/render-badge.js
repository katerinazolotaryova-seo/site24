const puppeteer = require('puppeteer');
const path = require('path');
(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.setViewport({ width: 600, height: 200, deviceScaleFactor: 3 });
  await page.goto('file://' + path.resolve(__dirname, 'google-partner.html'), { waitUntil: 'networkidle0' });
  const el = await page.$('#badge');
  await el.screenshot({ path: path.resolve(__dirname, '..', 'badges', 'google-partner.png'), omitBackground: true });
  await browser.close();
  console.log('DONE');
})();
