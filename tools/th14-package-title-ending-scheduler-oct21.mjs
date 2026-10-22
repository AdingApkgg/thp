// Package the frozen TH14 Title/Ending scheduler candidate without changing an existing release.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex');
const json=p=>JSON.parse(read(p));
const folder=resolve(root,'artifacts/th14/title-ending-scheduler-sdl-oct21');
const buildBytes=read(resolve(folder,'build.json')),build=json(resolve(folder,'build.json'));
const publicFolder=resolve(root,'artifacts/th14/title-ending-public-evidence-oct21');
const evidenceBytes=read(resolve(publicFolder,'final-evidence.json')),evidence=JSON.parse(evidenceBytes);
const independentBytes=read(resolve(publicFolder,'sdl-independent-verification.json')),independent=JSON.parse(independentBytes);
const headerProofBytes=read(resolve(folder,'header-proof/verification.json')),headerProof=JSON.parse(headerProofBytes);
const releaseNoteBytes=read(resolve(publicFolder,'release-note.txt'));
assert.equal(sha(evidenceBytes),'960bc7660cb9b9c3ae219fc23ac18e2e0ca6e129a612be9ee02afbba155931a5');
assert.equal(sha(independentBytes),'cf4cadb47ceaa86a44579fd14f8e1b9cc287e14046277d7f630d65e74754d4c8');
assert.equal(sha(releaseNoteBytes),'67fa5214d6948b02938d3693dcbe4f086727776a66244521f5f83d1f5767814f');
assert(independent.passed&&headerProof.passed);assert.equal(independent.sourceFilesVerified,146);assert.equal(independent.headerFilesVerified,149);assert.equal(independent.linkedObjectHashesVerified,146);assert.equal(independent.freshLinkedObjects,2);assert.equal(independent.reusedObjectsByteEqual,144);
const verifyBinding=row=>{const b=read(resolve(root,row.path));assert.equal(sha(b),row.sha256,row.path);if(row.bytes!==undefined)assert.equal(b.length,row.bytes,row.path);};
for(const row of independent.bindings)verifyBinding(row);for(const row of evidence.evidence)verifyBinding(row);verifyBinding(evidence.handoff);verifyBinding(evidence.runtimeArtifact.newSdlBuildReceipt);verifyBinding(evidence.runtimeArtifact.independentVerification);
assert.equal(build.wasmSha256,'0e1ba6d1531edb51cfcf3f45aa0e01c4221788716369154470c95834d114a4bd');assert.equal(evidence.runtimeArtifact.wasmSha256,build.wasmSha256);assert.equal(evidence.runtimeArtifact.loaderSha256,build.loaderSha256);assert.equal(evidence.runtimeArtifact.browserValidated,false);assert.equal(evidence.runtimeArtifact.priorBrowserAcceptanceInherited,false);assert.equal(build.browserValidated,false);assert.equal(build.reusedSourceCount,144);assert.equal(build.recompiledSources.length,2);
assert(build.compiled&&build.releaseProfile&&build.title===14&&build.importsUnchanged&&build.exportsUnchanged);
assert.equal(Object.keys(build.objectHashes).length,146);
assert.equal(build.sourceHashes['th12_web/cpp/game/ResourceCrypt.cpp'],'d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef');
for(const group of [build.sourceHashes,build.headerHashes])for(const[n,h]of Object.entries(group))assert.equal(sha(read(resolve(folder,'source',n))),h,n);
for(const[n,h]of Object.entries(build.objectHashes))assert.equal(sha(read(resolve(folder,n))),h,n);
const wasm=read(resolve(folder,'th11.wasm')),loader=read(resolve(folder,'th11.mjs'));
assert.equal(sha(wasm),build.wasmSha256);assert.equal(sha(loader),build.loaderSha256);
const runtimeName='th14-launcher-runtime-title-ending-scheduler-oct21.json',siteName='th14-launcher-site-title-ending-scheduler-oct21.json',evidenceName='th14-title-ending-scheduler-evidence-oct21.json',noteName='TH14_TITLE_ENDING_SCHEDULER_FIX_OCT21.md';
for(const n of [runtimeName,siteName,evidenceName,noteName])assert(!existsSync(resolve(root,'docs/porting',n)));
const priorBytes=read(resolve(root,'docs/porting/th14-launcher-runtime-replay-resume-final-oct21.json')),prior=JSON.parse(priorBytes);
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
const scope='TH14 Title6 requests preserve the current overlay8/normal29 pass and are consumed on the next Supervisor1 entry. Ending runs overlay8/fade16/normal29/Ending31; return6 repeats input sampling state and the complete animation/fade/interpreter pass. Natural Ending completion enters and updates Results on the next supervisor-equivalent tick. Validation covers four ordinary Title routes (2975 ticks), 32 original-code controlled cases (672 callback passes), two natural six-stage SakuyaA Easy runs using actual production score persistence, and 298 eligible staff fast-forward ticks. These source-bound WASI/component observations do not certify every game object, native full-campaign equivalence, physical GPU/audio, the new SDL browser flow or a new campaign matrix. New SDL146-source/149-header snapshot links two rebuilt TUs and144 verified reused objects; GameBattle/Application header-dependent controls are byte-identical. Existing02669 browser/matrix results are not inherited.';
const runtime={passed:true,completeGame:false,nativeEquivalent:false,out,buildDirectory:folder,
 build:{...build,kind:'th14-sdl3-web-release',sources:build.sourceHashes,headers:build.headerHashes,sha256:build.wasmSha256,bytes:build.wasmBytes},files,
 exports:WebAssembly.Module.exports(new WebAssembly.Module(wasm)),toolSha256:sha(read(import.meta.filename)),sourceSaveDeltaSha256:prior.sourceSaveDeltaSha256,
 sourceShellSha256:prior.sourceShellSha256,baseRuntimeReportSha256:sha(priorBytes),sdlBuildReportSha256:sha(buildBytes),publicEvidenceSha256:sha(evidenceBytes),independentSdlVerificationSha256:sha(independentBytes),headerDependencyProofSha256:sha(headerProofBytes),
 changedFiles:changed,sameProductionWasm:false,baseProductionWasmSha256:prior.build.sha256,sourceSnapshotBound:true,currentWorkspaceSourcesVerified:false,browserValidated:false,priorBrowserAcceptanceInherited:false,campaignMatrixForThisModuleVerified:false,newOriginalAssetsAdded:false,scope};
const runtimeBytes=Buffer.from(JSON.stringify(runtime,null,2)+'\n');writeFileSync(resolve(root,'docs/porting',runtimeName),runtimeBytes,{flag:'wx'});
const baseBytes=read(resolve(root,'docs/porting/th14-launcher-site-replay-resume-final-oct21.json')),base=JSON.parse(baseBytes),siteFiles=new Map();
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
 changedFiles:siteChanged,sameProductionWasm:false,sourceSaveDeltaSha256:runtime.sourceSaveDeltaSha256,browserValidated:false,priorBrowserAcceptanceInherited:false,campaignMatrixForThisModuleVerified:false,newOriginalAssetsAdded:false,publicEvidenceSha256:sha(evidenceBytes),scope};
const siteBytes=Buffer.from(JSON.stringify(siteReport,null,2)+'\n');write(siteOut,'release.json',siteBytes);writeFileSync(resolve(root,'docs/porting',siteName),siteBytes,{flag:'wx'});
writeFileSync(resolve(root,'docs/porting',evidenceName),evidenceBytes,{flag:'wx'});
const note=Buffer.from('# TH14 标题切换与结局调度修复（2026-10-21）\n\n'+releaseNoteBytes.toString().trim()+'\n\n证据：[精简验证摘要]('+evidenceName+')；[运行包报告]('+runtimeName+')；[站点包报告]('+siteName+')。\n');
writeFileSync(resolve(root,'docs/porting',noteName),note,{flag:'wx'});
console.log(JSON.stringify({passed:true,wasmSha256:build.wasmSha256,out,site,buildId,files:siteFiles.size,runtimeReportSha256:sha(runtimeBytes),siteReportSha256:sha(siteBytes),evidenceSha256:sha(evidenceBytes),noteSha256:sha(note),browserValidated:false,campaignMatrixForThisModuleVerified:false}));
