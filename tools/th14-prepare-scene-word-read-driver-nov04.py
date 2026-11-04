"""Add observed normalize writes and an inferred legal two-REP Scene read schedule."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];NAME='th14-compare-native-scene-word-read-nov04.mjs'


def source():
 path=R/'tools/th14-prepare-source-camera-rng-driver-nov04.py';spec=importlib.util.spec_from_file_location('parent_rng_source',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 text=m.source().decode().replace('\r\n','\n')
 def replace(old,new):
  nonlocal text
  assert text.count(old)==1,(old[:70],text.count(old));text=text.replace(old,new)
 replace("'first-script-read-point']);","'first-script-read-point','partial-scene-copy-mode']);")
 replace('assert.equal(c.replay_cursor_install(),1);','assert.equal(c.replay_cursor_install(),1);assert.equal(c.partial_scene_capture_install(),1);')
 replace('const sourceReadWindows=[];',"const partialSceneCopyMode=Number(options.get('partial-scene-copy-mode')??1);assert([0,1,2].includes(partialSceneCopyMode));\nconst partialSceneCopies=[],auxiliaryCameraReads=[];\nconst sourceReadWindows=[];")
 replace('  const boundary=e.lastMainCameraBoundary;', '''  const boundary=e.lastMainCameraBoundary;
  const publicationRead=cameraSourceReads.find(row=>row.stage===e.stage),publicationAfter=sceneEvents.find(row=>row.stage===e.stage&&row.event==='scene-camera-copy-after');
  if(partialSceneCopyMode&&phase==='update'&&publicationRead?.mainThreadRegisters.eip===0x40dae9){
   assert(publicationAfter&&publicationRead.copiedDwords>=15&&publicationRead.copiedDwords<75&&publicationRead.precedingPlayerCallbacks===callback);
   assert.equal(publicationRead.registers.ecx,75-publicationRead.copiedDwords);
   const originalBefore=Buffer.from(e.worldCameraHexAtWorkerEvent,'hex'),published=Buffer.from(publicationRead.worldCameraHex,'hex'),copied=Buffer.from(publicationAfter.copiedCameraHex,'hex');
   const changed=Array.from({length:75},(_,word)=>word).filter(word=>published.readUInt32LE(word*4)!==copied.readUInt32LE(word*4));assert.deepEqual(changed,[13,14]);
   for(const word of changed)assert.equal(copied.readUInt32LE(word*4),originalBefore.readUInt32LE(word*4));
   assert(e.debugEventSequence<publicationRead.debugEventSequence&&publicationRead.debugEventSequence<publicationAfter.debugEventSequence);
   const firstNs=publicationRead.hostMonotonicNs,lastNs=publicationAfter.hostMonotonicNs;
   assert.equal(c.observed_partial_scene_copy(e.stage,callback,13,publicationRead.copiedDwords,75,baseNow+BigInt(firstNs)-playerOrigin,baseNow+BigInt(lastNs)-playerOrigin,partialSceneCopyMode),1);
   partialSceneCopies.push({stage:e.stage,callback,publisherStart:13,readerPause:publicationRead.copiedDwords,publisherEnd:75,firstNs,lastNs,readerPausePrefixObserved:true,publisherStart13AndResumeScheduleInferred:true,exactOriginalScheduleRecovered:false});
   continue;
  }''')
 replace("   assert.equal(sourceRead.worldCameraHex,copyAfter.copiedCameraHex);", '''   const normalizePending=sourceRead.mainThreadD3dx?.mainPcRva===0x1bcaa4&&sourceRead.mainThreadRegisters.esi===0x4d9514;
   if(!normalizePending)assert.equal(sourceRead.worldCameraHex,copyAfter.copiedCameraHex);''')
 replace('   let point=null,ordinal=0,readyNs=null,sourcePcMapsDirectlyToCameraPoint=false;', "   let point=null,ordinal=0,readyNs=null,sourcePcMapsDirectlyToCameraPoint=false,referenceKind='actualSourceAtRead';")
 replace('   if(sourceRead.mainThreadRegisters.eip===0x446594&&sourceRead.mainThreadRegisters.esi===0x4d9514){', '''   if(normalizePending){
    const following=frame.find(row=>row.debugEventSequence>sourceRead.debugEventSequence);assert(following);
    ordinal=frame.findIndex(row=>row.debugEventSequence===following.debugEventSequence)+1;point=5;readyNs=copyAfter.hostMonotonicNs;referenceKind='completedCopiedCamera';
    assert.equal(copyAfter.worldCameraHexAtWorkerEvent,copyAfter.copiedCameraHex);
    const partial=Buffer.from(sourceRead.worldCameraHex,'hex'),completed=Buffer.from(copyAfter.copiedCameraHex,'hex');
    assert.deepEqual(Array.from({length:75},(_,word)=>word).filter(word=>partial.readUInt32LE(word*4)!==completed.readUInt32LE(word*4)),[13,14]);
    assert.equal(c.observed_auxiliary_camera_read(e.stage,callback,ordinal,6),1);auxiliaryCameraReads.push({stage:e.stage,callback,ordinal,point:6,observedNativeNormalizeRva:0x1bcaa4});
   }else if(sourceRead.mainThreadRegisters.eip===0x4465a6&&sourceRead.mainThreadRegisters.esi===0x4d9514){
    const current=frame.find(row=>row.debugEventSequence>sourceRead.debugEventSequence);assert(current);
    ordinal=frame.findIndex(row=>row.debugEventSequence===current.debugEventSequence)+1;point=5;readyNs=sourceRead.hostMonotonicNs;sourcePcMapsDirectlyToCameraPoint=true;
   }else if(sourceRead.mainThreadRegisters.eip===0x446594&&sourceRead.mainThreadRegisters.esi===0x4d9514){''')
 replace('sourceReadWindows.push({stage:e.stage,callback,ordinal,point,readyNs,sourcePcMapsDirectlyToCameraPoint,', 'sourceReadWindows.push({stage:e.stage,callback,ordinal,point,readyNs,referenceKind,sourcePcMapsDirectlyToCameraPoint,')
 replace('   const words=sceneWordDelivery.get(stage);if(words){readyNs=words.readyNs;completionSource=words.completionSource;}', '''   const words=sceneWordDelivery.get(stage);if(words){readyNs=words.readyNs;completionSource=words.completionSource;}
   const partial=partialSceneCopies.find(row=>row.stage===stage);if(partial){readyNs=partial.firstNs;completionSource='originalReadPrefixWithInferredResumableTwoRepSchedule';}''')
 replace("const native=cameraSourceReads.find(row=>row.stage===window.stage),expected=Buffer.from(native.worldCameraHex,'hex'),actual=Buffer.alloc(300),differences=[];", "const native=cameraSourceReads.find(row=>row.stage===window.stage),copy=sceneEvents.find(row=>row.stage===window.stage&&row.event==='scene-camera-copy-after'),expected=Buffer.from(window.referenceKind==='completedCopiedCamera'?copy.copiedCameraHex:native.worldCameraHex,'hex'),actual=Buffer.alloc(300),differences=[];")
 replace('sourceReadSnapshots.push({stage:window.stage,state,words:75,', 'sourceReadSnapshots.push({stage:window.stage,state,referenceKind:window.referenceKind,words:75,')
 replace("write(resolve(out,'source-read-camera-report.json'),", '''const auxiliaryReadSnapshots=[];
for(const window of auxiliaryCameraReads){
 const expected=Buffer.from(cameraSourceReads.find(row=>row.stage===window.stage).worldCameraHex,'hex'),actual=Buffer.alloc(300),differences=[];
 const state=Array.from({length:5},(_,word)=>c.auxiliary_camera_read_meta(window.stage,word)>>>0);assert.equal(state[4],1);
 for(let word=0;word<75;word++){const value=c.auxiliary_camera_read_word(window.stage,word)>>>0;actual.writeUInt32LE(value,word*4);if(value!==expected.readUInt32LE(word*4))differences.push(word);}
 write(resolve(out,'auxiliary-source-read-stage'+window.stage+'.u32'),actual,{flag:'wx'});auxiliaryReadSnapshots.push({window,state,differences,actualSha256:sha(actual),nativeSha256:sha(expected)});
}
const partialSceneSnapshots=[];
for(const window of partialSceneCopies){
 const expected=Buffer.from(sceneEvents.find(row=>row.stage===window.stage&&row.event==='scene-camera-copy-after').copiedCameraHex,'hex'),actual=Buffer.alloc(300),differences=[];
 const state=Array.from({length:12},(_,word)=>c.partial_scene_copy_meta(word)>>>0);assert.equal(state[4],1);assert.equal(state[5],1);assert.equal(state[9],1);assert.equal(state[10],0);
 if(partialSceneCopyMode===1){assert(state[7]>0&&state[8]>0,'The read must wait while the private incoming owner is retained');}
 for(let word=0;word<75;word++){const value=c.partial_scene_copy_word(word)>>>0;actual.writeUInt32LE(value,word*4);if(value!==expected.readUInt32LE(word*4))differences.push(word);}
 write(resolve(out,'partial-scene-copy-stage'+window.stage+'.u32'),actual,{flag:'wx'});partialSceneSnapshots.push({window,state,differences,actualSha256:sha(actual),nativeSha256:sha(expected)});
}
write(resolve(out,'scene-word-read-report.json'),JSON.stringify({partialSceneCopyMode,partialSceneCopies,partialSceneSnapshots,auxiliaryCameraReads,auxiliaryReadSnapshots,nativeValuesProvidedToEngine:false,exactOriginalScheduleRecovered:false,completeGame:false},null,2)+'\\n',{flag:'wx'});
report.partialSceneCopies=partialSceneCopies;report.auxiliaryCameraReads=auxiliaryCameraReads;report.partialSceneCopyMode=partialSceneCopyMode;
write(resolve(out,'source-read-camera-report.json'),''')
 text+="\nassert(auxiliaryReadSnapshots.every(row=>row.differences.length===0),'Intermediate normalize source differs');\nassert(partialSceneSnapshots.every(row=>row.differences.length===0),'Resumable Scene camera copy differs');\n"
 return text.replace('\n','\r\n').encode()


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();raw=source();target=R/'tools'/NAME
 if a.check:assert target.read_bytes()==raw
 else:assert not target.exists();target.write_bytes(raw)
 print(json.dumps(dict(path=NAME,sha256=hashlib.sha256(raw).hexdigest(),inferredLegalSchedule=True,exactOriginalScheduleRecovered=False)))
