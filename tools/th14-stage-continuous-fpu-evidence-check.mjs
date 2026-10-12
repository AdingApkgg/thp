import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';

const root=resolve(import.meta.dirname,'..'), evidence={};
const sha=b=>createHash('sha256').update(b).digest('hex');
function read(p){return readFileSync(resolve(root,p));}
function track(p){const b=read(p);evidence[p]={bytes:b.length,sha256:sha(b)};return b;}
function json(p){return JSON.parse(track(p));}
const exe=sha(readFileSync('H:/Games/th/14/th14.exe'));
const dll=sha(readFileSync('C:/Windows/SysWOW64/d3dx9_43.dll'));
const source=json('artifacts/th14/dialogue-text-check/objects.json');
for(const [p,h] of Object.entries(source.sourceHashes))assert.equal(sha(read('runtimes/th12/th12_web/'+p)),h,p);
const summaries=[];
for(const [folder,baseline,draw] of [
 ['stage-fpu-live-asset-update','stage-constructor-asset-update',false],
 ['stage-fpu-every-frame-live-asset-render','stage-every-frame-live-asset-render',true]
]){
 const nativeBytes=track(`artifacts/th14/${folder}/native.json`),n=JSON.parse(nativeBytes);
 const r=json(`docs/porting/th14-${folder}-observed-oct12.json`);
 assert(r.passed);assert.equal(r.frames,8400);assert.equal(r.words,30716776);assert.equal(r.routes,7);assert.equal(r.differences.length,0);
 assert.equal(n.initialFpcw,0x7f);assert.equal(n.continuousFpuControl,true);
 assert.equal(n.executableSha256,exe);assert.equal(n.dllSha256,dll);
 assert.equal(n.toolSha256,sha(track(`tools/th14-${folder}-native.py`)));
 assert.equal(n.parserSha256,sha(track('tools/th-anm-script-dump.py')));
 assert.equal(n.loaderSha256,sha(track('tools/th14-native-stage-fpu-resource-loader.py')));
 if(draw)assert.equal(n.rendererSha256,sha(track('tools/th14-native-stage-fpu-queued-live-render.py')));
 assert.equal(r.nativeProofSha256,sha(nativeBytes));
 assert.equal(r.toolSha256,sha(track(`tools/th14-${folder}-check.mjs`)));
 assert.deepEqual(r.sourceHashes,source.sourceHashes);
 const fixture=draw?'th14-stage-live-asset-render-fixture.cpp':'th14-stage-asset-update-fixture.cpp';
 assert.equal(r.fixtureSha256,sha(track('runtimes/th12/th12_web/tests/cpp/'+fixture)));
 for(const [p,h] of Object.entries(r.includeHashes))assert.equal(h,sha(track('runtimes/th12/th12_web/'+p)));
 assert.equal(r.wasmSha256,sha(track(`artifacts/th14/${folder}/stage.wasm`)));
 const binary=track(`artifacts/th14/${folder}/states.bin`);
 assert.equal(n.binarySha256,sha(binary));assert.equal(r.nativeBinarySha256,n.binarySha256);assert.equal(n.binaryBytes,binary.length);
 const old=json(`artifacts/th14/${baseline}/native.json`);
 assert.equal(old.executableSha256,exe);assert.equal(old.dllSha256,dll);
 assert.equal(old.toolSha256,sha(track(`tools/th14-${baseline}-native.py`)));
 let offset=0,words=0;
 for(const row of n.rows){
  assert.equal(row.rate,1);assert.equal(row.timeline.length,1201);
  const original=old.rows.find(o=>o.stage===row.stage&&o.rate===row.rate);assert(original);
  for(let i=0;i<row.timeline.length;i++){
   const t=row.timeline[i];assert.equal(t.frame,i-1);assert.equal(t.offset,offset);
   assert.equal(t.fpcw,row.stage===2?0x37f:0x7f);
   assert.equal(sha(binary.subarray(t.offset,t.offset+t.words*4)),t.sha256);
   assert.equal(t.sha256,original.timeline[i].sha256);assert.equal(t.words,original.timeline[i].words);
   offset+=t.words*4;words+=t.words;
  }
  if(draw){
   assert.equal(row.renders.length,1200);
   for(let i=0;i<row.renders.length;i++){
    const current={...row.renders[i]},oldRender=original.renders[i];
    assert.equal(current.fpcwBefore,row.stage===2?0x37f:0x7f);assert.equal(current.fpcwAfter,current.fpcwBefore);
    delete current.fpcwBefore;delete current.fpcwAfter;assert.deepEqual(current,oldRender);
   }
  }
 }
 assert.equal(offset,binary.length);assert.equal(words,30716776);
 if(draw){assert.equal(r.renderSamples,8400);assert.equal(r.renderWords,59409734);}
 summaries.push({folder,routes:r.routes,frames:r.frames,words:r.words,renderSamples:r.renderSamples,renderWords:r.renderWords,scope:r.scope});
}
const owner=json('docs/porting/th14-device-owner-native-verified-oct12.json');
assert(owner.passed);assert.equal(owner.entry,'0x46b1a0');assert.equal(owner.rows.length,11);
assert.equal(owner.executableSha256,exe);assert.equal(owner.toolSha256,sha(track('tools/th14-device-owner-native.py')));
assert.equal(owner.rows[0].requests[0].behaviorFlags,0x40);assert.equal(owner.rows[0].requests[0].deviceType,1);
assert.equal(owner.rows.find(r=>r.name==='create-all-failed').requests.length,60);
assert.equal(owner.rows.find(r=>r.name==='reset-all-failed').requests.length,20);
const inventory=json('artifacts/th14/fpu-control-audit/inventory.json');
assert.equal(inventory.executableSha256,exe);assert.equal(inventory.toolSha256,sha(track('tools/th14-fpu-control-audit.py')));
for(const address of ['0x403475','0x4034b5','0x4034f5','0x41cb7f','0x432143','0x435ac8'])assert(inventory.controls.some(c=>c.address===address&&c.mnemonic==='fninit'));
track('tools/th14-stage-continuous-fpu-evidence-check.mjs');
const report={passed:true,completeGame:false,nativeEquivalent:false,summaries,deviceOwnerCases:11,evidence,sourceHashes:source.sourceHashes,
 limits:'Continuous x87 precision-control evidence in isolated original resource/Stage entries, not full retail thread FPU state: status/tag controlled between calls, other world callbacks absent. HAL pixels/actual D3DX texture upload not included. Complete create/reset owner observes controlled COM/service results, not live driver/device creation. Historical fixed0x037f Stage states/submissions remain byte-identical within these seven rate1/1200-frame routes; no full-game equivalence claim.'};
writeFileSync(resolve(root,'docs/porting/th14-stage-continuous-fpu-verified-oct12.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,updateRoutes:7,updateFrames:8400,stateWords:30716776,renderFrames:8400,renderWords:59409734,deviceOwnerCases:11}));
