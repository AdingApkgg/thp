"""Verify the bounded read/write camera trace and its unchanged-driver strict comparison."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();h=R/'artifacts/th14/camera-source-read-trace-nov04';n=h/'native';bindings={}
 def raw(path):
  b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
 def load(path):return json.loads(raw(path))
 report=load(n/'report.json');prepared=load(h/'prepared.json');end=load(h/'process-end.json')
 assert report['callbacks']==18000 and report['childExited']and not report['error']and not report['debugErrors']and end['exitCode']==1 and end['guardStop']is None
 assert report['hardwareBreakpointsOnly']and report['instructionBytesPatched']==report['rngOrCounterWrites']==0 and report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']and not report['inputInjected']
 assert bytes.fromhex(report['configHex'])[0x22:0x24]==bytes(2)
 assert report['sourceSha256']==prepared['observerSha256']==SHA(raw(h/'observer.py'))==SHA(raw(n/'observer-source.py'))
 assert prepared['preparerSha256']==SHA(raw(R/'tools/th14-prepare-camera-source-read-observer-nov04.py'))and prepared['controllerReadSlotPreservedByObservedWriteRotation']
 controls=[json.loads(x)for x in raw(n/'controller-phase-events.jsonl').splitlines()];assert any(x['stage']==2 for x in controls)
 reads_raw=raw(n/'worker-camera-source-read-events.jsonl');assert SHA(reads_raw)==report['cameraSourceReadEventsSha256'];reads=[json.loads(x)for x in reads_raw.splitlines()];assert len(reads)==report['cameraSourceReadEvents']==1
 copies=[json.loads(x)for x in raw(n/'scene-camera-copy-events.jsonl').splitlines()];summaries=[]
 for row in reads:
  assert row['pc']==0x40d445 and row['hardwareReadWriteWatch']and row['watchAddress']==0x4d9544 and row['readOnly']and not row['providedToEngine']
  regs=row['registers'];count=row['copiedDwords'];assert 13<=count<=75 and regs['ecx']==75-count and regs['esi']==0x4d9514+count*4 and regs['edi']==row['scene']+0x4274+count*4
  before=next(x for x in copies if x['event']=='scene-camera-copy-before'and x['threadId']==row['threadId']and x['stage']==row['stage'])
  after=next(x for x in copies if x['event']=='scene-camera-copy-after'and x['threadId']==row['threadId']and x['stage']==row['stage'])
  assert before['hostMonotonicNs']<row['hostMonotonicNs']<after['hostMonotonicNs']and before['scene']==after['scene']==row['scene']
  world=bytes.fromhex(row['worldCameraHex']);at_read=bytes.fromhex(row['copiedCameraHex']);completed=bytes.fromhex(after['copiedCameraHex'])
  assert len(world)==len(at_read)==len(completed)==300 and at_read[0x30:0x34]==world[0x30:0x34]==completed[0x30:0x34]
  assert completed[:292]==world[:292]
  summaries.append(dict(stage=row['stage'],callback=row['precedingPlayerCallbacks'],workerCopiedDwords=count,mainPc=row['mainThreadRegisters']['eip'],rightX=struct.unpack_from('<I',completed,0x30)[0],completeMappedCopyEqualsWorldAtRead=True,mainPublicationInProgress='mainPublicationRepProgress'in row))
 rawproof=load(h/'comparison-current/raw-verified.json');strict=load(h/'comparison-current/end.json')
 assert strict['strictAndIndependentPassed']and rawproof['verifiedFiniteEvidence']and rawproof['callbacks']==18000 and rawproof['wasmSha256']=='f4eef7dc05bffe2b9692205bf93e77fc07f400895d36a3aa9c2fcd8eaefc917e'
 for name,binding in rawproof['bindings'].items():
  b=raw(R/name);assert len(b)==binding['bytes']and SHA(b)==binding['sha256']
 for name in ['exceptions','timing','scene']:assert load(h/'comparison-current'/(name+'.json'))['passed']
 result=dict(verifiedCameraSourceReadTraceAndFiniteComparison=True,callbacks=18000,sourceReadEvents=len(reads),controllerStage2Events=sum(x['stage']==2 for x in controls),reads=summaries,unchangedStandardDriverUsed=True,additionalClockOverrides=False,nativeStateValuesProvidedToEngine=False,old35000CameraFailureClosed=False,oldRngFailuresClosed=False,originalWholePixelsOrPcmAccepted=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))
 out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k!='bindings'}),flush=True)
if __name__=='__main__':main()
