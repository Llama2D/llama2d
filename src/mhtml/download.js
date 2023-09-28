// playwright

const playwright = require('playwright');
const { setTimeout } = require('timers/promises');

(async () => {
    const browser = await playwright.chromium.launch({headless:false});
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto("https://google.com/");
    await setTimeout(20_000);

    const session = await page.context().newCDPSession(page)
    const doc = await session.send('Page.captureSnapshot', { format: 'mhtml' });
    console.log(doc.data);

    // save
    const {writeFileSync} = require('fs');
    writeFileSync('./finance.mhtml', doc.data);

})();