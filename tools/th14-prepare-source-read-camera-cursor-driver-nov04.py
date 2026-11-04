"""Derive source-read camera windows from native PCs; never provide camera values."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];NAME='th14-compare-native-source-read-camera-cursor-nov04.mjs'


def source():
 path=R/'tools/th14-prepare-camera-cursor-driver-nov04.py';spec=importlib.util.spec_from_file_location('parent_cursor',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 text=m.source().decode().replace('\r\n','\n')
 def replace(old,new):
  nonlocal text
  assert text.count(old)==1,(old[:80],text.count(old));text=text.replace(old,new)
 replace("const sceneEvents=phasedScheduler?stageEvents('scene-camera-copy-events.jsonl'):[];", "const sourceReadWindows=[];\nconst cameraSourceReads=phasedScheduler?stageEvents('worker-camera-source-read-events.jsonl'):[];\nconst sceneEvents=phasedScheduler?stageEvents('scene-camera-copy-events.jsonl'):[];")
 replace("  const map=boundary.event==='world-perspective-right-written'?afterDrawWorker:beforeDrawWorker;", '''  const sourceRead=cameraSourceReads.find(row=>row.stage===e.stage),copyAfter=sceneEvents.find(row=>row.stage===e.stage&&row.event==='scene-camera-copy-after');
  if(sourceRead&&copyAfter){
   assert.equal(sourceRead.precedingPlayerCallbacks,callback);assert.equal(sourceRead.pc,0x40d445);assert.equal(sourceRead.copiedDwords,13);
   assert(e.hostClockSharedAtDebugEventReceipt&&sourceRead.hostClockSharedAtDebugEventReceipt&&copyAfter.hostClockSharedAtDebugEventReceipt);
   assert(e.debugEventSequence<sourceRead.debugEventSequence&&sourceRead.debugEventSequence<copyAfter.debugEventSequence);
   assert.equal(sourceRead.worldCameraHex,copyAfter.copiedCameraHex);
   const frame=cameraBoundaryEvents.filter(row=>row.event==='world-perspective-right-written'&&row.precedingPlayerCallbacks===callback);
   let point=null,ordinal=0,readyNs=null,sourcePcMapsDirectlyToCameraPoint=false;
   if(sourceRead.mainThreadRegisters.eip===0x446594&&sourceRead.mainThreadRegisters.esi===0x4d9514){
    // Native446590 stores XY.446594 is the next instruction, before the Z store.
    point=3;ordinal=1+frame.filter(row=>row.debugEventSequence<sourceRead.debugEventSequence).length;readyNs=sourceRead.hostMonotonicNs;sourcePcMapsDirectlyToCameraPoint=true;
    assert(frame[ordinal-1]&&sourceRead.debugEventSequence<frame[ordinal-1].debugEventSequence);
   }else if(boundary.event==='world-perspective-right-written'){
    const lastNormalized=frame.filter(row=>row.debugEventSequence<sourceRead.debugEventSequence).at(-1);assert(lastNormalized);
    ordinal=frame.findIndex(row=>row.debugEventSequence===lastNormalized.debugEventSequence)+1;
    assert(ordinal>0&&ordinal<frame.length);
    assert(lastNormalized.debugEventSequence<sourceRead.debugEventSequence&&copyAfter.debugEventSequence<frame[ordinal].debugEventSequence);
    assert.equal(e.worldCameraHexAtWorkerEvent,sourceRead.worldCameraHex);
    point=5;readyNs=sourceRead.hostMonotonicNs;
   }
   if(point!==null){
    assert.equal(c.observed_source_read_window(e.stage,callback,ordinal,point,baseNow+BigInt(readyNs)-playerOrigin),1);
    sourceReadWindows.push({stage:e.stage,callback,ordinal,point,readyNs,sourcePcMapsDirectlyToCameraPoint,sourceReadMainPc:sourceRead.mainThreadRegisters.eip,sourceReadEventSequence:sourceRead.debugEventSequence,exactWorkerCopyScheduleRecovered:false});
    continue;
   }
  }
  const map=boundary.event==='world-perspective-right-written'?afterDrawWorker:beforeDrawWorker;''')
 replace('const fullBytes=Buffer.from(new Uint32Array(fullCameraRows).buffer);', '''const sourceReadSnapshots=[];
for(const window of sourceReadWindows){
 const native=cameraSourceReads.find(row=>row.stage===window.stage),expected=Buffer.from(native.worldCameraHex,'hex'),actual=Buffer.alloc(300),differences=[];
 const state=Array.from({length:6},(_,field)=>c.source_read_window_state(window.stage,field)>>>0);
 assert.equal(state[4],1);assert.equal(state[5],0);
 for(let word=0;word<75;word++){const value=c.source_read_camera_word(window.stage,word)>>>0;actual.writeUInt32LE(value,word*4);if(value!==expected.readUInt32LE(word*4))differences.push({word,actual:value,expected:expected.readUInt32LE(word*4)});}
 write(resolve(out,'source-read-camera-stage'+window.stage+'.u32'),actual,{flag:'wx'});
 sourceReadSnapshots.push({stage:window.stage,state,words:75,differences,actualSha256:sha(actual),nativeSha256:sha(expected),readOnlySourceCameraBeforeProductionPoll:true});
}
write(resolve(out,'source-read-camera-report.json'),JSON.stringify({windows:sourceReadWindows,snapshots:sourceReadSnapshots,nativeValuesProvidedToEngine:false,hostClockBoundaryReplayAdded:true,exactWorkerCopyScheduleRecovered:false,completeGame:false},null,2)+'\\n',{flag:'wx'});
report.sourceReadWindows=sourceReadWindows;report.originalSourceReadPcObserved=true;report.hostClockBoundaryReplayAdded=true;report.exactWorkerCopyScheduleRecovered=false;
const fullBytes=Buffer.from(new Uint32Array(fullCameraRows).buffer);''')
 text=text.replace('hostClockOverridesAdded:false','hostClockOverridesAdded:true')
 text+="\nassert(sourceReadSnapshots.every(row=>row.differences.length===0),'Observed source camera words differ');\n"
 return text.replace('\n','\r\n').encode()


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args();raw=source();target=R/'tools'/NAME
 if args.check:assert target.read_bytes()==raw
 else:assert not target.exists();target.write_bytes(raw)
 print(json.dumps(dict(path=NAME,sha256=hashlib.sha256(raw).hexdigest(),nativeCameraFields=75,productionCoreChanged=False)))
