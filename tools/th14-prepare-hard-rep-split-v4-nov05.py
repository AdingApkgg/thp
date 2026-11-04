"""Retain native read-result prefixes and infer explicit perspective/REP splits.

No camera/RNG/state values are submitted to the engine. The private diagnostic
schedule uses observed read prefixes and native write generations; it does not
claim independent timing or an exact original instruction interleaving.
"""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'tools/th14-compare-native-easy-context-nov04.mjs';D=R/'tools/th14-compare-native-hard-rep-split-v4-nov05.mjs';assert not D.exists();s=P.read_text();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(P.read_bytes())=='c5312ce1e4ecff13c0fbc37c75688ae4cfd6a9b8f806c91d79000b0ba7758ef1'
def replace(a,b):
    global s
    assert s.count(a)==1,(a[:90],s.count(a));s=s.replace(a,b)
replace('const partialSceneCopies=[],auxiliaryCameraReads=[];','const partialSceneCopies=[],auxiliaryCameraReads=[],perspectiveRepSplits=[];')
anchor='   const normalizePending=sourceRead.mainThreadD3dx?.mainPcRva===0x1bcaa4&&sourceRead.mainThreadRegisters.esi===0x4d9514;'
replace(anchor,'''   const readSource=Buffer.from(sourceRead.worldCameraHex,'hex'),readPrefix=Buffer.from(sourceRead.copiedCameraHex,'hex'),finishedCopy=Buffer.from(copyAfter.copiedCameraHex,'hex');
   const changedNativeWords=Array.from({length:75},(_,word)=>word).filter(word=>readSource.readUInt32LE(word*4)!==finishedCopy.readUInt32LE(word*4));
   const splitFrame=cameraBoundaryEvents.filter(row=>row.event==='world-perspective-right-written'&&row.precedingPlayerCallbacks===callback);
   let split=null;
   if(sourceRead.mainThreadRegisters.eip===0x4465a6&&sourceRead.mainThreadRegisters.esi===0x4d9514&&sourceRead.copiedDwords===13&&changedNativeWords.length===1&&changedNativeWords[0]===12){
    const written=sourceRead.lastMainCameraRightWrite;assert(written?.hardwareDataWrite&&written.debugEventSequence<sourceRead.debugEventSequence);
    assert.equal(written.rightHex,readSource.subarray(48,60).toString('hex'));
    const following=splitFrame.find(row=>row.debugEventSequence>sourceRead.debugEventSequence);assert(following);
    split={stage:e.stage,callback,ordinal:splitFrame.indexOf(following)+1,pause:13,start:4,end:5,reason:'completedReadPrefixPrecedesNormalizedXGenerationAtDebugReceipt'};
   }else if(sourceRead.mainThreadRegisters.eip===0x40e363&&sourceRead.copiedDwords===16&&changedNativeWords.length&&changedNativeWords.every(word=>word>=24&&word<56)){
    const ordinal=1+splitFrame.filter(row=>row.debugEventSequence<sourceRead.debugEventSequence).length;
    assert(splitFrame[ordinal-1]&&copyAfter.debugEventSequence<splitFrame[ordinal-1].debugEventSequence);
    split={stage:e.stage,callback,ordinal,pause:16,start:0,end:2,reason:'observedPrefixBeforeViewAndProjectionPublication'};
   }
   if(split){
    assert(readPrefix.subarray(0,split.pause*4).equals(finishedCopy.subarray(0,split.pause*4)),'An already-copied native prefix changed');
    const firstNs=sourceRead.hostMonotonicNs,lastNs=copyAfter.hostMonotonicNs;
    assert.equal(c.observed_perspective_rep_split(split.stage,callback,split.ordinal,split.pause,split.start,split.end,baseNow+BigInt(firstNs)-playerOrigin,baseNow+BigInt(lastNs)-playerOrigin),1);
    perspectiveRepSplits.push({...split,firstNs,lastNs,changedNativeWords,nativeReadGenerationClassificationUsed:true,readerPausePrefixObserved:true,publisherInterleavingInferred:true,exactOriginalScheduleRecovered:false});continue;
   }
'''+anchor)
replace('assert.deepEqual(Array.from({length:75},(_,word)=>word).filter(word=>partial.readUInt32LE(word*4)!==completed.readUInt32LE(word*4)),[13,14]);','''const normalizedTailChanges=Array.from({length:75},(_,word)=>word).filter(word=>partial.readUInt32LE(word*4)!==completed.readUInt32LE(word*4));
    assert(normalizedTailChanges.length&&normalizedTailChanges.every(word=>word===13||word===14),'Only normalized Y/Z may change after the observed X store');''')
replace('assert.equal(c.partial_scene_capture_install(),1);','assert.equal(c.partial_scene_capture_install(),1);assert.equal(c.perspective_rep_split_capture_install(),1);')
anchor="write(resolve(out,'scene-word-read-report.json'),"
replace(anchor,'''const perspectiveRepSplitSnapshots=[];
for(const window of perspectiveRepSplits){
 const readEvent=cameraSourceReads.find(row=>row.stage===window.stage),copy=sceneEvents.find(row=>row.stage===window.stage&&row.event==='scene-camera-copy-after');
 const expectedPrefix=Buffer.from(readEvent.copiedCameraHex,'hex').subarray(0,window.pause*4),expected=Buffer.from(copy.copiedCameraHex,'hex'),actual=Buffer.alloc(300),prefixBytes=Buffer.alloc(window.pause*4),differences=[];
 const state=Array.from({length:14},(_,index)=>c.perspective_rep_split_meta(window.stage,index)>>>0);
 assert.equal(state[7],1);assert.equal(state[8],1);assert(state[9]>0&&state[10]>0);assert.equal(state[11],1);assert.equal(state[12],1);assert.equal(state[13],0);
 for(let word=0;word<75;word++){const value=c.perspective_rep_split_word(window.stage,0,word)>>>0;actual.writeUInt32LE(value,word*4);if(value!==expected.readUInt32LE(word*4))differences.push(word);}
 for(let word=0;word<window.pause;word++)prefixBytes.writeUInt32LE(c.perspective_rep_split_word(window.stage,1,word)>>>0,word*4);
 write(resolve(out,'perspective-rep-scene-stage'+window.stage+'.u32'),actual,{flag:'wx'});
 perspectiveRepSplitSnapshots.push({window,state,differences,prefixEqual:prefixBytes.equals(expectedPrefix),actualSha256:sha(actual),nativeSha256:sha(expected),prefixSha256:sha(prefixBytes),nativePrefixSha256:sha(expectedPrefix)});
}
write(resolve(out,'perspective-rep-split-report.json'),JSON.stringify({windows:perspectiveRepSplits,snapshots:perspectiveRepSplitSnapshots,nativeReadGenerationClassificationUsed:true,noNativeStateValuesProvidedToEngine:true,independentTimingAccepted:false,exactOriginalScheduleRecovered:false,completeGame:false},null,2)+'\\n',{flag:'wx'});
report.perspectiveRepSplits=perspectiveRepSplits;report.perspectiveRepSplitSnapshots=perspectiveRepSplitSnapshots;
'''+anchor)
replace('assert.equal(e.worldCameraHexAtWorkerEvent,sourceRead.worldCameraHex);', 'assert(readPrefix.subarray(0,sourceRead.copiedDwords*4).equals(readSource.subarray(0,sourceRead.copiedDwords*4)));')
# Keep the evidence on disk, then reject any mismatched private read snapshot.
s += "\nassert(perspectiveRepSplitSnapshots.every(row=>row.prefixEqual&&row.differences.length===0),'Perspective/REP prefix or completed camera differs');\n"
D.write_text(s);out=R/'artifacts/th14/reimub-hard-full-context-nov05/retry1/hard-rep-driver-v4-prepared.json';assert not out.exists();out.write_text(json.dumps(dict(driver=D.relative_to(R).as_posix(),driverSha256=sha(D.read_bytes()),parentDriverSha256=sha(P.read_bytes()),nativeStateValuesProvidedToEngine=False,nativeReadGenerationClassificationUsed=True,diagnosticInferredPublisherSchedule=True,independentTimingAccepted=False,completeGame=False),indent=2)+'\n');print(json.dumps(dict(prepared=True,driverSha256=sha(D.read_bytes()),independentTimingAccepted=False)))
