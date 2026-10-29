"""Recompute a declared warm-case prefix and its retained negative control.

Original recordings, archives and memory remain private. This tool reads them;
it never launches or changes an original process. A running capture's binding
explicitly covers the stated prefix bytes, not its changing suffix or exit.
"""
from pathlib import Path
import argparse,array,gzip,hashlib,importlib.util,json,struct,subprocess

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/mode-coverage-oct29'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence():
    bindings={}
    def raw(path,limit=None):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        with path.open('rb')as stream:data=stream.read()if limit is None else stream.read(limit)
        row=dict(bytes=len(data),sha256=SHA(data))
        if limit is not None:assert len(data)==limit;row['prefixBytes']=limit
        bindings[path.relative_to(R).as_posix()]=row;return data
    def load(path):return json.loads(raw(path))
    native=H/'marisaa-easy-toho-native';positive=H/'marisaa-easy-toho-prefix30000-warm-flag'
    negative=H/'marisaa-easy-toho-prefix2400-legacy';count=30000
    build=load(H/'warm-flag-observer/observer-build.json')
    base_home=R/'artifacts/th14/native-frame-readback-oct28/later-stage-native-core'
    base=load(base_home/'observer-build.json')
    assert build['engineSourcesRecompiledForThisLink']==0 and build['engineObjectsReusedForThisLink']==141
    assert build['objectBindings']==base['objectBindings'] and build['sourceHashes']==base['sourceHashes']
    for row in build['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    assert SHA(raw(H/'warm-flag-observer/observer.wasm'))==build['wasmSha256']
    before=raw(base_home/'fixture.cpp').replace(b'\r\n',b'\n')
    fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-native-campaign-fixture.cpp'
    after=raw(fixture).replace(b'\r\n',b'\n')
    old=b'if(warm_at_first_player){session.state.demo=false;session.battle->demo=false;warm_at_first_player=false;}'
    new=b'''if(warm_at_first_player){
  session.state.demo=false;session.battle->demo=false;
  // Match the warm oracle's one declared write at first Player entry: clear
  // only attract bit0x40. ECL554 and spell visuals read this live flag cell;
  // changing the convenience demo booleans alone leaves them in attract mode.
  session.battle->enemy_commands.th14_run_flags&=~0x40u;
  warm_at_first_player=false;
 }'''
    assert before.count(old)==after.count(new)==1 and before.replace(old,new)==after
    assert build['expandedFixtureSha256']==SHA(fixture.read_bytes())
    for path,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(path)))==digest
    initial=load(native/'untouched-first-player.json');assert initial['attractFlags']==64 and initial['replayManagerMode']==1
    assert initial['words'][27:31]==[1,0,0,1]
    observer=raw(native/'observer-source.py')
    observer_commit='babc4e04e4b37f98cbf89d5117065e084fbd8b26'
    published_observer=subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),
        'show',observer_commit+':tools/th14-native-campaign-observer-oct25.py'])
    assert observer==published_observer and SHA(observer)=='b3ff99666cc99816c0ab07ad5fe449a5acdc9843bd83e6e112da25eef450861e'
    load(native/'process-start.json')
    assets=load(R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-b1d9e367e7e5/manifest.json')
    assert assets['changedEntries']==['demo0.rpy']and assets['unchangedEntries']==226
    assert assets['originalArchiveSha256']=='57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233'
    replay=raw(Path(assets['replayPath']));assert len(replay)==103350 and SHA(replay)==assets['replaySha256']=='b1d9e367e7e5e29e0d7bd08fe493062164171d5d88c52f954b8565fcd2e81a2d'
    report=load(positive/'report.json');assert report['diagnosticPrefixOnly']and report['callbacks']==count
    assert report['noPerFrameStateOverrides']and report['noNativePublicationValuesProvidedToEngine']
    assert report['sourceReplaySha256']==assets['replaySha256']and report['wasmSha256']==build['wasmSha256']
    assert report['schedulerPhases']=='observed'and report['allPortableBulletOpcodesSupported']
    selected=raw(native/'selected-state.u32',count*128);assert selected==raw(positive/'selected-state.u32')
    stages=sorted({struct.unpack_from('<I',selected,n*128+120)[0]for n in range(count)});assert stages==[1,2]
    camera=raw(native/'world-camera.raw',count*0x124);offsets=[*range(0,88,4),0x104,0x108,0x10c]
    words=array.array('I',(struct.unpack_from('<I',camera,n*0x124+off)[0]for n in range(count)for off in offsets))
    assert words.tobytes()==raw(positive/'portable-camera.u32')
    assert raw(native/'hud-score.u32',count*8)==raw(positive/'portable-hud.u32')
    spec=importlib.util.spec_from_file_location('warm_vm_words',R/'tools/th14-hud-completion-evidence-check-oct25.py')
    vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)
    raw(R/'tools/th14-hud-completion-evidence-check-oct25.py');snapshots=[]
    for callback in [1,30000]:
        rows=load(native/f'live-vms-callback-{callback}.json')['rows'];portable=load(positive/f'portable-live-{callback}.json')
        blobs=[bytes.fromhex(row['rawVmHex'])for row in rows]
        handles={struct.unpack_from('<I',blob,0x570)[0]:struct.unpack_from('<I',blob,0x540)[0]for blob in blobs}
        assert len(handles)==len(rows) and [row['handle']for row in rows]==[row[0]for row in portable]
        assert [vm.vm_words(blob,handles)for blob in blobs]==portable
        snapshots.append(dict(callback=callback,rows=len(rows),selectedWords=303))
    # The native process can append checkpoints while this prefix is checked.
    # Bind a declared canonical projection, never a hash of its changing tail.
    index=json.loads((native/'combat-pool-index.json').read_bytes())
    index={**index,'snapshots':[row for row in index['snapshots']if row['callback']<=count]}
    projection=json.dumps(index,sort_keys=True,separators=(',',':')).encode()
    bindings[(native/'combat-pool-index.json').relative_to(R).as_posix()]=dict(
        canonicalProjection='schemaAndSnapshotsThrough30000',bytes=len(projection),sha256=SHA(projection))
    totals={key:0 for key in index['fields']};checkpoints=0;active=0
    for entry in index['snapshots']:
        if entry['callback']>count:continue
        compressed=raw(native/'combat-pools'/entry['file']);assert SHA(compressed)==entry['sha256']
        original=json.loads(gzip.decompress(compressed));portable=load(positive/f"combat-{entry['callback']}.json")
        assert (original['callback'],original['stage'],original['stageFrame'])==(portable['callback'],portable['stage'],portable['stageFrame'])
        nonempty=False
        for family,fields in index['fields'].items():
            expected=[]
            for row in original['original'][family]:
                blob=bytes.fromhex(row['rawHex']);expected.append([row['slot']if off is None else struct.unpack_from('<H'if family=='bullets'and name=='state'else'<I',blob,off)[0]for name,off in fields])
            assert expected==portable['rows'][family],(entry['callback'],family)
            totals[family]+=len(expected);nonempty=nonempty or bool(expected)
        checkpoints+=1;active+=int(nonempty)
    assert checkpoints==162
    publications=[json.loads(line)for line in raw(native/'allocation-events.jsonl').decode().splitlines()]
    allocations=load(positive/'portable-allocations-initial-through-1000.json');assert len(publications)==len(allocations)==2870
    assert [(r['handle'],r['file'],r['script'])for r in publications]==[(r['handle'],r['file'],r['script'])for r in allocations]
    previous=load(negative/'allocation-report.json')['windows'][0];assert not previous['allHandlesFileScriptEqual']
    first=previous['firstIdentityDifference'];assert first['index']==1800 and first['native']['precedingPlayerCallbacks']==662
    assert [(row['file'],row['script'])for row in publications[1800:1805]]==[(6,4),(6,3),(6,5),(6,6),(6,0)]
    bad=load(negative/'combat-snapshots.json');assert len(bad['differences'])==120 and not bad['allCapturedCombatWordsEqual']
    no_events=H/'first-stage-prefix2400-no-transition-events';view=load(no_events/'prefix-view.json');assert view['capturedPrefixOnly']==2400 and not view['processLaunched']
    assert not (no_events/'scene-camera-copy-events.jsonl').exists()and not (no_events/'controller-phase-events.jsonl').exists()
    first_model=H/'marisaa-easy-toho-prefix2400-observed-no-events';small=load(first_model/'report.json')
    assert small['callbacks']==2400 and small['schedulerPhases']=='observed'and small['allRaw32ByteIdentical']
    assert raw(first_model/'selected-state.u32')==selected[:2400*128]
    assert not load(first_model/'combat-snapshots.json')['differences']
    longer=H/'marisaa-easy-toho-prefix48000-warm-flag';failure=load(longer/'report.json')
    expected=raw(native/'selected-state.u32',48000*128);actual=raw(longer/'selected-state.u32')
    assert expected==raw(longer/'native-selected-state.u32')and len(actual)==len(expected)
    expected_words=array.array('I',expected);actual_words=array.array('I',actual)
    differences=[(index,a,b)for index,(a,b)in enumerate(zip(expected_words,actual_words))if a!=b]
    first_index,a,b=differences[0];callback,word=divmod(first_index,32)
    assert (callback,word,a,b)==(30990,21,56097,5435)and not failure['allRaw32ByteIdentical']
    assert failure['firstDifference']==dict(index=callback,stage=3,stageFrame=0,word=word,native=a,portable=b)
    assert struct.unpack_from('<I',expected,callback*128+88)[0]==struct.unpack_from('<I',actual,callback*128+88)[0]==953620
    events=[json.loads(line)for line in (native/'transition-events.jsonl').read_text().splitlines()]
    events=[row for row in events if row['stage']<=3]
    event_projection=json.dumps(events,sort_keys=True,separators=(',',':')).encode()
    bindings[(native/'transition-events.jsonl').relative_to(R).as_posix()]=dict(canonicalProjection='eventsThroughStage3',bytes=len(event_projection),sha256=SHA(event_projection))
    restore=next(row for row in events if row['stage']==3 and row['event']=='replay-seeds-restored-before-globals-copy')
    assert restore['pc']==0x456133 and restore['precedingPlayerCallbacks']==30990 and restore['mainThreadPcAtWorkerEvent']==0x4041a0
    native_rng=struct.unpack('<4I',bytes.fromhex(restore['rngHex']));assert native_rng==(30962,953574,30962,0)
    def rng_steps(seed,target):
        for steps in range(1000):
            if seed==target:return steps
            mixed=((seed^0x9630)-0x6553)&0xffff;seed=((mixed<<2)|(mixed>>14))&0xffff
        raise AssertionError('Target absent from diagnostic RNG trajectory')
    assert rng_steps(30962,a)==46 and rng_steps(30962,b)==22
    longer_failure=dict(callbacks=48000,strictPassed=False,firstMismatchCallback=30991,stage=3,stageFrame=0,word=21,
        nativeScriptSeed=a,portableScriptSeed=b,equalScriptCallsAtFirstMismatch=953620,
        nativeObservedRestorePc=0x456133,mainPcAtRestore=0x4041a0,scriptCallsAtRestore=953574,
        diagnosticStepsFromHeaderSeed=dict(native=46,portable=22),valuesNeverProvidedToEngine=True,
        exactSubcallbackPlacementAccepted=False)
    return dict(verifiedFiniteWarmReplayFlagCorrection=True,productionGameplayChanged=False,
        fixtureOnlyAtDeclaredWarmBoundary=True,clearsAttractFlagOnly=True,callbacks=count,stagesObservedInPrefix=stages,
        originalNaturalEndOrClearClaimed=False,allSelected32Camera25Hud2Equal=True,vm303Snapshots=snapshots,vmRows=sum(row['rows']for row in snapshots),
        combatCheckpoints=checkpoints,nonemptyCombatCheckpoints=active,combatRows=totals,orderedInitialPublications=2870,
        negativeFirstPublicationMismatchCallback=662,negativeMissingLogoFamily=[4,3,5,6,0],negativeCombatWordDifferences=120,
        stage1WithoutTransitionEventFilesPassed=True,laterStageObservationFilesRemainRequired=True,
        longerPrefixRetainedStrictFailure=longer_failure,
        coreObjectsReused=141,coreSourcesChanged=0,wasmSha256=build['wasmSha256'],sourceReplaySha256=SHA(replay),
        captureObserverFrozenAtSourceCommit=observer_commit,captureObserverSha256=SHA(observer),
        limitations=['Declared warm replay initialization, host time and observed resource readiness inputs; ordinary original menu initialization is not proved.',
            'Only stated fields, two VM snapshots and sampled combat objects; no whole-frame GPU or original PCM comparison.',
            'Explicit30000-callback prefix. Later bytes, process exit, all-stage entries, natural completion and all modes remain outside this proof.',
            'Historical frozen fixture results are retained; this corrected fixture does not inherit their whole-run acceptance.'],
        completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    proof=evidence();target=R/'docs/porting/th14-warm-replay-flags-verified-oct29.json'
    if args.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:proof[key]for key in ['verifiedFiniteWarmReplayFlagCorrection','callbacks','vmRows','combatCheckpoints','productionGameplayChanged','completeGame']}))
if __name__=='__main__':main()
