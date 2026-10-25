import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });

  console.log('1. Navigating to http://localhost:8501...');
  await page.goto('http://localhost:8501', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(3000);

  console.log('2. Capturing landing page...');
  await page.screenshot({ path: 'landing_page_view.png', fullPage: false });

  console.log('3. Navigating to signup auth page...');
  await page.goto('http://localhost:8501/?auth=signup', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'auth_signup_view.png', fullPage: false });

  console.log('Done initial checks.');
  await browser.close();
})();
