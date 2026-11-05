// A synchronous Wasm run is compared with a same-thread timer and real Worker.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {Worker} from 'node:worker_threads';
import {performance} from 'node:perf_hooks';
import {WASI} from 'node:wasi';
const root=resolve(process.argv[3]??resolve(import.meta.dirname,'..')),home=resolve(process.argv[2]);
assert(home.startsWith(resolve(root,'artifacts/th14')+'\\')||home.startsWith(resolve(root,'artifacts/th14')+'/'));
const proof=JSON.parse(readFileSync(resolve(home,'build.json'))),bytes=readFileSync(resolve(home,'component.wasm'));
const sha=data=>createHash('sha256').update(data).digest('hex');assert.equal(sha(bytes),proof.wasmSha256);
const workerPath=resolve(home,'worker.mjs');
assert.equal(sha(readFileSync(workerPath)),proof.workerSha256);
const module=await WebAssembly.compile(bytes),cases=[];
async function instance(ready,commit){
    const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
    const wasm=await WebAssembly.instantiate(module,{wasi_snapshot_preview1:wasi.wasiImport,
        delivery:{ready,commit,now:()=>performance.now()}});wasi.initialize(wasm);return wasm.exports;
}
function state(c){const words=Array.from({length:64},(_,i)=>c.delivery_value(i)>>>0);return {
    complete:words[0]===1,stores:words[1],commits:words[2],iterations:words[3],progress:words[4],
    invalid:words[5],gameSeed:words[6],gameCalls:words[7],scriptSeed:words[8],scriptCalls:words[9],
    entry:words[10],lastValue:words[11],elapsedUs:words[12],observerStillInstalled:words[13],
    commitRows:Array.from({length:words[2]},(_,i)=>words.slice(16+i*16,32+i*16))};}
// Same-thread timers cannot execute inside the synchronous Wasm call.
let frontier=0,timerFired=false;
const baseline=await instance(index=>frontier>=index+1?1:0,()=>{});
const timer=setTimeout(()=>{timerFired=true;frontier=3;},60);
assert.equal(baseline.delivery_run(120),1);const blocked=state(baseline);
assert(!timerFired&&!blocked.complete&&blocked.stores===0&&blocked.iterations>0);
await new Promise(resolve=>setImmediate(resolve));
if(!timerFired)await new Promise(resolve=>setTimeout(resolve,1));
assert(timerFired);assert.equal(baseline.delivery_run(120),1);const yielded=state(baseline);
assert(yielded.complete&&yielded.stores===3&&yielded.commits===3);clearTimeout(timer);
cases.push({name:'same-thread-timer',blockedUntilReturn:true,blocked,yielded});
for(const name of ['worker-a','worker-b','worker-c','cancel-after-script','stale-generation']){
    const buffer=new SharedArrayBuffer(6*4),shared=new Int32Array(buffer),generation=37;
    Atomics.store(shared,0,generation);
    const worker=new Worker(workerPath,{workerData:{buffer,generation,minimumMs:60}});
    let workerStatus,returned=false,commitsBeforeReturn=0;
    const completion=new Promise((resolve,reject)=>{worker.on('error',reject);worker.on('message',message=>{
        if(message.status!==undefined){workerStatus=message.status;resolve(message);}
    });worker.on('exit',code=>{if(code!==0)reject(new Error('Worker exit '+code));});});
    // Attach rejection handling immediately, even while the main thread blocks.
    completion.catch(()=>{});
    await new Promise((resolve,reject)=>{worker.once('error',reject);worker.on('message',message=>{if(message.online)resolve();});});
    const c=await instance(index=>{
        if(Atomics.load(shared,0)!==generation||Atomics.load(shared,1)===2)return 2;
        return Atomics.load(shared,2)>=index+1?1:0;
    },index=>{
        if(!returned)++commitsBeforeReturn;
        assert.equal(Atomics.load(shared,3),index);
        Atomics.store(shared,3,index+1);Atomics.notify(shared,3);
        if(name==='cancel-after-script'&&index===1){Atomics.store(shared,1,2);Atomics.store(shared,3,-1);Atomics.notify(shared,1);Atomics.notify(shared,3);}
    });
    if(name==='stale-generation')Atomics.store(shared,0,generation+1);
    Atomics.store(shared,5,1);Atomics.notify(shared,5);
    let observed;
    try{
        assert.equal(c.delivery_run(2500),1);returned=true;observed=state(c);
        if(name.startsWith('worker-')){
            assert(observed.complete&&observed.stores===3&&observed.commits===3);
            assert.equal(commitsBeforeReturn,3);assert(observed.iterations>0);
        }else if(name==='cancel-after-script'){
            assert(!observed.complete&&observed.stores===2&&observed.progress===2);
            assert.equal(observed.gameCalls,19);assert.equal(commitsBeforeReturn,2);
        }else assert(!observed.complete&&observed.stores===0&&observed.progress===2);
        assert.equal(observed.invalid,0);assert.equal(observed.observerStillInstalled,0);
        await Promise.race([completion,new Promise((_,reject)=>{const t=setTimeout(()=>reject(new Error('Worker terminal timeout')),3000);t.unref();})]);
        assert.equal(workerStatus,name.startsWith('worker-')?2:3);
        cases.push({name,commitsBeforeSynchronousReturn:commitsBeforeReturn,observed,workerStatus});
    }finally{
        Atomics.store(shared,1,2);Atomics.store(shared,3,-1);Atomics.notify(shared,1);Atomics.notify(shared,3);Atomics.notify(shared,5);
        await worker.terminate();
    }
}
const result={schema:'th14/independent-rng-delivery-component/1',passed:true,cases,
    wasmSha256:proof.wasmSha256,workerSha256:proof.workerSha256,driverSha256:sha(readFileSync(import.meta.filename)),
    realProductionRestoreJob:true,realProductionRngNext32:true,syntheticInputsOnly:true,
    producerSuppliesRngWords:false,producerSuppliesFrameOrVmIdentity:false,
    sharedWasmMemoryRequired:false,wasmThreadsRebuilt:false,
    producerWaitsForMainStoreAcknowledgements:true,extraSynchronizationCostUncalibrated:true,
    ordinaryApplicationIntegrated:false,originalSchedulingEquivalent:false,
    wholeReplayCompared:false,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(home,'verified.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,cases:cases.length,workerRuns:3,cancelledAndStaleControls:2,
    realStoresDuringSynchronousWasm:true,ordinaryApplicationIntegrated:false,completeGame:false}));
