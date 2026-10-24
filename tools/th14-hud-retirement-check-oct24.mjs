import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,process.argv[2]??'artifacts/th14/stage-owner-retirement-oct24/unit'),sha=b=>createHash('sha256').update(b).digest('hex');
const proofBytes=read(resolve(home,'native.json')),proof=JSON.parse(proofBytes);assert.equal(proof.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const results={};
for(const label of ['before','after']){
 const bytes=read(resolve(home,label+'.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,counts={},first={};
 function equal(name,a,b,entry){if(JSON.stringify(a)===JSON.stringify(b))return;counts[name]=(counts[name]??0)+1;first[name]??={entry,expected:b,observed:a};}
 for(const [n,r]of proof.rows.entries()){
  assert.equal(c.run(r.variant,r.prior,r.position,r.displayed,r.hidden),1);
  equal('created',Array.from({length:c.count()},(_,i)=>c.script(i)),r.created,n);
  equal('name',[Boolean(c.name_value(0)),Boolean(c.name_value(1))],[r.nameRetained,r.nameRetired],n);
  equal('retirementFlagWords',Array.from({length:15},(_,i)=>c.retirement_word(i)>>>0),r.retirementFlagWords,n);
  for(const [slot,row]of r.observed.entries()){
   equal('state',Array.from({length:5},(_,k)=>c.state(slot,k)>>>0),row.state,n);
   equal('marks',Array.from({length:4},(_,k)=>c.mark(slot,k)>>>0),row.marks,n);
   for(const [i,vm]of row.vms.entries()){
    equal('presence',Boolean(c.present(slot,i)),vm!==null,n);
    if(vm){const expected=vm.slice();expected[0]&=6;equal('vmWords',Array.from({length:7},(_,k)=>c.value(slot,i,k)>>>0),expected,n);}
    equal('retired',Boolean(c.retired(slot,i)),r.retired[slot*7+i],n);
   }
  }
 }
 results[label]={wasmSha256:sha(bytes),differenceCounts:counts,firstDifferences:first,allEqual:Object.keys(counts).length===0};
}
assert(!results.before.allEqual);assert(results.after.allEqual);
const sources=['runtimes/th12/th12_web/tests/cpp/th14-hud-boss-rings-fixture.cpp','runtimes/th12/th12_web/cpp/game/HudTh14Boss.cpp','runtimes/th12/th12_web/cpp/game/GameBattle.cpp','tools/th14-hud-retirement-native-oct24.py','tools/th14-hud-retirement-check-oct24.mjs'];
const result={passed:true,cases:proof.rows.length,rawRetirementWordsPerCase:15,nativeExecutableSha256:proof.executableSha256,nativeProofSha256:sha(proofBytes),results,sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(read(resolve(root,p)))])),scope:proof.scope+' Actual production bosses_th14 before/after; old fixture retirement getters also corrected to observe flags2 bit0x20 directly. Prior VMs explicitly start with the ordinary factory bit0x200 in both controls. All15 complete flags2 words compare, alongside the existing scalar/creation/VM words. Native ANM allocation, binding, interpreter, lookup and interrupt remain declared services. No GPU or full-game equivalence.',completeGame:false,nativeEquivalent:false};
write(resolve(root,'docs/porting/th14-hud-retirement-verified-oct24.json'),JSON.stringify(result,null,2)+'\n');write(resolve(home,'verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:result.cases,before:results.before.differenceCounts,after:results.after.differenceCounts}));
