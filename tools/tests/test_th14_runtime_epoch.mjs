import assert from 'node:assert/strict';
import {createManagedRuntimeGenerationLease} from '../../runtimes/th12/th12_web/launcher/.cache/build/browser/assets/launcher/runtime-generation-lease.mjs';
import {runtimeEpochContract} from '../../runtimes/th12/th12_web/sdl-runtime/runtime-epoch.mjs';
const lease=createManagedRuntimeGenerationLease(),generation={id:'same-installed-data',game:'th14'};
lease.bind('th14',generation,1);
assert.equal(lease.resolve({game:'th14',generation:generation.id,epoch:1}),generation);
lease.bind('th14',generation,2);
// A restarted frame uses identical installed DATA but must reject its predecessor.
for(const epoch of [1,undefined,'2',0,-1])assert.throws(()=>lease.resolve({game:'th14',generation:generation.id,epoch}),/inactive/);
assert.equal(lease.resolve({game:'th14',generation:generation.id,epoch:2}),generation);
assert.throws(()=>lease.bind('th14',generation,NaN),/epoch/);
assert.equal(lease.resolve({game:'th14',generation:generation.id,epoch:2}),generation);
lease.clear();assert.throws(()=>lease.resolve({game:'th14',generation:generation.id,epoch:2}),/inactive/);
// Earlier non-epoch Runtime deployments retain the existing generation contract.
const legacy={id:'legacy',game:'th08'};lease.bind('th08',legacy);
assert.equal(lease.resolve({game:'th08',generation:'legacy'}),legacy);
assert.throws(()=>lease.resolve({game:'th14',generation:'legacy'}),/inactive/);
console.log('TH14 same-generation restart / stale epoch / legacy lease: PASS');
const current=runtimeEpochContract('th14','2');
assert.deepEqual(current.fields,{epoch:2});assert.equal(current.accepts({epoch:2}),true);
for(const epoch of [1,undefined,'2',null,NaN,0])assert.equal(current.accepts({epoch}),false);
for(const raw of [null,'',NaN,'0','2.5','Infinity'])assert.equal(runtimeEpochContract('th14',raw).accepts({epoch:Number(raw)}),false);
for(const game of ['th11','th12','th13']){const legacy=runtimeEpochContract(game,null);assert.deepEqual(legacy.fields,{});assert.equal(legacy.accepts({command:'configure'}),true);}
console.log('TH14 Runtime strict epoch / TH11-13 legacy command compatibility: PASS');
