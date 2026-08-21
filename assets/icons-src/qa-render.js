const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const proj = path.resolve(__dirname, '..', '..');
const out = path.resolve(proj, 'scratchpad-qa');
if (!fs.existsSync(out)) fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.setViewport({ width: 1100, height: 700, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(proj, '2026-07-15-EN-site24-company-short.html'), { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 400));
  const slides = await page.$$('.slide');
  for (let i = 0; i < slides.length; i++) {
    await slides[i].screenshot({ path: path.resolve(out, `slide-${i + 1}.png`), type: 'png' });
    console.log('slide', i + 1);
  }
  await browser.close();
  console.log('DONE', slides.length);
})();
