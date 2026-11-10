// Run against a local TH14 preview. Only the runtime iframe is a protocol fixture.
// An optional compiled launcher module lets CI verify a source change before packaging it.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';

const require = createRequire(import.meta.url);
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [urlText, modulePath] = process.argv.slice(2);
const url = new URL(urlText);
assert(['localhost', '127.0.0.1'].includes(url.hostname));
const runtimeFixture = `<!doctype html><canvas></canvas><script>
  const epoch = Number(new URLSearchParams(location.search).get('runtimeEpoch'));
  const envelope = {game: 'th14', protocol: 'eagler-touhou/1', epoch};
  window.reportFrame = (fields = {}) => parent.postMessage({...envelope, event: 'first-frame', ...fields}, location.origin);
  addEventListener('message', ({data, source, origin}) => {
    if (source !== parent || origin !== location.origin || data.epoch !== epoch) return;
    if (data.request) parent.postMessage({...envelope, request: data.request, ok: true}, origin);
  });
  parent.postMessage({...envelope, event: 'ready'}, location.origin);
</script>`;
const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || undefined,
  args: ['--mute-audio'],
});
try {
  const context = await browser.newContext({serviceWorkers: 'block'});
  if (modulePath) {
    const body = await readFile(modulePath);
    await context.route('**/assets/launcher/app.mjs', route => route.fulfill({contentType: 'text/javascript', body}));
  }
  await context.route('**/runtime/th14/th14.html*', route => route.fulfill({
    contentType: 'text/html', body: runtimeFixture,
    headers: {'Cross-Origin-Embedder-Policy': 'require-corp'},
  }));
  const page = await context.newPage();
  await page.addLocatorHandler(page.locator('#changelogDialog[open]'), async () => {
    await page.locator('#changelogConfirm').click();
  });
  await page.goto(url.href);
  if (!await page.locator('#launch').isVisible()) {
    await page.locator('.game[data-game="th14"]').first().click();
  }
  await page.locator('#launch').click();
  const confirm = page.locator('#decisionDialog[open] #decisionConfirm');
  if (await confirm.isVisible()) await confirm.click();
  const report = page.locator('#startupErrorText');
  try {
    await report.filter({hasText: 'launch_ack=true'}).waitFor({timeout: 45_000});
  } catch (error) {
    throw new Error(JSON.stringify(await page.evaluate(() => ({
      status: document.querySelector('#playerStatus').textContent,
      detail: document.querySelector('#startupErrorText').textContent,
      frame: document.querySelector('#gameFrame').src,
      dialog: document.querySelector('dialog[open]')?.id,
      importShown: !document.querySelector('#gameDataImportWindow').hidden,
    }))), {cause: error});
  }
  const status = page.getByRole('status').filter({hasText: '12 秒内没有出现首帧'});
  assert.equal(await status.count(), 1);
  const iframe = await page.locator('#gameFrame').elementHandle();
  const runtime = await iframe.contentFrame();
  await runtime.evaluate(() => window.reportFrame({epoch: -1}));
  await runtime.evaluate(() => new Promise(resolve => setTimeout(resolve, 50)));
  assert.equal(await status.count(), 1);
  await runtime.evaluate(() => window.reportFrame());
  await page.locator('#startupError').waitFor({state: 'hidden'});
  assert.equal(await page.locator('#playerStatus').textContent(), '运行中');
  assert.equal(await status.count(), 0);
  console.log('Late first frame replaced the live status and dismissed the diagnostic; a stale epoch did neither.');
} finally {
  await browser.close();
}
