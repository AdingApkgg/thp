"""Verify an actual read-only hit/push/Z-read/factory/registry birth chain."""
from pathlib import Path
import argparse,ast,collections,hashlib,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R);b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    native=home/'native';plan=load(home/'plan.json');end=load(home/'process-end.json');report=load(native/'report.json');opt=report['observerOptions']
    assert plan['diagnosticPrefixOnly']and not plan['expectedNaturalReplayEnd']and end['guardStop']is None
    assert report['callbacks']==plan['maximumCallbacks']==opt['maximum_callbacks']
    assert report['childExited']and not report['error']and not report['debugErrors']and report['observerTerminationRequested']
    assert not report['observedForcedReplayEndMenu']and end['exitCode']==1
    assert report['hardwareBreakpointsOnly']and report['instructionBytesPatched']==report['rngOrCounterWrites']==0
    assert report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']and not report['inputInjected']
    tool=raw(R/'tools/th14-focused-hit-live-observer-nov01.py');frozen=raw(native/'observer-source.py');assert tool==frozen and SHA(tool)==report['sourceSha256']==plan['sourceSha256']
    base=raw(R/'tools/th14-native-campaign-observer-oct25.py');assert SHA(base)=='ce533a0503163d69a6b93f3a132b950ba96b40cc24bc1f9bbabd9b33b6ca2da7'
    # All actual process-memory writes and explicit suspend/resume calls are
    # unchanged ASTs from the retained observer. New observations only read.
    def side_effects(source):
        return [ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(source))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in ['WriteProcessMemory','SuspendThread','ResumeThread']]
    assert side_effects(tool)==side_effects(base)
    assert [opt['focused_hit_start'],opt['focused_hit_end']]==plan['focusedHitWindow']
    rows=[json.loads(line)for line in raw(native/'focused-hit-live-events.jsonl').decode().splitlines()]
    assert rows and all(opt['focused_hit_start']<=r['precedingPlayerCallbacks']<=opt['focused_hit_end']and r['readOnly']and not r['providedToEngine']for r in rows)
    assert all(a['hostMonotonicNs']<b['hostMonotonicNs']for a,b in zip(rows,rows[1:]))
    wrapper=push=read=factory=None;births=[];counts=collections.Counter()
    for row in rows:
        pc=row['pc'];counts[hex(pc)]+=1
        if pc==0x451760:
            assert read is factory is None
            wrapper=row;push=None
            assert row['registers']['edx']==row['targetPosition']
            assert len(row['liveEnemyIdentityMatches'])==1
            enemy=row['liveEnemyIdentityMatches'][0];assert enemy['address']+0x1234==row['targetPosition']
        elif pc==0x453aae:
            assert wrapper is not None and push is None
            push=row;assert row['wrapper']['wrapperEsp']==wrapper['wrapperEsp']and row['pushedTargetPointer']==wrapper['targetPosition']
            assert row['pushAddress']==wrapper['wrapperEsp']-56 and row['originalInstructionBytes'].startswith('57')
        elif pc==0x4520f2:
            assert push is not None and read is None and factory is None
            assert wrapper['callbackAddress']==0x452050
            read=row;assert row['scratchAddress']==push['pushAddress']and row['scratchWord']==push['pushedTargetPointer']
            assert row['scratchAddress']==row['registers']['ebp']-12 and row['originalInstructionBytes'].startswith('f30f5845f4')
        elif pc==0x47ed10:
            assert read is not None and factory is None and row['script']==149
            factory=row
            f=lambda u:struct.unpack('<f',struct.pack('<I',u))[0]
            z=struct.unpack('<I',struct.pack('<f',f(read['shotPositionZWord'])+f(read['scratchWord'])))[0]
            assert row['positionWords'][2]==z
        else:
            assert pc==0x452188 and factory is not None
            assert row['handleOutputAddress']==factory['handleOutputAddress']and len(row['createdLiveVmMatches'])==1
            vm=row['createdLiveVmMatches'][0];blob=bytes.fromhex(vm['rawVmHex'])
            assert (vm['file'],vm['script'])==(8,149)and vm['handle']==row['handle']==struct.unpack_from('<I',blob,0x540)[0]
            assert struct.unpack_from('<I',blob,0x5a4)[0]==factory['positionWords'][2]
            births.append(dict(callback=row['precedingPlayerCallbacks'],handle=row['handle'],enemyInstance=wrapper['liveEnemyIdentityMatches'][0]['instance'],worldZWord=factory['positionWords'][2]))
            read=factory=None
    assert read is factory is None and births
    return dict(verifiedFiniteActualLiveStackAndFactoryBirth=True,callbacks=report['callbacks'],window=plan['focusedHitWindow'],events=len(rows),counts=dict(counts),verifiedBirths=len(births),births=births,wrapperTargetAndPushAndScratchAndFactoryAndLiveVmZAllEqual=True,liveEnemyIdentityObservedAtHit=True,syntheticComponentNotRelabeledLive=True,hardwareBreakpointsOnly=True,gameStateWordWrites=1,attractBitClearOnly=True,additionalMemoryWritesOrSuspendCalls=0,diagnosticPrefixOnly=True,naturalReplayEndAccepted=False,nativeValuesProvidedToEngine=False,productionAddressModelImplemented=False,strictReimuaEasyPassed=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','births']}))
