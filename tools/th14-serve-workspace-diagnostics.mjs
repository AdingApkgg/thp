import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync, writeFileSync, mkdirSync, realpathSync, lstatSync} from 'node:fs';
import {resolve, relative, isAbsolute, extname, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {Readable} from 'node:stream';
import {prepareCurrentWorkspace, createCurrentWorkspaceHandler} from './th14-serve-workspace-current.mjs';
import {createWorkspaceHandler, injectQuietHtml, ORIGIN} from './th14-serve-workspace.mjs';

// Only the pinned descriptor changes between experiments. The current/site,
// quiet and local SW implementation remain imported and hash-bound.
const root = realpathSync(resolve(import.meta.dirname, '..'));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const frozenSources = Object.freeze({
  'th14-serve-workspace-current.mjs':'36accd68398804cb03803d2bc28d4f01d4d199633bba1536e32b6c33a5f07293',
  'th14-serve-workspace.mjs':'18ebc5a34401dd57b07305d1135edc851885835b28c0a5efc7fd5d634cf619ca',
  'th14-serve-workspace-direct.mjs':'d62f6d696fbd425f87084f5ffd5fbc6852b839d162187a5c4356493145bf020c',
  'th14-serve-workspace-links.mjs':'102872ea4908e7b364460160d56825b989dc8579ea151381d12c6977dba934e8',
  'th14-local-quiet-audio.js':'216745e0d5459c0546e3fed01866092e67f40c383380dd47c5aafa5bac4a134c',
});
const headers = Object.freeze({'Cross-Origin-Opener-Policy':'same-origin',
  'Cross-Origin-Embedder-Policy':'require-corp', 'Cross-Origin-Resource-Policy':'same-origin',
  'Cache-Control':'no-store'});
const mime = Object.freeze({'.html':'text/html; charset=utf-8', '.mjs':'text/javascript; charset=utf-8',
  '.js':'text/javascript; charset=utf-8', '.json':'application/json; charset=utf-8', '.wasm':'application/wasm',
  '.bin':'application/octet-stream', '.bgra':'application/octet-stream', '.rgba32f':'application/octet-stream',
  '.f32':'application/octet-stream', '.u32':'application/octet-stream', '.pixels':'application/octet-stream'});
const jsonLimit = 2_000_000, binaryLimit = 64 * 1024 * 1024;

function exactKeys(value, required, optional = []) {
  assert(value && Object.getPrototypeOf(value) === Object.prototype && !Array.isArray(value), 'Object required');
  assert(required.every(key => Object.hasOwn(value, key)), 'Missing descriptor field');
  assert(Object.keys(value).every(key => [...required, ...optional].includes(key)), 'Unknown descriptor field');
}
function digestString(value) {assert(typeof value === 'string' && /^[0-9a-f]{64}$/.test(value), 'SHA256 required');}
function size(value, bound) {assert(Number.isSafeInteger(value) && value >= 0 && value <= bound, 'Invalid byte bound');}
function segment(value) {
  assert(typeof value === 'string' && /^[a-z0-9_][a-z0-9._-]{0,95}$/i.test(value) && !value.endsWith('.'), 'Literal path segment required');
  assert(!/^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(value), 'Windows device name forbidden');
}
function literalPath(value, empty = false) {
  assert(typeof value === 'string' && value.length <= 512 && (empty && value === '' || value.length), 'Literal relative path required');
  if (value === '' && empty) return;
  assert(!isAbsolute(value));
  for (const part of value.split('/')) segment(part);
}
function contained(base, path) {
  const name = relative(base, path);
  assert(name && !isAbsolute(name) && name !== '..' && !name.startsWith('..\\') && !name.startsWith('../'), 'Path outside allowed root');
}
function noRedirect(path) {
  const name = relative(root, path); contained(root, path);
  let current = root;
  for (const part of name.split(/[\\/]/)) {
    current = resolve(current, part);
    assert(!lstatSync(current).isSymbolicLink(), 'Workspace links are not diagnostic inputs/outputs');
    assert.equal(realpathSync(current).toLowerCase(), current.toLowerCase(), 'Workspace path redirects');
  }
  return path;
}
function localPath(name) {literalPath(name); return noRedirect(resolve(root, name));}
function verified(entry) {
  noRedirect(entry.path);
  const bytes = readFileSync(entry.path);
  assert.equal(bytes.length, entry.bytes, 'Changed diagnostic byte count');
  assert.equal(sha(bytes), entry.sha256, 'Changed diagnostic SHA256');
  return bytes;
}

// version1 schema: {version,slug,artifactRoot,get:[{name,path,bytes,sha256}],
// post:[{name,basename,kind:'json',maxBytes,jsonEquals?} |
//       {name,basename,kind:'bytes',bytes,sha256?}]}.
// name is a literal relative HTTP route ('' is the sole HTML root). POST names
// begin capture/; each basename is one immutable file in artifactRoot/capture.
export function validateDiagnosticDescriptor(value) {
  exactKeys(value, ['version', 'slug', 'artifactRoot', 'get', 'post']);
  assert.equal(value.version, 1); assert(/^[a-z0-9][a-z0-9-]{0,63}$/.test(value.slug), 'Literal slug required');
  literalPath(value.artifactRoot);
  assert(value.artifactRoot.startsWith('artifacts/th14/') && value.artifactRoot.split('/').length >= 3, 'Experiment artifactRoot required');
  assert(Array.isArray(value.get) && value.get.length >= 1 && value.get.length <= 64, 'GET inventory bound');
  assert(Array.isArray(value.post) && value.post.length >= 1 && value.post.length <= 16, 'POST inventory bound');
  const names = new Set(), outputs = new Set(); let html = 0;
  for (const row of value.get) {
    exactKeys(row, ['name', 'path', 'bytes', 'sha256']); literalPath(row.name, true); literalPath(row.path);
    assert(!names.has(row.name), 'Duplicate route'); names.add(row.name); digestString(row.sha256); size(row.bytes, 256 * 1024 * 1024);
    const extension = extname(row.path); assert(Object.hasOwn(mime, extension), 'Unsupported diagnostic input format');
    if (extension === '.html') {
      assert.equal(row.name, ''); assert(row.path.startsWith('tools/'), 'Diagnostic HTML must be a tools file'); ++html;
    } else assert(row.path.startsWith('artifacts/th14/'), 'Diagnostic runtime/input must be a TH14 artifact');
    assert(!row.path.startsWith(value.artifactRoot + '/capture/'), 'Current output is not an input');
  }
  assert.equal(html, 1, 'Exactly one root HTML required');
  for (const row of value.post) {
    if (row.kind === 'json') {
      exactKeys(row, ['name', 'basename', 'kind', 'maxBytes'], ['jsonEquals']); size(row.maxBytes, jsonLimit); assert(row.maxBytes > 0);
      if (row.jsonEquals !== undefined) {
        assert(row.jsonEquals && Object.getPrototypeOf(row.jsonEquals) === Object.prototype);
        assert(Object.keys(row.jsonEquals).length <= 16);
        for (const [key, field] of Object.entries(row.jsonEquals)) {
          assert(/^[a-zA-Z][a-zA-Z0-9_]{0,63}$/.test(key));
          assert(field === null || ['string', 'number', 'boolean'].includes(typeof field));
          if (typeof field === 'number') assert(Number.isFinite(field));
          if (typeof field === 'string') assert(field.length <= 256);
        }
      }
      assert.equal(extname(row.basename), '.json');
    } else {
      assert.equal(row.kind, 'bytes'); exactKeys(row, ['name', 'basename', 'kind', 'bytes'], ['sha256']);
      size(row.bytes, binaryLimit); assert(row.bytes > 0); if (row.sha256 !== undefined) digestString(row.sha256);
      assert(['.pixels', '.rgba32f', '.bgra', '.f32', '.u32', '.bin'].includes(extname(row.basename)));
    }
    literalPath(row.name); assert(row.name.startsWith('capture/') && row.name.split('/').length <= 4, 'Fixed capture route required');
    segment(row.basename); assert(!names.has(row.name) && !outputs.has(row.basename), 'Duplicate capture route/output');
    names.add(row.name); outputs.add(row.basename);
  }
  return value;
}
export function prepareDiagnosticWorkspace(reportName, descriptorName, descriptorSha256) {
  assert.equal(ORIGIN, 'http://127.0.0.1:8208');
  for (const [name, expected] of Object.entries(frozenSources)) assert.equal(sha(readFileSync(resolve(root, 'tools', name))), expected, name);
  literalPath(descriptorName); assert(descriptorName.startsWith('artifacts/th14/') && extname(descriptorName) === '.json');
  digestString(descriptorSha256);
  const descriptorPath = localPath(descriptorName), bytes = readFileSync(descriptorPath);
  assert(bytes.length <= 200_000); assert.equal(sha(bytes), descriptorSha256, 'Changed descriptor');
  const descriptor = validateDiagnosticDescriptor(JSON.parse(new TextDecoder('utf-8', {fatal:true}).decode(bytes)));
  const artifactRoot = localPath(descriptor.artifactRoot); assert(lstatSync(artifactRoot).isDirectory());
  const gets = new Map(descriptor.get.map(row => [row.name, {...row, path:localPath(row.path)}]));
  for (const entry of gets.values()) verified(entry);
  const sourceHtml = verified(gets.get('')).toString('utf8');
  assert(!/<audio\b|\b(?:Audio|AudioContext|webkitAudioContext)\s*\(/i.test(sourceHtml), 'Diagnostic must be silent');
  const current = prepareCurrentWorkspace(reportName);
  // The imported base handles only the frozen Launcher and quiet script here;
  // disabling its old check list prevents any inherited POST/proxy routes.
  return {current:{...current, checks:[]}, descriptorName, descriptorPath, descriptorSha256, descriptorBytes:bytes.length,
    descriptor, artifactRoot, capture:resolve(artifactRoot, 'capture'), mount:`/checks/${descriptor.slug}/`, gets,
    posts:new Map(descriptor.post.map(row => [row.name, row]))};
}
function descriptorVerified(state) {
  noRedirect(state.descriptorPath); const bytes = readFileSync(state.descriptorPath);
  assert.equal(bytes.length, state.descriptorBytes); assert.equal(sha(bytes), state.descriptorSha256);
}
function parsedRequest(raw) {
  assert(typeof raw === 'string' && raw.startsWith('/') && !raw.startsWith('//') && !raw.includes('#'));
  const path = raw.split('?')[0];
  assert(!/%|\\|\0/.test(path), 'Encoded/redirected request paths forbidden');
  for (const part of path.split('/').filter(Boolean)) segment(part);
  return {path, query:raw.includes('?')};
}
async function bodyLimited(req, limit) {
  const parts = []; let length = 0;
  for await (const part of req) {length += part.length; assert(length <= limit, 'Capture body exceeds declared size'); parts.push(part);}
  return Buffer.concat(parts);
}
export function validateCapture(rule, bytes) {
  if (rule.kind === 'bytes') {
    assert.equal(bytes.length, rule.bytes, 'Capture pixel size mismatch');
    if (rule.sha256 !== undefined) assert.equal(sha(bytes), rule.sha256);
  } else {
    assert(bytes.length > 0 && bytes.length <= rule.maxBytes);
    const json = JSON.parse(new TextDecoder('utf-8', {fatal:true}).decode(bytes));
    assert(json && Object.getPrototypeOf(json) === Object.prototype && !Array.isArray(json), 'Capture JSON object required');
    for (const [name, expected] of Object.entries(rule.jsonEquals || {})) assert(Object.hasOwn(json, name) && json[name] === expected, 'Capture field mismatch: ' + name);
  }
}
// IO is injectable only for read-only units; HTTP never accepts an IO selector.
export function storeExclusive(path, bytes, io = {writeFileSync, readFileSync, realpathSync, lstatSync}) {
  try {io.writeFileSync(path, bytes, {flag:'wx'}); return 'created';}
  catch (error) {
    if (error.code !== 'EEXIST') throw error;
    assert(io.lstatSync(path).isFile() && !io.lstatSync(path).isSymbolicLink());
    assert.equal(io.realpathSync(path).toLowerCase(), path.toLowerCase());
    const existing = io.readFileSync(path); assert.equal(existing.length, bytes.length);
    assert.equal(sha(existing), sha(bytes), 'Existing capture evidence is immutable'); return 'identical';
  }
}
function commitCapture(state, rule, bytes) {
  noRedirect(state.capture); assert(lstatSync(state.capture).isDirectory());
  segment(rule.basename); const path = resolve(state.capture, rule.basename); contained(state.capture, path);
  return storeExclusive(path, bytes);
}
function defaultWriter(state, rule, bytes) {
  noRedirect(state.artifactRoot);
  try {mkdirSync(state.capture, {recursive:false});} catch (error) {if (error.code !== 'EEXIST') throw error;}
  return commitCapture(state, rule, bytes);
}
function visibleLink(bytes, mount) {
  const html = bytes.toString('utf8'), nav = `<nav id="th14-workspace-diagnostic" aria-label="本机诊断" style="position:fixed;bottom:12px;left:12px;z-index:2147483646;padding:10px 14px;background:#17212df2;font:14px system-ui"><a href="${mount}" style="color:#d9edff">本机诊断</a></nav>`;
  assert(/<\/body\s*>/i.test(html)); return Buffer.from(html.replace(/<\/body\s*>/i, match => nav + match));
}
export function createDiagnosticWorkspaceHandler(state, writer = defaultWriter) {
  const site = createWorkspaceHandler(state.current, async () => {throw Error('No inherited diagnostic forwarding');});
  const delegate = createCurrentWorkspaceHandler(state.current, site);
  return async (req, res) => {
    for (const [name, value] of Object.entries(headers)) res.setHeader(name, value);
    try {
      descriptorVerified(state);
      const {path, query} = parsedRequest(req.url), method = req.method;
      if (path.startsWith('/checks/')) {
        if (!path.startsWith(state.mount)) return res.writeHead(404).end('Unmapped diagnostic');
        if (query) return res.writeHead(400).end('Diagnostic queries are not supported');
        const name = path.slice(state.mount.length);
        if (method === 'GET' || method === 'HEAD') {
          const entry = state.gets.get(name); if (!entry) return res.writeHead(404).end('Unmapped diagnostic file');
          const original = verified(entry), bytes = name === '' ? injectQuietHtml(original) : original;
          res.setHeader('Content-Type', mime[extname(entry.path)]); res.setHeader('Content-Length', bytes.length);
          return res.writeHead(200).end(method === 'HEAD' ? undefined : bytes);
        }
        if (method !== 'POST') return res.writeHead(405).end();
        const rule = state.posts.get(name); if (!rule) return res.writeHead(404).end('Unmapped capture file');
        const bytes = await bodyLimited(req, rule.kind === 'json' ? rule.maxBytes : rule.bytes); validateCapture(rule, bytes);
        // All input hashes are rechecked at POST time, tying the capture write
        // to the frozen descriptor's complete input inventory.
        for (const entry of state.gets.values()) verified(entry);
        const disposition = writer(state, rule, bytes);
        const response = Buffer.from(JSON.stringify({saved:true, disposition, bytes:bytes.length, sha256:sha(bytes)}));
        res.setHeader('Content-Type', mime['.json']); res.setHeader('Content-Length', response.length);
        return res.writeHead(200).end(response);
      }
      if (['/', '/index.html'].includes(path) && ['GET', 'HEAD'].includes(method)) {
        const wrapper = {status:undefined, setHeader(name, value){res.setHeader(name, value);},
          writeHead(status){this.status = status; return this;}, end(bytes){
            if (this.status === 200) {
              const linked = visibleLink(injectQuietHtml(verified(state.current.files.get('/index.html'))), state.mount);
              bytes = method === 'GET' ? linked : undefined; res.setHeader('Content-Length', linked.length);
            }
            return res.writeHead(this.status).end(bytes);
          }};
        return await delegate(req, wrapper);
      }
      return await delegate(req, res);
    } catch {return res.writeHead(500).end('Workspace diagnostic integrity/request failure');}
  };
}
export async function checkDiagnosticsReadOnly(state) {
  let assertions = 0; const test = (actual, expected) => {assert.deepEqual(actual, expected); ++assertions;};
  const writes = [], handler = createDiagnosticWorkspaceHandler(state, (_state, rule, bytes) => {writes.push({basename:rule.basename, bytes:bytes.length, sha256:sha(bytes)}); return 'declared-created';});
  async function simulate(url, method = 'GET', body = Buffer.alloc(0), use = handler) {
    const req = Readable.from(body.length ? [body] : []); Object.assign(req, {url, method, headers:{}});
    const res = {headers:{}, setHeader(name, value){this.headers[name] = value;}, writeHead(status){this.status = status; return this;}, end(bytes){this.body = bytes; return this;}};
    await use(req, res); return res;
  }
  let response = await simulate(state.mount); test(response.status, 200);
  test(sha(response.body), sha(injectQuietHtml(verified(state.gets.get('')))));
  test(response.headers['Cache-Control'], 'no-store'); test(response.headers['Cross-Origin-Embedder-Policy'], 'require-corp');
  response = await simulate(state.mount, 'HEAD'); test(response.status, 200); test(response.body, undefined);
  const wasm = [...state.gets].find(([, entry]) => extname(entry.path) === '.wasm'); assert(wasm); ++assertions;
  response = await simulate(state.mount + wasm[0]); test(sha(response.body), wasm[1].sha256);
  for (const [url, status] of [[state.mount + '?mode=color', 400], [state.mount + 'missing', 404], ['/checks/not-declared/', 404],
    [state.mount + '../outside', 500], [state.mount + '%2e%2e/private', 500], [state.mount + 'capture%2freport.json', 500],
    ['http://evil/', 500], ['//evil/', 500], [state.mount + 'a\\b', 500], [state.mount + 'capture/report.json#x', 500]]) test((await simulate(url)).status, status);
  test((await simulate(state.mount, 'PUT')).status, 405);
  test((await simulate('/checks/deferred-copy-success/capture/report.json', 'POST')).status, 404);
  test((await simulate(state.mount + 'capture/unmapped.json', 'POST')).status, 404);
  const rule = state.descriptor.post.find(row => row.kind === 'json'); assert(rule); ++assertions;
  const payload = Buffer.from(JSON.stringify({...rule.jsonEquals}));
  response = await simulate(state.mount + rule.name, 'POST', payload); test(response.status, 200); test(writes[0].basename, rule.basename);
  const beforeBad = writes.length;
  test((await simulate(state.mount + rule.name, 'POST', Buffer.from('{bad'))).status, 500);
  test((await simulate(state.mount + rule.name, 'POST', Buffer.alloc(rule.maxBytes + 1))).status, 500); test(writes.length, beforeBad);
  assert.throws(() => validateCapture({kind:'bytes', bytes:4}, Buffer.alloc(3))); ++assertions;
  assert.throws(() => validateCapture({kind:'json', maxBytes:100, jsonEquals:{frames:21}}, Buffer.from('{"frames":23}'))); ++assertions;
  for (const change of [d => {d.unknown = true;}, d => {d.slug = '../x';}, d => {d.artifactRoot = 'tools';},
    d => {d.get[0].path = 'H:/Games/th/14/th14.exe';}, d => {d.get[0].path = 'artifacts/th14/a/../b.bin';},
    d => {d.get[0].path = 'artifacts/th14/a/x.dat';}, d => {d.post[0].basename = '../outside.json';},
    d => {d.post[0].basename = 'nul.json';}, d => {d.post = Array.from({length:17}, () => d.post[0]);}]) {
    const altered = structuredClone(state.descriptor); change(altered); assert.throws(() => validateDiagnosticDescriptor(altered)); ++assertions;
  }
  const virtualFiles = new Map(), virtualPath = resolve(state.capture, 'declared-writer-unit.json');
  const io = {writeFileSync(path, bytes, options){assert.equal(options.flag, 'wx'); if (virtualFiles.has(path)) {const error = Error('Declared existing file'); error.code = 'EEXIST'; throw error;} virtualFiles.set(path, Buffer.from(bytes));},
    readFileSync:path => virtualFiles.get(path), realpathSync:path => path, lstatSync:() => ({isFile:() => true, isSymbolicLink:() => false})};
  test(storeExclusive(virtualPath, payload, io), 'created'); test(storeExclusive(virtualPath, payload, io), 'identical');
  assert.throws(() => storeExclusive(virtualPath, Buffer.from('changed'), io)); ++assertions;
  const altered = {...state, descriptorSha256:'0'.repeat(64)};
  test((await simulate(state.mount, 'GET', Buffer.alloc(0), createDiagnosticWorkspaceHandler(altered))).status, 500);
  response = await simulate('/'); test(response.status, 200); test(response.body.toString().includes(`href="${state.mount}"`), true);
  response = await simulate('/app-shell-sw.js'); test(response.status, 200); test(response.body.toString().includes('local workspace passthrough'), true);
  response = await simulate('/__workspace/quiet-audio.js'); test(sha(response.body), state.current.quiet.sha256);
  return {prepared:true, readOnlyVerified:true, serverStarted:false, browserExecuted:false, actualHttpRequests:0, networkRequests:0,
    actualEvidenceWrites:0, assertions, origin:ORIGIN, fixedListenHost:'127.0.0.1', fixedPort:8208,
    report:state.current.reportName, reportSha256:state.current.reportSha256, launcherFiles:127, inheritedDiagnosticRoutesEnabled:false,
    descriptor:{path:state.descriptorName, bytes:state.descriptorBytes, sha256:state.descriptorSha256}, mount:state.mount,
    getInventory:state.descriptor.get, postInventory:state.descriptor.post, output:relative(root, state.capture).replaceAll('\\', '/'),
    frozenSources, declaredCaptureWriterCalls:writes, declaredExclusiveWriter:['created','identical','changed-rejected'],
    localQuietDefaultPreserved:true, passthroughSwPreserved:true, deletesCachesOrSaves:false, remoteProxy:false,
    completeGame:false, nativeEquivalent:false, graphicsExecuted:false, toolSha256:sha(readFileSync(fileURLToPath(import.meta.url))),
    scope:'Prepared reusable fixed8208 descriptor gateway. Current/base Launcher127, quiet script and passthrough worker stay imported/hash-bound; old diagnostic route list is disabled. Exact schema, pinned descriptor, literal GET/POST mapping, workspace path/link checks, source hashes and exclusive-create/identical-SHA output contract are exercised by a small declared handler/IO unit set. GET verifies requested frozen bytes; POST rechecks all diagnostic inputs. Output is only the descriptor experiment capture directory with at most16 basenames. No listener/browser/HTTP/GL is started; units use a recording writer and a declared in-memory wx/EEXIST filesystem, so they do not prove actual HTTP or operating-system write execution. No frozen tools, receipt, production source, existing evidence, cache or save is modified.'};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2), options = new Map(); let check = false;
  for (let i = 0; i < args.length; ++i) {
    if (args[i] === '--check') {assert(!check); check = true; continue;}
    assert(['--report','--descriptor','--descriptor-sha256'].includes(args[i]) && !options.has(args[i]) && args[i + 1]);
    options.set(args[i], args[++i]);
  }
  assert(options.size === 3, 'Usage: node tools/th14-serve-workspace-diagnostics.mjs --report NAME.json --descriptor artifacts/th14/EXPERIMENT/descriptor.json --descriptor-sha256 SHA256 [--check]');
  const state = prepareDiagnosticWorkspace(options.get('--report'), options.get('--descriptor'), options.get('--descriptor-sha256'));
  if (check) console.log(JSON.stringify(await checkDiagnosticsReadOnly(state), null, 2));
  else createServer(createDiagnosticWorkspaceHandler(state)).listen(8208, '127.0.0.1', () =>
    console.log(`TH14 diagnostic workspace: ${ORIGIN}/ ${state.mount} (descriptor ${state.descriptorSha256}; quiet/passthrough)`));
}
