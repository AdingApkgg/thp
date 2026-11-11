import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=process.cwd(),home=resolve(root,'artifacts/th14/initial-pause-owner-nov11'),component=resolve(home,'component-v2');
const load=p=>JSON.parse(readFileSync(p)),sha=b=>createHash('sha256').update(b).digest('hex');
const build=load(resolve(component,'build.json')),results={};
assert.equal(sha(readFileSync(resolve(home,'fixture.cpp'))),build.fixtureSha256);
for(const [p,h]of Object.entries(build.frozenSourceBindings))assert.equal(sha(readFileSync(resolve(root,p))),h,p);
for(const r of build.providers)assert.equal(sha(readFileSync(resolve(root,r.object))),r.objectSha256,r.object);
for(const mode of ['baseline','candidate']){
 const bytes=readFileSync(resolve(component,mode+'.wasm'));assert.equal(sha(bytes),build.outputs[mode]);
 const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/stock':resolve(root,'artifacts/th14/node-gles-host-nov08/native-later/work')},returnOnExit:true});
 const env={memory};for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{throw Error('Unexpected platform call '+i.name);};
 const instance=new WebAssembly.Instance(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const count=instance.exports.run();assert.equal(count,52);
 const words=Array.from(new Uint32Array(memory.buffer,instance.exports.data(),count));results[mode]={cycles:Array.from({length:4},(_,n)=>words.slice(n*10,n*10+10)),tail:words.slice(40)};
}
assert.deepEqual(results.candidate.cycles.map(r=>r[3]),[0,1,2,0],'Native per-entry reset avoids stale disabled choices');
assert.deepEqual(results.candidate.cycles.map(r=>r[4]),[1,1,1,1],'Reuse object state across pause/resume');
assert.deepEqual(results.candidate.cycles.map(r=>r[8]),[0,0,0,0],'Do not destroy the native owner on resume');
assert.deepEqual(results.candidate.tail,[1,1,0,1,1,2,2,1,1,1,1,1],'Prepare privately without RNG, destroy once on shutdown');
assert.deepEqual(results.baseline.cycles.map(r=>r[8]),[1,2,3,4]);
assert.deepEqual(results.baseline.tail,[0,1,4,4,4,0,0,0,0,0,0,0]);
writeFileSync(resolve(home,'component-v2-results.json'),JSON.stringify({fields:['cycle','allocationsAtEntry','freesAtEntry','disabledCount','retainedNameByte','selected','state','timer','freesAfterResume','allocationsAfterResume'],...results,fullGameplayAcceptance:false,audioDevicesOpened:0},null,2)+'\n');
console.log(JSON.stringify({passed:true,cyclesPerMode:4,baselineAllocations:4,candidateAllocations:1,candidateResumeFrees:0,candidateShutdownFrees:1,rngPreserved:true,closeBeforeActivation:true,rejectWrongThread:true,resultEntryReusesOwner:true,rejectDuplicatePreparation:true,audioDevicesOpened:0}));
