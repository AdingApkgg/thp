// Freeze the verified dialogue-damage module over the published signed-byte save runtime.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex');
const i=process.argv.indexOf('--report'),reportName=process.argv[i+1];
assert(i>=0&&/^[a-z0-9-]+\.json$/.test(reportName)&&!existsSync(resolve(root,'docs/porting',reportName)));
const priorBytes=read(resolve(root,'docs/porting/th14-launcher-runtime-dialogue-damage-oct19.json')),prior=JSON.parse(priorBytes);
const folder=resolve(root,'artifacts/th14/primitive-viewport-bounded-sdl-v2-oct19'),buildBytes=read(resolve(folder,'build.json')),raw=JSON.parse(buildBytes);
const coreBytes=read(resolve(root,'artifacts/th14/primitive-viewport-bounded-v2-candidate-oct19/color/build.json')),core=JSON.parse(coreBytes);
assert(raw.compiled&&raw.title===14&&raw.releaseProfile&&raw.exportsUnchanged&&Object.keys(raw.objectHashes).length===146);
assert.equal(raw.graphicsCandidateBuildSha256,sha(coreBytes));
assert.equal(raw.wasmSha256,'9e01f35d99a13325543c6329a02cdbdd73919bd6a66ec66846bef3a8d3d556d8');
for(const group of [raw.sourceHashes,raw.headerHashes])for(const[n,h]of Object.entries(group))assert.equal(sha(read(resolve(folder,'source',n))),h,n);
for(const[n,h]of Object.entries(raw.objectHashes))assert.equal(sha(read(resolve(folder,n))),h,n);
for(const n of ['Renderer.cpp','Shaders.hpp'])assert.equal(sha(read(resolve(root,'artifacts/th14/primitive-viewport-bounded-v2-candidate-oct19/color',n))),raw[n.endsWith('.cpp')?'sourceHashes':'headerHashes']['portable/sdl/'+n],n);
const save=read(resolve(root,'runtimes/th14/th14_web/browser-save-delta.mjs'));assert.equal(sha(save),prior.sourceSaveDeltaSha256);
const pending=new Map();for(const[n,row]of Object.entries(prior.files)){const b=read(resolve(prior.out,n));assert.equal(b.length,row.bytes);assert.equal(sha(b),row.sha256);pending.set(n,b);}
assert.equal(pending.size,40);
const wasm=read(resolve(folder,'th11.wasm')),loader=read(resolve(folder,'th11.mjs'));assert.equal(sha(wasm),raw.wasmSha256);assert.equal(sha(loader),raw.loaderSha256);
pending.set('th14-sdl.wasm',wasm);pending.set('th14-sdl.mjs',loader);
let shell=pending.get('shell.mjs').toString();assert.equal(shell.split(prior.build.sha256).length-1,1);shell=shell.replace(prior.build.sha256,raw.wasmSha256);pending.set('shell.mjs',Buffer.from(shell));
const manifest=JSON.parse(pending.get('manifest.json'));manifest.execution.sha256=raw.wasmSha256;manifest.execution.loaderSha256=raw.loaderSha256;pending.set('manifest.json',Buffer.from(JSON.stringify(manifest,null,2)+'\n'));
const files=Object.fromEntries([...pending].map(([n,b])=>[n,{bytes:b.length,sha256:sha(b)}]));
const changed=Object.keys(files).filter(n=>files[n].sha256!==prior.files[n].sha256).sort();
assert.deepEqual(changed,['manifest.json','shell.mjs','th14-sdl.mjs','th14-sdl.wasm']);
const label=raw.wasmSha256.slice(0,16)+'-'+sha(Buffer.from(JSON.stringify(files))).slice(0,12),out=resolve(root,'runtimes/th14/th14_web/artifacts/launcher-runtime',label);
const write=(n,b)=>{const p=resolve(out,n);mkdirSync(dirname(p),{recursive:true});if(existsSync(p))assert.equal(sha(read(p)),sha(b));else writeFileSync(p,b,{flag:'wx'});};
for(const[n,b]of pending)write(n,b);
write('runtime-files.json',Buffer.from(JSON.stringify({schema:'eagler-touhou/runtime-directory/1',game:'th14',files},null,2)+'\n'));
const build={...raw,kind:'th14-sdl3-web-release',sources:raw.sourceHashes,headers:raw.headerHashes,sha256:raw.wasmSha256,bytes:raw.wasmBytes};
const report={passed:true,completeGame:false,nativeEquivalent:false,out,buildDirectory:folder,build,files,
 exports:WebAssembly.Module.exports(new WebAssembly.Module(wasm)),toolSha256:sha(read(import.meta.filename)),
 sourceSaveDeltaSha256:sha(save),sourceShellSha256:prior.sourceShellSha256,baseRuntimeReportSha256:sha(priorBytes),sdlBuildReportSha256:sha(buildBytes),
 changedFiles:changed,sameProductionWasm:false,baseProductionWasmSha256:prior.build.sha256,sourceSnapshotBound:true,currentWorkspaceSourcesVerified:false,
 scope:'Bounded whole-primitive viewport compatibility candidate changes only Renderer.cpp and Shaders.hpp. All146 SDL objects rebuilt from the dialogue-fix snapshot; game sources unchanged. Loader is paired with its new WASM (imports changed; public exports unchanged). Save byte-view fix and28 private resources retained. Independent Root ResourceCrypt edit excluded. Browser validation separate; no complete/native equivalence.'};
writeFileSync(resolve(root,'docs/porting',reportName),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,out,files:40,changedFiles:changed,sha256:raw.wasmSha256}));
