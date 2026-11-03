"""Check one intact Sakuya A Extra recording against the activation-reset core."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/replay-cadence-reset-nov04/sakuyaa-extra-full'
N=H/'native';B=H.parent/'core/observer-build.json';bindings={}
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def read(path):
    raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
def load(path):return json.loads(read(path))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    q=load(H/'queue-end.json');n=load(N/'report.json');end=load(H/'process-end.json')
    plan=load(H/'plan.json');quiet=load(H/'native-silence-verified.json');build=load(B)
    assert q['strictV4Passed'] and q['modelExitCode']==q['verifierExitCode']==0 and q['modelGuardStop']is None
    assert end['exitCode']==0 and end['guardStop']is None and end['actualMastersZero']
    assert n['childExited'] and not n['error'] and not n['debugErrors'] and n['observedForcedReplayEndMenu']
    assert n['hardwareBreakpointsOnly'] and not n['instructionBytesPatched'] and not n['rngOrCounterWrites'] and not n['inputInjected']
    assert n['gameStateWordWrites']==1 and n['caseInitialization']['attractBitClearOnly']
    assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==n['pid']
    assert all(all(s[k]==0 for k in ('musicConfig','effectsConfig','musicMaster','effectsMaster'))for s in quiet['samples'])
    assert plan['selection']==[2,0,4,7] and plan['buildSha256']==sha(read(B))
    assert plan['sourceSha256']==n['sourceSha256']==sha(read(N/'observer-source.py'))
    assert plan['maximumCallbacks']==60000 and plan['maximumObservationMiB']==128 and plan['minimumFreeGiB']==100
    selected=read(N/'selected-state.u32');count=n['callbacks'];assert count==q['callbacks']==38977 and len(selected)==count*128 and sha(selected)==n['selectedSha256']
    for i in range(count):assert struct.unpack_from('<4I',selected,i*128+108)==(2,0,4,7)
    assert n['recordedStages']==[7]
    for name,tool in [('exceptions.json','th14-verify-native-debug-exceptions-nov03.py'),('initialize.json','th14-verify-native-initialize-timing-v3-nov03.py'),('scene.json','th14-verify-native-scene-boundaries-nov03.py')]:
        gate=load(H/name);assert gate['passed'] and gate['nativeReportSha256']==sha(read(N/'report.json'))
        assert gate['verifierSha256']==sha(read(R/'tools'/tool))
    proof=load(H/'raw.json');assert proof['verifiedFiniteEvidence'] and proof['callbacks']==count
    assert proof['verifierSha256']==sha(read(R/'tools/th14-verify-native-campaign.py'))
    for name,value in proof['bindings'].items():assert sha((R/name).read_bytes())==value['sha256']
    assert proof['selection']==[2,0,4,7] and proof['stagesObserved']==[7]
    for key in ('allSelected32Equal','allCamera25Equal','allHud2Equal','allVm303AndRegistryOrderEqual','allCapturedCombatWordsEqual'):assert proof[key]
    assert proof['wasmSha256']==build['wasmSha256']==sha(read(B.parent/'observer.wasm'))=='88c98a25a2eb23b367f1a7a63b33057011f30c4d42902f66438ad170b82f1e5a'
    assert proof['vm303Rows']==6461 and proof['combatCheckpoints']==48 and proof['orderedPublications']==3205
    for name,digest in {**build['sourceHashes'],**build['headerHashes']}.items():
        assert sha((Path(build['sourceSnapshotRoot'])/name).read_bytes())==digest
        if name!='th12_web/cpp/game/ResourceCrypt.cpp':assert sha((R/'runtimes/th12'/name).read_bytes())==digest
    for obj in build['objectBindings']:assert sha(Path(obj['path']).read_bytes())==obj['sha256']
    manifest=load(Path(plan['argv'][plan['argv'].index('--assets')+1])/'manifest.json')
    assert manifest['passed'] and manifest['changedEntries']==['demo0.rpy'] and manifest['unchangedEntries']==226
    assert manifest['replaySha256']==n['sourceFullReplaySha256']==sha(read(Path(manifest['replayPath'])))
    report=dict(verifiedFiniteSakuyaAExtraCurrent=True,coreCommit='5309e338232613bad6be96f1c2ad65090aaa74a2',callbacks=count,selection=[2,0,4,7],observedStages=[7],debugExceptions=0,actualMastersZero=True,strictV4Passed=True,allSelected32Camera25AndHud2Equal=True,vm303Rows=6461,combatCheckpoints=48,orderedInitialPublications=3205,coreWasmSha256=build['wasmSha256'],forcedReplayEndMenuObserved=True,sourceReplayEofProved=False,clearCompletionNotAsserted=True,previousZeroCallbackStartupFailureCauseResolved=False,wholeModeEquivalent=False,ordinaryOriginalGuiAccepted=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    target=R/'docs/porting/th14-sakuyaa-extra-current-nov04.json';raw=(json.dumps(report,indent=2)+'\n').encode()
    if a.check:assert target.read_bytes()==raw
    else:target.write_bytes(raw)
    print(json.dumps({k:v for k,v in report.items()if k!='bindings'}))
if __name__=='__main__':main()
