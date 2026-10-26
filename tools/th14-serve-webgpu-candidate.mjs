// HTTP transport for an immutable local route overlay; never opens a browser.
import assert from 'node:assert/strict';
import {readFileSync,realpathSync} from 'node:fs';
import {resolve} from 'node:path';
import {createServer} from 'node:http';
import {root,digest,inside,options,handler,isMain} from './th14-local-audio-policy.mjs';

export function prepare(argv=[]) {
  const settings=options(argv,['--report']);
  assert(settings.report,'An explicit candidate report is required');
  const reportPath=realpathSync(inside(resolve(root,'artifacts/th14'),resolve(settings.report)));
  inside(resolve(root,'artifacts/th14'),reportPath);
  const proof=JSON.parse(readFileSync(reportPath));
  assert.equal(proof.schema,'th14/webgpu-launcher-routes/1');
  assert(proof.prepared&&proof.candidateOnly&&!proof.browserRun&&!proof.browserAcceptance);
  const roots=proof.roots.map(name=>realpathSync(inside(root,resolve(root,name))));
  for (const path of roots) {
    assert(path.startsWith(resolve(root,'artifacts/th14')+'\\')||path.startsWith(resolve(root,'runtimes/th14/th14_web/artifacts')+'\\')||
      path.startsWith(resolve(root,'artifacts/th14')+'/')||path.startsWith(resolve(root,'runtimes/th14/th14_web/artifacts')+'/'));
  }
  const files=new Map();
  for (const [name,row] of Object.entries(proof.files)) {
    assert(name&&!name.startsWith('/')&&!name.includes('\\')&&!name.split('/').some(part=>part==='..'||part==='.'||!part));
    const path=realpathSync(inside(root,resolve(root,row.path)));
    assert(roots.some(base=>{try{inside(base,path);return true;}catch{return false;}}),'Route outside frozen candidate roots');
    assert(/^[a-f0-9]{64}$/.test(row.sha256)&&Number.isSafeInteger(row.bytes)&&row.bytes>=0);
    files.set('/'+name,{path,length:row.bytes,sha256:row.sha256});
  }
  assert(files.has('/index.html')&&files.has('/runtime/th14/Th14WebGpuRuntime.mjs'));
  files.set('/',files.get('/index.html'));
  return {settings,files,request:handler(files,settings),reportPath,reportSha256:digest(readFileSync(reportPath)),proof};
}

if (isMain(import.meta.url)) {
  const state=prepare(process.argv.slice(2));
  createServer(state.request).listen(state.settings.port,'127.0.0.1',()=>console.log(JSON.stringify({
    url:`http://localhost:${state.settings.port}/?game=th14`,quiet:!state.settings.sound,
    wasmSha256:state.proof.wasmSha256,candidateOnly:true,browserAcceptance:false})));
}
