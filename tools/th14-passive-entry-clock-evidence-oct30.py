"""Check the finite passive VM-entry clock diagnosis without promoting it to fidelity.

No original VM, RNG, handle or pixel values are used as game operands. The private
comparison advances only the existing host-clock fixture at a declared registry
boundary. This projection does not establish independent worker timing.
"""
from pathlib import Path
import argparse,hashlib,json,struct,importlib.util
R=Path(__file__).resolve().parents[1]
S=lambda b:hashlib.sha256(b).hexdigest()

def vm_values(n,address_handles):
    blob=bytes.fromhex(n['rawVmHex']);assert len(blob)==0x5cc
    u=lambda at:struct.unpack_from('<I',blob,at)[0]
    handle=lambda address:address_handles[address]if address else 0
    offsets=[0x534,0x538,0x24,0x1c,0x548,0x54c,0x550,0x55c,0x560,0x564,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x78,0x7c,0x88,0x8c,0x3d8,0x3dc,0x80,0x84,*range(0x3b8,0x3d8,4),*range(0x4ac,0x4cc,4)]
    flags=u(0x18)
    values=[n[k]for k in ['handle','file','script','timerPrevious','timerCurrent','timerFraction','pendingInterrupt','ageCurrent']]
    values += [flags&1,(flags>>25)&31,*map(u,offsets),(u(0x28)-u(0x38))&0xffffffff if u(0x28)else 0xffffffff,
        *map(u,[0x59c,0x5a0,0x5a4]),(flags>>17)&3,(flags>>5)&15,int(bool(flags&0x2000)),int(bool(flags&0x800)),
        int(bool(flags&0x1000)),(flags>>21)&3,(flags>>23)&3,flags>>30,int(bool(flags&0x8000)),
        *map(u,[0x4cc,0x4d0,0x4d4,0x4d8,0x4dc,0x4e0,0x4e4,0x4e8,0x70,0x74])]
    assert len(values)==80
    for base,count in [(0x9c,3),(0xf4,3),(0x14c,1),(0x17c,3),(0x204,2),(0x2d0,3),(0x328,1),(0x358,1),(0x388,1),(0x248,2),(0x28c,2)]:
        values.extend(u(base+i*4)for i in range(4*count))
        values.extend(u(base+5*count*4+offset)for offset in [0,4,8,16,20,24])
    assert len(values)==234
    values += [*map(u,[0x4ec,0x4f0,0x4f4,0x90,0x94,0x598]),handle(u(0x594)),u(0x558),u(0x56c),*map(u,range(0x3e0,0x4a0,4))]
    for at,base in [(0x574,0x570),(0x578,0x570),(0x584,0x580),(0x588,0x580)]:values.append(handle(u(at)-base)if u(at)else 0)
    values += [u(0),u(4),u(8),int(bool(u(12))),u(16),(u(20)-u(0x38))&0xffffffff if u(20)else 0xffffffff,u(0x4a4),u(0x53c)]
    assert len(values)==303;return values

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14')
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=S(data));return data
    def load(path):return json.loads(raw(path))
    verifier=R/'tools/th14-passive-vm-entry-evidence-oct30.py';raw(verifier)
    spec=importlib.util.spec_from_file_location('passive_entry_evidence',verifier);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    passive=module.evidence(home/'native');assert passive==load(home/'verified.json');bindings.update(passive['bindings'])
    assert passive['pendingCallEntriesDrained']==1 and passive['callbacks']==33000
    baseline=home/'current-compare';projected=home/'entry-clock'
    for case,exit_code in [(baseline,1),(projected,0)]:
        end=load(case/'process-end.json');assert end['exitCode']==exit_code and end['guardStop']is None
        plan=load(case/'plan.json');assert plan['maximumObservationBytes']<=128*1024**2 and plan['minimumFreeBytes']>=100*1024**3
        assert not plan['originalProcessLaunched']and plan['physicalAudioDevicesOpened']==0
    before=load(baseline/'model/report.json');after=load(projected/'model/report.json')
    for report in [before,after]:
        assert report['completed']and report['callbacks']==33000 and report['diagnosticPrefixOnly']
        assert report['intactOriginalReplay']and report['stageHeaderInputAndFpsRetainedExactly']and report['noPerFrameStateOverrides']
        assert report['noNativePublicationValuesProvidedToEngine']and not report['actualGpuOrAudio']and not report['nativeEquivalent']and not report['completeGame']
    assert before['wasmSha256']==after['wasmSha256']=='7c4c9066a9e8a86fb7db162638ad2d50d73441dad90d2418e5b5aa2b0e84b0ee'
    assert before['differenceCounts']=={'21':2004,'22':28}and before['firstDifference']['index']==30996
    assert before['hostNormalBoundaryMode']=='none'and not before['allRaw32ByteIdentical']
    assert after['hostNormalBoundaryMode']=='passive-entry-projected-registry-clock'and after['allRaw32ByteIdentical']and not after['differenceCounts']
    clock=load(projected/'clock-observation.json');assert clock['callback']==30996 and clock['stage']==3 and clock['nativePendingEntryPc']==0x47e65b
    assert clock['exactRegistryEntryWallTimeNotObserved']and clock['projectionToExistingProductionRegistryPoll']and clock['engineInputsOnlyHostClock']
    assert not clock['originalIndependentThreadScheduleAccepted']
    assert clock['nativeReportSha256']==S(raw(home/'native/report.json'))and clock['passiveProofSha256']==S(raw(home/'verified.json'))
    script=raw(projected/'compare.mjs');base=raw(R/'tools/th14-compare-native-campaign.mjs')
    # All original compare/check logic is retained; only a host clock setup and
    # truthful diagnostic scope text are added to this private driver.
    expected=base.decode().replace('\r\n','\n').replace("const root=resolve(import.meta.dirname,'..')","const root='H:/code/thp'")
    insertion="""const passiveEntryClock=JSON.parse(read(resolve(import.meta.dirname,'clock-observation.json')));
assert(prefix===33000 && schedulerPhases==='observed' && !normalBoundary);
assert.equal(sha(read(resolve(nativeHome,'report.json'))),passiveEntryClock.nativeReportSha256);
normalBoundary={...passiveEntryClock,scope:'diagnostic projection of passive worker ready time to existing normal-registry poll'};
assert.equal(c.observed_normal_clock(normalBoundary.callback,baseNow+BigInt(normalBoundary.readyNs)-playerOrigin),1);
"""
    expected=expected.replace('let normalVmBoundary=null;',insertion+'let normalVmBoundary=null;').replace("normalBoundary?'controlled':'none'","normalBoundary?'passive-entry-projected-registry-clock':'none'")
    assert script.decode().replace('\r\n','\n')==expected and S(script)==after['comparisonToolSha256']
    for case in [baseline,projected]:
        model=case/'model';report=before if case==baseline else after
        a=raw(model/'selected-state.u32');b=raw(model/'native-selected-state.u32');assert len(a)==len(b)==33000*128
        assert S(a)==report['selectedSha256']and S(b)==report['nativeSelectedSha256']
        counts={}
        for index in range(33000):
            for word in range(32):
                at=index*128+word*4
                if a[at:at+4]!=b[at:at+4]:counts[str(word)]=counts.get(str(word),0)+1
        assert counts==report['differenceCounts']
        for name,field in [('camera-report.json','allCameraWordsEqual'),('hud-report.json','allHudWordsEqual')]:
            assert load(model/name)[field]
        live=load(model/'live-report.json');combat=load(model/'combat-snapshots.json')
        camera=raw(model/'portable-camera.u32');native_camera=raw(home/'native/world-camera.raw')
        offsets=[*range(0,88,4),0x104,0x108,0x10c]
        expected_camera=b''.join(native_camera[i*0x124+off:i*0x124+off+4]for i in range(33000)for off in offsets)
        assert len(camera)==33000*25*4 and camera==expected_camera
        assert raw(model/'portable-hud.u32')==raw(home/'native/hud-score.u32')[:33000*8]
        allocations=load(model/'allocation-report.json');assert allocations['completed']and len(allocations['windows'])==1
        window=allocations['windows'][0];assert window['nativeCount']==window['portableCount']==2870 and window['allHandlesFileScriptEqual']
        native_allocations=[json.loads(line)for line in raw(home/'native/allocation-events.jsonl').decode().splitlines()]
        native_allocations=[n for n in native_allocations if n['precedingPlayerCallbacks']<1000]
        portable_allocations=load(model/'portable-allocations-initial-through-1000.json')
        assert len(native_allocations)==len(portable_allocations)==2870
        assert [[n[k]for k in ['handle','file','script']]for n in native_allocations]==[[n[k]for k in ['handle','file','script']]for n in portable_allocations]
        if case==projected:
            assert live['allLiveValuesEqual']and all(not x['differenceCount']and x['registryOrderEqual']and x['portableRegistryComplete']for x in live['snapshots'])
            assert not combat['differences']
            for snapshot in live['snapshots']:
                frame=snapshot['frame'];native_vms=load(home/f'native/live-vms-callback-{frame}.json')['rows'];portable_vms=load(model/f'portable-live-{frame}.json')
                addresses={struct.unpack_from('<I',bytes.fromhex(n['rawVmHex']),0x570)[0]:n['handle']for n in native_vms}
                assert [vm_values(n,addresses)for n in native_vms]==portable_vms
        else:assert not live['allLiveValuesEqual']
    tracehome=R/'artifacts/th14/nested-vm-rng-trace-v2-oct30';analysis=load(tracehome/'analysis.json')
    assert S(raw(tracehome/'analysis.json'))==clock['neutralTraceAnalysisSha256']and analysis['neutralOnAllCommonGamePayloads']
    for row in analysis['matchedPayloads']:
        a=raw(baseline/'model'/row['file']);b=raw(tracehome/'model'/row['file']);assert a==b and S(a)==row['sha256']and len(a)==row['bytes']
    trace=load(tracehome/'model/diagnostic-trace.json');assert trace['overflow']==0 and len(trace['rows'])==1006
    # The old proposed nested-VM explanation is not promoted: this trace shows
    # the reset after NORMAL registry exit and before OVERLAY registry entry.
    sequence=[x for x in trace['rows']if x[0]==30996]
    exit_at=next(i for i,x in enumerate(sequence)if x[1]==41);overlay=next(i for i,x in enumerate(sequence)if x[1]==50)
    assert exit_at+1==overlay and sequence[exit_at][9:13]!=sequence[overlay][9:13]
    child=[x for x in sequence if x[1]in(21,22)];assert len(child)==2 and child[0][5:7]==child[1][5:7]==[2,16]
    assert child[1][10]-child[0][10]==24
    raw(R/'runtimes/th12/th12_web/tests/cpp/th14-normal-worker-fixture.cpp')
    raw(R/'runtimes/th12/th12_web/cpp/game/AnmManager.cpp');raw(R/'runtimes/th12/th12_web/cpp/game/GameBattle.cpp')
    return dict(verifiedFinitePassiveEntryClockDiagnosis=True,callbacks=33000,selectedWordsPerCallback=32,
        passiveOriginalCallEdges=passive['observedCallEdges'],pendingCallEntryDrained=1,
        baselineExpectedStrictFailureRetained=True,baselineDifferingSeedRows=2004,baselineDifferingCallCountRows=28,
        projectedCurrentGamePayloadsEqual=True,selectedVmWordsPerSnapshot=303,cameraWordsPerCallback=25,hudWordsPerCallback=2,
        tracePayloadFilesByteEqual=len(analysis['matchedPayloads']),traceRows=1006,nestedChildRngDrawsBeforeBaselineRestore=24,
        resetObservedBetweenNormalAndOverlayInBaselineModel=True,productionGameplayModifiedForDiagnosis=False,
        existingProductionNormalRegistryPollUsed=True,onlyHostClockProvidedToEngine=True,
        exactRegistryEntryWallTimeNotObserved=True,originalDebuggerPausesAffectTiming=True,
        ordinaryIndependentThreadTimingAccepted=False,old80324FailureClosed=False,ordinaryMenuInitializationAccepted=False,
        completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=S(Path(__file__).read_bytes()))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    target=a.output.resolve();assert target.is_relative_to(R/'artifacts/th14')or target.is_relative_to(R/'docs/porting')
    result=evidence(a.case)
    if a.check:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
if __name__=='__main__':main()
