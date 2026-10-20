// Package the frozen TH14 Replay GameOver candidate without changing an existing release.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex');
const json=p=>JSON.parse(read(p));
const folder=resolve(root,'artifacts/th14/replay-resume-title-guard-sdl-oct21');
const buildBytes=read(resolve(folder,'build.json')),build=json(resolve(folder,'build.json'));
const verificationBytes=read(resolve(root,'artifacts/th14/replay-resume-title-guard-integration-oct21/verification.json'));
const soundVerificationBytes=read(resolve(root,'artifacts/th14/sound-pause-pcm-v2-oct21/verification.json'));
assert.equal(JSON.parse(soundVerificationBytes).passed,true);
assert.equal(JSON.parse(verificationBytes).passed,true);
assert(build.compiled&&build.releaseProfile&&build.title===14&&build.importsUnchanged&&build.exportsUnchanged);
assert.equal(Object.keys(build.objectHashes).length,146);
assert.equal(build.sourceHashes['th12_web/cpp/game/ResourceCrypt.cpp'],'d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef');
for(const group of [build.sourceHashes,build.headerHashes])for(const[n,h]of Object.entries(group))assert.equal(sha(read(resolve(folder,'source',n))),h,n);
for(const[n,h]of Object.entries(build.objectHashes))assert.equal(sha(read(resolve(folder,n))),h,n);
const wasm=read(resolve(folder,'th11.wasm')),loader=read(resolve(folder,'th11.mjs'));
assert.equal(sha(wasm),build.wasmSha256);assert.equal(sha(loader),build.loaderSha256);
const runtimeName='th14-launcher-runtime-replay-resume-final-oct21.json',siteName='th14-launcher-site-replay-resume-final-oct21.json';
for(const n of [runtimeName,siteName])assert(!existsSync(resolve(root,'docs/porting',n)));
const priorBytes=read(resolve(root,'docs/porting/th14-launcher-runtime-native-fog-mix-oct20.json')),prior=JSON.parse(priorBytes);
const pending=new Map();for(const[n,row]of Object.entries(prior.files)){
 const b=read(resolve(prior.out,n));assert.equal(b.length,row.bytes);assert.equal(sha(b),row.sha256);pending.set(n,b);
}
assert.equal(pending.size,40);pending.set('th14-sdl.wasm',wasm);pending.set('th14-sdl.mjs',loader);
let shell=pending.get('shell.mjs').toString();assert.equal(shell.split(prior.build.sha256).length,2);
pending.set('shell.mjs',Buffer.from(shell.replace(prior.build.sha256,build.wasmSha256)));
const manifest=JSON.parse(pending.get('manifest.json'));manifest.execution.sha256=build.wasmSha256;manifest.execution.loaderSha256=build.loaderSha256;
pending.set('manifest.json',Buffer.from(JSON.stringify(manifest,null,2)+'\n'));
const files=Object.fromEntries([...pending].map(([n,b])=>[n,{bytes:b.length,sha256:sha(b)}]));
const changed=Object.keys(files).filter(n=>files[n].sha256!==prior.files[n].sha256).sort();
assert(['manifest.json','shell.mjs','th14-sdl.wasm'].every(n=>changed.includes(n)));
assert(changed.every(n=>['manifest.json','shell.mjs','th14-sdl.mjs','th14-sdl.wasm'].includes(n)));
const label=build.wasmSha256.slice(0,16)+'-'+sha(Buffer.from(JSON.stringify(files))).slice(0,12);
const out=resolve(root,'runtimes/th14/th14_web/artifacts/launcher-runtime',label);
const write=(base,n,b)=>{const p=resolve(base,n);mkdirSync(dirname(p),{recursive:true});if(existsSync(p))assert.equal(sha(read(p)),sha(b));else writeFileSync(p,b,{flag:'wx'});};
for(const[n,b]of pending)write(out,n,b);
write(out,'runtime-files.json',Buffer.from(JSON.stringify({schema:'eagler-touhou/runtime-directory/1',game:'th14',files},null,2)+'\n'));
const scope='TH14 forced Replay GameOver menu, pause/resume/continue callback order and sound pause/resume. Full intact MarisaB Lunatic: 89235 callback raw32/active/owner prefixes unchanged in noninteractive/title/restart runs; 120 idle menu ticks freeze combat. SDL146-source and WASI141-source frozen graphs: final title guard recompiled one object in each, proving all objects and actual test modules byte-identical to the preceding verified pause/audio candidate. All three actual Replay result sets independently rehashed and reused under exact module equality. PauseResume events preserve the intermediate transition when GameOver recurs in the same tick. Whole-game, cold-start, final ordinary browser flow and original DirectSound PCM equality remain separate acceptance work.';
const runtime={passed:true,completeGame:false,nativeEquivalent:false,out,buildDirectory:folder,
 build:{...build,kind:'th14-sdl3-web-release',sources:build.sourceHashes,headers:build.headerHashes,sha256:build.wasmSha256,bytes:build.wasmBytes},files,
 exports:WebAssembly.Module.exports(new WebAssembly.Module(wasm)),toolSha256:sha(read(import.meta.filename)),sourceSaveDeltaSha256:prior.sourceSaveDeltaSha256,
 sourceShellSha256:prior.sourceShellSha256,baseRuntimeReportSha256:sha(priorBytes),sdlBuildReportSha256:sha(buildBytes),integrationVerificationSha256:sha(verificationBytes),soundVerificationSha256:sha(soundVerificationBytes),
 changedFiles:changed,sameProductionWasm:false,baseProductionWasmSha256:prior.build.sha256,sourceSnapshotBound:true,currentWorkspaceSourcesVerified:false,scope};
const runtimeBytes=Buffer.from(JSON.stringify(runtime,null,2)+'\n');writeFileSync(resolve(root,'docs/porting',runtimeName),runtimeBytes,{flag:'wx'});
const baseBytes=read(resolve(root,'docs/porting/th14-launcher-site-native-fog-mix-oct20.json')),base=JSON.parse(baseBytes),siteFiles=new Map();
assert.equal(Object.keys(base.files).length,127);
for(const[n,row]of Object.entries(base.files)){const b=read(resolve(base.site,n));assert.equal(b.length,row.bytes);assert.equal(sha(b),row.sha256);siteFiles.set(n,b);}
for(const[n,b]of pending){assert(siteFiles.has('runtime/th14/'+n));siteFiles.set('runtime/th14/'+n,b);}
siteFiles.set('runtime/th14/runtime-files.json',read(resolve(out,'runtime-files.json')));
const precache=[...siteFiles.keys()].filter(n=>n!=='files.json'&&n!=='app-shell-sw.js'&&!n.startsWith('packages/')&&!/^runtime\/[^/]+\/(?:music|fonts)\//.test(n));
const entries=[{url:'./',revision:sha(siteFiles.get('index.html'))},...precache.sort().map(n=>({url:n,revision:sha(siteFiles.get(n))}))];
const buildId=sha(Buffer.from(JSON.stringify(entries))).slice(0,20),swName='runtimes/th12/th12_web/launcher/src/app-shell-sw.js';
const publication=json(resolve(root,'docs/github-publication-manifest.json')),expectedSw=publication.files.find(r=>r.path===swName),sw=read(resolve(root,swName));
assert(expectedSw);assert.equal(sw.length,expectedSw.bytes);assert.equal(sha(sw),expectedSw.sha256);
siteFiles.set('app-shell-sw.js',Buffer.from(sw.toString().replaceAll('__APP_SHELL_BUILD_ID__',buildId).replace('self.__WB_MANIFEST',JSON.stringify(entries))));
const siteFileRows=Object.fromEntries([...siteFiles.keys()].sort().map(n=>[n,{bytes:siteFiles.get(n).length,sha256:sha(siteFiles.get(n))}]));
siteFiles.set('files.json',Buffer.from(JSON.stringify(Object.fromEntries(Object.entries(siteFileRows).map(([n,r])=>[n,r.sha256])),null,2)+'\n'));
const toolSha256=sha(read(import.meta.filename)),siteLabel=build.wasmSha256.slice(0,16)+'-'+sha(Buffer.from(JSON.stringify({files:siteFileRows,toolSha256}))).slice(0,12);
const siteOut=resolve(root,'runtimes/th14/th14_web/artifacts/launcher-preview',siteLabel),site=resolve(siteOut,'site');
for(const[n,b]of siteFiles)write(site,n,b);
const siteChanged=Object.keys(siteFileRows).filter(n=>siteFileRows[n].sha256!==base.files[n].sha256).sort();
assert(siteChanged.every(n=>['app-shell-sw.js','runtime/th14/runtime-files.json','runtime/th14/shell.mjs','runtime/th14/manifest.json','runtime/th14/th14-sdl.mjs','runtime/th14/th14-sdl.wasm'].includes(n)));
const siteReport={passed:true,completeGame:false,nativeEquivalent:false,out:siteOut,site,files:siteFileRows,moduleSources:base.moduleSources,buildId,revision:base.revision,
 runtimeManifestSha256:sha(runtimeBytes),toolSha256,baseLauncherReportSha256:sha(baseBytes),frozenLauncherReused:true,currentWorkspaceGameSourcesVerified:false,
 changedFiles:siteChanged,sameProductionWasm:false,sourceSaveDeltaSha256:runtime.sourceSaveDeltaSha256,scope};
const siteBytes=Buffer.from(JSON.stringify(siteReport,null,2)+'\n');write(siteOut,'release.json',siteBytes);writeFileSync(resolve(root,'docs/porting',siteName),siteBytes,{flag:'wx'});
console.log(JSON.stringify({passed:true,wasmSha256:build.wasmSha256,out,site,buildId,files:siteFiles.size}));
