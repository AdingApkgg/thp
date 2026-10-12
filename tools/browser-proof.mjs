// Drive a runtime page in headless Chrome over the DevTools Protocol and report
// what actually happened: console errors, the page's own status elements, and
// one or more screenshots.
//
//   node tools/browser-proof.mjs --url http://127.0.0.1:8113/?autostart=1 \
//        --out artifacts/th12 --shots 2 --interval 3000 --wait 60000
//
// Chrome's --screenshot flag writes the file before the renderer has flushed and
// reports a bogus "access denied" here, so verification goes through CDP instead:
// Page.captureScreenshot is synchronous with the renderer and the DOM state is
// read from the live page rather than a re-serialised dump.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdtempSync } from 'node:fs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function arg(name, fallback = null) {
  const at = process.argv.indexOf('--' + name);
  return at < 0 ? fallback : process.argv[at + 1];
}

const url = arg('url');
if (!url) throw Error('--url is required');
const outDir = resolve(root, arg('out', 'artifacts/browser-proof'));
const shots = Number(arg('shots', '1'));
const interval = Number(arg('interval', '0'));
const waitMs = Number(arg('wait', '60000'));
const port = Number(arg('port', '9444'));
const prefix = arg('prefix', 'frame');
// Keyboard injection, so a proof can press keys rather than only watch. Each --repeat is
// <code>:<holdMs>:<everyMs>: the key goes down every <everyMs> and comes back up <holdMs> later. Codes are DOM
// KeyboardEvent.code values; the virtual key code is derived so pages that read either one behave the same.
const KEYS = {
  KeyZ: ['z', 90], KeyX: ['x', 88], KeyC: ['c', 67], Enter: ['Enter', 13], Escape: ['Escape', 27],
  ShiftLeft: ['Shift', 16], ShiftRight: ['Shift', 16], ControlLeft: ['Control', 17], ControlRight: ['Control', 17],
  ArrowLeft: ['ArrowLeft', 37], ArrowUp: ['ArrowUp', 38],
  ArrowRight: ['ArrowRight', 39], ArrowDown: ['ArrowDown', 40], Space: [' ', 32],
};
const repeats = [];
for (let i = 0; i < process.argv.length; i++) {
  if (process.argv[i] !== '--repeat') continue;
  const spec = (process.argv[i + 1] ?? '').split(':').map(Number);
  const code = (process.argv[i + 1] ?? '').split(':')[0];
  const [, hold, every] = spec;
  if (!KEYS[code]) throw Error(`--repeat does not know the key ${code}`);
  if (!(hold > 0) || !(every >= hold)) throw Error(`--repeat ${process.argv[i + 1]} needs <holdMs> <= <everyMs>`);
  repeats.push({ code, hold, every, next: 0, up: -1 });
}

const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find(existsSync);
if (!CHROME) throw Error('no headless-capable Chrome or Edge found');

mkdirSync(outDir, { recursive: true });
// A fresh profile per run. A reused one can restore a blank tab, and the target choice below then lands on it:
// every probe reads an empty page and every screenshot is the same blank frame - which looks like a quiet run.
const profile = mkdtempSync(resolve(root, 'tools/tmp/browser-profile-'));

// No --disable-gpu: under remote debugging that makes canvas.getContext('webgl2')
// return null even with --enable-unsafe-swiftshader. Verified against six flag
// sets in tools/tmp/glprobe.mjs.
const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--enable-unsafe-swiftshader',
  '--no-first-run', '--no-default-browser-check', '--mute-audio',
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  '--window-size=640,540', url,
], { stdio: 'ignore' });

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function target() {
  for (let attempt = 0; attempt < 100; attempt++) {
    try {
      const list = await fetch(`http://127.0.0.1:${port}/json/list`).then(r => r.json());
      const page = list.find(t => t.type === 'page' && t.webSocketDebuggerUrl);
      if (page) return page.webSocketDebuggerUrl;
    } catch {}
    await sleep(200);
  }
  throw Error('Chrome never exposed a page target');
}

const socket = new WebSocket(await target());
await new Promise((ok, bad) => { socket.onopen = ok; socket.onerror = bad; });

let nextId = 0;
const pending = new Map();
const consoleErrors = [];
const consoleAll = [];
const pageErrors = [];
let started = 0;

socket.onmessage = event => {
  const msg = JSON.parse(event.data);
  if (msg.id) {
    const entry = pending.get(msg.id);
    if (!entry) return;
    pending.delete(msg.id);
    msg.error ? entry.reject(Error(msg.error.message)) : entry.resolve(msg.result);
    return;
  }
  if (msg.method === 'Runtime.consoleAPICalled') {
    const text = msg.params.args.map(a => a.value ?? a.description ?? a.type).join(' ');
    consoleAll.push({ type: msg.params.type, text });
    if (msg.params.type === 'error') consoleErrors.push(text);
  }
  if (msg.method === 'Runtime.exceptionThrown')
    pageErrors.push({ ms: Date.now() - started, text:
      msg.params.exceptionDetails.exception?.description
      ?? msg.params.exceptionDetails.text });
};

function send(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve_, reject) => {
    pending.set(id, { resolve: resolve_, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) return { error: r.exceptionDetails.text };
  return { value: r.result.value };
}

await send('Runtime.enable');
await send('Page.enable');
// Optional stable CSS viewport for screenshots that include the whole canvas.
// The default remains unchanged for existing evidence scripts.
const viewport = arg('viewport');
if (viewport) {
  const match = /^(\d+)x(\d+)$/.exec(viewport);
  if (!match || Number(match[1]) < 1 || Number(match[2]) < 1) throw Error('--viewport expects WIDTHxHEIGHT');
  await send('Emulation.setDeviceMetricsOverride', {width:Number(match[1]),height:Number(match[2]),deviceScaleFactor:1,mobile:false});
}

// The first page target is not reliably the one the URL was given as a start argument: a browser can expose a
// blank page first, and then every probe below reads nothing while still reporting no error. Navigating explicitly
// makes which page is under test a property of this run rather than of the browser's startup order.
const here = await evaluate('document.location.href');
if (String(here.value ?? '') !== new URL(url).href) {
  await send('Page.navigate', { url });
}

// Timestamps are taken from the same clock as the sample loop below, so a scheduled press lands where the
// specification says regardless of how long a screenshot or evaluation took.
const press = (code, down) => {
  const [key, vk] = KEYS[code];
  return send('Input.dispatchKeyEvent', {
    type: down ? 'keyDown' : 'keyUp', key, code,
    windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk,
    text: down && key.length === 1 ? key : undefined,
  });
};
function serviceKeys(elapsed) {
  for (const r of repeats) {
    if (r.up >= 0 && elapsed >= r.up) { press(r.code, false).catch(() => {}); r.up = -1; }
    if (r.up < 0 && elapsed >= r.next) { press(r.code, true).catch(() => {}); r.up = r.next + r.hold; r.next += r.every; }
  }
}

// Some of the shipped hosts reach their running state from a click handler and only accept keys afterwards, so a
// keyboard-only proof shows a title screen and reports no error - which reads like success and is not. The click is
// a real mouse click at the element's centre, not a scripted call to its handler, so the path taken is the one a
// user takes.
async function clickAt(selector) {
  const box = await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});
    if(!e)return {missing:true};const r=e.getBoundingClientRect();
    return {x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height};})()`);
  if (box.error) { clickNote = 'evaluate failed: ' + box.error; return false; }
  if (!box.value || box.value.missing) { clickNote = 'no element for ' + selector; return false; }
  const { x, y } = box.value;
  const common = { x, y, button: 'left', clickCount: 1 };
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', ...common });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', ...common });
  clickNote = `clicked ${selector} at ${Math.round(x)},${Math.round(y)} (${Math.round(box.value.w)}x${Math.round(box.value.h)})`;
  return true;
}
let clickNote = '';

// Give the page until it reports either an error or a running game, then keep
// watching for the rest of the budget so late failures are still caught.
const deadline = Date.now() + waitMs;
started = Date.now();
const timeline = [];
let status = null;
let clicked = false;
// The start control, if the page has one. Clicking it is what a user does; keys alone are not enough when the
// host waits for it, and the proof should fail loudly rather than pass on a title screen.
const clickSelector = arg('click', '');
// The page the target actually points at must be the harness page before any probe means anything. Without this,
// an empty tab produces a report full of empty strings and a screenshot nobody can tell apart from a title screen.
for (let i = 0; i < 50; i++) {
  const ready = await evaluate("!!document.getElementById('canvas')");
  if (ready.value) break;
  if (i === 49) throw Error('the target page has no #canvas: the proof would read an empty tab');
  await sleep(200);
}
const clickAfterMs = Number(arg('click-after', '1200'));
// A stall is only visible in the samples around it, so the period and the number kept are both settable.
const sampleMs = Number(arg('sample', '1000'));
const keepAll = process.argv.includes('--all-samples');
// The run's policy cannot dodge, so a proof of the campaign needs the player kept alive while the stage machinery is
// what is being watched. The page exposes the switch next to its other verification hooks.
const invincible = process.argv.includes('--invincible');
const clickCount = Number(arg('clicks', '1'));
let clicks = 0, lastClickAt = 0;
while (Date.now() < deadline) {
  serviceKeys(Date.now() - deadline + waitMs);
  if (invincible) await evaluate(`window.__th12_keep_invincibility&&window.__th12_keep_invincibility(true)`);
  if (clickSelector.length && clicks < clickCount) {
    // The page's start control initializes the runtime on the first click and only begins a stage on a later
    // one, so a proof that clicks once waits on the title screen - where the frame counter still advances and
    // every reading looks like a running game while `phase` stays 0. Later clicks wait for the page to report
    // that it is running, because the first one also fetches the game's data.
    const running = !!(status && status.value && status.value.probe && status.value.probe.running);
    const due = clicks === 0 ? Date.now() - started >= clickAfterMs : running && Date.now() - lastClickAt >= 2000;
    if (due && await clickAt(clickSelector)) {
      ++clicks; lastClickAt = Date.now(); clicked = true;
      clickNote = `${clicks} click(s): ${clickNote}`;
    }
  }
  if (clickSelector.length && clicks < clickCount && Date.now() - started > Math.max(clickAfterMs + 90000, 90000)) {
    throw Error(`--click ${clickSelector} never landed ${clickCount} time(s): ${clickNote || 'not attempted'}`);
  }
  status = await evaluate(`(()=>{
    const error=document.getElementById('error');
    const health=document.getElementById('health');
    const welcome=document.getElementById('welcome');
    const pause=document.getElementById('pause-panel');
    const loading=document.getElementById('status');
    return {error:error&&!error.hidden?error.textContent:'', health:health?health.textContent:'',
            loading:loading?loading.textContent:'',
            welcomeHidden:!!(welcome&&welcome.hidden),
            paused:!!(pause&&!pause.hidden),
            probe:typeof window.__th12_probe==='function'?window.__th12_probe():null};
  })()`);
  timeline.push({ ms: Date.now() - started, ...(status.value ?? {}) });
  // Run the whole budget unless the page reports a failure: title idleness can
  // trigger the attract demo after ~1800 frames, and that is worth waiting for.
  if (status.value?.error) break;
  await sleep(sampleMs);
}

const frames = [];
for (let i = 0; i < shots; i++) {
  if (i) await sleep(interval);
  const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  const name = `${prefix}${i ? '-' + i : ''}.png`;
  const file = resolve(outDir, name);
  writeFileSync(file, Buffer.from(shot.data, 'base64'));
  frames.push({ file: name, bytes: Buffer.from(shot.data, 'base64').length });
}

const report = {
  url, chrome: CHROME, dom: status?.value ?? null,
  consoleErrors, console: consoleAll,
  pageErrors,
  started: status?.value?.health ? true : false,
  clicked,
  clicks,
  clickNote,
  argv: process.argv.slice(2),
  timeline: (keepAll ? timeline : timeline.filter((e, i) => i % 5 === 0 || e.error)).slice(0, keepAll ? 4000 : 40),
  frames,
};
writeFileSync(resolve(outDir, 'browser-proof.json'), JSON.stringify(report, null, 2) + '\n');

// A run is judged on more than the absence of errors. Every failure mode seen so far - a 404 entry, a restored
// blank tab, a click that never landed, a host waiting for a start it never got - produced a report with no errors
// in it. This turns the properties that were actually required into conditions the run checks for itself, and fails
// on them, so "ran clean" and "played the game" cannot be the same result again.
const stages = timeline.map(t => Number(/(?:^|\s)stage=(\d+)/.exec(t.health ?? '')?.[1])).filter(Number.isFinite);
const observed = {
  stageMax: stages.length ? Math.max(...stages) : null,
  framesServed: Math.max(0, ...frames.map(f => f.bytes)),
};
const expectStart = arg('expect-start') !== null;
const expectStage = arg('expect-stage') === null ? null : Number(arg('expect-stage'));
// The health line cannot tell the title from a stage. The title increments the same frame counter on its own
// update path, so "stage=0 frame=384" at sixty frames a second is a title screen and reads exactly like play.
// The probe reports the session phase, and phase 1 is the only reading that means a stage is being played.
const inStage = timeline.filter(t => t.probe && t.probe.phase === 1);
const framesInStage = inStage
  .map(t => Number(/(?:^|\s)frame=(\d+)/.exec(t.health ?? '')?.[1]))
  .filter(Number.isFinite);
const played = { samples: inStage.length, frameMax: framesInStage.length ? Math.max(...framesInStage) : 0 };
const required = [];
// A stage frame that stops advancing while the harness still ticks means the session left its stage phase: the
// game over, result and title branches update menus and animations without incrementing the stage frame, so the
// run looks healthy - sixty ticks a second, no error, no pause panel - while nothing is being played. This is
// checked rather than assumed, because one bomb press is enough to reach that state.
if (expectStart && process.argv.includes('--expect-progress')) {
  const recent = timeline.slice(-8)
    .map(t => Number(/(?:^|\s)frame=(\d+)/.exec(t.health ?? '')?.[1]))
    .filter(Number.isFinite);
  const everAdvanced = timeline.some(t => /frame=(\d+)/.test(t.health ?? ''));
  if (!everAdvanced) required.push('no stage frame was ever reported');
  else if (recent.length >= 8 && new Set(recent).size === 1) {
    required.push(`the stage frame stopped advancing at ${recent[0]} for the last ${recent.length} samples`);
  }
}
if (expectStart && (pageErrors.length || consoleErrors.length)) {
  required.push(`${pageErrors.length} page and ${consoleErrors.length} console errors`);
}
if (expectStart && !report.started) required.push('the run never reported a health line');
if (expectStart && clickSelector.length && !clicked) required.push(`--click ${clickSelector} never landed (${clickNote || 'not attempted'})`);
if (expectStage !== null && !(observed.stageMax >= expectStage)) {
  required.push(`no stage at or past ${expectStage} was reached (saw ${observed.stageMax ?? 'none'})`);
}
if (expectStage !== null && played.samples === 0) {
  required.push('the run never reported phase 1: every stage reading may be the title screen, which counts frames too');
}
if (expectStart && observed.framesServed < 5000) {
  required.push(`the largest frame was ${observed.framesServed} bytes, which is the size a blank or error page produces`);
}

// The compact record is what a checkout without a browser can check, so it is written to a tracked path.
const recordPath = arg('record');
if (recordPath) {
  const record = {
    kind: 'th12-browser-run',
    url,
    started: report.started,
    clicked,
    clickNote,
    pageErrors: pageErrors.length,
    consoleErrors: consoleErrors.length,
    stageMax: observed.stageMax,
    framesServed: observed.framesServed,
    seconds: Math.round((Date.now() - started) / 1000),
    samples: timeline.length,
    stageTransitions: stages.filter((s, i) => i > 0 && s !== stages[i - 1]).length,
    // The order the stages were reached in, and the phases seen, because a run that jumps stages by other means
    // would still report the same maximum: five stages and an ending are only evidence if they came in order.
    stageSequence: stages.filter((s, i) => i === 0 || s !== stages[i - 1]),
    phaseMax: timeline.reduce((m, t) => Math.max(m, t.probe?.phase ?? -1), -1),
    phaseSequence: timeline.map(t => t.probe?.phase).filter((p, i, a) => p !== undefined && p !== null && (i === 0 || p !== a[i - 1])),
    playedSamples: played.samples,
    playedFrameMax: played.frameMax,
  };
  writeFileSync(resolve(root, recordPath), JSON.stringify(record, null, 2) + '\n');
}
console.log(JSON.stringify({ ...report, observed, required }));
if (required.length) {
  socket.close(); chrome.kill();
  console.error('browser proof failed: ' + required.join('; '));
  process.exit(1);
}

socket.close();
chrome.kill();
