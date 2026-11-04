"""Verify the common-clock original trace and its unchanged-driver comparison."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/unified-event-context-trace-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();bindings={}
 def raw(path):
  b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
 def load(path):return json.loads(raw(path))
 def rows(path):return [json.loads(x)for x in raw(path).splitlines()]
 N=H/'native';report=load(N/'report.json');prep=load(H/'prepared.json');end=load(H/'process-end.json')
 assert report['callbacks']==35000 and report['childExited']and not report['error']and not report['debugErrors']
 assert end['exitCode']==1 and end['guardStop']is None and report['observerTerminationRequested']
 assert report['hardwareBreakpointsOnly']and report['instructionBytesPatched']==report['rngOrCounterWrites']==0 and not report['inputInjected']
 assert report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']and bytes.fromhex(report['configHex'])[0x22:0x24]==bytes(2)
 assert report['debugEventReceiptClockShared']and report['maxMainStackCaptureBytes']==2048
 assert SHA(raw(H/'observer.py'))==SHA(raw(N/'observer-source.py'))==prep['observerSha256']==report['sourceSha256']
 assert prep['preparerSha256']==SHA(raw(R/'tools/th14-prepare-unified-event-context-observer-nov04.py'))and load(H/'clock-preflight.json')['passed']
 journal_raw=raw(N/'debug-event-clock.jsonl');assert SHA(journal_raw)==report['debugEventClockSha256']
 journal=[json.loads(x)for x in journal_raw.splitlines()];assert len(journal)==report['debugEventClockRows']==56734
 lookup={x['debugEventSequence']:x for x in journal};assert len(lookup)==len(journal)
 assert all(x['hostMonotonicNs']==x['debugEventReceiptHostNs']and x['hostClockSharedAtDebugEventReceipt']for x in journal)
 assert all(a['debugEventSequence']<b['debugEventSequence']and a['hostMonotonicNs']<b['hostMonotonicNs']for a,b in zip(journal,journal[1:]))
 files=['allocation-events.jsonl','resource-ready-events.jsonl','controller-phase-events.jsonl','camera-boundary-events.jsonl','camera-right-write-events.jsonl','scene-camera-copy-events.jsonl','worker-camera-source-read-events.jsonl','stage-object-vm-window-events.jsonl','replay-rng-store-events.jsonl','transition-events.jsonl','hud-initialization-events.jsonl'];shared={}
 for name in files:
  data=rows(N/name);shared[name]=len(data)
  for row in data:
   entry=lookup[row['debugEventSequence']];assert row['hostMonotonicNs']==row['debugEventReceiptHostNs']==entry['hostMonotonicNs']and row['threadId']==entry['threadId']and row['pc']==entry['pc']and row['hostClockSharedAtDebugEventReceipt']
 players=[x for x in journal if x['pc']==0x44dbd0];times=raw(N/'player-host-monotonic.u64')
 assert len(players)==35000 and [x['precedingPlayerCallbacks']for x in players]==list(range(35000))and times==struct.pack('<35000Q',*[x['hostMonotonicNs']for x in players])
 stores=rows(N/'replay-rng-store-events.jsonl');transition=rows(N/'transition-events.jsonl');assert len(stores)==8
 for stage in(2,3):
  selected=[x for x in stores if x['stage']==stage];assert [x['pc']for x in selected]==[0x456115,0x456129,0x456133,0x456135]
  init=next(x for x in transition if x['stage']==stage and x['event']=='replay-seeds-restored-before-globals-copy');counter=selected[2]
  assert init['debugEventSequence']==counter['debugEventSequence']and init['hostMonotonicNs']==counter['hostMonotonicNs']
  assert selected[-1]['registers']['ecx']==0 and selected[-1]['registers']['edi']==0x4f5898
  assert all(x['mainThreadContextAtWorkerDebugEvent']['stackBytes']>64 for x in selected)
 edges=rows(N/'stage-object-vm-window-events.jsonl');assert len(edges)==1964 and not report['stageObjectVmWindowHasActiveCallAtEnd']and not report['stageObjectVmReturnEventPendingAtEnd']
 for call,ret in zip(edges[::2],edges[1::2]):
  assert call['pc']==0x40f2a2 and ret['pc']==0x40f2a7 and ret['callEntryOrdinal']==call['ordinal']and call['vm']==ret['vm']
  assert call['stageObjectContext']['actualVmArrayAndPrimitiveIndexAgree']and ret['stageObjectContext']['currentExecutingObjectIdentityObserved']
 reads=rows(N/'worker-camera-source-read-events.jsonl');copies=rows(N/'scene-camera-copy-events.jsonl');read_summaries=[]
 for row in reads:
  assert row['pc']==0x40d445 and row['registers']['ecx']==75-row['copiedDwords']and row['copiedDwords']==13
  world=bytes.fromhex(row['worldCameraHex']);copy=next(x for x in copies if x['stage']==row['stage']and x['event']=='scene-camera-copy-after')
  assert world==bytes.fromhex(copy['copiedCameraHex'])
  main=row['mainThreadRegisters'];cut=None
  if main['eip']in(0x40dae7,0x40e363,0x40e7ef):
   cut=(main['edi']-0x4d9514)//4;assert main['edi']==0x4d9514+cut*4 and main['ecx']==75-cut
   owner=main['esi']-cut*4-0x4274
   if main['eip']!=0x40dae7:assert owner==main['ebx']
  read_summaries.append(dict(stage=row['stage'],callback=row['precedingPlayerCallbacks'],event=row['debugEventSequence'],workerReadWords=13,mainPc=main['eip'],mainPublicationCopiedWords=cut,sourceAtReadEqualsCompletedCamera=True))
 assert read_summaries[0]['mainPc']==0x40e363 and read_summaries[0]['mainPublicationCopiedWords']==13 and len(read_summaries)==2
 # Unwind only actual captured EBP words; bind returns to original call opcodes.
 snapshot=next(x for x in stores if x['stage']==3 and x['pc']==0x456135);ctx=snapshot['mainThreadContextAtWorkerDebugEvent'];regs=ctx['registers'];stack=bytes.fromhex(ctx['stackHex']);start=regs['esp'];frame=regs['ebp'];frames=[]
 for _ in range(8):
  if not start<=frame<=start+len(stack)-8:break
  parent,ret=struct.unpack_from('<II',stack,frame-start);frames.append(dict(frame=frame,parent=parent,returnPc=ret))
  if parent<=frame or parent%4:break
  frame=parent
 assert regs['eip']==0x473bc3 and [x['returnPc']for x in frames[:2]]==[0x472ca0,0x44e1b4]
 sys.path.insert(0,str(R/'tools'));image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
 assert SHA(image.data)==report['executableSha256']
 for pc,target in [(0x472c9b,0x473af0),(0x44e1af,0x46fe50)]:
  code=image.read(pc,5);assert code[0]==0xe8 and pc+5+struct.unpack_from('<i',code,1)[0]==target
 proof=load(H/'comparison-current/raw-verified.json');assert load(H/'comparison-current/end.json')['strictAndIndependentPassed']and proof['verifiedFiniteEvidence']and proof['callbacks']==35000
 for name,binding in proof['bindings'].items():
  b=raw(R/name);assert len(b)==binding['bytes']and SHA(b)==binding['sha256']
 for gate in('exceptions','timing','scene'):assert load(H/'comparison-current'/(gate+'.json'))['passed']
 result=dict(verifiedUnifiedOriginalDebugEventClock=True,callbacks=35000,debugJournalRows=len(journal),sharedRowsByFile=shared,allPlayerTimesBoundToReceiptEvents=True,rngWriteCompletionEvents=8,initializeAndCounterRowsShareSameStopClock=True,pairedStageVmCalls=982,cameraReads=read_summaries,playerBodyCallerObservedAtGlobalsCompletion=True,bodyUpdateCallPc=0x44e1af,bodyUpdateTarget=0x46fe50,actualCapturedStackFrames=frames,unchangedStandardDriverStrictPassed=True,coreWasmSha256=proof['wasmSha256'],vm303Rows=proof['vm303Rows'],combatCheckpoints=proof['combatCheckpoints'],configuredMusicAndSoundVolumesZero=True,originalPcmNotMeasured=True,receiptTimeNotExactInstructionExecutionTime=True,debuggerPausesAffectTiming=True,oldRecordingExactScheduleRecovered=False,oldRngFailureClosed=False,oldCameraFailureClosed=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))
 out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k not in('bindings','actualCapturedStackFrames','sharedRowsByFile')}))
if __name__=='__main__':main()
