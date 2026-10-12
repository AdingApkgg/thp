import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/layers-check');mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th14-layers-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/layers-native.json'),'utf8')),sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','AnmManager','Interpolation'].map(n=>`cpp/game/${n}.cpp`).concat('tests/cpp/th14-layers-fixture.cpp');
const path=resolve(out,'th14.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
for(const [index,row] of proof.cases.entries()){
 assert.equal(c.run(row.overlay,row.start,row.variant),1);
 assert.deepEqual(Array.from({length:c.updates_size()},(_,i)=>c.update_value(i)),row.updates,`walk ${index} updates`);
 for(let i=0;i<8;++i)assert.equal(c.alive(i),row.deleted.includes(i)?0:1,`walk ${index} retirement ${i}`);
 for(let layer=0;layer<36;++layer){
  if(row.layers[layer][0]===-1)continue;const values=[];
  for(let i=0;i<=8;++i){const v=c.layer_value(layer,i);if(v===-1)break;values.push(v);}
  assert.deepEqual(values,row.layers[layer],`walk ${index} layer ${layer}`);
 }
}
writeFileSync(resolve(root,'docs/porting/th14-layers-verified.json'),JSON.stringify({passed:true,nativeExecutableSha256:proof.executableSha256,nativeCases:proof.cases.length,
 scope:'Normal layers 0..33 and overlay 34/35; overlay fallback, stable registration order, post-update layer changes, deletion flags and update-status retirement. Native VM-update/deletion are controlled boundaries; production manager runs its real idle VM and retirement.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/AnmManager.hpp','cpp/game/AnmVm.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-layers-native.py','tools/th14-layers-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');
console.log(`PASS: ${proof.cases.length} TH14 normal/overlay registry walks.`);
