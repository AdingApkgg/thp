// Data-free independent readiness producer. No game RNG word crosses this channel.
import {workerData,parentPort} from 'node:worker_threads';
import {performance} from 'node:perf_hooks';
const state=new Int32Array(workerData.buffer),generation=workerData.generation;
const owns=()=>Atomics.load(state,0)===generation&&Atomics.load(state,1)!==2;
const finish=status=>{Atomics.store(state,4,status);parentPort.postMessage({status});};
parentPort.postMessage({online:true});
while(owns()&&Atomics.load(state,5)===0)Atomics.wait(state,5,0,1000);
if(!owns()){finish(3);}else{
    Atomics.store(state,4,1);
    // The already-established ordinary loader minimum, not a per-record offset.
    Atomics.wait(state,1,0,workerData.minimumMs);
    let failed=false;
    for(let operation=1;operation<=3&&owns();++operation){
        Atomics.store(state,2,operation);Atomics.notify(state,2);
        const deadline=performance.now()+2000;
        while(owns()){
            // Reuse the value which failed the predicate. A second load here
            // could already see the acknowledgement, then sleep on that new
            // value after its notification has passed.
            const acknowledged=Atomics.load(state,3);
            if(acknowledged>=operation)break;
            if(performance.now()>deadline){failed=true;break;}
            Atomics.wait(state,3,acknowledged,100);
        }
        if(failed)break;
    }
    finish(failed?4:owns()?2:3);
}
