"""Verify stored TH14 stage-two continuation evidence; never execute the game.

Private original resources and RAM remain local. This verifier binds the
executed producers and checks their stored outputs; it is not a fresh Native
capture, a current browser run, or whole-game equivalence.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / 'docs/porting/th14-stage2-callback-observed-oct15.json'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()
# Filled from the completed, immutable local producers before publication.
BINDINGS = {'productionBuild': {'path': 'artifacts/th14/screen-camera-production-build-oct14/build-result.json', 'bytes': 229508, 'sha256': '26fc6f89e33f19bcc48b57d58ebb8582fdc79688c0166d27b01a620e5a5dfb09'}, 'objectNames': {'path': 'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json', 'bytes': 33491, 'sha256': '75050d7a652d63dd7cc777925848bee85aee018729ad23f0c3aafa3ba21915c1'}, 'stageEnemyHelper': {'path': 'artifacts/th14/stage-enemy-main-pump-prepared-oct15/receipt.json', 'bytes': 69920, 'sha256': 'b49acba20606ee9e0464a9c7a51cd2d0f55b2fd896ac151ecf86108721309b42'}, 'stageEnemyHelperSource': {'path': 'artifacts/th14/stage-enemy-main-pump-prepared-oct15/slice.py', 'bytes': 14042, 'sha256': '5d5c3f57c258d6eb116445f476d4d4059c79c6a95af0748d6db0e3c93f66c53c'}, 'stageEnemyHelperPlan': {'path': 'artifacts/th14/stage-enemy-main-pump-prepared-oct15/plan.json', 'bytes': 1771, 'sha256': '3d947fc0bec232dad336e38e898346c0bd014de80fee4bf11801fe561b755bbe'}, 'stageEnemyTextures': {'path': 'artifacts/th14/stage-enemy-main-pump-prepared-oct15/cpu_textures.py', 'bytes': 7797, 'sha256': '820f8b5341f88c326ff449dd9ee58ecaef104e426b265b8d257310fe5375df38'}, 'stageEnemyTemplates': {'path': 'artifacts/th14/stage-enemy-main-pump-prepared-oct15/templates.bin', 'bytes': 47488, 'sha256': 'dab74c31fdb970412ce2805035985a6056894835b13044b1930aa7132bc4c0e6'}, 'includeRun': {'path': 'artifacts/th14/worker-timeline-includes-v2-oct15/run/receipt.json', 'bytes': 25080, 'sha256': 'd7aaa15595cda2b4df7c4592c65e7b8a236ca1ee31235597820aaa05dbe20808'}, 'includeSource': {'path': 'artifacts/th14/worker-timeline-includes-v2-oct15/resume.py', 'bytes': 31505, 'sha256': '2cbbdeb267431337c211fda38068a18881d3024a556f85e28598ea2c3c35306f'}, 'independentExtraction': {'path': 'artifacts/archive-differential/th14.json', 'bytes': 33614, 'sha256': '4cd201cae19e606e6ac258bf2241a9bb7ae9adde811bae9c3ff7d1513ffcdf78'}, 'stageEnemyDecoded': {'path': 'artifacts/th14/worker-timeline-stage-anm-decode-oct15/run/decoded-0.bin', 'bytes': 4669024, 'sha256': '0a4c10fca0a4ed65fe8fa65b58364ceef0a2713a6b2c5b5528170bc51c539d5c'}, 'callbackRun': {'path': 'artifacts/th14/worker-after-audio-queue-v2-oct15/run/receipt.json', 'bytes': 5194, 'sha256': '50ffe316b223ae54dbb8e99b6c9ebe973304dbe2c6d2605ad861a5c86e0a4053'}, 'callbackSource': {'path': 'artifacts/th14/worker-after-audio-queue-v2-oct15/resume.py', 'bytes': 31676, 'sha256': 'db9563143f18ec2da3502c4719c6d840f73b18382d1dd951236ea1c5a95476ec'}, 'crtRun': {'path': 'artifacts/th14/worker-crt-exit-ready-oct15/run/receipt.json', 'bytes': 7887, 'sha256': '7899d93b68a4549d0cbd27031439cbad2e73e8337c5e64b461bb25a3edf5382f'}, 'crtSource': {'path': 'artifacts/th14/worker-crt-exit-ready-oct15/resume.py', 'bytes': 31352, 'sha256': 'ff2ae1c738969422175fb06a0947a4f152f5c8f2fba237aaf762ab512765c1a7'}, 'firstFrameRun': {'path': 'artifacts/th14/main-after-worker-frame-checkpoint-oct15/receipt.json', 'bytes': 190400, 'sha256': 'd15d7be9ac5055fa6b72e08e10504d2fee75841648de01c0e3694644d6ba0d08'}, 'firstFrameSource': {'path': 'artifacts/th14/main-after-worker-frame-checkpoint-oct15/slice.py', 'bytes': 12566, 'sha256': '3a748100174aed3e710cbe7a5d8d6c97c3bec001339c2237e318c269e8772219'}, 'secondFrameRun': {'path': 'artifacts/th14/main-stage2-input-none-oct15/receipt.json', 'bytes': 192675, 'sha256': '8e0cb34852d90e57e86d05bd065b5444eb9d4815811f300b5196d2e3c6174e38'}, 'secondFrameSource': {'path': 'artifacts/th14/main-stage2-input-none-oct15/slice.py', 'bytes': 15532, 'sha256': '56f1f004fad2456b417e95e65dfa6a8a2dcc24989959c5705b3aa29bb02ea16b'}, 'finalCheckpoint': {'path': 'artifacts/th14/main-stage2-input-none-oct15/checkpoint/manifest.json', 'bytes': 275469, 'sha256': '948a319013ccb24c2728e2bc9428e4d637ed3f168afa7b59d925af233d6c1537'}, 'finalRuntime': {'path': 'artifacts/th14/main-stage2-input-none-oct15/checkpoint/runtime-state.json', 'bytes': 102581, 'sha256': 'a726d509146dd1a2a9e3cc0554218bd623978f1c8df3d035aad433fbaa96ef90'}, 'audioQueueRun': {'path': 'artifacts/th14/audio-queue-main-ready-oct15/receipt.json', 'bytes': 48957, 'sha256': 'ff610e79b76bfa385809e0b1266f4f78d7acffa0de3c9d6683307b4ee50baeee'}, 'audioQueueSource': {'path': 'artifacts/th14/audio-queue-main-ready-oct15/slice.py', 'bytes': 8219, 'sha256': '9b5fed693c819a094e7c38238e8982b9018be5eac82f02bf4247aaaf5e229def'}, 'audioQueueModel': {'path': 'artifacts/th14/audio-queue-main-ready-oct15/cpu_audio.py', 'bytes': 2849, 'sha256': '69f9bb3d76ac9df56dd7a6fc0bc3950fc2cafdb52649beb38c15fa1ffbfbe568'}, 'preservedIdleClockLimitation': {'path': 'artifacts/th14/main-stage2-next-frame-strict-oct15/runtime-clock-limitation.json', 'bytes': 295, 'sha256': 'cf5879f1e5d1fcfb6ec32bb2cbfc433d1cbbc0c44ef00c042cb6c95fe6c5542c'}, 'preservedSuccessStoreWhitelistFailure': {'path': 'artifacts/th14/worker-after-audio-queue-oct15/run/receipt.json', 'bytes': 4702, 'sha256': '122e74003c7962c464df29ceffd2bef18f311494dc61481f54fb1f033c7e8d0b'}, 'enemyComparison': {'path': 'artifacts/th14/enemy-current-core-comparison-oct15/receipt.json', 'bytes': 1633, 'sha256': 'ab666321f3ebefa3aa9b56446720624986aea410771af505fde74696bcf3cbcb'}, 'enemyExpected': {'path': 'artifacts/th14/enemy-current-core-comparison-oct15/expected.json', 'bytes': 144662, 'sha256': '3ca1fbcfec39b33a62b20319dc67c67560a939e8e68f2b56eaf4ac0d747cef92'}, 'enemyFixture': {'path': 'artifacts/th14/enemy-current-core-comparison-oct15/fixture.cpp', 'bytes': 4528, 'sha256': 'c99b4436c12d584e4d22175f1de582c0688155d149f127c2e70570921f1c1d70'}, 'enemyWasm': {'path': 'artifacts/th14/enemy-current-core-comparison-oct15/check.wasm', 'bytes': 873226, 'sha256': 'c6fdc9187adbf2d169819d3913fb41a898c34b519338ea2aba99f49987443017'}, 'enemyCheckSource': {'path': 'artifacts/th14/enemy-current-core-comparison-oct15/check.mjs', 'bytes': 6729, 'sha256': '437c53c14ed3827c1575c88fb3af73f5bc06fbf0d29d480155f949e84ea16254'}, 'enemySourceAnm': {'path': 'artifacts/th14/enemy-current-core-comparison-oct15/source.anm', 'bytes': 718412, 'sha256': '89f12708a0cf4567dd420b15666f048208154e77df123154a6302ca5056836e6'}, 'stageEnemyComparison': {'path': 'artifacts/th14/stage-enemy-current-core-comparison-oct15/receipt.json', 'bytes': 1684, 'sha256': '659b958597010cf1c0d9cc8153908e6bf0cbff065c8fba2e47386cf8f9bc4e55'}, 'stageEnemyExpected': {'path': 'artifacts/th14/stage-enemy-current-core-comparison-oct15/expected.json', 'bytes': 35696, 'sha256': 'ffdf03ad9f1c8f17d88f2407563e543e6e15a6a09d10e1c84c95f80a33b5fa1f'}, 'stageEnemyFixture': {'path': 'artifacts/th14/stage-enemy-current-core-comparison-oct15/fixture.cpp', 'bytes': 5610, 'sha256': '6e5b6b3dff4c8cd368d0943c7d3a1a56dc9da6c3b0151ec21b93357f5052b9f3'}, 'stageEnemyWasm': {'path': 'artifacts/th14/stage-enemy-current-core-comparison-oct15/check.wasm', 'bytes': 883613, 'sha256': 'ca90fe097f079690e4a3360c8ffb8258dfa67badecbb20956bac30b7d528b98d'}, 'stageEnemyCheckSource': {'path': 'artifacts/th14/stage-enemy-current-core-comparison-oct15/check.mjs', 'bytes': 6985, 'sha256': '06b949bf81d909b50c1387222aadcecd571acbd8e04c6efb6f2dfa4554c53060'}, 'stageEnemySourceAnm': {'path': 'artifacts/th14/stage-enemy-current-core-comparison-oct15/source.anm', 'bytes': 4669024, 'sha256': '0a4c10fca0a4ed65fe8fa65b58364ceef0a2713a6b2c5b5528170bc51c539d5c'}, 'includeBytes0': {'path': 'artifacts/th14/worker-timeline-includes-v2-oct15/run/decoded-0.bin', 'bytes': 6020, 'sha256': 'b17f658e543b48dd09863e5d538d33da22ab77078b12385ef5f26046e6ea4f54'}, 'includeBytes1': {'path': 'artifacts/th14/worker-timeline-includes-v2-oct15/run/decoded-1.bin', 'bytes': 10064, 'sha256': '83514fe968ed0398e07f71f703c250ba98fd5514ba662765eeb9c1987ea6ed8a'}, 'includeBytes2': {'path': 'artifacts/th14/worker-timeline-includes-v2-oct15/run/decoded-2.bin', 'bytes': 27956, 'sha256': '37992e7f4d56ff6d744267bdab14615e5f4e8ea355822865b196dca0c5d06372'}, 'firstFramePlan': {'path': 'artifacts/th14/main-after-worker-frame-checkpoint-oct15/plan.json', 'bytes': 2405, 'sha256': 'e0d8c1670eddc786832262829c319672bc158c3e49cfd1f5163ccb7d10f25af2'}, 'firstFrameLocks': {'path': 'artifacts/th14/main-after-worker-frame-checkpoint-oct15/main_locks.py', 'bytes': 1451, 'sha256': '144beb42e90b075ea3118be739abf500fed50231c042c2233632a80fdf67306e'}, 'firstFrameCheckpointHelper': {'path': 'artifacts/th14/main-after-worker-frame-checkpoint-oct15/checkpoint.py', 'bytes': 8125, 'sha256': '348e6cb4ef52cf3dc26b8664f6a534504405bfa89108e0a15c68d15c243692c6'}, 'firstFrameWorker': {'path': 'artifacts/th14/main-after-worker-frame-checkpoint-oct15/cooperative_worker.py', 'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'secondFramePlan': {'path': 'artifacts/th14/main-stage2-input-none-oct15/plan.json', 'bytes': 3733, 'sha256': '0cdc929366e88ca51724af3cf667950d15a88695729d027a2f35aec26c4edb13'}, 'secondFrameLocks': {'path': 'artifacts/th14/main-stage2-input-none-oct15/main_locks.py', 'bytes': 1451, 'sha256': '144beb42e90b075ea3118be739abf500fed50231c042c2233632a80fdf67306e'}, 'secondFrameCheckpointHelper': {'path': 'artifacts/th14/main-stage2-input-none-oct15/checkpoint.py', 'bytes': 8125, 'sha256': '348e6cb4ef52cf3dc26b8664f6a534504405bfa89108e0a15c68d15c243692c6'}, 'secondFrameWorker': {'path': 'artifacts/th14/main-stage2-input-none-oct15/cooperative_worker.py', 'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'secondFrameAudio': {'path': 'artifacts/th14/main-stage2-input-none-oct15/silent_audio.py', 'bytes': 2130, 'sha256': '3969290b1fb8e5ab1c67337648538e48de8bd188a0e397fd29b80ccebdfa0e42'}}


def read(name):
    row = BINDINGS[name]
    path = (ROOT / row['path']).resolve()
    assert path.is_relative_to(ROOT) and not path.is_symlink()
    raw = path.read_bytes()
    assert len(raw) == row['bytes'] and SHA(raw) == row['sha256'], name
    return raw


def document(name):
    return json.loads(read(name))


def check_manifest(name, expected_pc):
    raw = read(name)
    state = json.loads(raw)
    base = (ROOT / BINDINGS[name]['path']).parent
    assert state['mainPausedAt'] == expected_pc
    total = 0
    for row in state['regions']:
        target = (base / row['path']).resolve()
        assert target.is_relative_to(base.resolve()) and not target.is_symlink()
        digest = hashlib.sha256()
        count = 0
        with target.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                count += len(block)
                digest.update(block)
        assert count == row['bytes'] and digest.hexdigest() == row['sha256']
        total += count
    for row in state['contexts'].values():
        target = (base / row['path']).resolve()
        assert target.is_relative_to(base.resolve()) and not target.is_symlink()
        context = target.read_bytes()
        assert len(context) == row['bytes'] and SHA(context) == row['sha256']
    assert total == state['totalGuestRamBytes']
    assert state['contexts']['main']['observedRegisters']['EIP'] == expected_pc
    assert state['workerFiberSlot5'] == 0
    assert state['ptd'] not in {key for key, _ in state['heap']['live']}
    assert state['originalWorkerSummary']['stop']['names'] == ['KERNEL32.dll!ExitThread']
    assert not state['completeGame'] and not state['nativeEquivalent']
    return dict(manifestSha256=SHA(raw), regions=len(state['regions']),
                fullRamBytesRehashed=total, bothSerializedContextsRehashed=True,
                mainPausedAt=hex(expected_pc), workerExitThreadStillUnserviced=True)


def main():
    assert sys.argv[1:] in ([], ['--write-summary'])
    assert BINDINGS
    for name in BINDINGS:
        read(name)
    rt = ROOT / 'runtimes/th12/th12_web'
    build = document('productionBuild')
    for name, expected in build['sourceHashes'].items():
        assert SHA((rt / name).read_bytes()) == expected, name
    object_hashes = {Path(row['path']).resolve(): row['sha256'] for row in build['outputs']}
    sources = document('objectNames')['sources']
    assert len(sources) == 141 and len(build['sourceHashes']) == 267
    object_dir = ROOT / 'artifacts/th14/screen-camera-production-build-oct14/engine/objects'
    for source in sources:
        path = (object_dir / (source.replace('/', '_') + '.o')).resolve()
        assert SHA(path.read_bytes()) == object_hashes[path]

    comparison_rows = []
    for case, templates, sprites, chunks, words in [('enemy', 147, 160, 3, 10221), ('stageEnemy', 32, 48, 16, 2452)]:
        report = document(case + 'Comparison')
        expected = document(case + 'Expected')
        assert report['passed'] and report['differences'] == []
        assert report['comparedWords'] == words == templates * 51 + sprites * 17 + 4
        assert (report['templates'], report['sprites'], report['chunks']) == (templates, sprites, chunks)
        assert report['expectedSha256'] == SHA(read(case + 'Expected'))
        assert report['fixtureSha256'] == SHA(read(case + 'Fixture'))
        assert report['wasmSha256'] == SHA(read(case + 'Wasm'))
        assert report['toolSha256'] == SHA(read(case + 'CheckSource'))
        assert report['baseBuildSha256'] == SHA(read('productionBuild'))
        assert report['nativeInputs'] == expected['nativeInputs']
        assert not report['physicalGraphicsSuccessMeasured'] and not report['ordinaryMainFramesMatched']
        assert not report['completeGame'] and not report['nativeEquivalent']
        comparison_rows.append(dict(resource='enemy.anm' if case == 'enemy' else 'st02enm.anm',
            templates=templates, sprites=sprites, chunks=chunks, selectedWords=words,
            differingWords=0, spriteOwnerChecks=templates,
            halfResolutionDescriptorAdapter=(case == 'stageEnemy'),
            physicalGpuOrWholeVmEquality=False))

    pump = document('stageEnemyHelper')
    assert pump['sourceSha256'] == SHA(read('stageEnemyHelperSource'))
    assert pump['planSha256'] == SHA(read('stageEnemyHelperPlan'))
    assert [row['pending'] for row in pump['helperReturns']] == list(range(2, 17)) + [0]
    assert pump['filePendingAfter'] == 0 and len(pump['cpuTextureChunks']) == 16
    assert pump['templateSha256'] == SHA(read('stageEnemyTemplates'))
    assert pump['cpuTextureResultsAreDeclared'] and not pump['actualGraphicsDeviceInvoked']
    decoded = document('includeRun')
    assert decoded['sourceSha256'] == SHA(read('includeSource'))
    assert [row['name'] for row in decoded['decodedResourceReturns']] == ['default.ecl', 'st02mbs.ecl', 'st02bs.ecl']
    archive = document('independentExtraction')
    include_rows = []
    for index, row in enumerate(decoded['decodedResourceReturns']):
        native = read('includeBytes' + str(index))
        separate = (Path(archive['extraction']) / row['name']).read_bytes()
        assert native == separate and len(native) == row['bytes'] and SHA(native) == row['sha256']
        include_rows.append(dict(name=row['name'], bytes=len(native), sha256=SHA(native), differingBytes=0))
    stage_native = read('stageEnemyDecoded')
    assert stage_native == read('stageEnemySourceAnm')
    assert stage_native == (Path(archive['extraction']) / 'st02enm.anm').read_bytes()

    callback = document('callbackRun')
    assert callback['sourceSha256'] == SHA(read('callbackSource'))
    assert callback['originalResourceCallbackReturned'] and not callback['actualThreadExited']
    assert callback['worker']['stop']['pc'] == '0x485a99'
    assert callback['worker']['workerContext']['EAX'] == 0
    assert [(row['pc'], row['address'], row['value']) for row in callback['originalOwnerCompletionWrites']] == [
        ('0x436067', '0x4d98fc', 0), ('0x436071', '0x4d98f8', 1)]
    assert callback['originalCompletionFieldsAtStop'] == [1, 0]
    crt = document('crtRun')
    assert crt['sourceSha256'] == SHA(read('crtSource'))
    assert crt['originalCrtExitThreadRequested'] and not crt['actualThreadExited']
    assert crt['worker']['stop']['caller'] == '0x485aec' and crt['worker']['stop']['firstArgument'] == 0
    assert crt['finalWorkerSlot5'] == 0
    assert [row['kind'] for row in crt['declaredFlsCalls']] == ['DECLARED_NEW_FIBER_FLS_GET', 'ORIGINAL_CRT_REQUESTED_DECLARED_FLS_CLEAR']
    assert [(row['pointer'], row['bytes']) for row in crt['declaredHeapCalls']] == [(0x3004b390, 0x3c0)]
    assert len(crt['declaredLockCalls']) == 4
    assert [row['enter'] for row in crt['declaredLockCalls']] == [True, False, True, False]

    frames = []
    for case, row_index in [('firstFrame', 9669), ('secondFrame', 9670)]:
        report = document(case + 'Run')
        assert report['sourceSha256'] == SHA(read(case + 'Source'))
        assert report['originalMainFrameReturned'] and report['stop']['kind'] == 'ORIGINAL_MAIN_FRAME_RETURNED'
        assert report['stop']['registers']['EIP'] == 0x469a56 and report['stop']['registers']['EAX'] == 0
        assert len(report['playerRows']) == 1 and report['playerRows'][0]['index'] == row_index
        assert report['playerRows'][0]['selection'][3] == 2
        assert sum(row['name'] == 'IDirect3DDevice9.Present' for row in report['existingNoOutputGpuEvents']) == 1
        assert all(not row['additionalWorkerTimeAdded'] and not row['nativeElapsedTimeMeasured'] for row in report['declaredClockCalls'])
        assert not report['actualAudioPlayed'] and not report['completeGame'] and not report['nativeEquivalent']
        frames.append(dict(beforePlayerIndex=row_index, beforePlayerStageFrame=report['playerRows'][0]['stageFrame'],
            codeHookObservations=report['observations'], gpuBoundaryCommands=len(report['existingNoOutputGpuEvents']),
            declaredMainLockRequests=len(report['declaredMainLocks']), declaredQpcCalls=len(report['declaredClockCalls']),
            actualGpuOrAudio=False, cppWholeFrameComparison=False))
    assert document('secondFrameRun')['frameReturns'] == [
        dict(invocation=0, presents=0, playerRows=0, eax=0),
        dict(invocation=1, presents=1, playerRows=1, eax=0)]
    final_checkpoint = check_manifest('finalCheckpoint', 0x469a56)
    runtime = document('finalRuntime')['declaredMainResume']
    assert runtime['presentCount'] == 9671 and runtime['returnedWithoutPresent'] == 1814
    assert runtime['totalPlayerRows'] == 9671
    result = dict(storedEvidenceVerified=True, completeGame=False, nativeEquivalent=False,
        currentProductionGameSourcesBound=267, currentProductionObjectsBound=141,
        comparisons=comparison_rows, independentlyComparedIncludes=include_rows,
        independentlyComparedIncludeBytes=sum(row['bytes'] for row in include_rows),
        independentlyComparedStageEnemyBytes=len(stage_native), originalSuccessCompletionWritesObserved=True,
        originalResourceCallbackReturnObserved=True, originalCrtExitThreadRequestObserved=True,
        physicalExitThreadServiced=False, returnedMainFrames=frames, finalCheckpoint=final_checkpoint,
        actualAudioPlayed=False, ordinaryBrowserStageTransitionVerified=False,
        sourceImplementationChangedInThisEvidenceIncrement=False,
        bindings=BINDINGS, verifierSha256=SHA(Path(__file__).read_bytes()),
        scope='Stored proof verification only. Original guest code continues from the reproduced9669-row warm Replay prefix with declared independent worker FLS, bounded owned heap/lock/read-only archive and relative wait services. Original main helpers use declared CPU textures; the two main-frame continuations reuse existing no-output GPU, stopped audio, absent physical input and60Hz clock services. The callback returns success and CRT requests ExitThread0, but the physical OS thread/API, concurrent clocks, complete VM/owner memory, current C++ whole-frame equality, actual GPU/audio, browser later-stage flow and whole-game1:1 remain unverified. Full RAM/context and original resources remain private. Prior failed fixture assumptions and idle-clock bookkeeping attempt remain preserved locally.')
    if sys.argv[1:]:
        with SUMMARY.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(dict(storedEvidenceVerified=True, comparedWords=sum(row['selectedWords'] for row in comparison_rows),
        includeBytes=result['independentlyComparedIncludeBytes'], returnedMainFrames=2,
        fullRamBytesRehashed=final_checkpoint['fullRamBytesRehashed'], completeGame=False)))


if __name__ == '__main__':
    main()
