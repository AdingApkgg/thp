"""Declare a missing pump anchor only for the sealed stage3 RNG watch gap.

Stopped original input registers constrain read generation. The preceding
Player is an inferred lower clock anchor; no missing pump event is invented
and no original RNG value is passed to the engine.
"""
from pathlib import Path
import hashlib,json

R=Path(__file__).resolve().parents[1]
P=R/'tools/th14-compare-native-rng-register-audit-nov05.mjs'
D=R/'tools/th14-compare-native-rng-register-audit-gap-nov05.mjs'
SHA=lambda b:hashlib.sha256(b).hexdigest()
raw=P.read_bytes();assert SHA(raw)=='0ab8cba5a9d8ccdc0cb8d423b9b0759e18f561fddee56d87deff9dd9b55c46d3'
s=P.read_text()
old=" assert(pumps.length);const pumpNs=pumps.at(-1).hostMonotonicNs,readyNs=stores[2].hostMonotonicNs;\n assert(previousNs<pumpNs&&pumpNs<readyNs&&readyNs<nextNs);"
new=""" const pumpNs=pumps.at(-1)?.hostMonotonicNs??previousNs,readyNs=stores[2].hostMonotonicNs;
 let lowerClockAnchor='observedResourcePump',nativeRegisterGenerationProofSha256=null;
 if(!pumps.length){
  assert.equal(stage,3);assert(nativeReport.mainResourcePumpObservationHasDeclaredStage3WatchGap);
  const proofPath=resolve(nativeHome,'../register-evidence.json'),proofRaw=read(proofPath),proof=JSON.parse(proofRaw);
  assert(proof.verifiedFiniteOriginalRegisterReadEvidence&&proof.callbacks===35000&&proof.arithmeticPairsEqual>0);
  assert.equal(proof.verifierSha256,sha(read(resolve(root,'tools/th14-rng-register-trace-evidence-nov05.py'))));
  assert.equal(proof.bindings[relative(root,resolve(nativeHome,'report.json')).replaceAll('\\\\','/')].sha256,sha(read(resolve(nativeHome,'report.json'))));
  const access=stageEvents('script-rng-access-events.jsonl'),arm=JSON.parse(read(resolve(nativeHome,'script-rng-watch-arm.json'))),firstRead=access[0];
  assert.equal(arm.precedingPlayerCallbacks,callback);assert.equal(firstRead.precedingPlayerCallbacks,callback);
  assert(firstRead.instructionValueDecoded&&firstRead.instructionContract.kind==='mix32');
  assert.equal(firstRead.valueRetainedByTrappedInstruction,(firstRead.registers.eax&65535)^0x9630);
  assert.equal(firstRead.valueRetainedByTrappedInstruction,rng[1][0]&65535);
  assert.notEqual(before[21],firstRead.valueRetainedByTrappedInstruction,'This record must distinguish old and restored seed generations');
  assert.equal(Buffer.from(firstRead.rngHexAtObservation,'hex').readUInt32LE(4),before[22]);
  assert(arm.hostMonotonicNs<stores[0].hostMonotonicNs&&stores[3].debugEventSequence<firstRead.debugEventSequence);
  lowerClockAnchor='precedingPlayerReceiptWithDeclaredRngWatchGap';nativeRegisterGenerationProofSha256=sha(proofRaw);
 }
 assert(previousNs<=pumpNs&&pumpNs<readyNs&&readyNs<nextNs);"""
assert s.count(old)==1;s=s.replace(old,new)
old=" firstScriptReadWindows.push({stage,callback,pumpNs,readyNs,completedScriptCallsAfterRestore:delta,"
new=" firstScriptReadWindows.push({stage,callback,pumpNs,readyNs,lowerClockAnchor,nativeRegisterGenerationProofSha256,nativeRegisterValuesOnlyClassifyReadGeneration:true,exactOriginalScheduleRecovered:false,inferredClockLowerAnchor:!pumps.length,completedScriptCallsAfterRestore:delta,"
assert s.count(old)==1;s=s.replace(old,new)
assert not D.exists();D.write_text(s,encoding='utf8',newline='\n')
out=R/'artifacts/th14/script-rng-read-generation-nov05/portable-audit-gap-driver-prepared.json';assert not out.exists()
out.write_text(json.dumps(dict(driver=D.relative_to(R).as_posix(),driverSha256=SHA(D.read_bytes()),parentDriverSha256=SHA(raw),
    declaredPumpGapLowerAnchorAdded=True,inferredScheduleOnly=True,exactOriginalScheduleRecovered=False,nativeRngValuesProvidedToEngine=False,
    completeGame=False,toolSha256=SHA(Path(__file__).read_bytes())),indent=2)+'\n')
print(json.dumps(dict(prepared=True,driverSha256=SHA(D.read_bytes()),inferredScheduleOnly=True)))
