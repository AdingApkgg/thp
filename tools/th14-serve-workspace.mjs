import assert from 'node:assert/strict';
import {createServer, request as httpRequest} from 'node:http';
import {readFileSync, realpathSync} from 'node:fs';
import {resolve, relative, extname, isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {Readable} from 'node:stream';
import {runInNewContext} from 'node:vm';

const root = resolve(import.meta.dirname, '..');
export const ORIGIN = 'http://127.0.0.1:8208';
const quietPath = '/__workspace/quiet-audio.js';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const mime = {'.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8',
  '.mjs':'text/javascript; charset=utf-8', '.css':'text/css; charset=utf-8',
  '.json':'application/json; charset=utf-8', '.wasm':'application/wasm',
  '.png':'image/png', '.svg':'image/svg+xml', '.jpg':'image/jpeg', '.webp':'image/webp',
  '.ico':'image/x-icon', '.woff':'font/woff', '.woff2':'font/woff2', '.flac':'audio/flac'};

// ROOT may add another reviewed literal mapping here. No CLI target, wildcard
// filesystem root, host/port/query selector or generic proxy endpoint exists.
export const CHECKS = Object.freeze([Object.freeze({
  mount: '/checks/deferred-copy-success/', host: '127.0.0.1', port: 8254,
  html: 'tools/th14-deferred-capture-webgl.html',
  native: 'artifacts/th14/deferred-capture-pixels-oct14',
  runtime: 'artifacts/th14/deferred-capture-success-dirty-oct14',
  runtimeFiles: Object.freeze(['webgl-build.json', 'capture.mjs', 'capture.wasm']),
  postPaths: Object.freeze(['/capture/report.json', ...Array.from({length:8},
    (_, i) => '/capture/portable-' + String(i).padStart(3, '0') + '.pixels')]),
})]);

function inside(base, path) {
  const name = relative(base, path);
  assert(name && !isAbsolute(name) && name !== '..' && !name.startsWith('..\\') && !name.startsWith('../'));
}
function checkedPath(base, name) {
  assert(typeof name === 'string' && !name.includes('\\') && !name.includes('%'));
  assert(!isAbsolute(name) && name.split('/').every(s => s && s !== '.' && s !== '..'));
  const path = realpathSync(resolve(base, name)); inside(base, path); return path;
}
function bytesVerified(entry) {
  const bytes = readFileSync(entry.path);
  assert.equal(sha(bytes), entry.sha256, 'Changed frozen file: ' + entry.path);
  if (entry.bytes != null) assert.equal(bytes.length, entry.bytes, entry.path);
  return bytes;
}
function snapshot(path, expected = {}) {
  const bytes = readFileSync(path), entry = {path, bytes:bytes.length, sha256:sha(bytes)};
  if (expected.sha256 != null) assert.equal(entry.sha256, expected.sha256, path);
  if (expected.bytes != null) assert.equal(entry.bytes, expected.bytes, path);
  return entry;
}
export function rewriteDiagnosticHtml(bytes, mount) {
  const original = bytes.toString('utf8');
  assert(!/<audio\b|\b(?:Audio|AudioContext|webkitAudioContext)\s*\(/i.test(original), 'Diagnostic must be silent');
  const rewritten = original
    .replace(/((?:fetch|import)\(\s*['"])\/(?!\/)/g, '$1' + mount)
    .replace(/(locateFile\s*:\s*[A-Za-z_$][\w$]*\s*=>\s*['"])\/(?!\/)/g, '$1' + mount);
  assert(!/\b(?:fetch|import)\(\s*['"]\/(?!checks\/)/.test(rewritten));
  assert(!/locateFile\s*:\s*[A-Za-z_$][\w$]*\s*=>\s*['"]\/(?!checks\/)/.test(rewritten));
  // The reverse transform must reproduce every original HTML byte.
  assert.equal(rewritten.replaceAll(mount, '/'), original);
  return Buffer.from(rewritten, 'utf8');
}
export function injectQuietHtml(bytes) {
  const html = bytes.toString('utf8');
  const script = `<script src="${quietPath}"></script>`;
  const head = /<head(?:\s[^>]*)?>/i.exec(html);
  if (head) return Buffer.from(html.slice(0, head.index + head[0].length) + script + html.slice(head.index + head[0].length));
  const doctype = /^\s*<!doctype[^>]*>/i.exec(html);
  const at = doctype ? doctype[0].length : 0;
  return Buffer.from(html.slice(0, at) + script + html.slice(at));
}

export function prepareWorkspace(reportName) {
  assert(/^[a-z0-9-]+\.json$/.test(reportName), 'Use a docs/porting report filename');
  const reportPath = resolve(root, 'docs/porting', reportName);
  const proof = JSON.parse(readFileSync(reportPath)); assert.equal(proof.passed, true);
  const site = realpathSync(resolve(proof.site));
  const allowedSite = realpathSync(resolve(root, 'runtimes/th14/th14_web/artifacts/launcher-preview'));
  inside(allowedSite, site);
  const files = new Map();
  for (const [name, expected] of Object.entries(proof.files)) {
    assert(/^[0-9a-f]{64}$/.test(expected.sha256));
    files.set('/' + name, snapshot(checkedPath(site, name), expected));
  }
  assert.equal(files.size, 127, 'Expected the frozen Launcher127 inventory');
  if (!files.has('/files.json')) files.set('/files.json', snapshot(checkedPath(site, 'files.json')));
  const checks = CHECKS.map(config => {
    assert.equal(config.host, '127.0.0.1'); assert.equal(config.port, 8254);
    const nativeRoot = realpathSync(resolve(root, config.native)); inside(root, nativeRoot);
    const runtimeRoot = realpathSync(resolve(root, config.runtime)); inside(root, runtimeRoot);
    const native = JSON.parse(readFileSync(checkedPath(nativeRoot, 'native.json')));
    assert.equal(native.cases.length, 8);
    const routes = new Map([['/', snapshot(checkedPath(root, config.html))]]);
    routes.set('/native.json', snapshot(checkedPath(nativeRoot, 'native.json')));
    const sourceBinding = native.bindings.find(b => b.path.endsWith('source.bgra'));
    assert(sourceBinding); routes.set('/source.bgra', snapshot(checkedPath(nativeRoot, 'source.bgra'), sourceBinding));
    for (const row of native.cases) {
      assert(/^[a-z0-9._-]+$/.test(row.pixelFile));
      routes.set('/' + row.pixelFile, snapshot(checkedPath(nativeRoot, row.pixelFile), {sha256:row.pixelSha256, bytes:row.bytes}));
    }
    for (const name of config.runtimeFiles) routes.set('/' + name, snapshot(checkedPath(runtimeRoot, name)));
    const build = JSON.parse(bytesVerified(routes.get('/webgl-build.json')));
    assert.equal(routes.get('/capture.wasm').sha256, build.wasmSha256);
    const rewritten = rewriteDiagnosticHtml(bytesVerified(routes.get('/')), config.mount);
    return {...config, routes, rewritten, rewrittenSha256:sha(rewritten)};
  });
  const quiet = snapshot(checkedPath(root, 'tools/th14-local-quiet-audio.js'));
  return {reportName, reportSha256:sha(readFileSync(reportPath)), site, files, checks, quiet};
}

function requestPath(raw) {
  assert(typeof raw === 'string' && raw.startsWith('/') && !raw.startsWith('//') && !raw.includes('#'));
  const queryAt = raw.indexOf('?'), rawPath = queryAt < 0 ? raw : raw.slice(0, queryAt);
  assert(!/%(?:2f|5c)/i.test(rawPath));
  const path = decodeURIComponent(rawPath);
  assert(!path.includes('\\') && !path.includes('%') && !path.includes('\0'));
  assert(path.split('/').every(s => s !== '.' && s !== '..'));
  return {path, query:queryAt >= 0};
}
async function bodyLimited(req) {
  const parts = []; let length = 0;
  for await (const part of req) {length += part.length; assert(length < 2_000_000); parts.push(part);}
  return Buffer.concat(parts);
}
async function fixedForward(check, method, path, body, contentType) {
  assert.equal(check.host, '127.0.0.1'); assert.equal(check.port, 8254);
  return new Promise((accept, reject) => {
    const request = httpRequest({host:check.host, port:check.port, path, method,
      headers:method === 'POST' ? {'Content-Length':body.length, 'Content-Type':contentType || 'application/octet-stream'} : {}}, response => {
      const parts = []; let length = 0;
      response.on('data', part => {length += part.length; if (length > 8_000_000) response.destroy(new Error('Diagnostic response exceeds bound')); else parts.push(part);});
      response.on('error', reject);
      response.on('end', () => accept({status:response.statusCode, contentType:response.headers['content-type'], body:Buffer.concat(parts)}));
    });
    request.setTimeout(15_000, () => request.destroy(new Error('Diagnostic upstream timeout')));
    request.on('error', reject); request.end(method === 'POST' ? body : undefined);
  });
}
export function createWorkspaceHandler(state, forward = fixedForward, reportError = error => console.error(error.message)) {
  return async (req, res) => {
    for (const [name, value] of Object.entries({'Cross-Origin-Opener-Policy':'same-origin',
      'Cross-Origin-Embedder-Policy':'require-corp', 'Cross-Origin-Resource-Policy':'same-origin', 'Cache-Control':'no-store'})) res.setHeader(name, value);
    try {
      const {path, query} = requestPath(req.url), method = req.method;
      if (path === quietPath) {
        if (!['GET', 'HEAD'].includes(method)) return res.writeHead(405).end();
        const bytes = bytesVerified(state.quiet);
        res.setHeader('Content-Type', mime['.js']); res.setHeader('Content-Length', bytes.length);
        return res.writeHead(200).end(method === 'HEAD' ? undefined : bytes);
      }
      const check = state.checks.find(c => path.startsWith(c.mount));
      if (path.startsWith('/checks/') && !check) return res.writeHead(404).end('Unmapped diagnostic');
      if (check) {
        if (query) return res.writeHead(400).end('Diagnostic query selectors are not supported');
        const upstreamPath = '/' + path.slice(check.mount.length);
        if (!['GET', 'HEAD', 'POST'].includes(method)) return res.writeHead(405).end();
        if (method === 'POST' ? !check.postPaths.includes(upstreamPath) : !check.routes.has(upstreamPath)) return res.writeHead(404).end('Unmapped diagnostic file');
        const body = method === 'POST' ? await bodyLimited(req) : Buffer.alloc(0);
        // HEAD uses a verified GET internally and emits no body to the browser.
        const response = await forward(check, method === 'HEAD' ? 'GET' : method, upstreamPath, body, req.headers['content-type']);
        if (response.status !== 200) return res.writeHead(response.status).end(method === 'HEAD' ? undefined : response.body);
        let bytes = response.body;
        if (method !== 'POST') {
          const entry = check.routes.get(upstreamPath); assert.equal(sha(bytes), entry.sha256, 'Changed diagnostic upstream file');
          assert.equal(bytes.length, entry.bytes);
          if (upstreamPath === '/') bytes = injectQuietHtml(rewriteDiagnosticHtml(bytes, check.mount));
        }
        res.setHeader('Content-Type', upstreamPath === '/' ? mime['.html'] : response.contentType || mime[extname(upstreamPath)] || 'application/octet-stream');
        res.setHeader('Content-Length', bytes.length); return res.writeHead(200).end(method === 'HEAD' ? undefined : bytes);
      }
      if (!['GET', 'HEAD'].includes(method)) return res.writeHead(405).end();
      const name = path === '/' ? '/index.html' : path, entry = state.files.get(name);
      if (!entry) return res.writeHead(404).end('Not found');
      const original = bytesVerified(entry), bytes = extname(name) === '.html' ? injectQuietHtml(original) : original;
      res.setHeader('Content-Type', mime[extname(name)] || 'application/octet-stream');
      res.setHeader('Content-Length', bytes.length); return res.writeHead(200).end(method === 'HEAD' ? undefined : bytes);
    } catch (error) {
      res.writeHead(500).end('Workspace integrity/request failure');
      reportError(error);
    }
  };
}

export async function checkReadOnly(state) {
  let assertions = 0; const test = (actual, expected) => {assert.deepEqual(actual, expected); ++assertions;};
  const forwarded = [];
  const forward = async (check, method, path, body) => {
    forwarded.push({host:check.host, port:check.port, method, path, bodySha256:sha(body)});
    return {status:200, contentType:method === 'POST' ? mime['.json'] : mime[extname(path)],
      body:method === 'POST' ? Buffer.from('{"saved":true}') : bytesVerified(check.routes.get(path))};
  };
  const rejected = [], recordRejection = error => rejected.push(error.message);
  const handler = createWorkspaceHandler(state, forward, recordRejection);
  async function simulate(url, method = 'GET', body = Buffer.alloc(0), use = handler) {
    const req = Readable.from(body.length ? [body] : []); Object.assign(req, {url, method, headers:{}});
    const res = {headers:{}, setHeader(name, value){this.headers[name] = value;},
      writeHead(status){this.status = status; return this;}, end(bytes){this.body = bytes; return this;}};
    await use(req, res); return res;
  }
  let response = await simulate('/'); test(response.status, 200); test(sha(response.body), sha(injectQuietHtml(bytesVerified(state.files.get('/index.html')))));
  response = await simulate('/', 'HEAD'); test(response.status, 200); test(response.body, undefined);
  for (const url of ['/missing', '/checks/unknown/', '/checks/deferred-copy-success/missing', '/checks/deferred-copy-success/capture/not-allowed']) test((await simulate(url)).status, 404);
  test((await simulate('/', 'POST')).status, 405);
  test((await simulate('/checks/deferred-copy-success/', 'PUT')).status, 405);
  for (const url of ['/checks/deferred-copy-success/?host=evil', '/checks/deferred-copy-success/?port=1', '/checks/deferred-copy-success/capture.wasm?x=1']) test((await simulate(url)).status, 400);
  const beforeBadRequests = forwarded.length;
  for (const url of ['http://evil/', '//evil/', '/checks/deferred-copy-success/../native.json', '/%2e%2e/private', '/checks/deferred-copy-success/%2fcapture.wasm', '/checks/deferred-copy-success/%252e%252e', '/checks/deferred-copy-success/%ZZ']) test((await simulate(url)).status, 500);
  test(forwarded.length, beforeBadRequests);
  const check = state.checks[0];
  for (const [name, entry] of check.routes) {
    response = await simulate(check.mount + name.slice(1)); test(response.status, 200);
    test(sha(response.body), name === '/' ? sha(injectQuietHtml(check.rewritten)) : entry.sha256);
  }
  response = await simulate(check.mount + 'capture.wasm', 'HEAD'); test(response.status, 200); test(response.body, undefined);
  const payload = Buffer.from('Declared POST unit only, never sent to the upstream');
  for (const name of check.postPaths) {
    response = await simulate(check.mount + name.slice(1), 'POST', payload); test(response.status, 200);
    test(forwarded.at(-1), {host:'127.0.0.1', port:8254, method:'POST', path:name, bodySha256:sha(payload)});
  }
  const mutatedForward = createWorkspaceHandler(state, async () => ({status:200, body:Buffer.from('declared tamper')}), recordRejection);
  test((await simulate(check.mount + 'capture.wasm', 'GET', Buffer.alloc(0), mutatedForward)).status, 500);
  const altered = {...state, files:new Map(state.files)};
  altered.files.set('/index.html', {...state.files.get('/index.html'), sha256:'0'.repeat(64)});
  test((await simulate('/', 'GET', Buffer.alloc(0), createWorkspaceHandler(altered, forward, recordRejection))).status, 500);
  response = await simulate(quietPath); test(response.status, 200); test(sha(response.body), state.quiet.sha256);
  const htmlFiles = [...state.files].filter(([name]) => extname(name) === '.html');
  for (const [name, entry] of htmlFiles) {
    response = await simulate(name); test(response.status, 200);
    const original = bytesVerified(entry), injected = injectQuietHtml(original);
    test(sha(response.body), sha(injected));
    test(injected.toString().replace(`<script src="${quietPath}"></script>`, ''), original.toString());
    const firstScript = injected.toString().indexOf('<script');
    test(injected.toString().slice(firstScript).startsWith(`<script src="${quietPath}"></script>`), true);
  }
  const quietUnit = checkQuietUnit(bytesVerified(state.quiet));
  return {readOnlyVerified:true, serverStarted:false, networkRequests:0, assertions,
    origin:ORIGIN, report:state.reportName, reportSha256:state.reportSha256,
    declaredRejectedRequests:rejected,
    launcherFiles:127, servedManifestIncluded:state.files.size,
    mappings:state.checks.map(c => ({mount:c.mount, upstream:`http://${c.host}:${c.port}`,
      getPaths:[...c.routes.keys()], postPaths:c.postPaths, sourceHtmlSha256:c.routes.get('/').sha256,
      rewrittenHtmlSha256:c.rewrittenSha256, originalHtmlRecoveredExactly:true, silentHtml:true,
      files:[...c.routes].map(([path, item]) => ({path, bytes:item.bytes, sha256:item.sha256}))})),
    quietAudio:{scriptSha256:state.quiet.sha256, htmlFiles:htmlFiles.length + 1, parentAndRuntimeHtmlCovered:true,
      ...quietUnit, browserExecuted:false,
      officialReferences:['https://developer.mozilla.org/en-US/docs/Web/API/AudioNode/connect',
        'https://developer.mozilla.org/en-US/docs/Web/API/AudioNode/disconnect', 'https://developer.mozilla.org/en-US/docs/Web/API/GainNode']},
    toolSha256:sha(readFileSync(fileURLToPath(import.meta.url))),
    scope:'No server opened or stopped, no POST written or network request sent. Declared request/response units exercise the actual handler and fixed mapping; upstream HTTP/browser execution remains a separate check.'};
}

function checkQuietUnit(script) {
  let assertions = 0;
  const test = (actual, expected) => {assert.deepEqual(actual, expected); ++assertions;};
  const calls = [], badges = [];
  class AudioParam {}
  class AudioNode {
    constructor(context){this.context = context;}
    connect(destination, ...indices){
      calls.push({method:'connect', source:this, destination, indices});
      if (indices[0] != null && indices[0] > 1) throw new Error('Declared IndexSizeError');
      if (indices[1] != null && indices[1] !== 0) throw new Error('Declared IndexSizeError');
      if (destination.context && destination.context !== this.context) throw new Error('Declared InvalidAccessError');
      return destination instanceof AudioParam || this.context.legacy ? undefined : destination;
    }
    disconnect(...args){calls.push({method:'disconnect', source:this, args}); return undefined;}
  }
  class OfflineAudioContext {}
  const document = {readyState:'complete', getElementById:() => null,
    createElement:() => ({style:{}}), body:{appendChild:badge => badges.push(badge)}};
  const sandbox = {AudioNode, OfflineAudioContext, document, console};
  runInNewContext(script.toString(), sandbox, {timeout:1000});
  const context = {createGain(){const gain = new AudioNode(context); gain.gain = {value:1}; return gain;}};
  context.destination = new AudioNode(context);
  const source = new AudioNode(context), other = new AudioNode(context), parameter = new AudioParam();
  test(source.connect(other, 1, 0), other); test(calls.at(-1).destination, other); test(calls.at(-1).indices, [1,0]);
  test(source.connect(parameter, 1), undefined); test(calls.at(-1).destination, parameter);
  const before = calls.length; test(source.connect(context.destination, 1, 0, 'ignored-extra'), context.destination);
  test(calls.length, before + 2); const gain = calls.at(-1).destination;
  test(gain.gain.value, 0); test(calls[before].source, gain); test(calls[before].destination, context.destination);
  test(calls.at(-1).indices, [1,0,'ignored-extra']);
  test(source.connect(context.destination), context.destination); test(calls.at(-1).destination, gain);
  test(calls.length, before + 3);
  test(source.disconnect(context.destination, 1, 0), undefined); test(calls.at(-1).args, [gain,1,0]);
  test(source.disconnect(other, 1, 0), undefined); test(calls.at(-1).args, [other,1,0]);
  test(source.disconnect(), undefined); test(calls.at(-1).args, []);
  test(source.disconnect(1), undefined); test(calls.at(-1).args, [1]);
  test(source.disconnect(parameter), undefined); test(calls.at(-1).args, [parameter]);
  for (const args of [[context.destination,2,0], [context.destination,0,1]]) {
    assert.throws(() => source.connect(...args), /IndexSizeError/); ++assertions;
  }
  context.legacy = true; test(source.connect(context.destination), undefined); context.legacy = false;
  const offline = new OfflineAudioContext(); offline.destination = new AudioNode(offline);
  const offlineSource = new AudioNode(offline); test(offlineSource.connect(offline.destination), offline.destination);
  test(calls.at(-1).destination, offline.destination);
  const firstConnect = AudioNode.prototype.connect;
  runInNewContext(script.toString(), sandbox, {timeout:1000}); test(AudioNode.prototype.connect, firstConnect);
  test(badges[0].textContent, '本机测试静音');
  return {declaredUnitAssertions:assertions, finalDestinationGain:0, normalGraphAndAudioParamPreserved:true,
    overloadIndicesReturnAndDisconnectPreserved:true, offlineRenderingPreserved:true,
    dependency:'Declared AudioNode/AudioParam/DOM recorder, no hardware audio'};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2), at = args.indexOf('--report');
  assert(at >= 0 && args[at + 1], 'Usage: node tools/th14-serve-workspace.mjs --report NAME.json [--check]');
  const rest = args.filter((_, i) => i !== at && i !== at + 1);
  assert(rest.length === 0 || (rest.length === 1 && rest[0] === '--check'), 'Only --report and --check are supported');
  const state = prepareWorkspace(args[at + 1]);
  if (rest.includes('--check')) console.log(JSON.stringify(await checkReadOnly(state), null, 2));
  else createServer(createWorkspaceHandler(state)).listen(8208, '127.0.0.1', () => {
    console.log(`TH14 workspace: ${ORIGIN}/ (${127} frozen Launcher files; report ${state.reportName})`);
    for (const check of state.checks) console.log(`Diagnostic: ${ORIGIN}${check.mount} -> fixed localhost:${check.port}`);
  });
}
