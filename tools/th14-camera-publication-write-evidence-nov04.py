"""Verify actual update-camera REP writes before the completed-publication event."""
from pathlib import Path
import argparse,collections,hashlib,importlib,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();n=a.native.resolve(strict=True);h=n.parent;bindings={}
 def raw(path):
  b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
 def load(path):return json.loads(raw(path))
 report=load(n/'report.json');end=load(h/'process-end.json');prepared=load(h/'prepared.json')
 assert report['callbacks']==18000 and report['childExited']and not report['error']and not report['debugErrors']and end['exitCode']==1 and end['guardStop']is None
 assert report['hardwareBreakpointsOnly']and report['instructionBytesPatched']==report['rngOrCounterWrites']==0 and not report['inputInjected']and report['caseInitialization']['attractBitClearOnly']
 assert bytes.fromhex(report['configHex'])[0x22:0x24]==bytes(2)
 assert report['sourceSha256']==prepared['observerSha256']==SHA(raw(n/'observer-source.py'))==SHA(raw(h/'observer.py'))
 assert prepared['preparerSha256']==SHA(raw(R/'tools/th14-prepare-camera-publication-write-observer-nov04.py'))
 writes_raw=raw(n/'camera-right-write-events.jsonl');assert SHA(writes_raw)==report['cameraRightWriteEventsSha256'];rows=[json.loads(x)for x in writes_raw.splitlines()];assert len(rows)==report['cameraRightWriteEvents']
 events=[json.loads(x)for x in raw(n/'camera-boundary-events.jsonl').splitlines()];edges=[json.loads(x)for x in raw(n/'stage-object-vm-window-events.jsonl').splitlines()];known_owners={x['stageObjectContext']['owner']for x in edges}
 image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert SHA(image.data)==report['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 assert image.read(0x40dad7,18).hex()=='81c674420000b94b000000bf14954d00f3a5'
 selected=[];counts=collections.Counter();last=0
 for row in rows:
  assert row['ordinal']==last+1;last=row['ordinal'];assert row['hardwareDataWrite']and row['watchAddress']==0x4d9544 and row['watchBytes']==4
  debug=row['debugRegisters'];assert debug['addresses'][2]==0x4d9544 and debug['status']&4 and debug['control']&0xf000000==0xd000000
  if row['pc']!=0x40dae7:continue
  ctx=row['mainPublicationRepProgress'];regs=row['registers'];assert row['mainPhaseAtObservation']=='update'and row['originalBytesAtPc'].startswith('f3a5')
  copied=(regs['edi']-0x4d9514)//4;assert 13<=copied<75 and regs['edi']==0x4d9514+copied*4 and regs['ecx']==75-copied
  assert regs['esi']==ctx['owner']+0x4274+copied*4 and ctx['remainingDwords']==regs['ecx']
  source=bytes.fromhex(ctx['sourceCameraHex']);world=bytes.fromhex(ctx['worldCameraHex']);assert len(source)==len(world)==300 and world[:copied*4]==source[:copied*4]and world[0x30:0x3c].hex()==row['rightHex']
  next_event=next(x for x in events if x['pc']==0x40dae9 and x['precedingPlayerCallbacks']==row['precedingPlayerCallbacks']and x['threadId']==row['threadId']and x['hostMonotonicNs']>row['hostMonotonicNs'])
  assert next_event['rightHex']==row['rightHex']
  counts[copied]+=1;selected.append(dict(ordinal=row['ordinal'],callback=row['precedingPlayerCallbacks'],stage=row['stage'],copiedDwords=copied,rightX=struct.unpack_from('<I',world,0x30)[0],ownerPreviouslyObservedAtObjectVm=ctx['owner']in known_owners,writeNs=row['hostMonotonicNs'],completedPublicationNs=next_event['hostMonotonicNs']))
 assert selected and any(x['ownerPreviouslyObservedAtObjectVm']for x in selected)
 result=dict(verifiedOriginalUpdateCameraRepWordWrites=True,callbacks=18000,totalDataWriteEvents=len(rows),updateRepEvents=len(selected),repProgressCounts=dict(counts),updates=selected,originalProducerPc=0x40dae7,completedPublicationEventPc=0x40dae9,dataWriteBreakpointDeliveryMayBatchRepIterations=True,nativeStateProvidedToEngine=False,old35000ExactProducerRecovered=False,oldCameraFailureClosed=False,newRecordingStrictlyAccepted=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))
 out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k not in('bindings','updates')}),flush=True)
if __name__=='__main__':main()
