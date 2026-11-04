"""Qualify the zero-exception Easy capture and its finite inferred-clock model."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/reimub-easy-full-context-nov04/startup-preserved';F=H/'full';N=F/'native';M=F/'current-core-comparison-v4/model'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def verify():
    bindings={}
    def raw(path):
        value=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(value),sha256=SHA(value));return value
    def load(path):return json.loads(raw(path))
    native=load(N/'report.json');sealed=load(F/'native-sealed.json');model=load(M/'report.json');gate=load(F/'raw-verified.json');strict=load(F/'strict-gates.json')
    count=native['callbacks'];assert count==238972 and native['recordedStages']==[1,2,3,4,5,6]
    assert sealed['originalCaptureGatePassed']and all(sealed['checks'].values())and not native['debugErrors']and not native['error']and native['childExited']
    assert sealed['nativeReportSha256']==SHA(raw(N/'report.json'))
    assert native['sourceSha256']==SHA(raw(H/'observer.py'))==SHA(raw(N/'observer-source.py'))
    assert native['configuredMusicAndSoundVolumeZero']and native['rngOrCounterWrites']==0 and native['gameStateWordWrites']==1
    assert load(F/'current-core-comparison-v4/process-end.json')['exitCode']==0
    assert model['allRaw32ByteIdentical']and not model['differenceCounts']and model['callbacks']==count
    selected=raw(N/'selected-state.u32');assert len(selected)==count*128 and selected==raw(M/'selected-state.u32')==raw(M/'native-selected-state.u32')
    camera=raw(N/'world-camera.raw');tail=raw(N/'world-camera-tail.u32');actual=raw(M/'full-camera.u32')
    assert len(camera)==count*292 and len(tail)==count*8 and len(actual)==(count-1)*300
    for index in range(1,count):assert actual[(index-1)*300:index*300]==camera[index*292:(index+1)*292]+tail[index*8:(index+1)*8]
    cursor=raw(N/'replay-cursor.u32');actual=raw(M/'replay-cursor.u32');assert len(cursor)==count*56 and len(actual)==(count-1)*16
    for index in range(1,count):assert struct.unpack_from('<4I',actual,(index-1)*16)==tuple(struct.unpack_from('<I',cursor,index*56+i*4)[0]for i in [3,7,8,9])
    assert raw(N/'hud-score.u32')==raw(M/'portable-hud.u32')
    assert gate['verifiedFiniteEvidence']and gate['callbacks']==count and gate['vm303Rows']==1301 and gate['combatCheckpoints']==1240 and gate['nonemptyCombatCheckpoints']==478
    assert gate['verifierSha256']==SHA(raw(R/'tools/th14-verify-native-campaign.py'))
    for name,item in gate['bindings'].items():
        value=raw(R/name);assert SHA(value)==item['sha256']and len(value)==item['bytes']
    assert not strict['overallStrictAccepted']and not strict['strictSceneWhitelistModified']
    assert [(x['gate'],x['passed'])for x in strict['results']]==[('exceptions',True),('initialize',False),('scene',False)]
    for item in strict['results']:assert SHA(raw(F/('strict-'+item['gate']+'.log')))==item['logSha256']
    driver=R/'tools/th14-compare-native-easy-interstore-read-v2-nov04.mjs';assert SHA(raw(driver))==model['comparisonToolSha256']=='90c837a0326cc4293552c6c9aa204cd2b6d530d654a15e13eac575f8642066e9'
    previous=load(F/'current-core-comparison-v2/model/report.json');assert previous['differenceCounts']=={'21':57744,'22':462}
    windows=model['firstScriptReadWindows'];assert len(windows)==1 and windows[0]['stage']==6 and windows[0]['callback']==181228
    assert windows[0]['completedScriptCallsBetweenObservedStores']==24 and windows[0]['lowerClockAnchor']=='precedingPlayerReceipt'
    assert windows[0]['inferredFirstReadOrder']and not windows[0]['exactIndependentCounterClearOrderRecovered']
    for name in ['th14-prepare-easy-context-driver-nov04.py','th14-prepare-easy-interstore-read-driver-nov04.py','th14-easy-full-after-capture-nov04.py']:raw(R/'tools'/name)
    return dict(schema='th14/easy-full-context/1',verifiedFiniteObservedClockEvidence=True,selection=[0,1,0,1],callbacks=count,
        nativeDebugExceptions=0,nativeEndMenuObserved=True,allSelected32Equal=True,all75CameraWordsEqual=True,
        comparedCameraWords=(count-1)*75,firstComparedCameraCallback=2,replayCursorFields=4,firstComparedCursorCallback=2,
        allHud2Equal=True,vm303Rows=1301,combatCheckpoints=1240,nonemptyCombatCheckpoints=478,initialPublications=479,
        intermediateScriptReads=24,intermediateRestoreCallback=181228,inferredFirstReadWindow=windows[0],
        exactIndependentCounterClearOrderRecovered=False,ordinaryIndependentThreadTimingAcceptance=False,
        originalRngValuesOrVmIdentityProvidedToEngine=False,strictInitializeAccepted=False,strictSceneAccepted=False,
        strictWhitelistModified=False,priorExceptionCaptureAccepted=False,priorStartupTimeoutCauseExplained=False,
        modelWasmSha256=model['wasmSha256'],modelDriverSha256=model['comparisonToolSha256'],
        productionGameplaySourcesChanged=False,browserAcceptance=False,wholeOriginalFramebufferOrPcmAccepted=False,
        limits=['Warm replay with declared host clocks and asynchronous completions; no independent ordinary scheduling acceptance.',
            'The inferred first script-read handoff matches finite observations. Exact separate counter-clear ordering is not recovered.',
            'Only retained fields, sampled objects and the initial publication window; no entire object or all-mode acceptance.',
            'The older Easy record with12 exceptions, earlier startup timeout and deliberately interrupted observation remain separate.'],
        completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=verify()
    if a.check:assert json.loads(out.read_bytes())==result
    else:assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ['verifiedFiniteObservedClockEvidence','callbacks','comparedCameraWords','vm303Rows','combatCheckpoints','strictInitializeAccepted','strictSceneAccepted']}))
