import assert from'node:assert/strict';import{readFileSync as read,writeFileSync as write}from'node:fs';import{resolve}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(process.argv[2]??resolve(root,'artifacts/th14/boss-name-input-oct25/unit')),sha=b=>createHash('sha256').update(b).digest('hex'),raw=read(resolve(root,'artifacts/th14/hud-boss-labels-native.json')),native=JSON.parse(raw),results={};
assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const rows=native.names.filter(r=>r.prior===0);assert.equal(rows.length,504);
for(const label of['before','after']){
 const bytes=read(resolve(home,label+'.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,differences=[];let cases=0;
 for(const r of rows)for(const current of[0,51,52,63,64,86,174]){
  assert(r.created.length<=1);const expected=r.created.length?r.created[0].script:-1,actual=c.name_input_run(r.stage,r.section,r.spell,r.subtype,current);++cases;
  if(actual!==expected)differences.push({stage:r.stage,section:r.section,practiceSelection:r.spell,subtype:r.subtype,currentSpell:current,native:expected,portable:actual});
 }
 results[label]={cases,differenceCount:differences.length,firstDifferences:differences.slice(0,12),differenceTraceSha256:sha(Buffer.from(JSON.stringify(differences))),wasmSha256:sha(bytes)};
}
assert(results.before.differenceCount>0);assert.equal(results.after.differenceCount,0);
const names=['runtimes/th12/th12_web/cpp/game/GameBattle.cpp','runtimes/th12/th12_web/cpp/game/HudTh14Boss.cpp','runtimes/th12/th12_web/tests/cpp/th14-hud-name-input-fixture.cpp','tools/th14-hud-boss-labels-native.py','tools/th14-hud-name-input-check-oct25.mjs'];
const report={passed:true,results,nativeReferenceSha256:sha(raw),sourceHashes:Object.fromEntries(names.map(n=>[n,sha(read(resolve(root,n)))])),scope:'504 original4350b0 boss-name controls with no prior handle, across seven stages, six sections, six global4f5844 values and both subtypes. Each repeats against seven unrelated active Spell+78 ids. Portable runs the actual private GameBattle::hud_input connection and real Hud::boss_name_th14; -fno-access-control is confined to the diagnostic translation unit. Stopped synthetic front scripts observe selection, not rendering. Original ANM service boundaries and exact native-control scope are declared by tools/th14-hud-boss-labels-native.py. Independent full replay snapshots separately check live VMs.',completeGame:false,nativeEquivalent:false};
write(resolve(home,'last-results.json'),JSON.stringify(results,null,2)+'\n');write(resolve(root,'docs/porting/th14-hud-name-input-verified-oct25.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,results}));
