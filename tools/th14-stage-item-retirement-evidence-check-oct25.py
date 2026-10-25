"""Verify the bounded full Reimu B Hard case from retained private observations.

Only counts, hashes and scope are published; original assets and memory stay local.
"""
import array
import gzip
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOME=ROOT/'artifacts/th14/stage-item-retirement-oct25'
NATIVE=ROOT/'artifacts/th14/retail-reimub-hard-full-bounded-hardware-oct25'
NAME='full-initial-worker-events-retail-reimub-hard-full-bounded-hardware-oct25-cpu-write'
MODEL=HOME/(NAME+'-stage-item-retirement-curve-cursor')
BEFORE=ROOT/'artifacts/th14/combat-pool-oct25/hard-full-bounded-control'/(NAME+'-bounded-queue-provenance-bound-v2')
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    native=load(NATIVE/'report.json');model=load(MODEL/'report.json')
    assert native['callbacks']==model['callbacks']==107662 and native['recordedStages']==list(range(1,7))
    assert native['childExited'] and native['observedForcedReplayEndMenu'] and native['error']==''
    assert native['hardwareBreakpointsOnly'] and native['instructionBytesPatched']==native['rngOrCounterWrites']==0
    assert not native['inputInjected'] and native['gameStateWordWrites']==1 and native['caseInitialization']['attractBitClearOnly']
    assert native['privateImmutableStorageCacheUsed'] and native['originalGameFilesNotHardlinked']
    assert native['observerOptions']['minimum_free_gib']==100 and native['observerOptions']['maximum_capture_gib']==2
    assert native['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert model['sourceReplaySha256']==native['sourceFullReplaySha256']=='c5db55756f58ed10281c6e4232a36873fb099a1b9567dc74b107f5a76e8ffc2b'
    assert model['noNativePublicationValuesProvidedToEngine'] and model['noPerFrameStateOverrides']
    assert model['asciiCreateObservedAtOriginal44477aCall'] and not model['asciiBeginDeliveryInferredFromFirstPublication']
    assert model['allPortableBulletOpcodesSupported'] and not model['portableUnsupportedBulletObservations']
    raw=read(NATIVE/'selected-state.u32');portable=read(MODEL/'selected-state.u32');old=read(BEFORE/'selected-state.u32')
    assert raw==portable and len(raw)==107662*128 and len(old)==len(raw)
    differences=[(i//32,i%32)for i,(a,b)in enumerate(zip(array.array('I',raw),array.array('I',old)))if a!=b]
    assert differences==[(i,19)for i in range(57140,57223)]
    assert SHA(raw)==native['selectedSha256']==model['selectedSha256']
    camera=read(NATIVE/'world-camera.raw');offsets=[*range(0,88,4),0x104,0x108,0x10c]
    selected=array.array('I',(struct.unpack_from('<I',camera,frame*0x124+off)[0]for frame in range(107662)for off in offsets))
    assert len(camera)==107662*0x124 and selected.tobytes()==read(MODEL/'portable-camera.u32')
    assert read(NATIVE/'hud-score.u32')==read(MODEL/'portable-hud.u32')
    spec=importlib.util.spec_from_file_location('vm_verifier',ROOT/'tools/th14-hud-completion-evidence-check-oct25.py')
    vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)
    snapshots=[]
    for frame in (1,26000,30000,36000,38900,60000,90000):
        rows=load(NATIVE/f'live-vms-callback-{frame}.json')['rows'];actual=load(MODEL/f'portable-live-{frame}.json')
        blobs=[bytes.fromhex(row['rawVmHex'])for row in rows]
        handles={struct.unpack_from('<I',b,0x570)[0]:struct.unpack_from('<I',b,0x540)[0]for b in blobs}
        assert len(handles)==len(rows) and [r['handle']for r in rows]==[r[0]for r in actual]
        assert [vm.vm_words(b,handles)for b in blobs]==actual
        snapshots.append(dict(callback=frame,rows=len(rows)))
    index=load(NATIVE/'combat-pool-index.json');schema=index['fields'];totals={k:0 for k in schema}
    assert {k:len(v)for k,v in schema.items()}==dict(enemies=31,bullets=18,shots=19,areas=19,items=13,lasers=26)
    assert dict(schema['lasers'])['transformIndex']==0x594 and dict(schema['bullets'])['size']==0x13bc
    for entry in index['snapshots']:
        compressed=(NATIVE/'combat-pools'/entry['file']).read_bytes();assert SHA(compressed)==entry['sha256']
        observation=json.loads(gzip.decompress(compressed));actual=json.loads((MODEL/f"combat-{entry['callback']}.json").read_text())
        assert observation['callback']==actual['callback']==entry['callback']
        assert observation['stage']==actual['stage'] and observation['stageFrame']==actual['stageFrame']
        for family,fields in schema.items():
            expected=[]
            for row in observation['original'][family]:
                blob=bytes.fromhex(row['rawHex'])
                expected.append([row['slot']if off is None else struct.unpack_from('<H'if family=='bullets'and name=='state'else'<I',blob,off)[0]for name,off in fields])
            assert expected==actual['rows'][family],(entry['callback'],family)
            totals[family]+=len(expected)
    assert len(index['snapshots'])==1496
    pubs=[json.loads(row)for row in read(NATIVE/'allocation-events.jsonl').decode().splitlines()]
    allocations=load(MODEL/'portable-allocations-initial-through-1000.json')
    assert len(pubs)==len(allocations)==5189
    assert [(r['handle'],r['file'],r['script'])for r in pubs]==[(r['handle'],r['file'],r['script'])for r in allocations]
    build=load(HOME/'observer-curve-cursor-build.json');assert SHA(read(HOME/'observer-curve-cursor.wasm'))==build['wasmSha256']==model['wasmSha256']
    for path,digest in build['fixtureDependencyHashes'].items():assert SHA(Path(path).read_bytes())==digest,path
    change=load(HOME/'source-change.json');assert SHA(read(ROOT/'runtimes/th12/th12_web/cpp/game/GameBattle.cpp'))==change['afterSha256']
    sdl=load(HOME/'build/build.json');assert sdl['exportsUnchanged'] and not sdl['addedImports'] and not sdl['removedImports']
    assert SHA(read(HOME/'build/th11.wasm'))==sdl['wasmSha256'] and sdl['sourceHashes']['th12_web/cpp/game/GameBattle.cpp']==change['afterSha256']
    result=dict(verifiedFiniteEvidence=True,productionChange='TH14 stage retirement clears item pools before enemy retirement and worker wait.',callbacks=107662,selectedWordsPerCallback=32,oldBombFragmentDifferenceFrames=83,newSelectedDifferences=0,allCamera25WordsEqual=True,allHud2WordsEqual=True,vm303Checkpoints=snapshots,vm303Rows=sum(r['rows']for r in snapshots),combatCheckpoints=1496,combatSelectedWords={k:len(v)for k,v in schema.items()},combatRows=totals,allCapturedCombatWordsEqual=True,orderedPublicationsThroughFirst1000=5189,curveCursorObserverCorrected=True,curveCursorProductionChange=False,wasmSha256=build['wasmSha256'],sdlSha256=sdl['wasmSha256'],browserValidated=False,sourceReplaySha256=model['sourceReplaySha256'],storageLimitsGiB=dict(minimumFree=100,maximumObservation=2),bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),limitations=['Warm replay initialization; ordinary cold menu initialization is not covered.','1496 checkpoints include empty loading frames; only listed selected fields are compared, not whole objects or all curve samples.','Publication ordering is covered only through first1000 callbacks.','Scene and Timeline worker completion times remain bounded by observed main resource boundaries.','No current-SDL browser acceptance, full pixels, original DirectSound PCM, all-mode complete execution or whole-game equivalence is claimed.'],completeGame=False,nativeEquivalent=False)
    output=ROOT/'docs/porting/th14-stage-item-retirement-verified-oct25.json';output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:result[k]for k in ['verifiedFiniteEvidence','callbacks','oldBombFragmentDifferenceFrames','newSelectedDifferences','vm303Rows','combatCheckpoints','allCapturedCombatWordsEqual']}))

if __name__=='__main__':main()
