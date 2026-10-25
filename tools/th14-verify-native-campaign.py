"""Independently recompute a complete campaign's retained selected observations."""
import argparse
import array
import gzip
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda data:hashlib.sha256(data).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['native','model','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();native=args.native.resolve();model=args.model.resolve();bindings={}
    assert all(p.is_relative_to(ROOT/'artifacts/th14')for p in (native,model))
    def read(path):
        data=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(read(path))
    original=load(native/'report.json');reported=load(model/'report.json');build=load(args.build.resolve());count=original['callbacks']
    assert original['childExited']and original['observedForcedReplayEndMenu']and not original['error']
    assert original['hardwareBreakpointsOnly']and original['instructionBytesPatched']==original['rngOrCounterWrites']==0
    assert not original['inputInjected']and original['gameStateWordWrites']==1 and original['caseInitialization']['attractBitClearOnly']
    assert original['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert not reported['diagnosticPrefixOnly']and reported['callbacks']==count
    assert reported['noNativePublicationValuesProvidedToEngine']and reported['noPerFrameStateOverrides']
    assert reported['allPortableBulletOpcodesSupported']and not reported['portableUnsupportedBulletObservations']
    asset=ROOT/original['observerOptions']['assets'];assets=load(asset/'manifest.json')
    replay=Path(assets['replayPath']);assert SHA(read(replay))==assets['replaySha256']==original['sourceFullReplaySha256']==reported['sourceReplaySha256']
    assert assets['passed']and assets['changedEntries']==['demo0.rpy']and assets['unchangedEntries']==226
    assert SHA(read(asset/'th14.dat'))==assets['referenceArchiveSha256']==reported['archiveSha256']==next(row['sha256']for row in original['files']if row['name']=='th14.dat')
    raw=read(native/'selected-state.u32');assert len(raw)==count*128 and raw==read(model/'selected-state.u32')
    assert SHA(raw)==original['selectedSha256']==reported['selectedSha256']
    camera=read(native/'world-camera.raw');offsets=[*range(0,88,4),0x104,0x108,0x10c]
    expected=array.array('I',(struct.unpack_from('<I',camera,n*0x124+offset)[0]for n in range(count)for offset in offsets))
    assert len(camera)==count*0x124 and expected.tobytes()==read(model/'portable-camera.u32')
    hud=read(native/'hud-score.u32');assert len(hud)==count*8 and hud==read(model/'portable-hud.u32')
    spec=importlib.util.spec_from_file_location('vm_fields',ROOT/'tools/th14-hud-completion-evidence-check-oct25.py');vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)
    snapshots=[]
    for path in sorted(native.glob('live-vms-callback-*.json')):
        frame=int(path.stem.rsplit('-',1)[1]);assert frame<=count
        rows=load(path)['rows'];actual=load(model/f'portable-live-{frame}.json');blobs=[bytes.fromhex(row['rawVmHex'])for row in rows]
        handles={struct.unpack_from('<I',blob,0x570)[0]:struct.unpack_from('<I',blob,0x540)[0]for blob in blobs}
        assert len(handles)==len(rows) and [row['handle']for row in rows]==[row[0]for row in actual]
        assert [vm.vm_words(blob,handles)for blob in blobs]==actual
        snapshots.append(dict(callback=frame,rows=len(rows),selectedWordsPerVm=303))
    assert snapshots
    index=load(native/'combat-pool-index.json');fields=index['fields'];totals={key:0 for key in fields};active=0
    spec=importlib.util.spec_from_file_location('combat_schema',ROOT/'tools/th14-combat-pool-readonly-v3-oct25.py');schema=importlib.util.module_from_spec(spec);spec.loader.exec_module(schema)
    assert fields==json.loads(json.dumps(schema.SCHEMA))and original['combatPoolSchemaVersion']==3
    for entry in index['snapshots']:
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
        active+=int(any_active)
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
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/porting')or output.is_relative_to(ROOT/'artifacts/th14')
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:result[key]for key in ['verifiedFiniteEvidence','callbacks','vm303Rows','combatCheckpoints','nonemptyCombatCheckpoints','allCapturedCombatWordsEqual']}))

if __name__=='__main__':main()
