"""Verify a newly captured Extra against the polar-Z production core."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence(native,model,build_path):
    native=native.resolve(strict=True);model=model.resolve(strict=True);build_path=build_path.resolve(strict=True)
    assert all(p.is_relative_to(R/'artifacts/th14')for p in [native,model,build_path]);bindings={}
    def raw(p):
        p=p.resolve(strict=True);assert p.is_relative_to(R)
        data=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(p):return json.loads(raw(p))
    original=load(native/'report.json');reported=load(model/'report.json');end=load(model.parent/'process-end.json')
    assert original['childExited']and not original['error']and original['observedForcedReplayEndMenu']
    assert original['hardwareBreakpointsOnly']and original['instructionBytesPatched']==original['rngOrCounterWrites']==0
    assert original['gameStateWordWrites']==1 and original['caseInitialization']['attractBitClearOnly']and not original['inputInjected']
    assert end['strictPassed']and end['exitCode']==0 and end['guardStop']is None
    assert reported['completed']and reported['callbacks']==original['callbacks']and not reported['diagnosticPrefixOnly']
    assert reported['hostNormalBoundaryMode']=='none'and reported['normalBoundaryObservation']is reported['normalVmBoundaryObservation']is None
    assert 'initializationBoundaryObservation'not in reported and not reported['ordinaryIndependentThreadTimingAcceptance']
    normal=raw(R/'tools/th14-native-campaign-observer-oct25.py').decode().replace('\r\n','\n')
    source=raw(native/'observer-source.py');assert SHA(source)==original['sourceSha256']
    selection=reported['declaredSelection'];assert selection==reported['selection']
    extra=selection[2:]==[4,7]
    comparison=raw(R/'tools/th14-compare-native-campaign.mjs').decode().replace('\r\n','\n')
    if extra:
        expected=normal.replace("parser.add_argument('--difficulty',type=int,choices=range(4),required=True)","parser.add_argument('--difficulty',type=int,choices=(4,),required=True)").replace('[opt.character,opt.subtype,opt.difficulty,1],words[27:31]','[opt.character,opt.subtype,opt.difficulty,7],words[27:31]')
        assert source.decode().replace('\r\n','\n')==expected
        assert SHA(raw(R/'tools/th14-native-extra-campaign-observer-nov01.py'))==SHA(source)
        assert original['recordedStages']==[7]and original['observerOptions']['difficulty']==4
        driver=raw(R/'tools/th14-compare-native-extra-campaign-nov01.mjs')
        expected="import{requireSingleExtra}from'./th14-extra-stage-topology-nov01.mjs';\n"+comparison
        anchor='const maxStage=nativeRaw.readUInt32LE((limit-1)*128+30*4);'
        expected=expected.replace(anchor,anchor+'\nconst singleExtra=requireSingleExtra(nativeRaw,limit,expectedSelection[2],expectedSelection[3]);')
        expected=expected.replace("assert.equal(maxStage,1,'Missing later-stage observation '+name)","assert(singleExtra,'Missing Extra observation without a validated single-stage payload '+name)").replace('for(let stage=2;stage<=maxStage;stage++)','for(let stage=2;stage<=(singleExtra?1:maxStage);stage++)')
        expected=expected.replace('phasedScheduler&&maxStage>=2','phasedScheduler&&!singleExtra&&maxStage>=2')
        assert driver.decode().replace('\r\n','\n')==expected
        raw(R/'tools/th14-extra-stage-topology-nov01.mjs')
        states=raw(native/'selected-state.u32');assert len(states)==original['callbacks']*128
        import struct
        assert all(struct.unpack_from('<II',states,i*128+29*4)==(4,7)for i in range(original['callbacks']))
    else:
        assert selection[2]in range(4)and selection[3]==1 and source.decode().replace('\r\n','\n')==normal
        driver=raw(R/'tools/th14-compare-native-campaign.mjs')
    assert SHA(driver)==reported['comparisonToolSha256']
    assert extra,'This verifier accepts an explicitly validated Extra only'
    build=load(build_path)
    assert build['wasmSha256']==reported['wasmSha256']==SHA(raw(build_path.parent/'observer.wasm'))=='31e86f11380950643cac3f7382c52c2f2a0704f4978836277982c22aa637d287'
    assert len(build['objectBindings'])==141 and build['all141ObjectsRecompiledForChangedClassLayout']
    for row in build['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    for name,digest in {**build['sourceHashes'],**build['headerHashes']}.items():
        path=R/'runtimes/th12'/name
        if name=='th12_web/cpp/game/ResourceCrypt.cpp':path=R/'tools/tmp/github-source-release/runtimes/th12'/name
        assert SHA(raw(path))==digest
    rebuild_path=build_path
    checker=R/'tools/th14-verify-native-campaign.py';raw(checker);payload=model.parent/'current-campaign-raw-verified-nov01.json'
    result=subprocess.run([sys.executable,'-X','utf8',str(checker),'--native',str(native),'--model',str(model),'--build',str(rebuild_path),'--output',str(payload)],capture_output=True)
    assert result.returncode==0,result.stderr.decode(errors='replace')[-2000:]
    finite=load(payload);assert finite['verifiedFiniteEvidence']and not finite['diagnosticPrefixOnly']and finite['originalNaturalReplayEndObserved']
    for name,binding in finite['bindings'].items():assert SHA(raw(R/name))==binding['sha256']
    terminals=original['terminalMenuSamples'];assert len(terminals)>=3
    stable=reported['stableMenuAfter90Ticks'];assert stable[0]==2 and stable[5]==3
    for t in terminals[-3:]:
        assert t['callbacks']==original['callbacks']and t['pauseWords']==[2,3]and t['stage']==stable[1]
        assert(t['score']&0xffffffff)==(stable[11]&0xffffffff)and(t['lives']&0xffffffff)==(stable[12]&0xffffffff)
        assert t['controlFrame']==stable[14]
    return dict(verifiedNaturalCurrentCoreCampaign=True,sourceCoreCommit='bd70b911a3c6a362331f561407a74b6aca3e031f',selection=selection,extraSingleStageTopologyVerified=extra,callbacks=finite['callbacks'],stagesObserved=original['recordedStages'],vmRows=finite['vm303Rows'],vmFields=303,combatCheckpoints=finite['combatCheckpoints'],initialPublications=finite['orderedPublications'],allSelectedCameraHudVmCombatAndInitialPublicationsExact=True,nativeTerminalSamples=3,stablePortableMenuTicks=90,extraVmBoundaryTimeSupplied=False,currentProductionCoreAndFullFixtureGraphVerified=True,all141CurrentObjectsVerified=True,originalWarmAttractBitClearOnly=True,ordinaryOriginalMenuAccepted=False,replayEofMarkerObserved=False,independentThreadSchedulingAccepted=False,originalWholePixelsOrPcmAccepted=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['native','model','build','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting')
    verified=evidence(a.native,a.model,a.build)
    if a.check:assert json.loads(out.read_bytes())==verified
    else:out.write_text(json.dumps(verified,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in verified.items()if k!='bindings'}))
