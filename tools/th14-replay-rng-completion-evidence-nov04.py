"""Verify post-write observations without claiming an unobserved old interleaving."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();n=a.native.resolve(strict=True);h=n.parent;bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    report=load(n/'report.json');prepared=load(h/'prepared.json');end=load(h/'process-end.json')
    assert report['callbacks']==35000 and report['childExited']and not report['error']and not report['debugErrors']and end['exitCode']==1 and end['guardStop']is None
    assert report['hardwareBreakpointsOnly']and report['instructionBytesPatched']==report['rngOrCounterWrites']==0 and not report['inputInjected']
    assert report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']
    assert bytes.fromhex(report['configHex'])[0x22:0x24]==bytes(2)
    assert report['sourceSha256']==prepared['observerSha256']==sha(read(h/'observer.py'))==sha(read(n/'observer-source.py'))
    assert prepared['preparerSha256']==sha(read(R/'tools/th14-prepare-replay-rng-completion-stage-observer-nov04.py'))
    assert report['replayRngWritesObservedAfterCompletion']and report['replayGlobalsCopyCompletionObserved']and not report['replayRngStoreAllInstructionsObservedBeforeExecution']
    raw=read(n/'replay-rng-store-events.jsonl');assert sha(raw)==report['replayRngStoreEventsSha256'];rows=[json.loads(x)for x in raw.splitlines()];assert len(rows)==8
    raw=read(n/'stage-object-vm-window-events.jsonl');assert sha(raw)==report['stageObjectVmWindowEventsSha256'];edges=[json.loads(x)for x in raw.splitlines()];active=None;pairs=0
    for i,edge in enumerate(edges):
        assert edge['ordinal']==i+1
        context=edge['stageObjectContext'];blob=bytes.fromhex(edge['rawVmHexAtCallEdge']);assert context['array']+context['animationIndex']*0x5cc==edge['vm']
        assert context['animationIndex']==struct.unpack_from('<h',bytes.fromhex(context['rawPrimitiveHex']),6)[0]
        assert (edge['file'],edge['script'])==(struct.unpack_from('<H',blob,0x36)[0],struct.unpack_from('<H',blob,0x4aa)[0])
        if edge['pc']==0x40f2a2:assert active is None;active=edge
        else:assert edge['pc']==0x40f2a7 and active and edge['callEntryOrdinal']==active['ordinal']and edge['vm']==active['vm'];active=None;pairs+=1
    assert active is None and not report['stageObjectVmWindowHasActiveCallAtEnd']and report['stageObjectVmWindowWorkerAtEnd']is None
    groups=[];active_events=0
    for stage in(2,3):
        group=[row for row in rows if row['stage']==stage];assert [row['pc']for row in group]==[0x456115,0x456129,0x456133,0x456135]
        assert [row['completedWritePc']for row in group]==[0x45610f,0x456123,0x456129,0x456133]
        assert len({row['replaySeedWord']for row in group})==1 and len({row['precedingPlayerCallbacks']for row in group})==1
        rng=[struct.unpack('<HHIHHI',bytes.fromhex(row['rngHex']))for row in group];assert rng[0][3]==group[0]['replaySeedWord']and rng[1][0]==group[1]['replaySeedWord']and rng[2][5]==rng[3][5]==0
        regs=[row['registers']for row in group];assert regs[0]['esi']==regs[1]['esi']==regs[2]['esi']and regs[3]['esi']==regs[2]['esi']+112 and regs[2]['ecx']==28 and regs[3]['ecx']==0 and regs[3]['edi']==0x4f5828+112
        active_events+=sum(row['stageObjectVmCallAtWorkerStore']['observedCall']is not None for row in group)
        groups.append(dict(stage=stage,callback=group[0]['precedingPlayerCallbacks'],completionPcs=[row['pc']for row in group],mainPcs=[row['mainThreadContextAtWorkerDebugEvent']['registers']['eip']for row in group],scriptCalls=[x[2]for x in rng],gameplayCalls=[x[5]for x in rng],globalsDwordsCopied=28))
    assert active_events==0 # This particular bounded sample did not exercise a final active VM.
    result=dict(verifiedPostWriteReplayObservations=True,callbacks=35000,workerEvents=8,pairedStageVmCalls=pairs,stageVmActiveAtWorkerEvents=active_events,finalActiveVmDrainExercised=False,groups=groups,configuredMusicAndSoundVolumeZero=True,debugExceptions=0,nativeValuesProvidedToEngine=False,oldExactThreadOrderRecovered=False,oldFailureClosed=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    output=a.output.resolve();assert output.is_relative_to(R/'artifacts/th14')and not output.exists();output.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k not in('groups','bindings')}),flush=True)
if __name__=='__main__':main()
