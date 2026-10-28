// Real HTTP and pure Launcher contract checks. No browser or DOM is created.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,createReadStream,mkdirSync} from 'node:fs';
import {resolve,dirname,posix} from 'node:path';
import {createHash} from 'node:crypto';
import {createServer} from 'node:http';
import {pathToFileURL} from 'node:url';
import {once} from 'node:events';
import {prepare} from './th14-serve-webgpu-candidate.mjs';
import {root,digest,inside,injectHtml,quietRoute} from './th14-local-audio-policy.mjs';

const at=process.argv.indexOf('--output');
assert(at>=0&&process.argv[at+1],'An output report is required');
const output=inside(resolve(root,'artifacts/th14'),resolve(process.argv[at+1]));
const args=process.argv.slice(2);args.splice(at-2,2);
const state=prepare(args);
assert.equal(state.settings.sound,false,'Transport verification uses quiet preview policy');
let checkedBytes=0;
for (const [name,row] of Object.entries(state.proof.files)) {
  const hash=createHash('sha256');let length=0;
  for await (const chunk of createReadStream(resolve(root,row.path))) {hash.update(chunk);length+=chunk.length;}
  assert.equal(length,row.bytes,name);assert.equal(hash.digest('hex'),row.sha256,name);checkedBytes+=length;
}
const file=name=>resolve(root,state.proof.files[name].path);
const json=name=>JSON.parse(readFileSync(file(name)));
const contractChecks=[];
for (const [name,method,value] of [
  ['assets/contracts/host-manifest.mjs','validateHostManifest',json('host-manifest.json')],
  ['assets/contracts/release-catalog.mjs','validateReleaseCatalog',json('release-catalog.json')],
  ['package/package-descriptor.mjs','validatePackageDescriptor',json('packages/th14/package.json')],
]) {
  const validator=await import(pathToFileURL(file(name)).href);
  assert(validator[method](value));contractChecks.push(method);
}
const managed=json('runtime/th14/runtime-files.json');
for (const [name,row] of Object.entries(managed.files)) {
  const actual=state.proof.files['runtime/th14/'+name];
  assert(actual&&actual.bytes===row.bytes&&actual.sha256===row.sha256,name);
}
const resources=json('runtime/th14/resources.json');
assert.equal(resources.game,'th14');assert.equal(resources.resources.length,28);
for (const row of resources.resources) {
  const name=posix.normalize(posix.join('runtime/th14',row.url));
  assert(!row.url.startsWith('/')&&!name.includes('..'));
  const actual=state.proof.files[name];assert(actual&&actual.bytes===row.bytes&&actual.sha256===row.sha256,name);
}
const dependencies=[];
for (const [name,row] of Object.entries(state.proof.files)) {
  if (!/\.(?:mjs|js)$/.test(name)) continue;
  const source=readFileSync(resolve(root,row.path),'utf8');
  if (!['runtime/th14/th14-sdl.mjs','runtime/th14/archive-decoder.mjs'].includes(name)) assert(!/(?:from\s*|import\s*\()['"]node:/.test(source),name);
  // Literal module edges; generated loader's computed Wasm/Runtime URLs are
  // checked separately. Sources are read rather than executed in a DOM shim.
  for (const match of source.matchAll(/(?:\b(?:import|export)\s+(?:[^'";]*?\s+from\s+)?|\bimport\s*\()\s*['"](\.[^'"]+)['"]/g)) {
    const target=posix.normalize(posix.join(posix.dirname(name),match[1]));
    assert(state.proof.files[target],`${name} -> ${target}`);dependencies.push({from:name,to:target});
  }
}
for (const name of ['th14-sdl.wasm','Th14WebGpuHost.mjs','Th14WebGpuRuntime.mjs','Th14WebGpuCore.mjs','Th14WebGpu.wgsl','Th14WebGpuResample.wgsl']) {
  assert(state.proof.files['runtime/th14/'+name]);
}
const server=createServer(state.request),requests=[];
server.listen(0,'127.0.0.1');await once(server,'listening');
const origin=`http://127.0.0.1:${server.address().port}`;
try {
  const checks=[
    ['/?game=th14','text/html; charset=utf-8'],
    ['/runtime/th14/th14.html','text/html; charset=utf-8'],
    ['/runtime/th14/th14-sdl.mjs','text/javascript; charset=utf-8'],
    ['/runtime/th14/th14-sdl.wasm','application/wasm'],
    ['/runtime/th14/Th14WebGpuHost.mjs','text/javascript; charset=utf-8'],
    ['/runtime/th14/Th14WebGpuRuntime.mjs','text/javascript; charset=utf-8'],
    ['/runtime/th14/Th14WebGpuCore.mjs','text/javascript; charset=utf-8'],
    ['/runtime/th14/Th14WebGpu.wgsl','application/octet-stream'],
    ['/runtime/th14/Th14WebGpuResample.wgsl','application/octet-stream'],
    ['/host-manifest.json','application/json; charset=utf-8'],
    ['/release-catalog.json','application/json; charset=utf-8'],
    ['/packages/th14/package.json','application/json; charset=utf-8'],
    ['/runtime/th14/resources.json','application/json; charset=utf-8'],
    ['/runtime/th14/runtime-files.json','application/json; charset=utf-8'],
    [quietRoute,'text/javascript; charset=utf-8'],
  ];
  for(const name of ['archive-decoder.mjs','archive-decoder.wasm','Th14ArchiveDecodeClient.mjs','Th14ArchiveReadAhead.mjs','Th14ArchiveDecodeEndpoint.mjs','Th14ArchiveDecodeWorker.mjs']) {
    if(state.proof.files['runtime/th14/'+name])checks.push(['/runtime/th14/'+name,name.endsWith('.wasm')?'application/wasm':'text/javascript; charset=utf-8']);
  }
  for (const [path,type] of checks) {
    const response=await fetch(origin+path);assert.equal(response.status,200,path);
    assert.equal(response.headers.get('content-type'),type,path);
    assert.equal(response.headers.get('cross-origin-opener-policy'),'same-origin');
    assert.equal(response.headers.get('cross-origin-embedder-policy'),'require-corp');
    assert.equal(response.headers.get('cache-control'),'no-store');
    const raw=Buffer.from(await response.arrayBuffer());assert.equal(Number(response.headers.get('content-length')),raw.length);
    let expected;
    if (path===quietRoute) expected=readFileSync(resolve(root,'tools/th14-local-quiet-audio.js'));
    else {
      const key=path.startsWith('/?')?'index.html':path.slice(1);expected=readFileSync(file(key));
      if (type.startsWith('text/html')) expected=injectHtml(expected,false);
    }
    assert.equal(digest(raw),digest(expected),path);requests.push({path,status:response.status,bytes:raw.length,sha256:digest(raw)});
  }
  for (const name of ['packages/th14/th14.data',...resources.resources.slice(0,1).map(row=>'runtime/th14/'+row.url.slice(2))]) {
    const response=await fetch(origin+'/'+name,{method:'HEAD'});assert.equal(response.status,200);
    assert.equal(Number(response.headers.get('content-length')),state.proof.files[name].bytes);
    assert.equal((await response.arrayBuffer()).byteLength,0);requests.push({path:'/'+name,method:'HEAD',status:200});
  }
  const worker=await fetch(origin+'/app-shell-sw.js');
  const workerText=await worker.text();assert.equal(worker.status,200);
  assert(workerText.includes('local preview passthrough')&&!workerText.includes('caches.delete'));
  requests.push({path:'/app-shell-sw.js',status:200,localPassthrough:true});
  for (const [path,method,status] of [['/__missing','GET',404],['/..%2Foutside','GET',404],['/','POST',405]]) {
    const response=await fetch(origin+path,{method});await response.arrayBuffer();assert.equal(response.status,status);
    requests.push({path,method,status});
  }
} finally {server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
const sourceBindings={};
for (const name of ['tools/th14-webgpu-launcher-transport-check.mjs','tools/th14-serve-webgpu-candidate.mjs','tools/th14-local-audio-policy.mjs','tools/th14-local-quiet-audio.js']) {
  sourceBindings[name]=digest(readFileSync(resolve(root,name)));
}
const report={schema:'th14/webgpu-launcher-transport/1',verifiedTransport:true,reportSha256:state.reportSha256,
  wasmSha256:state.proof.wasmSha256,routes:Object.keys(state.proof.files).length,checkedBytes,contractChecks,
  moduleDependencies:dependencies,requests,sourceBindings,quietByDefault:true,payloadFilesCopied:false,
  browserRun:false,browserAcceptance:false,completeGame:false,nativeEquivalent:false,
  scope:'Real loopback HTTP, frozen route hashes, Launcher pure contract validators, literal module dependencies and runtime resources. No browser, DOM, canvas, GPU, OS input, audio device, persistence or offline execution.'};
mkdirSync(dirname(output),{recursive:true});writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({verifiedTransport:true,routes:report.routes,requests:requests.length,contractChecks,browserAcceptance:false}));
