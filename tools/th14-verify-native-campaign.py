"""Recompute retained campaign observations, with a separately declared prefix scope."""
import argparse
import array
import gzip
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda data:hashlib.sha256(data).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['native','model','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--prefix',type=int,default=0,help='Explicitly verify only this diagnostic prefix; never accepts it as a natural full run')
    parser.add_argument('--scene-copy-observation',type=Path,help='Separately verified original TF-copy observation; only the declared15000-callback prefix is accepted')
    parser.add_argument('--controlled-thread-observation',type=Path,help='Explicitly controlled original normal-ANM worker observation; finite diagnostic prefixes only, never ordinary timing acceptance')
    parser.add_argument('--controlled-vm-observation',type=Path,help='Explicit two-thread original VM-return schedule; finite diagnostic prefix only')
    parser.add_argument('--proposed-normal-boundary',action='store_true',help='Explicitly retain a proposed host-clock delivery boundary; field equality never accepts its exact original instruction placement')
    args=parser.parse_args();native=args.native.resolve();model=args.model.resolve();bindings={}
    assert args.prefix>=0
    assert sum(bool(value)for value in [args.scene_copy_observation,args.controlled_thread_observation,args.controlled_vm_observation])<=1
    assert not(args.proposed_normal_boundary and(args.scene_copy_observation or args.controlled_thread_observation or args.controlled_vm_observation))
    assert all(p.is_relative_to(ROOT/'artifacts/th14')for p in (native,model))
    def read(path):
        data=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(read(path))
    original=load(native/'report.json');reported=load(model/'report.json');build=load(args.build.resolve());captured=original['callbacks'];count=args.prefix or captured
    assert not reported.get('proposedScenePublicationWindowDiagnostic'), 'Proposed Scene publication-window timing is diagnostic only'
    assert not reported.get('proposedSignatureDrawClockDiagnostic'), 'Proposed signature draw-clock timing is diagnostic only'
    assert (reported.get('hostNormalBoundaryMode')=='proposed')==args.proposed_normal_boundary
    if args.proposed_normal_boundary:
        assert reported['normalBoundaryTimestampAssumptionDeclared']and not reported['vmCallbackPointersWrapped']
        assert not reported['ordinaryIndependentThreadTimingAcceptance']and not reported['exactOriginalInstructionBoundaryAccepted']
    assert original['childExited']and not original['error']
    if args.prefix:assert count<=captured and reported['diagnosticPrefixOnly']
    else:assert original['observedForcedReplayEndMenu']and not reported['diagnosticPrefixOnly']
    if args.scene_copy_observation:
        assert args.prefix==15000 and original.get('hardwareDebugRegistersAndTrapFlagOnly')
        proof_path=args.scene_copy_observation.resolve();proof=load(proof_path)
        assert proof['verifiedFiniteOriginalSceneCopyObservation']and proof['diagnosticPrefixOnly']and proof['callbacks']==args.prefix
        assert proof['bindings'][(native/'report.json').relative_to(ROOT).as_posix()]['sha256']==SHA(read(native/'report.json'))
        prepared=[ROOT/path for path in proof['bindings']if path.endswith('/prepared.json')]
        plans=[ROOT/path for path in proof['bindings']if path.endswith('/native-word-step-prefix-plan.json')]
        assert len(prepared)==len(plans)==1
        subprocess.run([sys.executable,str(ROOT/'tools/th14-scene-copy-word-evidence-oct26.py'),'--native',str(native),'--build',str(prepared[0].parent),'--plan',str(plans[0]),'--output',str(proof_path),'--check'],check=True)
        assert reported['sceneCopyObservationSha256']==SHA(read(proof_path))and len(reported['sceneCopyWordHandoffs'])==1
    elif args.controlled_thread_observation:
        assert args.prefix>0 and reported['hostNormalBoundaryMode']=='controlled'
        assert reported['productionNormalAnmBoundaryPoll']and not reported['vmCallbackPointersWrapped']
        assert not reported['ordinaryIndependentThreadTimingAcceptance']
        proof_path=args.controlled_thread_observation.resolve();proof=load(proof_path)
        subprocess.run([sys.executable,str(ROOT/'tools/th14-controlled-worker-boundary-evidence-oct29.py'),
            '--native',str(native),'--output',str(proof_path),'--check'],check=True)
        assert proof['verifiedControlledOriginalNormalAnmBoundary']and proof['diagnosticPrefixOnly']
        assert not proof['ordinaryIndependentThreadTimingAcceptance']and count<=proof['capturedCallbacks']
        assert proof['bindings'][(native/'report.json').relative_to(ROOT).as_posix()]['sha256']==SHA(read(native/'report.json'))
    elif args.controlled_vm_observation:
        assert args.prefix==33000 and reported['hostNormalBoundaryMode']=='controlled-vm-return'
        assert reported['productionNormalVmReturnPoll']and not reported['normalVmReturnBoundaryUnsupported']and not reported['vmCallbackPointersWrapped']
        assert not reported['ordinaryIndependentThreadTimingAcceptance']
        proof_path=args.controlled_vm_observation.resolve();proof=load(proof_path)
        subprocess.run([sys.executable,str(ROOT/'tools/th14-controlled-vm-worker-evidence-oct29.py'),
            '--native',str(native),'--output',str(proof_path),'--check'],check=True)
        assert proof['verifiedControlledOriginalNormalVmReturnBoundary']and proof['diagnosticPrefixOnly']
        assert not proof['ordinaryIndependentThreadTimingAcceptance']and count<=proof['capturedCallbacks']
        assert proof['bindings'][(native/'report.json').relative_to(ROOT).as_posix()]['sha256']==SHA(read(native/'report.json'))
        boundary=reported['normalVmBoundaryObservation'];clock=boundary['modelClock']
        assert boundary['callback']==proof['precedingPlayerCallbacks']and boundary['originalPc']==0x47e660
        assert (boundary['file'],boundary['script'])==(proof['targetVmFile'],proof['targetVmScript'])and not boundary['retainedBaseline']
        assert boundary['readyNs']==original['controlledScheduleEvents'][4]['hostMonotonicNs']
        assert clock['delivered']==1 and clock['failed']==0 and 2<=clock['ownVmPollSlot']<=clock['visits']
    else:assert original['hardwareBreakpointsOnly']
    assert original['instructionBytesPatched']==original['rngOrCounterWrites']==0
    assert not original['inputInjected']and original['gameStateWordWrites']==1 and original['caseInitialization']['attractBitClearOnly']
    assert original['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert reported['callbacks']==count
    assert reported['noNativePublicationValuesProvidedToEngine']and reported['noPerFrameStateOverrides']
    assert reported['allPortableBulletOpcodesSupported']and not reported['portableUnsupportedBulletObservations']
    asset=ROOT/original['observerOptions']['assets'];assets=load(asset/'manifest.json')
    replay=Path(assets['replayPath']);assert SHA(read(replay))==assets['replaySha256']==original['sourceFullReplaySha256']==reported['sourceReplaySha256']
    assert assets['passed']and assets['changedEntries']==['demo0.rpy']and assets['unchangedEntries']==226
    assert SHA(read(asset/'th14.dat'))==assets['referenceArchiveSha256']==reported['archiveSha256']==next(row['sha256']for row in original['files']if row['name']=='th14.dat')
    raw_full=read(native/'selected-state.u32');assert len(raw_full)==captured*128 and SHA(raw_full)==original['selectedSha256']
    raw=raw_full[:count*128];assert raw==read(model/'selected-state.u32')and SHA(raw)==reported['selectedSha256']
    camera_full=read(native/'world-camera.raw');assert len(camera_full)==captured*0x124
    camera=camera_full[:count*0x124];offsets=[*range(0,88,4),0x104,0x108,0x10c]
    expected=array.array('I',(struct.unpack_from('<I',camera,n*0x124+offset)[0]for n in range(count)for offset in offsets))
    assert len(camera)==count*0x124 and expected.tobytes()==read(model/'portable-camera.u32')
    hud_full=read(native/'hud-score.u32');assert len(hud_full)==captured*8
    hud=hud_full[:count*8];assert hud==read(model/'portable-hud.u32')
    spec=importlib.util.spec_from_file_location('vm_fields',ROOT/'tools/th14-hud-completion-evidence-check-oct25.py');vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)
    snapshots=[]
    for path in sorted(native.glob('live-vms-callback-*.json')):
        frame=int(path.stem.rsplit('-',1)[1]);assert frame<=captured
        if frame>count:continue
        rows=load(path)['rows'];actual=load(model/f'portable-live-{frame}.json');blobs=[bytes.fromhex(row['rawVmHex'])for row in rows]
        handles={struct.unpack_from('<I',blob,0x570)[0]:struct.unpack_from('<I',blob,0x540)[0]for blob in blobs}
        assert len(handles)==len(rows) and [row['handle']for row in rows]==[row[0]for row in actual]
        assert [vm.vm_words(blob,handles)for blob in blobs]==actual
        snapshots.append(dict(callback=frame,rows=len(rows),selectedWordsPerVm=303))
    assert snapshots
    index=load(native/'combat-pool-index.json');fields=index['fields'];totals={key:0 for key in fields};active=0;checkpoints=0
    spec=importlib.util.spec_from_file_location('combat_schema',ROOT/'tools/th14-combat-pool-readonly-v3-oct25.py');schema=importlib.util.module_from_spec(spec);spec.loader.exec_module(schema)
    assert fields==json.loads(json.dumps(schema.SCHEMA))and original['combatPoolSchemaVersion']==3
    for entry in index['snapshots']:
        if entry['callback']>count:continue
        compressed=(native/'combat-pools'/entry['file']).read_bytes();assert SHA(compressed)==entry['sha256']
        observation=json.loads(gzip.decompress(compressed));actual=json.loads((model/f"combat-{entry['callback']}.json").read_text())
        assert (observation['callback'],observation['stage'],observation['stageFrame'])==(actual['callback'],actual['stage'],actual['stageFrame'])
        any_active=False
        for family,layout in fields.items():
            expected=[]
            for row in observation['original'][family]:
                blob=bytes.fromhex(row['rawHex']);expected.append([row['slot']if offset is None else struct.unpack_from('<H'if family=='bullets'and name=='state'else'<I',blob,offset)[0]for name,offset in layout])
            assert expected==actual['rows'][family],(entry['callback'],family)
            totals[family]+=len(expected);any_active=any_active or bool(expected)
        active+=int(any_active);checkpoints+=1
    publications=[json.loads(line)for line in read(native/'allocation-events.jsonl').decode().splitlines()]
    cutoff=original['anmPublicationTraceCutoffPlayerCallbacks'];portable=load(model/f'portable-allocations-initial-through-{cutoff}.json')
    assert len(publications)==len(portable)==original['allAnmPublications']
    assert [(row['handle'],row['file'],row['script'])for row in publications]==[(row['handle'],row['file'],row['script'])for row in portable]
    assert build['wasmSha256']==reported['wasmSha256']==SHA(read(args.build.resolve().parent/'observer.wasm'))
    for row in build['objectBindings']:assert SHA(Path(row['path']).read_bytes())==row['sha256']
    for path,digest in build['fixtureDependencyHashes'].items():
        current=Path(path);retained=ROOT/'artifacts/th14/shared-observer-source-cache'/(digest+'.bin')
        assert (current.exists()and SHA(current.read_bytes())==digest)or(retained.exists()and SHA(retained.read_bytes())==digest),path
    timing=[row for row in reported['observedPhaseInputs']if row['phase']=='Timeline']
    result=dict(verifiedFiniteEvidence=True,callbacks=count,sourceReplaySha256=assets['replaySha256'],selection=reported['selection'],stagesObserved=original['recordedStages'],allSelected32Equal=True,allCamera25Equal=True,allHud2Equal=True,vm303Snapshots=snapshots,vm303Rows=sum(row['rows']for row in snapshots),allVm303AndRegistryOrderEqual=True,combatCheckpoints=len(index['snapshots']),nonemptyCombatCheckpoints=active,combatRows=totals,combatFieldCounts={key:len(value)for key,value in fields.items()},allCapturedCombatWordsEqual=True,publicationCutoffCallbacks=cutoff,orderedPublications=len(publications),timelineCompletionSources=timing,wasmSha256=build['wasmSha256'],comparisonToolSha256=reported.get('comparisonToolSha256'),verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,limitations=['Warm replay with declared host time, entropy and asynchronous resource completion inputs; ordinary original cold-menu initialization is not proved.','Only stated fields and sampled objects, including empty loading frames; whole objects and all curve samples are not compared.','Publication order covers only the declared initial window.','No actual GPU/PCM, all-mode equivalence, browser acceptance or persistence is proved.'],completeGame=False,nativeEquivalent=False)
    result.update(diagnosticPrefixOnly=bool(args.prefix),originalCapturedCallbacks=captured,originalNaturalReplayEndObserved=bool(original['observedForcedReplayEndMenu']),combatCheckpoints=checkpoints)
    result.update(hostNormalBoundaryMode=reported.get('hostNormalBoundaryMode','none'),ordinaryIndependentThreadTimingAcceptance=False)
    if args.scene_copy_observation:
        result.update(sceneCopyObservationSha256=SHA(read(args.scene_copy_observation.resolve())),hardwareDebugInputKind='verified original hardware watches and TF copy steps')
        result['limitations'].append('The explicit Scene-copy observation validates only this TF-stepped diagnostic prefix; historical camera failures remain independent.')
    if args.controlled_thread_observation:
        result.update(controlledThreadObservationSha256=SHA(read(args.controlled_thread_observation.resolve())),
            hardwareDebugInputKind='hardware breakpoints with one explicitly controlled main-thread suspend increment',ordinaryIndependentThreadTimingAcceptance=False)
        result['limitations'].append('Original timing was explicitly controlled at normal ANM entry; ordinary independent original/browser scheduling is not accepted.')
    if args.proposed_normal_boundary:
        result.update(proposedNormalBoundaryAssumption=True,exactOriginalInstructionBoundaryAccepted=False)
        result['limitations'].append('The host clock is delivered at a proposed normal-ANM boundary; exact placement in this original record is an assumption, not accepted original instruction evidence.')
    if args.controlled_vm_observation:
        result.update(controlledVmReturnObservationSha256=SHA(read(args.controlled_vm_observation.resolve())),
            hardwareDebugInputKind='hardware breakpoints with one declared suspend increment per original thread',
            ownVmClockPollSlot=reported['normalVmBoundaryObservation']['modelClock']['ownVmPollSlot'],
            ordinaryIndependentThreadTimingAcceptance=False)
        result['limitations'].append('Both original threads are explicitly scheduled at a verified VM return. This supports that legal boundary only; the older independent instruction placement and ordinary timing remain unaccepted.')
    if args.prefix:result['limitations'].append('Explicit diagnostic prefix only; neither the original process exit nor this prefix proves natural replay completion.')
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/porting')or output.is_relative_to(ROOT/'artifacts/th14')
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:result[key]for key in ['verifiedFiniteEvidence','callbacks','vm303Rows','combatCheckpoints','nonemptyCombatCheckpoints','allCapturedCombatWordsEqual']}))

if __name__=='__main__':main()
