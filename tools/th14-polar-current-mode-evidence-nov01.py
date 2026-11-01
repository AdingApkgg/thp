"""Verify another complete retained mode against the actual polar-Z production core."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(p):
        p=p.resolve(strict=True);assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(p):return json.loads(raw(p))
    plan=load(home/'plan.json');end=load(home/'process-end.json');assert end['strictPassed']and end['exitCode']==0 and end['guardStop']is None
    assert plan['coreCommit']=='bd70b911a3c6a362331f561407a74b6aca3e031f'and not plan['previousResultInherited']and plan['originalProcessesStarted']==plan['physicalAudioDevicesOpened']==0
    assert plan['maximumSeconds']in (180,300) and plan['maximumOutputBytes']==128*1024**2 and plan['minimumFreeBytes']==100*1024**3
    native=R/plan['native'];original=load(native/'report.json');model=home/'model';report=load(model/'report.json')
    assert SHA(raw(native/'report.json'))==plan['nativeReportSha256']
    assert original['childExited']and not original['error']and original['observedForcedReplayEndMenu']
    assert original['hardwareBreakpointsOnly']and original['instructionBytesPatched']==original['rngOrCounterWrites']==0
    assert original['gameStateWordWrites']==1 and original['caseInitialization']['attractBitClearOnly']and not original['inputInjected']
    frozen=native/'observer-source.py';assert original['sourceSha256']==SHA(raw(frozen))
    assert report['completed']and report['callbacks']==plan['callbacks']==original['callbacks']and not report['diagnosticPrefixOnly']
    assert report['selection']==report['declaredSelection']==plan['selection']and report['allRaw32ByteIdentical']
    assert report['hostNormalBoundaryMode']=='none'and report['normalBoundaryObservation']is report['normalVmBoundaryObservation']is None
    assert report['noNativePublicationValuesProvidedToEngine']and report['noPerFrameStateOverrides']and not report['ordinaryIndependentThreadTimingAcceptance']
    standard=raw(R/'tools/th14-compare-native-campaign.mjs')
    driver_path=Path(plan['argv'][1]);driver=raw(driver_path)
    assert report['comparisonToolSha256']==plan['driverSha256']==SHA(driver)
    if driver!=standard:
        before="write(resolve(out,'native-camera.raw'),cameraRaw,{flag:'wx'});"
        after="write(resolve(out,'native-camera-reference.json'),JSON.stringify({reference:resolve(nativeHome,'world-camera.raw'),bytes:cameraRaw.length,sha256:sha(cameraRaw),prefixCallbacks:limit,alreadyRetainedNativeBytesNotCopied:true})+'\\n',{flag:'wx'});"
        expected=standard.decode().replace('\r\n','\n');assert expected.count(before)==1
        assert driver.decode()==expected.replace(before,after)
        reference=load(model/'native-camera-reference.json');native_camera=raw(native/'world-camera.raw')
        assert Path(reference['reference']).resolve()==(native/'world-camera.raw').resolve()and reference['prefixCallbacks']==plan['callbacks']
        assert reference['bytes']==len(native_camera)and reference['sha256']==SHA(native_camera)and reference['alreadyRetainedNativeBytesNotCopied']
        assert not(model/'native-camera.raw').exists()
    build_path=R/plan['build'];build=load(build_path);assert SHA(raw(build_path))==plan['buildSha256']
    assert build['wasmSha256']==report['wasmSha256']==plan['wasmSha256']==SHA(raw(build_path.parent/'observer.wasm'))=='31e86f11380950643cac3f7382c52c2f2a0704f4978836277982c22aa637d287'
    assert len(build['objectBindings'])==141 and build['all141ObjectsRecompiledForChangedClassLayout']
    for row in build['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    for name,digest in {**build['sourceHashes'],**build['headerHashes']}.items():
        p=R/'runtimes/th12'/name
        if name=='th12_web/cpp/game/ResourceCrypt.cpp':p=R/'tools/tmp/github-source-release/runtimes/th12'/name
        assert SHA(raw(p))==digest,name
    tool=R/'tools/th14-verify-native-campaign.py';raw(tool);out=home/'current-mode-raw-verified-nov01.json'
    run=subprocess.run([sys.executable,'-X','utf8',str(tool),'--native',str(native),'--model',str(model),'--build',str(build_path),'--output',str(out)],capture_output=True)
    assert run.returncode==0,run.stderr.decode(errors='replace')[-2000:]
    verified=load(out);assert verified['verifiedFiniteEvidence']and verified['originalNaturalReplayEndObserved']and not verified['diagnosticPrefixOnly']
    for path,binding in verified['bindings'].items():assert SHA(raw(R/path))==binding['sha256']
    stable=report['stableMenuAfter90Ticks'];assert stable[0]==2 and stable[5]==3
    terminals=original['terminalMenuSamples'];assert len(terminals)>=3
    for t in terminals[-3:]:
        assert t['callbacks']==original['callbacks']and t['pauseWords']==[2,3]and t['stage']==stable[1]
        assert (t['score']&0xffffffff)==(stable[11]&0xffffffff)and(t['lives']&0xffffffff)==(stable[12]&0xffffffff)and t['controlFrame']==stable[14]
    return dict(verifiedFiniteCurrentProductionMode=True,sourceCoreCommit=plan['coreCommit'],selection=plan['selection'],callbacks=plan['callbacks'],stagesObserved=original['recordedStages'],vmRows=verified['vm303Rows'],vmFields=303,combatCheckpoints=verified['combatCheckpoints'],orderedInitialPublications=verified['orderedPublications'],allSelectedCameraHudVmCombatAndInitialPublicationsExact=True,nativeTerminalSamples=3,stablePortableMenuTicks=90,extraVmBoundaryClockSupplied=False,all141CurrentCoreObjectsVerified=True,nativeValuesProvidedToEngine=False,ordinaryOriginalMenuAccepted=False,replayEofMarkerObserved=False,independentSchedulingAccepted=False,originalWholePixelsOrPcmAccepted=False,browserAcceptance=False,wholeModeEquivalent=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
