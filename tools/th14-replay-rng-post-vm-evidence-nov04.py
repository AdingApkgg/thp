"""Audit original post-script snapshots without turning them into engine inputs."""
from pathlib import Path
import argparse, hashlib, json, struct
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    native=a.native.resolve(strict=True);assert native.is_relative_to(R/'artifacts/th14');home=native.parent;bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    report=load(native/'report.json');prepared=load(home/'prepared.json');end=load(home/'process-end.json')
    assert report['childExited']and not report['error']and not report['debugErrors']and report['callbacks']==35000
    assert end['exitCode']==1 and end['guardStop']is None and report['diagnosticPrefixOnly']
    assert report['hardwareBreakpointsOnly']and report['instructionBytesPatched']==report['rngOrCounterWrites']==0 and not report['inputInjected']
    assert report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']
    assert bytes.fromhex(report['configHex'])[0x22:0x24]==bytes(2)
    assert report['sourceSha256']==prepared['observerSha256']==sha(read(native/'observer-source.py'))==sha(read(home/'observer.py'))
    assert prepared['preparerSha256']==sha(read(R/'tools/th14-prepare-replay-rng-post-vm-observer-nov04.py'))
    assert prepared['noAdditionalMainThreadBreakpoints']and not prepared['mainNormalVmCallReturnBreakpointsAdded']
    raw=read(native/'replay-rng-store-events.jsonl');assert sha(raw)==report['replayRngStoreEventsSha256']
    events=[json.loads(line)for line in raw.splitlines()];assert len(events)==8 and [x['ordinal']for x in events]==list(range(1,9))
    times=read(native/'player-host-monotonic.u64');selected=read(native/'selected-state.u32')
    assert len(times)==35000*8 and len(selected)==35000*128
    assert sha(times)==report['playerHostTimesSha256']and sha(selected)==report['selectedSha256']
    transitions=[json.loads(line)for line in read(native/'transition-events.jsonl').splitlines()];groups=[]
    for stage in(2,3):
        rows=[row for row in events if row['stage']==stage]
        assert len(rows)==4 and [x['pc']for x in rows]==[0x45610f,0x456123,0x456129,0x456133]
        identity_rows=[]
        for row in rows:
            callback=row['precedingPlayerCallbacks'];assert 1<=callback<35000
            assert struct.unpack_from('<Q',times,(callback-1)*8)[0]<row['hostMonotonicNs']<struct.unpack_from('<Q',times,callback*8)[0]
            context=row.get('mainAnimationVmAtWorkerStore')
            if context is None:continue
            regs=row['mainThreadContextAtWorkerDebugEvent']['registers'];blob=bytes.fromhex(context['rawVmHex']);assert len(blob)==0x5cc
            assert context['pc']==regs['eip']and context['register']=={0x473c93:'esi',0x473253:'ecx'}[regs['eip']]
            assert context['vm']==regs[context['register']]and context['snapshotAtThisWorkerEventOnly']and context['readOnly']and not context['providedToEngine']
            assert [context['file'],context['script'],context['handle'],context['instructionPointer']]==[
                struct.unpack_from('<H',blob,0x36)[0],struct.unpack_from('<H',blob,0x4aa)[0],
                struct.unpack_from('<I',blob,0x540)[0],struct.unpack_from('<I',blob,0x28)[0]]
            frame=regs['ebp'];frames=context['frameChain'];assert len(frames)<=4
            for entry in frames:
                data=bytes.fromhex(entry['rawFrameHex']);assert len(data)==32 and entry['frame']==frame
                assert(entry['savedFrame'],entry['returnPc'])==struct.unpack_from('<II',data)
                frame=entry['savedFrame']
            normal=any(x['returnPc']==0x47e660 for x in frames);assert normal==context['normalCallReturnInFrameChain']
            identity_rows.append(dict(workerPc=row['pc'],callback=callback,mainPc=context['pc'],file=context['file'],script=context['script'],
                handle=context['handle'],normalReturnInFrameChain=normal,afterUpdateCallback=struct.unpack_from('<I',blob,0x5a8)[0],
                drawingMode=(struct.unpack_from('<I',blob,0x18)[0]>>25)&31))
        final=rows[-1];canonical=next(x for x in transitions if x['stage']==stage and x['pc']==0x456133)
        assert canonical['rngHex']==final['rngHex']and canonical['registers']==final['registers']
        assert canonical['mainThreadContextAtWorkerEvent']['registers']==final['mainThreadContextAtWorkerDebugEvent']['registers']
        callback=final['precedingPlayerCallbacks'];words=struct.unpack('<HHIHHI',bytes.fromhex(final['rngHex']))
        next_player=struct.unpack_from('<32I',selected,callback*128);draws=(next_player[22]-words[2])&0xffffffff
        assert draws<=4096
        seed=words[0]
        for _ in range(draws):
            mixed=((seed^0x9630)-0x6553)&0xffff;seed=((mixed<<2)|(mixed>>14))&0xffff
        groups.append(dict(stage=stage,callback=callback,workerMainPcs=[x['mainThreadContextAtWorkerDebugEvent']['registers']['eip']for x in rows],
            scriptDrawsAfterFinalStoreBeforeNextPlayer=draws,recurrenceMatchesNextPlayerSeed=seed==next_player[21],postScriptVmSnapshots=identity_rows,
            canonicalHelperTimestampAliasNs=canonical['hostMonotonicNs']-final['hostMonotonicNs']))
    result=dict(verifiedReadOnlyOriginalPostVmObservations=True,callbacks=35000,workerStoreEvents=8,stages=groups,
        additionalMainThreadBreakpoints=False,nativeValuesProvidedToEngine=False,ordinaryIndependentTimingAccepted=False,
        originalTraceDoesNotRecoverEarlierRecords=True,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    output=a.output.resolve();assert output.is_relative_to(home)and not output.exists()
    output.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k!='bindings'}),flush=True)


if __name__=='__main__':main()
