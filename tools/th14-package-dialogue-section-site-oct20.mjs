// Reuse the signed-byte-save Launcher graph with the verified dialogue-damage module.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex');
const read=p=>readFileSync(p),json=p=>JSON.parse(read(p));
const option=name=>{const i=process.argv.indexOf(name);assert(i>=0&&process.argv[i+1]);return process.argv[i+1];};
const reportName=option('--report');assert(/^[a-z0-9-]+\.json$/.test(reportName));assert(!existsSync(resolve(root,'docs/porting',reportName)));
const baseBytes=read(resolve(root,'docs/porting/th14-launcher-site-fixed20-depth-oct19.json')),base=JSON.parse(baseBytes);
const runtimeBytes=read(resolve(root,'docs/porting/th14-launcher-runtime-dialogue-section-oct20.json')),runtime=JSON.parse(runtimeBytes);
assert(base.passed&&runtime.passed&&runtime.sourceSnapshotBound&&!runtime.sameProductionWasm);
assert.equal(runtime.build.sha256,'92750edf37c0e364b993de65a61145690d27991514d1c9bb3b4339182644cd0a');
assert.equal(Object.keys(base.files).length,127);assert.equal(Object.keys(runtime.files).length,40);
const pending=new Map();
for(const[name,row]of Object.entries(base.files)){const bytes=read(resolve(base.site,name));assert.equal(bytes.length,row.bytes);assert.equal(sha(bytes),row.sha256);pending.set(name,bytes);}
for(const[name,row]of Object.entries(runtime.files)){const bytes=read(resolve(runtime.out,name));assert.equal(bytes.length,row.bytes);assert.equal(sha(bytes),row.sha256);assert(pending.has('runtime/th14/'+name));pending.set('runtime/th14/'+name,bytes);}
const manifestName='runtime/th14/runtime-files.json',runtimeFiles=read(resolve(runtime.out,'runtime-files.json'));assert(pending.has(manifestName));pending.set(manifestName,runtimeFiles);
const precache=[...pending.keys()].filter(n=>n!=='files.json'&&n!=='app-shell-sw.js'&&!n.startsWith('packages/')&&!/^runtime\/[^/]+\/(?:music|fonts)\//.test(n));
const entries=[{url:'./',revision:sha(pending.get('index.html'))},...precache.sort().map(n=>({url:n,revision:sha(pending.get(n))}))];
const buildId=sha(Buffer.from(JSON.stringify(entries))).slice(0,20),swName='runtimes/th12/th12_web/launcher/src/app-shell-sw.js';
const publication=json(resolve(root,'docs/github-publication-manifest.json')),expectedSw=publication.files.find(r=>r.path===swName);assert(expectedSw);
const sw=read(resolve(root,swName));assert.equal(sw.length,expectedSw.bytes);assert.equal(sha(sw),expectedSw.sha256,'Published SW template changed');
pending.set('app-shell-sw.js',Buffer.from(sw.toString().replaceAll('__APP_SHELL_BUILD_ID__',buildId).replace('self.__WB_MANIFEST',JSON.stringify(entries))));
const files=Object.fromEntries([...pending.keys()].sort().map(n=>[n,{bytes:pending.get(n).length,sha256:sha(pending.get(n))}]));
pending.set('files.json',Buffer.from(JSON.stringify(Object.fromEntries(Object.entries(files).map(([n,r])=>[n,r.sha256])),null,2)+'\n'));
const toolSha256=sha(read(import.meta.filename)),label=runtime.build.sha256.slice(0,16)+'-'+sha(Buffer.from(JSON.stringify({files,toolSha256}))).slice(0,12);
const out=resolve(root,'runtimes/th14/th14_web/artifacts/launcher-preview',label),site=resolve(out,'site');
for(const[name,bytes]of pending){const p=resolve(site,name);mkdirSync(dirname(p),{recursive:true});if(existsSync(p))assert.equal(sha(read(p)),sha(bytes),'Immutable delta site');else writeFileSync(p,bytes);}
const changed=Object.keys(files).filter(n=>files[n].sha256!==base.files[n].sha256).sort();
assert(['app-shell-sw.js','runtime/th14/manifest.json','runtime/th14/runtime-files.json','runtime/th14/shell.mjs','runtime/th14/th14-sdl.wasm'].every(n=>changed.includes(n)));assert(changed.every(n=>['app-shell-sw.js','runtime/th14/runtime-files.json','runtime/th14/shell.mjs','runtime/th14/manifest.json','runtime/th14/th14-sdl.mjs','runtime/th14/th14-sdl.wasm'].includes(n)));
const shell=pending.get('runtime/th14/shell.mjs').toString();assert(shell.includes('th14SaveDelta.flush()')&&shell.includes('await th14SaveDelta.loaded()')&&!/^export function /m.test(shell));
const report={passed:true,completeGame:false,nativeEquivalent:false,out,site,files,moduleSources:base.moduleSources,buildId,revision:base.revision,
 runtimeManifestSha256:sha(runtimeBytes),toolSha256,baseLauncherReportSha256:sha(baseBytes),frozenLauncherReused:true,currentWorkspaceGameSourcesVerified:false,
 changedFiles:changed,sameProductionWasm:false,sourceSaveDeltaSha256:runtime.sourceSaveDeltaSha256,
 scope:'TH14 dialogue section retention in a fresh146-object SDL build over the frozen fixed20 graphics and Launcher graph. Same127 site paths and28 private resources, save byte-view and dialogue damage fixes retained. Browser integration separate; no whole-game/native equivalence.'};
const bytes=Buffer.from(JSON.stringify(report,null,2)+'\n');writeFileSync(resolve(out,'release.json'),bytes,{flag:'wx'});writeFileSync(resolve(root,'docs/porting',reportName),bytes,{flag:'wx'});
console.log(JSON.stringify({passed:true,site,files:Object.keys(files).length,buildId,changedFiles:changed}));
