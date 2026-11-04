"""Infer a bounded first RNG-read handoff from intermediate store observations.

No observed RNG words, call counts or VM identities are supplied to the engine.
The complete restore is delivered before the first script read; exact ordering
of the independent gameplay-counter clear is not claimed.
"""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'tools/th14-compare-native-easy-context-nov04.mjs';raw=P.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='c5312ce1e4ecff13c0fbc37c75688ae4cfd6a9b8f806c91d79000b0ba7758ef1'
s=raw.decode();
def replace(old,new):
    global s
    assert s.count(old)==1,(old[:80],s.count(old));s=s.replace(old,new)
replace('const sourceReadWindows=[];', 'const sourceReadWindows=[],interStoreReadStages=[];')
old="if(initialized){assert.equal(initialized.pc,0x456133);assert(initialized.originalInstructionBytes.startsWith('f3a5'));assert.equal(c.observed_worker_initialize(stage,baseNow+BigInt(initialized.hostMonotonicNs)-playerOrigin),1);phaseInputs.push({stage,phase:'Initialize',readyNs:initialized.hostMonotonicNs,completionSource:'original456133AfterSeedsRestoredBeforeGlobalsCopy',globalCopyAlreadyCompletedNotAsserted:true});}"
replace(old,"""if(initialized){
   assert.equal(initialized.pc,0x456133);assert(initialized.originalInstructionBytes.startsWith('f3a5'));
   const stores=stageEvents('replay-rng-store-events.jsonl').filter(row=>row.stage===stage);
   const rng=stores.map(row=>{const bytes=Buffer.from(row.rngHex,'hex');return Array.from({length:4},(_,i)=>bytes.readUInt32LE(i*4));});
   const interStore=rng.length===4&&rng[1][1]>rng[0][1];
   const readyNs=interStore?stores[0].hostMonotonicNs:initialized.hostMonotonicNs;
   if(interStore){assert.deepEqual(stores.map(row=>row.pc),[0x456115,0x456129,0x456133,0x456135]);assert(stores.every(row=>row.precedingPlayerCallbacks===stores[0].precedingPlayerCallbacks));interStoreReadStages.push(stage);}
   assert.equal(c.observed_worker_initialize(stage,baseNow+BigInt(readyNs)-playerOrigin),1);
   phaseInputs.push({stage,phase:'Initialize',readyNs,observedCompletedStoresNs:initialized.hostMonotonicNs,completionSource:interStore?'inferredBeforeFirstScriptReadBetweenObservedStores':'original456133AfterSeedsRestoredBeforeGlobalsCopy',globalCopyAlreadyCompletedNotAsserted:true,exactIndependentCounterClearOrderRecovered:false});
  }""")
replace(" if(delta===0){firstScriptReadSkipped.push({stage,reason:'no completed script calls before next Player'});continue;}",""" if(interStoreReadStages.includes(stage)){
  const completedBetween=(rng[1][1]-rng[0][1])>>>0;
  assert(completedBetween>0&&completedBetween<10000&&delta===0);
  assert.equal(before[22],rng[0][1]);assert.equal(after[22],rng[1][1]);assert.deepEqual(rng[1],rng[2].map((v,i)=>i===3?rng[1][3]:v));assert.deepEqual(rng[2],rng[3]);
  assert.equal(rng[0][2],rng[1][2]);assert.equal(rng[0][3],rng[1][3]);assert.equal(rng[2][3],0);
  // The replay header supplies the seed through normal engine playback.
  // Native values here constrain the ordering proof only.
  let seed=before[23];for(let i=0;i<completedBetween;i++){const mixed=((seed^0x9630)-0x6553)&65535;seed=((mixed<<2)|(mixed>>>14))&65535;}
  assert.equal(seed,rng[1][0]);assert.equal(after[21],rng[1][0]);
  const previousNs=Number(times.readBigUInt64LE((callback-1)*8)),nextNs=Number(times.readBigUInt64LE(callback*8));
  const pumps=resourceEvents.filter(row=>row.event==='main-resource-pump'&&previousNs<row.hostMonotonicNs&&row.hostMonotonicNs<stores[0].hostMonotonicNs);
  const pumpNs=pumps.at(-1)?.hostMonotonicNs??previousNs,readyNs=stores[0].hostMonotonicNs;
  assert(previousNs<=pumpNs&&pumpNs<readyNs&&readyNs<stores[1].hostMonotonicNs&&stores[2].hostMonotonicNs<nextNs);
  assert(firstScriptReadPoint===0);assert.equal(c.observed_first_script_read_window(stage,callback,baseNow+BigInt(pumpNs)-playerOrigin,baseNow+BigInt(readyNs)-playerOrigin,0),1);
  firstScriptReadWindows.push({stage,callback,pumpNs,readyNs,lowerClockAnchor:pumps.length?'observedResourcePump':'precedingPlayerReceipt',completedScriptCallsBetweenObservedStores:completedBetween,inferredFirstReadOrder:true,exactIndependentCounterClearOrderRecovered:false,originalRngValuesProvidedToEngine:false,originalVmIdentityIsInput:false});continue;
 }
 if(delta===0){firstScriptReadSkipped.push({stage,reason:'no completed script calls before next Player'});continue;}""")
target=R/'tools/th14-compare-native-easy-interstore-read-v2-nov04.mjs';assert not target.exists();target.write_bytes(s.encode())
print(json.dumps(dict(path=target.relative_to(R).as_posix(),sha256=hashlib.sha256(s.encode()).hexdigest(),inferredFiniteOrderOnly=True,originalCounterClearOrderRecovered=False,strictWhitelistModified=False,completeGame=False)))
