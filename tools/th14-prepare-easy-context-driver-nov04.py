"""Handle observed final-draw copies and REP batching without state injection."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'tools/th14-compare-native-scene-word-read-nov04.mjs'
raw=P.read_bytes();assert hashlib.sha256(raw).hexdigest()=='2ab9b608568fa6de14f1a5f3f495d94fd74c773e8f036c87d25cc9040b93d0c1'
s=raw.decode().replace('\r\n','\n')
def replace(old,new):
    global s
    assert s.count(old)==1,(old[:90],s.count(old));s=s.replace(old,new)
replace("assert.equal(sourceRead.pc,0x40d445);assert.equal(sourceRead.copiedDwords,13);", "assert.equal(sourceRead.pc,0x40d445);assert(sourceRead.copiedDwords>=13&&sourceRead.copiedDwords<75);assert.equal(sourceRead.registers.ecx,75-sourceRead.copiedDwords);")
replace("   }else if(boundary.event==='world-perspective-right-written'){", "   }else if(boundary.event==='world-perspective-right-written'&&frame.some(row=>row.debugEventSequence>sourceRead.debugEventSequence)){")
replace("  const map=boundary.event==='world-perspective-right-written'?afterDrawWorker:beforeDrawWorker;", '''  if(boundary.event==='world-perspective-right-written'&&sourceRead&&copyAfter){
   // The copy occurs after the final observed draw-camera publication, before
   // the next controller publication. There is no following draw in this frame.
   const frame=cameraBoundaryEvents.filter(row=>row.event==='world-perspective-right-written'&&row.precedingPlayerCallbacks===callback);
   assert(frame.length&&frame.every(row=>row.debugEventSequence<e.debugEventSequence));
   const next=cameraBoundaryEvents.find(row=>row.event==='controller-camera-published'&&row.precedingPlayerCallbacks===callback&&row.debugEventSequence>copyAfter.debugEventSequence);assert(next);
   assert(frame.at(-1).hostMonotonicNs<e.hostMonotonicNs&&copyAfter.hostMonotonicNs<next.hostMonotonicNs);
   assert.equal(sourceRead.worldCameraHex,copyAfter.copiedCameraHex);
  }
  const map=boundary.event==='world-perspective-right-written'?afterDrawWorker:beforeDrawWorker;''')
target=R/'tools/th14-compare-native-easy-context-nov04.mjs';assert not target.exists();target.write_bytes(s.encode())
print(json.dumps(dict(path=target.relative_to(R).as_posix(),parentSha256=hashlib.sha256(raw).hexdigest(),sha256=hashlib.sha256(s.encode()).hexdigest(),nativeStateProvidedToEngine=False,strictSceneWhitelistModified=False,ordinaryIndependentTimingAcceptance=False,completeGame=False)))
