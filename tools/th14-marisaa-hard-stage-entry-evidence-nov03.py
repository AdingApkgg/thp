"""Verify retained Hard original stage entries without asserting a clear or equivalence."""
from pathlib import Path
import argparse,hashlib,json,struct

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-candidates-second-nov03/case-marisaa-hard-retry';N=H/'native';bindings={}
def raw(path):
 path=path.resolve();assert path.is_relative_to(R);data=path.read_bytes();bindings[path.relative_to(R).as_posix()]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()};return data
def load(path):return json.loads(raw(path))
sha=lambda b:hashlib.sha256(b).hexdigest()
report=load(N/'report.json');end=load(H/'process-end.json');quiet=load(H/'native-silence-verified.json');meta=load(H.parent/'th14_ud0552-source.json');codec=load(H.parent/'native-codec-verified.json');initial=load(N/'untouched-first-player.json')
assert end['exitCode']==0 and end['guardStop'] is None and end['actualMastersZero'] and report['childExited'] and not report['error']
assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==report['pid'] and len(quiet['samples'])>=2 and all(all(sample[k]==0 for k in ['musicConfig','effectsConfig','musicMaster','effectsMaster']) for sample in quiet['samples'])
assert report['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353' and report['hardwareBreakpointsOnly'] and not report['instructionBytesPatched'] and not report['rngOrCounterWrites'] and not report['inputInjected'] and report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']
observer=raw(N/'observer-source.py');assert sha(observer)==report['sourceSha256']==sha(raw(R/'tools/th14-native-terminal-exception-observer-nov03.py'))
source=raw(H.parent/'th14_ud0552.rpy');decoded=raw(H.parent/'th14_ud0552-decoded.bin');assert sha(source)==meta['sha256']==report['sourceFullReplaySha256'] and sha(decoded)==meta['decodedSha256'] and meta['actualNativeCodecVerified'] and codec['passed']
matches=[row for row in codec['rows'] if row['sha256']==meta['sha256']];assert len(matches)==1 and matches[0]['decodedSha256']==meta['decodedSha256'] and matches[0]['nativeCodecObserverSha256']==codec['toolSha256']
assert meta['expectedSelection']==list(struct.unpack_from('<3I',decoded,0x7c))==[1,0,2] and initial['words'][27:31]==[1,0,2,1]
selected=raw(N/'selected-state.u32');count=report['callbacks'];assert 0<count<=160000 and len(selected)==count*128 and sha(selected)==report['selectedSha256']
first={};active={};previous_stage=1
for index in range(count):
 frame=struct.unpack_from('<I',selected,index*128)[0];stage=struct.unpack_from('<I',selected,index*128+120)[0];assert previous_stage<=stage<=6;previous_stage=stage
 first.setdefault(stage,index+1)
 if frame>0:active.setdefault(stage,index+1)
stages=sorted(first);assert stages==report['recordedStages'] and stages==sorted(active) and stages==list(range(1,max(stages)+1))
exceptions=len(report['debugErrors']);clean=exceptions==0;all_stages=stages==[1,2,3,4,5,6]
result=dict(verifiedRetainedOriginalStageEntries=True,observedStages=stages,firstStageEntryCallbacks=first,firstActiveStageCallbacks=active,callbacks=count,debugExceptions=exceptions,allSixStageEntriesObserved=all_stages,allSixStageEntriesInExceptionFreeCapture=all_stages and clean,actualMastersZero=True,forcedReplayEndMenuObserved=bool(report['observedForcedReplayEndMenu']),sourceReplayEofProved=False,clearCompletionNotAsserted=True,strictComparisonNotAsserted=True,wholeModeEquivalent=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=H/'stage-entry-verified.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(H) or out.is_relative_to(R/'docs/porting');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:
 assert not out.exists();out.write_bytes(data)
 if all_stages and clean:
  public=R/'docs/porting/th14-marisaa-hard-stage-entry-nov03.json'
  if public.exists():assert public.read_bytes()==data
  else:public.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
