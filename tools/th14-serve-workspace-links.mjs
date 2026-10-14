import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {Readable} from 'node:stream';
import {prepareWorkspace, createWorkspaceHandler, injectQuietHtml, ORIGIN} from './th14-serve-workspace.mjs';

const root = resolve(import.meta.dirname, '..');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const frozenGatewaySha256 = '18ebc5a34401dd57b07305d1135edc851885835b28c0a5efc7fd5d634cf619ca';
const frozenQuietSha256 = '216745e0d5459c0546e3fed01866092e67f40c383380dd47c5aafa5bac4a134c';
export const DIAGNOSTIC_LINK = '<nav id="th14-workspace-checks" aria-label="本机诊断" style="position:fixed;top:12px;right:12px;z-index:2147483646;padding:10px 14px;border:1px solid #b6d8ff;border-radius:6px;background:#17212df2;font:14px system-ui"><a href="/checks/deferred-copy-success/" style="color:#d9edff;text-decoration:underline">本机诊断：延迟拷贝像素比对</a></nav>';

export function injectVisibleLink(bytes) {
  const html = bytes.toString('utf8');
  assert(!html.includes('id="th14-workspace-checks"'));
  assert(/<\/body\s*>/i.test(html), 'Main index has no closing body');
  return Buffer.from(html.replace(/<\/body\s*>/i, match => DIAGNOSTIC_LINK + match));
}

export function createLinkedWorkspaceHandler(state) {
  const original = createWorkspaceHandler(state);
  return async (req, res) => {
    const name = req.url.split('?')[0];
    if (!['/', '/index.html'].includes(name) || !['GET', 'HEAD'].includes(req.method)) return original(req, res);
    // Delay writeHead only for this main HTML response so Content-Length reflects
    // the visible link; the original handler still performs its hash checks.
    const wrapper = {
      status:undefined,
      setHeader(name, value){res.setHeader(name, value);},
      writeHead(status){this.status = status; return this;},
      end(bytes){
        if (this.status === 200) {
          if (req.method === 'GET') bytes = injectVisibleLink(bytes);
          const length = req.method === 'GET' ? bytes.length : injectVisibleLink(injectQuietHtml(readFileSync(state.files.get('/index.html').path))).length;
          res.setHeader('Content-Length', length);
        }
        return res.writeHead(this.status).end(bytes);
      },
    };
    return original(req, wrapper);
  };
}

function checkDependencies() {
  assert.equal(sha(readFileSync(resolve(root, 'tools/th14-serve-workspace.mjs'))), frozenGatewaySha256);
  assert.equal(sha(readFileSync(resolve(root, 'tools/th14-local-quiet-audio.js'))), frozenQuietSha256);
}

export async function checkLinksReadOnly(state) {
  let assertions = 0; const test = (actual, expected) => {assert.deepEqual(actual, expected); ++assertions;};
  const handler = createLinkedWorkspaceHandler(state);
  async function simulate(url, method = 'GET') {
    const req = Readable.from([]); Object.assign(req, {url, method, headers:{}});
    const res = {headers:{}, setHeader(name, value){this.headers[name] = value;},
      writeHead(status){this.status = status; return this;}, end(body){this.body = body; return this;}};
    await handler(req, res); return res;
  }
  const index = readFileSync(state.files.get('/index.html').path), quietIndex = injectQuietHtml(index);
  let response = await simulate('/'); test(response.status, 200);
  const linkedIndex = response.body;
  test(linkedIndex.toString().includes(DIAGNOSTIC_LINK), true);
  test(linkedIndex.toString().replace(DIAGNOSTIC_LINK, ''), quietIndex.toString());
  test(response.headers['Content-Length'], linkedIndex.length);
  test(response.headers['Cross-Origin-Embedder-Policy'], 'require-corp');
  response = await simulate('/index.html'); test(sha(response.body), sha(linkedIndex));
  response = await simulate('/', 'HEAD'); test(response.status, 200); test(response.body, undefined);
  test(response.headers['Content-Length'], linkedIndex.length);
  const moduleName = '/runtime/th14/th14-sdl.wasm';
  response = await simulate(moduleName); test(response.status, 200); test(sha(response.body), state.files.get(moduleName).sha256);
  response = await simulate('/__workspace/quiet-audio.js'); test(sha(response.body), frozenQuietSha256);
  response = await simulate('/missing'); test(response.status, 404);
  return {readOnlyVerified:true, serverStarted:false, networkRequests:0, assertions,
    origin:ORIGIN, report:state.reportName, reportSha256:state.reportSha256,
    visibleLink:'/checks/deferred-copy-success/', sameTabNavigation:true,
    mainHtmlOnlyChanged:true, mainWithQuietWithoutLinkSha256:sha(quietIndex), linkedMainSha256:sha(linkedIndex),
    frozenGatewaySha256, frozenQuietSha256,
    toolSha256:sha(readFileSync(fileURLToPath(import.meta.url))),
    scope:'New wrapper adds only a visible main-index link; frozen gateway/quiet sources, CPP/WASM/diagnostic assets, POST mapping and existing evidence remain untouched. Real browser navigation is for ROOT to verify from the allowed8208 main tab.'};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2), at = args.indexOf('--report');
  assert(at >= 0 && args[at + 1], 'Usage: node tools/th14-serve-workspace-links.mjs --report NAME.json [--check]');
  const rest = args.filter((_, i) => i !== at && i !== at + 1);
  assert(rest.length === 0 || (rest.length === 1 && rest[0] === '--check'));
  checkDependencies(); const state = prepareWorkspace(args[at + 1]);
  if (rest.includes('--check')) console.log(JSON.stringify(await checkLinksReadOnly(state), null, 2));
  else createServer(createLinkedWorkspaceHandler(state)).listen(8208, '127.0.0.1', () => {
    console.log(`TH14 workspace with visible checks: ${ORIGIN}/ (${state.reportName})`);
  });
}
