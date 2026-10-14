import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync, writeFileSync, mkdirSync, existsSync, realpathSync} from 'node:fs';
import {resolve, relative, isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {Readable} from 'node:stream';
import {prepareWorkspace, createWorkspaceHandler, injectQuietHtml, ORIGIN} from './th14-serve-workspace.mjs';
import {injectVisibleLink, DIAGNOSTIC_LINK} from './th14-serve-workspace-links.mjs';

const root = resolve(import.meta.dirname, '..');
const output = resolve(root, 'artifacts/th14/deferred-capture-success-dirty-oct14/webgl-capture');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const fixedPosts = ['/capture/report.json', ...Array.from({length:8}, (_, i) => '/capture/portable-' + String(i).padStart(3, '0') + '.pixels')];
const frozenSources = {'th14-serve-workspace.mjs':'18ebc5a34401dd57b07305d1135edc851885835b28c0a5efc7fd5d634cf619ca',
  'th14-serve-workspace-links.mjs':'102872ea4908e7b364460160d56825b989dc8579ea151381d12c6977dba934e8',
  'th14-local-quiet-audio.js':'216745e0d5459c0546e3fed01866092e67f40c383380dd47c5aafa5bac4a134c'};

function validatePost(check, path, bytes) {
  assert.equal(check.mount, '/checks/deferred-copy-success/');
  assert(fixedPosts.includes(path)); assert(bytes.length < 2_000_000);
  const name = path.slice('/capture/'.length);
  if (name === 'report.json') assert.equal(JSON.parse(bytes).frames, 8);
  else {
    const nativeEntry = check.routes.get('/native.json'), nativeBytes = readFileSync(nativeEntry.path);
    assert.equal(sha(nativeBytes), nativeEntry.sha256);
    const native = JSON.parse(nativeBytes), index = Number(name.slice(9, 12));
    assert.equal(bytes.length, native.cases[index].bytes);
  }
  return name;
}
function writeEvidenceOnce(name, bytes) {
  mkdirSync(output, {recursive:true});
  assert.equal(realpathSync(output).toLowerCase(), output.toLowerCase(), 'Capture output may not redirect through a link');
  const path = resolve(output, name), rel = relative(output, path);
  assert(!isAbsolute(rel) && rel === name && !name.includes('/') && !name.includes('\\'));
  try {writeFileSync(path, bytes, {flag:'wx'});}
  catch (error) {
    if (error.code !== 'EEXIST') throw error;
    const actual = realpathSync(path); assert.equal(actual.toLowerCase(), path.toLowerCase());
    assert.equal(sha(readFileSync(path)), sha(bytes), 'Existing evidence immutable');
  }
}
export function createLocalForward(writer = writeEvidenceOnce) {
  return async (check, method, path, bytes) => {
    if (method === 'POST') {
      const name = validatePost(check, path, bytes); writer(name, bytes);
      return {status:200, contentType:'application/json', body:Buffer.from(JSON.stringify({saved:true, bytes:bytes.length, sha256:sha(bytes)}))};
    }
    assert.equal(method, 'GET'); const entry = check.routes.get(path); assert(entry);
    // The original handler rechecks these immutable bytes before serving them.
    return {status:200, body:readFileSync(entry.path)};
  };
}
export function createDirectWorkspaceHandler(state, localForward = createLocalForward()) {
  const original = createWorkspaceHandler(state, localForward);
  return async (req, res) => {
    if (!['/', '/index.html'].includes(req.url.split('?')[0]) || !['GET', 'HEAD'].includes(req.method)) return original(req, res);
    const wrapper = {status:undefined,
      setHeader(name, value){res.setHeader(name, value);},
      writeHead(status){this.status = status; return this;},
      end(bytes){
        if (this.status === 200) {
          if (req.method === 'GET') bytes = injectVisibleLink(bytes);
          res.setHeader('Content-Length', req.method === 'GET' ? bytes.length : injectVisibleLink(injectQuietHtml(readFileSync(state.files.get('/index.html').path))).length);
        }
        return res.writeHead(this.status).end(bytes);
      }};
    return original(req, wrapper);
  };
}
export async function checkDirectReadOnly(state) {
  let assertions = 0; const test = (actual, expected) => {assert.deepEqual(actual, expected); ++assertions;};
  const writes = [], forward = createLocalForward((name, bytes) => writes.push({name, bytes:bytes.length, sha256:sha(bytes)}));
  const handler = createDirectWorkspaceHandler(state, forward);
  async function simulate(url, method = 'GET', bytes = Buffer.alloc(0)) {
    const req = Readable.from(bytes.length ? [bytes] : []); Object.assign(req, {url, method, headers:{}});
    const res = {headers:{}, setHeader(name, value){this.headers[name] = value;},
      writeHead(status){this.status = status; return this;}, end(body){this.body = body; return this;}};
    await handler(req, res); return res;
  }
  let response = await simulate('/'); test(response.status, 200); test(response.body.toString().includes(DIAGNOSTIC_LINK), true);
  const check = state.checks[0], entry = check.routes.get('/capture.wasm');
  response = await simulate(check.mount + 'capture.wasm'); test(response.status, 200); test(sha(response.body), entry.sha256);
  response = await simulate(check.mount); test(response.status, 200);
  test(response.body.toString().includes("fetch('/checks/deferred-copy-success/native.json')"), true);
  test(response.body.toString().includes('/__workspace/quiet-audio.js'), true);
  const native = JSON.parse(readFileSync(check.routes.get('/native.json').path)), bytes = Buffer.alloc(native.cases[0].bytes);
  response = await simulate(check.mount + 'capture/portable-000.pixels', 'POST', bytes);
  test(response.status, 200); test(writes[0], {name:'portable-000.pixels', bytes:bytes.length, sha256:sha(bytes)});
  response = await simulate(check.mount + 'capture/report.json', 'POST', Buffer.from('{"frames":8}'));
  test(response.status, 200); test(writes[1].name, 'report.json');
  assert.throws(() => validatePost(check, '/capture/portable-000.pixels', Buffer.alloc(1))); ++assertions;
  assert.throws(() => validatePost(check, '/capture/report.json', Buffer.from('{"frames":7}'))); ++assertions;
  test((await simulate(check.mount + 'capture/other.json', 'POST')).status, 404);
  // Read-only IO contract: validate every existing output by the same write-once
  // rule, without creating/replacing files or touching current evidence.
  const existing = [];
  if (existsSync(output)) {
    assert.equal(realpathSync(output).toLowerCase(), output.toLowerCase());
    for (const path of fixedPosts) {
      const name = path.slice('/capture/'.length), file = resolve(output, name);
      if (!existsSync(file)) continue;
      assert.equal(realpathSync(file).toLowerCase(), file.toLowerCase());
      const current = readFileSync(file); validatePost(check, path, current);
      existing.push({name, bytes:current.length, sha256:sha(current)});
    }
  }
  return {readOnlyVerified:true, serverStarted:false, networkRequests:0, actualEvidenceWrites:0,
    assertions, origin:ORIGIN, report:state.reportName, reportSha256:state.reportSha256,
    localDiagnosticOnly:true, httpUpstreamRequired:false, existingEvidence:existing,
    postPaths:fixedPosts, output:relative(root, output).replaceAll('\\', '/'),
    frozenSources, toolSha256:sha(readFileSync(fileURLToPath(import.meta.url))),
    scope:'Thin direct local adapter uses the old hash-checking/allowlisting handler, with the visible main link and identical quiet script. POST writer is exclusive-create or identical-byte receipt; short checks use a declared writer and read-only current evidence. No existing server, browser, output or historical receipt modified.'};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2), at = args.indexOf('--report');
  assert(at >= 0 && args[at + 1], 'Usage: node tools/th14-serve-workspace-direct.mjs --report NAME.json [--check]');
  const rest = args.filter((_, i) => i !== at && i !== at + 1);
  assert(rest.length === 0 || (rest.length === 1 && rest[0] === '--check'));
  for (const [name, expected] of Object.entries(frozenSources)) assert.equal(sha(readFileSync(resolve(root, 'tools', name))), expected);
  const state = prepareWorkspace(args[at + 1]);
  if (rest.includes('--check')) console.log(JSON.stringify(await checkDirectReadOnly(state), null, 2));
  else createServer(createDirectWorkspaceHandler(state)).listen(8208, '127.0.0.1', () => {
    console.log(`TH14 direct workspace: ${ORIGIN}/ (${state.reportName}; local diagnostics, no8254 dependency)`);
  });
}
