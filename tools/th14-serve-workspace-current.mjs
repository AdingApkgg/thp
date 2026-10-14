import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {Readable} from 'node:stream';
import {runInNewContext} from 'node:vm';
import {prepareWorkspace, ORIGIN} from './th14-serve-workspace.mjs';
import {createDirectWorkspaceHandler} from './th14-serve-workspace-direct.mjs';

const root = resolve(import.meta.dirname, '..');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const swPath = '/app-shell-sw.js';
const headers = Object.freeze({'Cross-Origin-Opener-Policy':'same-origin',
  'Cross-Origin-Embedder-Policy':'require-corp', 'Cross-Origin-Resource-Policy':'same-origin',
  'Cache-Control':'no-store'});
const frozenSources = Object.freeze({
  'th14-serve-workspace.mjs':'18ebc5a34401dd57b07305d1135edc851885835b28c0a5efc7fd5d634cf619ca',
  'th14-serve-workspace-direct.mjs':'d62f6d696fbd425f87084f5ffd5fbc6852b839d162187a5c4356493145bf020c',
  'th14-serve-workspace-links.mjs':'102872ea4908e7b364460160d56825b989dc8579ea151381d12c6977dba934e8',
  'th14-local-quiet-audio.js':'216745e0d5459c0546e3fed01866092e67f40c383380dd47c5aafa5bac4a134c',
});

// Local preview response only: retain stored caches and saves, while replacing
// the controlling worker with one that lets every fetch reach the local server.
export const LOCAL_SW_SOURCE = "// TH14 local workspace passthrough; never packaged for release.\n" +
  "self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));\n" +
  "self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));\n";

function publishedSw(state) {
  const entry = state.files.get(swPath); assert(entry, 'Frozen published SW missing');
  const bytes = readFileSync(entry.path);
  assert.equal(sha(bytes), entry.sha256, 'Changed frozen published SW');
  assert.equal(bytes.length, entry.bytes, 'Changed frozen published SW length');
  return {entry, bytes};
}
export function prepareCurrentWorkspace(reportName) {
  assert.equal(ORIGIN, 'http://127.0.0.1:8208');
  for (const [name, expected] of Object.entries(frozenSources))
    assert.equal(sha(readFileSync(resolve(root, 'tools', name))), expected, name);
  const state = prepareWorkspace(reportName); publishedSw(state); return state;
}
export function createCurrentWorkspaceHandler(state, delegate = createDirectWorkspaceHandler(state)) {
  return async (req, res) => {
    // Query strings follow the original static-file policy; only the canonical
    // SW pathname is adapted. Encoded/traversal paths retain the old parser.
    const canonicalSw = typeof req.url === 'string' && !req.url.includes('#') &&
      req.url.split('?')[0] === swPath;
    if (!canonicalSw || !['GET', 'HEAD'].includes(req.method)) return delegate(req, res);
    for (const [name, value] of Object.entries(headers)) res.setHeader(name, value);
    try {
      publishedSw(state); // Check the original bytes on every GET/HEAD first.
      const bytes = Buffer.from(LOCAL_SW_SOURCE, 'utf8');
      res.setHeader('Content-Type', 'text/javascript; charset=utf-8');
      res.setHeader('Content-Length', bytes.length);
      return res.writeHead(200).end(req.method === 'HEAD' ? undefined : bytes);
    } catch {
      return res.writeHead(500).end('Workspace published SW integrity failure');
    }
  };
}
export async function checkCurrentReadOnly(state) {
  let assertions = 0;
  const test = (actual, expected) => {assert.deepEqual(actual, expected); ++assertions;};
  const original = publishedSw(state), local = Buffer.from(LOCAL_SW_SOURCE, 'utf8');
  const handler = createCurrentWorkspaceHandler(state);
  async function simulate(url, method = 'GET', use = handler) {
    const req = Readable.from([]); Object.assign(req, {url, method, headers:{}});
    const res = {headers:{}, setHeader(name, value){this.headers[name] = value;},
      writeHead(status){this.status = status; return this;}, end(body){this.body = body; return this;}};
    await use(req, res); return res;
  }
  let response = await simulate(swPath);
  test(response.status, 200); test(sha(response.body), sha(local));
  test(response.headers['Content-Length'], local.length);
  for (const [name, value] of Object.entries(headers)) test(response.headers[name], value);
  response = await simulate(swPath, 'HEAD');
  test(response.status, 200); test(response.body, undefined); test(response.headers['Content-Length'], local.length);
  response = await simulate(swPath + '?local-check=1'); test(sha(response.body), sha(local));
  const altered = {...state, files:new Map(state.files)};
  altered.files.set(swPath, {...original.entry, sha256:'0'.repeat(64)});
  test((await simulate(swPath, 'GET', createCurrentWorkspaceHandler(altered))).status, 500);
  const delegated = [], spy = createCurrentWorkspaceHandler(state, async (req, res) => {
    delegated.push({url:req.url, method:req.method}); return res.writeHead(204).end();
  });
  for (const [url, method] of [['/', 'GET'], ['/checks/deferred-copy-success/', 'GET'],
    ['/checks/deferred-copy-success/capture/report.json', 'POST'], [swPath, 'POST'],
    ['/checks/deferred-copy-success/../native.json', 'GET']]) {
    test((await simulate(url, method, spy)).status, 204);
    test(delegated.at(-1), {url, method});
  }
  // Declared Service Worker event model only: no browser, registration, cache
  // access, network, storage access or actual POST writer is invoked here.
  const events = new Map(), calls = [], waits = [];
  const self = {addEventListener(name, callback){events.set(name, callback);},
    skipWaiting(){calls.push('skipWaiting'); return Promise.resolve();},
    clients:{claim(){calls.push('clients.claim'); return Promise.resolve();}}};
  runInNewContext(LOCAL_SW_SOURCE, {self}, {timeout:1000});
  test([...events.keys()], ['install', 'activate']);
  for (const name of ['install', 'activate']) events.get(name)({waitUntil(value){waits.push(value);}});
  await Promise.all(waits); test(calls, ['skipWaiting', 'clients.claim']); test(waits.length, 2);
  test(sha(readFileSync(original.entry.path)), original.entry.sha256);
  return {readOnlyVerified:true, serverStarted:false, networkRequests:0, actualEvidenceWrites:0,
    browserExecuted:false, assertions, origin:ORIGIN, report:state.reportName,
    reportSha256:state.reportSha256, adaptedPath:swPath, adaptedMethods:['GET', 'HEAD'],
    publishedSw:{path:original.entry.path, bytes:original.entry.bytes, sha256:original.entry.sha256},
    localSw:{bytes:local.length, sha256:sha(local), source:LOCAL_SW_SOURCE,
      installSkipWaiting:true, activateClientsClaim:true, fetchListener:false,
      cacheDeletion:false, saveDeletion:false}, frozenSources,
    toolSha256:sha(readFileSync(fileURLToPath(import.meta.url))),
    scope:'Local response adapter only; each SW request verifies the untouched frozen published file before serving the passthrough worker. All other requests and fixed POST persistence remain delegated to the frozen direct handler. Declared event/HTTP units do not prove browser takeover or physical execution. No existing server, cache, save, evidence or release source is changed.'};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2), at = args.indexOf('--report');
  assert(at >= 0 && args[at + 1], 'Usage: node tools/th14-serve-workspace-current.mjs --report NAME.json [--check]');
  const rest = args.filter((_, i) => i !== at && i !== at + 1);
  assert(rest.length === 0 || (rest.length === 1 && rest[0] === '--check'));
  const state = prepareCurrentWorkspace(args[at + 1]);
  if (rest.includes('--check')) console.log(JSON.stringify(await checkCurrentReadOnly(state), null, 2));
  else createServer(createCurrentWorkspaceHandler(state)).listen(8208, '127.0.0.1', () =>
    console.log(`TH14 current workspace: ${ORIGIN}/ (${state.reportName}; local passthrough SW, direct diagnostics)`));
}
