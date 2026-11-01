"""Verify the new fixture against two actual observations in the retained prefix."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1]
S=lambda b:hashlib.sha256(b).hexdigest()

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=S(data));return data
    def load(path):return json.loads(raw(path))
    checker=R/'tools/th14-passive-return-clock-evidence-nov01.py';raw(checker)
    spec=importlib.util.spec_from_file_location('retained_return_checker',checker);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    reference_home=R/'artifacts/th14/worker-vm-extended-oct31';reference=module.evidence(reference_home)
    assert reference==load(R/'docs/porting/th14-passive-return-clock-nov01.json');bindings.update(reference['bindings'])
    reference_model=reference_home/'observed-return-current/model'
    fixture=raw(R/'runtimes/th12/th12_web/tests/cpp/th14-passive-vm-clocks-fixture-nov01.cpp')
    build=load(home/'observer-build.json');rebuilt=load(R/'artifacts/th14/passive-multiclock-build-public-nov01/observer-build.json')
    assert build['fixtureSha256']==rebuilt['fixtureSha256']==S(fixture)
    assert build['objectBindings']==rebuilt['objectBindings']and build['engineObjectsReusedForThisLink']==rebuilt['engineObjectsReusedForThisLink']==141
    assert build['wasmSha256']==rebuilt['wasmSha256']==S(raw(home/'observer.wasm'))==S(raw(R/'artifacts/th14/passive-multiclock-build-public-nov01/observer.wasm'))
    assert rebuilt['buildToolSha256']==S(raw(R/'tools/th14-passive-vm-clocks-build-nov01.py'))
    single=home/'single-compat';double=home/'two-observations'
    for case in [single,double]:
        end=load(case/'process-end.json');assert end['exitCode']==0 and end['guardStop']is None
        report=load(case/'model/report.json');assert report['allRaw32ByteIdentical']and report['callbacks']==48000 and report['wasmSha256']==build['wasmSha256']
        assert report['normalVmBoundaryObservation']['modelClock']==dict(delivered=1,failed=0,ownVmPollSlot=6,visits=6)
        plan=load(case/'plan.json');assert plan['maximumObservationBytes']<=128*1024**2 and plan['minimumFreeBytes']>=100*1024**3
        assert not plan['originalProcessLaunched']and plan['physicalAudioOrGpuDevicesOpened']==0
    points=load(double/'clock-points.json');assert not points['multipleDistinctStageRestores']and len(points['points'])==2
    events_raw=raw(reference_home/'native/normal-vm-window-events.jsonl');assert S(events_raw)==points['returnEventsSha256']
    events=[json.loads(x)for x in events_raw.decode().splitlines()]
    earlier=next(x for x in events if x['ordinal']==points['points'][0]['sourceEventOrdinal'])
    assert earlier['precedingPlayerCallbacks']==31048 and earlier['pc']==0x47e660 and earlier['file']==5 and earlier['script']==4
    assert earlier['hostMonotonicNs']==points['points'][0]['readyNs']<points['points'][1]['readyNs']
    assert points['points'][1]==load(reference_home/'observed-return-current/return-clock-observation.json')
    states=load(double/'model/passive-multiple-clock-state.json')
    assert states['observations']==[dict(callback=q,delivered=1,failed=0,slot=6,visits=6)for q in [31048,31049]]and not states['distinctStageRestores']
    # The executed single-case driver contains direct rejecting controls; both
    # drivers retain the entire strict comparison already verified above.
    one_script=raw(single/'compare.mjs');two_script=raw(double/'compare.mjs')
    assert S(one_script)==load(single/'model/report.json')['comparisonToolSha256']and S(two_script)==load(double/'model/report.json')['comparisonToolSha256']
    assert S(one_script)=='1d6cae15a94c49df67e5455e1f69efa03ca4e08fb5e535e4f147d7dbec246258'
    assert S(two_script)=='50b645e6c4c2d8a5bac30b54094528d1050a8b10ccd6a29c9307cb5866a220cc'
    assert b'observed_passive_vm_clock_add(0,ready'in one_script and b'normalVmBoundary.callback-1'in one_script and b'ready-1n'in one_script
    assert b'assert.equal(c.observed_passive_vm_clock_count(),1)'in one_script and b'assert.equal(c.observed_passive_vm_clock_count(),2)'in two_script
    file_count=0;byte_count=0
    for path in reference_model.iterdir():
        if path.is_file()and(path.suffix in('.u32','.u64','.raw','.bin')or path.name.startswith(('combat-','portable-live-','portable-allocations-'))):
            ref=raw(path);assert ref==raw(single/'model'/path.name)==raw(double/'model'/path.name)
            file_count+=1;byte_count+=len(ref)
    assert file_count==444 and byte_count==34858669
    return dict(verifiedFiniteMulticlockFixture=True,callbacksPerRun=48000,actualRuns=2,
        secondRunActualClockObservations=2,bothClocksDeliveredExactlyOnce=True,clockCallbacks=[31048,31049],
        distinctStageSeedRestores=1,multipleDistinctStageRestoresNotYetAccepted=True,
        commonGamePayloadFilesPerRunByteEqual=file_count,commonGamePayloadBytesPerRun=byte_count,
        zeroCallbackDuplicateOutOfOrderAndDecreasingTimeRejected=True,gameObjectsReused=141,gameObjectsRecompiled=0,
        publicRebuildWasmByteIdentical=True,productionGameplayChanged=False,productionWasmChanged=False,
        onlyObservedHostClockProvided=True,vmCallbacksWrapped=False,independentSchedulingAccepted=False,
        completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=S(Path(__file__).read_bytes()))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    target=a.output.resolve();assert target.is_relative_to(R/'artifacts/th14')or target.is_relative_to(R/'docs/porting')
    result=evidence(a.case)
    if a.check:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
if __name__=='__main__':main()
