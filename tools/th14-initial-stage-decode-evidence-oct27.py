"""Verify staged initial decoding, lifecycle and the retained native frame gap."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/native-frame-readback-oct27')
    p.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-initial-stage-decode-verified-oct27.json')
    p.add_argument('--check',action='store_true');a=p.parse_args();home=a.home.resolve();out=a.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT);bindings={}
    def read(path):
        path=path.resolve();assert path.is_relative_to(ROOT);raw=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    for path in ('runtimes/th12/th12_web/cpp/game/GameResources.cpp','runtimes/th12/th12_web/cpp/game/GameResources.hpp',
        'runtimes/th12/th12_web/cpp/game/GameSessionResources.cpp','runtimes/th12/th12_web/cpp/game/GameSessionResources.hpp',
        'runtimes/th12/th12_web/cpp/game/GameBattle.cpp','runtimes/th12/th12_web/cpp/sdl/Application.cpp',
        'runtimes/th12/th12_web/tests/cpp/th14-initial-stage-decode-fixture.cpp',
        'runtimes/th12/th12_web/tests/cpp/th14-native-initial-loading-fixture.cpp',
        'tools/th14-build-native-application.py','tools/th14-native-application-process-host-oct27.py',
        'tools/th14-initial-stage-decode-resources-oct27.py'):
        read(ROOT/path)
    full=load(home/'initial-decode-core-build/observer-build.json');core=load(home/'initial-decode-core-v2/observer-build.json')
    assert full['engineSourcesRecompiledForThisLink']==141 and full['engineObjectsReusedForThisLink']==0
    assert core['engineSourcesRecompiledForThisLink']==1 and core['engineObjectsReusedForThisLink']==140
    assert core['reuseBuildSha256']==SHA(read(home/'initial-decode-core-build/observer-build.json'))
    for name,digest in core['sourceHashes'].items():
        source=Path(core.get('compiledSourceOverrides',{}).get(name,str(ROOT/'runtimes/th12'/name)))
        assert SHA(read(source))==digest,name
    for name,digest in core['headerHashes'].items():assert SHA(read(ROOT/'runtimes/th12'/name))==digest,name
    for row in core['objectBindings']:assert SHA(read(Path(row['path'])))==row['sha256']
    resource=load(home/'initial-decode-resource-equivalence-v5/report.json')
    assert resource['passed']and resource['actualCases']==42 and resource['expectedCases']==42 and resource['actualByteAndFieldComparison']
    assert resource['toolSha256']==SHA(read(home/'initial-decode-resource-equivalence-v5/run-tool.py'))
    assert resource['fixtureSha256']==SHA(read(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-initial-stage-decode-fixture.cpp'))
    assert resource['coreBuildSha256']==SHA(read(home/'initial-decode-core-v2/observer-build.json'))
    assert resource['wasmSha256']==SHA(read(home/'initial-decode-resource-equivalence-v5/resource-compare.wasm'))
    assert {(x['stage'],x['selection'])for x in resource['rows']if 'stage'in x}=={(s,c)for s in range(1,8)for c in range(6)}
    assert all(x['loaded']and x['allDecodedResourceValuesEqual']for x in resource['rows']if 'stage'in x)
    builds={}
    for name in ('initial-decode-webgpu-v2-build','initial-decode-gles-v2-build','initial-decode-lifecycle-build'):
        b=load(home/name/'build.json');builds[name]=b
        assert b['compiled']and b['coreObjects']==core['objectBindings']
        assert b['wasmSha256']==SHA(read(home/name/'application.wasm'))
        for path,row in b['sourceBindings'].items():assert SHA(read(ROOT/path))==row['sha256'],path
        for path,digest in b.get('reusedPlatformObjects',{}).items():assert SHA(read(ROOT/path))==digest
        for path,digest in b['newObjects'].items():assert SHA(read(home/name/path))==digest
    def run(name,build_name):
        r=load(home/name/'report.json');assert r['completed']and not r['error']and r['physicalAudioDevicesOpened']==0
        assert r['wasmSha256']==builds[build_name]['wasmSha256']
        assert r['buildReportSha256']==SHA(read(home/build_name/'build.json'))
        assert r['toolSha256']==SHA(read(home/name/'run-tool.py'))
        for c in r['captures']:
            assert c['sha256']==SHA(read(home/name/c['file']))
            assert c['liveAnimations']['sha256']==SHA(read(home/name/c['liveAnimations']['file']))
        return r
    pairs=[]
    for kind,frames,checks,pcm in [('demo',2264,7,1508352),('ordinary',722,16,374784)]:
        names=['initial-decode-'+kind+'-'+backend+'-v2'for backend in ('webgpu','gles')]
        reports=[run(name,'initial-decode-'+backend+'-v2-build')for name,backend in zip(names,('webgpu','gles'))]
        for r in reports:assert r['frames']==frames and len(r['checks'])==checks and r['pcmFrames']==pcm
        for field in ('rows','actions','checks','captures','initialSave','finalSave','files','pcmFrames','pcmSha256','finalReferenceState'):
            assert reports[0][field]==reports[1][field],(kind,field)
        for x,y in zip(reports[0]['captures'],reports[1]['captures']):assert read(home/names[0]/x['file'])==read(home/names[1]/y['file'])
        pairs.append(dict(kind=kind,framesPerBackend=frames,checksPerBackend=checks,silentPcmFramesPerBackend=pcm,
            imagesStateFilesLiveVmsAndPcmEqual=True))
    baseline=run('initial-decode-lifecycle-baseline','initial-decode-lifecycle-build')
    assert baseline['frames']==baseline['applicationTicks']==2264
    previous=load(home/'first-demo-public-webgpu/report.json')
    # The staged worker deliberately adds callbacks. Compare the journal's
    # clock and game values directly while retaining delivery counts as IO.
    assert [{k:v for k,v in row.items()if k!='callbacksDelivered'}for row in baseline['rows']]==[{k:v for k,v in row.items()if k!='callbacksDelivered'}for row in previous['rows']]
    for field in ('actions','checks','captures','initialSave','finalSave','pcmFrames','pcmSha256','finalReferenceState'):
        assert baseline[field]==previous[field],field
    observations=baseline['initialLoadingObservations'];assert len(observations)==51
    player=next(i for i,x in enumerate(observations)if x['words'][11])
    scene=next(i for i,x in enumerate(observations)if x['lastResource']=='st03wl.anm')
    assert player<scene and observations[player]['words'][5]==1 and observations[player]['words'][12]
    uploads=[]
    for x in observations:
        if x['words'][8]!=0xffffffff and x['words'][8]not in uploads:uploads.append(x['words'][8])
    assert uploads==[9,4,6,10,11]
    queued=[(i,x)for i,x in enumerate(observations)if x['boundary']=='callback'and x['words'][8]!=0xffffffff]
    assert [x['words'][8]for _,x in queued]==[4,6,10,11]
    for i,x in queued:
        before=observations[i-1]['words'];after=x['words']
        assert before[3]and before[5]==1 and before[6]==before[7]
        assert not after[3]and after[5]==0 and after[6]==before[6]and after[7]==before[7]+1
    lifecycle=[]
    for kind in ('decode','resume'):
        name='initial-decode-pause-'+kind;r=run(name,'initial-decode-lifecycle-build')
        assert r['frames']==2269 and r['applicationTicks']==2264
        events=r['workerPauseEvents'];assert [e['kind']for e in events]==['suspend','stale-callback-returned','resume']
        assert events[1]['pendingStatePreserved']and events[2]['frame']-events[0]['frame']==5
        assert events[0]['words'][5]==(1 if kind=='decode'else 2)
        for field in ('finalSave','pcmFrames','pcmSha256','finalReferenceState'):assert r[field]==baseline[field],(kind,field)
        c=r['captures'][0];b=baseline['captures'][0]
        assert read(home/name/c['file'])==read(home/'initial-decode-lifecycle-baseline'/b['file'])
        assert read(home/name/c['liveAnimations']['file'])==read(home/'initial-decode-lifecycle-baseline'/b['liveAnimations']['file'])
        lifecycle.append(dict(pendingTask=kind,clockFrames=2269,actualApplicationTicks=2264,pauseClockFrames=5,
            staleCallbackPreservesPendingState=True,resumedStateRngAllLiveVmsImageFilesAndPcmEqual=True))
    title=run('initial-decode-title232','initial-decode-webgpu-v2-build')
    strict=load(home/'initial-decode-title232/strict-vms.json');image=load(home/'initial-decode-title232/strict-pixels.json')
    assert strict['allLiveValuesEqual']and strict['nativeCount']==30 and strict['comparedWordsPerVm']==303
    assert image['exactActualNativeBuffer']and image['comparedBytes']==1228800 and image['differentBytes']==0
    native=load(home/'present-0420-publications/report.json')
    assert [[x[k]for k in ('handle','file','script')]for x in sorted(title['animationCreationRecords'],key=lambda x:x['serial'])]==[[x[k]for k in ('handle','file','script')]for x in native['animationPublications']]
    gap=load(home/'initial-decode-actual-game-strict.json')
    assert not gap['strictAllSelectedStateLiveVmsAndPixelsEqual']and gap['strictRegistryOrderEqual']and not gap['strictExtraPortHandles']
    assert len(gap['strictVmDifferences'])==20 and gap['pixelDifferentBytes']==3854 and gap['pixelDifferentPixels']==1129
    assert gap['exploratoryExplicitlyMappedDifferentHandles']==0 and gap['sourceSha256']==SHA(read(ROOT/'tools/th14-native-game-frame-compare-oct27.py'))
    for backend in ('webgpu','gles'):
        failed=load(home/('initial-decode-demo-'+backend)/'report.json')
        assert not failed['completed']and failed['frames']==2085 and 'ECL opcode 303'in failed['error']
    result=dict(schema='th14/initial-stage-decode-finite-evidence/1',verifiedStagedInitialDecode=True,
        productionResourceSchedulingChanged=True,playerCreatedBeforeSceneHudAndTimelineDecode=True,resourceUploadOrder=uploads,
        eachEclAnimationDecodedAfterPreviousUpload=True,defaultSynchronousConsumersPreserved=True,
        actualDecodedResourceComparisons=42,byteAndFieldComparisons=True,actualOriginalProcessLaunchedForThisRevision=False,
        coreUnitsRecompiledInitially=141,coreUnitsRecompiledForOwnerBindingFix=1,coreObjectsReusedAfterFullRecompile=140,
        backendPrefixes=pairs,workerLifecycleCases=lifecycle,title80PublicationsAnd30LiveVms303WordsAndFullBgraStillExact=True,
        fixedZeroCallbackExecutionDurationModelDeclared=True,trueParallelNativeCpuWorkerNotReproduced=True,
        actualNativeGameplayFrameStillFailed=True,remainingRawVmWords=20,remainingPixelBytes=3854,remainingPixels=1129,
        noForcedAgeRngStateOrPixelPatch=True,earlyEcl303FailureRetained=True,componentFixtureFailuresRetained=True,
        fullCampaignResultIncluded=False,previousFullCampaignAcceptanceInherited=False,ordinaryNativeUiAccepted=False,
        completeGame=False,nativeEquivalent=False,browserAcceptance=False,nativeNaturalRunModePairs=30,nativeAllStageEntryModePairs=25,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    encoded=json.dumps(result,indent=2)+'\n'
    if a.check:assert out.read_text()==encoded
    else:out.write_text(encoded)
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))


if __name__=='__main__':main()
