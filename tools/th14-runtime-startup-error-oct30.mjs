// Exercise the actual Launcher function against declared Package/Runtime I/O.
// No browser, game state, installed files or security preferences are changed.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const file='runtimes/th12/th12_web/launcher/src/launcher/app.mts';
const base='29e1a8ef759d1fc8c87b18882b0f074eeccb05d2';
const hash=data=>createHash('sha256').update(data).digest('hex');
const current=readFileSync(resolve(root,file),'utf8');
const legacy=execFileSync('git',['-C',resolve(root,'tools/tmp/github-source-release'),'show',`${base}:${file}`],{encoding:'utf8'});
function extract(source){
  const start=source.indexOf('async function ensureRuntime(');
  assert(start>=0&&source.indexOf('async function ensureRuntime(',start+1)<0);
  const end=source.indexOf('\n}\n',start);assert(end>start);
  return stripTypeScriptTypes(source.slice(start,end+2),{mode:'strip'});
}
const cases=[
  {name:'th14-download-error',game:'th14',phase:'install',error:'network'},
  {name:'th14-installed-runtime-timeout',game:'th14',phase:'runtime',error:'本地游戏加载超时'},
  {name:'th14-installed-runtime-device-error',game:'th14',phase:'runtime',error:'No WebGPU adapter'},
  {name:'th14-install-cancel',game:'th14',phase:'install',cancel:true},
  {name:'th14-no-host-download-error',game:'th14',phase:'install',host:false,error:'network'},
  {name:'th14-first-launch-success',game:'th14'},
  {name:'th10-download-legacy-fallback',game:'th10',phase:'install',error:'network'},
  {name:'th10-runtime-legacy-fallback',game:'th10',phase:'runtime',error:'runtime'},
  {name:'th10-no-host-download-error',game:'th10',phase:'install',host:false,error:'network'},
  {name:'th10-first-launch-success',game:'th10'},
  {name:'th14-existing-runtime-error',game:'th14',phase:'runtime',existing:true,error:'runtime'},
  {name:'th10-existing-runtime-error',game:'th10',phase:'runtime',existing:true,error:'runtime'},
];
async function run(source,test){
  const events=[],original=test.cancel?new DOMException('cancel','AbortError'):new Error(test.error||'unused');
  const fallback=new Error('test boundary: legacy data source');
  let committed=!!test.existing,caught=null;
  const context={
    state:{game:test.game},releaseCatalog:{games:{[test.game]:{}}},releaseCatalogUrl:'http://localhost/test-catalog.json',hostManifestAvailable:test.host!==false,
    remoteReleasePromise:Promise.resolve(),remoteCatalogError:null,importServer:false,
    readCurrentPackageGeneration:async()=>test.existing?{generation:{id:'test-generation'}}:null,
    checkTh14PlayerScope:()=>{},currentTh14PlayerScope:()=>true,maybeUpdateInstalledPackageBeforeLaunch:async()=>'none',
    openPlayerViewForScope:()=>events.push('open'),setPlayerStatus:()=>events.push('status'),
    beginBlockingNetworkOperation:()=>({controller:new AbortController()}),packageTrackedFetch:()=>async()=>{},
    installPublishedPackage:async()=>{events.push('install');if(test.phase==='install')throw original;committed=true;},
    ensureInstalledPackageRuntime:async()=>{events.push('runtime');if(test.phase==='runtime')throw original;return true;},
    finishBlockingNetworkOperation:()=>events.push('finish'),hideTransfer:()=>events.push('hide-transfer'),
    isCancelledDownload:error=>error.name==='AbortError',errorMessage:error=>error.message,
    showToast:()=>events.push('fallback-toast'),gameDataDescriptor:()=>{events.push('legacy-source');throw fallback;},
  };
  const fn=vm.runInNewContext(extract(source)+';ensureRuntime',context);
  try{await fn(true,null);}catch(error){caught=error;}
  return {name:test.name,game:test.game,events,packageCommitted:committed,
    errorPreserved:caught===original,legacyFallbackReached:caught===fallback,
    genericPackageError:!!caught&&String(caught.message).includes('辉针城需要已安装的本地游戏包'),
    success:caught===null};
}
const rows=[];
for(const test of cases){
  const before=await run(legacy,test),after=await run(current,test);
  if(test.game==='th14'&&test.phase&&!test.cancel&&!test.existing){
    assert(after.errorPreserved&&!after.genericPackageError&&!after.legacyFallbackReached,test.name);
    assert(after.events.includes('hide-transfer')&&after.events.filter(x=>x==='finish').length===1,test.name);
    if(test.host!==false){assert(before.genericPackageError&&!before.errorPreserved,test.name);}
  }else{
    assert.deepEqual(after,before,test.name+' changed outside intended TH14 error handling');
  }
  if(!test.phase)assert(after.success&&!after.events.includes('hide-transfer'),test.name);
  if(test.existing)assert(after.errorPreserved&&!after.events.includes('install'),test.name);
  if(test.phase==='runtime')assert(after.packageCommitted,test.name+' must fail after Package commit');
  rows.push({before,after});
}
const result={schema:'th14/runtime-startup-error-controls/1',verified:true,cases:rows.length,
  oldErrorMaskedCases:rows.filter(x=>x.before.genericPackageError).length,
  currentErrorMaskedCases:rows.filter(x=>x.after.genericPackageError).length,
  actualProductionFunctionExecuted:true,declaredPackageAndRuntimeIo:true,rows,
  sourcePath:file,sourceSha256:hash(current),legacySourceSha256:hash(legacy),legacyCommit:base,
  toolSha256:hash(readFileSync(fileURLToPath(import.meta.url))),browserAcceptance:false,completeGame:false,nativeEquivalent:false};
const options=process.argv.slice(2);assert(options.length===2&&options[0]==='--output');
const output=resolve(root,options[1]);assert(output.startsWith(resolve(root,'artifacts/th14')+'/')||output.startsWith(resolve(root,'artifacts/th14')+'\\'));
writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({verified:true,cases:rows.length,oldErrorMaskedCases:result.oldErrorMaskedCases,currentErrorMaskedCases:result.currentErrorMaskedCases}));
