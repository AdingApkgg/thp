"""Read frozen loading observations; do not run Native, replay or game code."""
import hashlib
import importlib
import json
import struct
import sys
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/th14/staged-loader-host-clock-audit-oct14'
DOC = ROOT / 'docs/porting/th14-staged-loader-host-clock-observed-oct14.json'
BINDINGS = {}


def bind(name, digest=None, size=None):
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT) or path == Path('H:/Games/th/14/th14.exe').resolve()
    key = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
    if key not in BINDINGS:
        with path.open('rb') as stream:
            h = hashlib.file_digest(stream, 'sha256').hexdigest()
        BINDINGS[key] = {'bytes':path.stat().st_size, 'sha256':h}
    assert digest is None or BINDINGS[key]['sha256'] == digest, key
    assert size is None or BINDINGS[key]['bytes'] == size, key
    return BINDINGS[key]


def load(name, digest=None):
    bind(name, digest)
    path = Path(name)
    return json.loads((path if path.is_absolute() else ROOT / path).read_text(encoding='utf-8-sig'))


def location(name, token):
    bind(name)
    lines = (ROOT / name).read_text(encoding='utf-8-sig').splitlines()
    found = [index + 1 for index, line in enumerate(lines) if token in line]
    assert found, (name, token)
    return {'path':name, 'lines':found, 'token':token}


def main():
    assert not DOC.exists(), 'Preserve completed audit'
    OUT.mkdir(parents=True, exist_ok=True)
    checkpoint = load('docs/porting/th14-staged-loader-current-checkpoint-oct14.json', '85ac83a9a8abd950ca4beffb4a907771e1863735fa750c5e9bc43b47caa58cb2')
    native_home = ROOT / 'artifacts/th14/native-zps-reimua-lunatic-full-oct14'
    native = load(native_home / 'reference.compact.json', '81178393c3e9bb952c59a2d2cedcf456e7bf9f7d1651062986b7d282e97349fb')
    receipt = load(native_home / 'reference.compact.compact-receipt.json')
    assert receipt['allValuesEqual'] and receipt['frames'] == native['capturedFrames'] == 90793
    bind(receipt['source'], receipt['sourceSha256'], receipt['sourceBytes'])
    bind('tools/th14-native-trace-compact.py', receipt['toolSha256'])
    manifest = load(native_home / 'manifest.json')
    bind(native_home / 'memory.bin.gz', manifest['memorySha256'])
    assert native['error'] == '' and native['rngWrites'] == [] and native['events'] == []
    assert native['captureToolSha256'] == manifest['captureToolSha256']
    for name, key in [('th14-native-session-capture.py', 'captureToolSha256'), ('th14-native-stored-bootstrap-capture.py', 'warmReplayCaptureToolSha256')]:
        bind(ROOT / 'tools' / name, native[key])
    assert 'clockHost' not in native and 'controlledHostCalls' not in native
    assert not any(set(row).intersection({'timestamp', 'qpc', 'clockNs', 'wallTime', 'sleepEntry', 'sleepReturn'}) for row in native['frames'])
    configuration = bytes.fromhex(native['configurationHex'])
    assert configuration[0x22:0x24] == b'\0\0'

    home = ROOT / 'artifacts/th14/staged-loader-production-playback/reimua-lunatic-staged-loader-oct14'
    production = load(home / 'report.json')
    assert production['sourceHashes'] == checkpoint['sourceHashes'] and production['frames'] == 90793
    raw_path = home / 'selected-state.u32'
    bind(raw_path, production['selectedStateSha256'])
    raw = raw_path.read_bytes()
    active_path = home / 'callback-active.u8'
    bind(active_path, production['callbackActiveSha256'])
    active = active_path.read_bytes()
    object_home = ROOT / 'artifacts/th14/staged-loader-production-objects/reimua-lunatic-oct14'
    object_report = load(object_home / 'report.json')
    detail_path = object_home / 'portable-details.json'
    bind(detail_path, object_report['rawDetailSha256'])
    details = json.loads(detail_path.read_text())
    assert len(details) == len(native['frames']) == len(active) == len(raw) // 128
    word = lambda index, column: struct.unpack_from('<I', raw, index * 128 + column * 4)[0]
    sample_ns = lambda index: (index + 1) * 1_000_000_000 // 60
    windows = []
    observations = []
    for stage in range(2, 7):
        first = next(i for i, row in enumerate(native['frames']) if row['selection'][3] == stage and row['stageFrame'] == 0)
        end = next(i for i in range(first, len(active)) if native['frames'][i]['stageFrame'] != 0)
        assert word(first, 30) == stage and word(first, 0) == 0 and not active[first]
        native_rng = next(i for i in range(first, end) if native['frames'][i]['replayRng'][2] == 0)
        portable_rng = next(i for i in range(first, end) if word(i, 24) == 0)
        native_id = next(i for i in range(first, end) if native['frames'][i]['enemyNextId'] >= 1)
        portable_id = next(i for i in range(first, end) if details[i]['enemyNextId'] >= 1)
        native_prior = native['frames'][first]['replayRng'][2]
        rng_mismatches = [i for i in range(first, end) if native['frames'][i]['replayRng'][2] != word(i, 24)]
        id_mismatches = [i for i in range(first, end) if native['frames'][i]['enemyNextId'] != details[i]['enemyNextId']]
        assert rng_mismatches == list(range(portable_rng, native_rng))
        assert id_mismatches == list(range(portable_id, native_id))
        # The request is handled after the preceding before-Player observation.
        # This formula is the actual fixture's declared clock, not a Native time.
        request_sample = sample_ns(first - 1)
        deadline = request_sample + 60_000_000
        earliest_sample = next(i for i in range(first, end) if sample_ns(i) >= deadline)
        assert portable_rng == earliest_sample
        windows.append({'stage':stage, 'firstLoadingCallback':first, 'firstNonzeroControlCallback':end,
          'nativeFirstZeroRngCountCallback':native_rng, 'productionFirstZeroRngCountCallback':portable_rng,
          'nativeFirstPositiveNextIdCallback':native_id, 'productionFirstPositiveNextIdCallback':portable_id,
          'rngDifferenceCallbackIndices':rng_mismatches, 'nextIdDifferenceCallbackIndices':id_mismatches,
          'nativePriorRngCalls':native_prior, 'declaredProductionRequestClockNs':request_sample,
          'declaredProductionDeadlineNs':deadline, 'declaredProductionFirstReadySampleNs':sample_ns(portable_rng),
          'declaredProductionPreviousSampleNs':sample_ns(portable_rng - 1),
          'nativeClockNs':None, 'nativeSleepEntryReturnRecorded':False,
          'scope':'Actual ordinal observations only. Positive nextId is not an independently captured raw owner pointer. No Native timestamp or fixed callback duration is inferred.'})
        for i in range(first - 1, max(native_rng, native_id, portable_rng, portable_id) + 2):
            observations.append({'index':i, 'stage':native['frames'][i]['selection'][3],
              'stageFrame':native['frames'][i]['stageFrame'], 'nativeGameplayCalls':native['frames'][i]['replayRng'][2],
              'productionGameplayCalls':word(i, 24), 'nativeNextId':native['frames'][i]['enemyNextId'],
              'productionNextId':details[i]['enemyNextId'], 'productionActive':active[i],
              'declaredProductionClockNs':sample_ns(i), 'nativeClockNs':None})
    assert sum(len(w['rngDifferenceCallbackIndices']) for w in windows) == 10
    assert sum(len(w['nextIdDifferenceCallbackIndices']) for w in windows) == 57
    observed_path = OUT / 'loading-callback-observations.json'
    observed_bytes = (json.dumps(observations, separators=(',', ':')) + '\n').encode()
    if observed_path.exists():
        assert json.loads(observed_path.read_bytes()) == observations
    else:
        observed_path.write_bytes(observed_bytes)
    bind(observed_path)

    historical = load('docs/porting/th14-native-bootstrap-verified-oct13.json')
    host_receipts = []
    for item in historical['bindings']:
        if not item['path'].endswith('/receipt.json'):
            continue
        host = load(item['path'], item['sha256'])
        provider = 'artifacts/th14/native-bootstrap-provider-d084-oct13/th14-native-bootstrap-run.py'
        bind(provider, host['sourceSha256'])
        assert host['clockHost']['enabled'] and host['clockHost']['completedPresents'] == 511
        assert host['prefixCapture']['capturedFrames'] == 512
        assert not any('Sleep' in key or 'CreateThread' in key for key in host['hostCallSummary']['counts'])
        host_receipts.append({'path':item['path'], 'providerSha256':host['sourceSha256'], 'clockHost':host['clockHost'],
          'heapHost':host['heapHost'], 'hostCallSummary':host['hostCallSummary'],
          'scope':'Frozen512 initial-stage emulator prefix: serialized locks, bounded heap, fixed QPC and command-only GPU. It contains no next-stage Sleep/worker observation and is not the full90793 retail-child oracle.'})

    sys.path.insert(0, str(ROOT / 'tools'))
    image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    bind('H:/Games/th/14/th14.exe', native['executableSha256'])
    bind('tools/th12-pe.py')
    disassembler = Cs(CS_ARCH_X86, CS_MODE_32)
    instructions = []
    for first, last in [(0x436560,0x4365df), (0x435ab0,0x435b42), (0x435f32,0x435f6f), (0x4228d0,0x422905)]:
        for ins in disassembler.disasm(image.read(first, last-first), first):
            instructions.append({'address':hex(ins.address), 'bytes':ins.bytes.hex(), 'mnemonic':ins.mnemonic, 'operands':ins.op_str})
    for name in ['th14-staged-loader-wait-predicate-verified-oct14.json', 'th14-staged-loader-host-boundary-verified-oct14.json']:
        evidence = load(DOC.parent / name)
        assert evidence['actualRetailProcessesStarted'] == 0
        bind(ROOT / 'tools' / ('th14-staged-loader-wait-predicate-check.py' if 'wait-predicate' in name else 'th14-staged-loader-host-boundary-evidence-check.py'), evidence['verifierSha256'])

    source_locations = [
      location('tools/th14-native-session-capture.py', 'checked(k.ContinueDebugEvent'),
      location('tools/th14-native-session-capture.py', "report['frames'].append(row)"),
      location('tools/th14-native-session-capture.py', "report['elapsedSeconds']"),
      location('tools/th14-staged-loader-production-replay-check.mjs', 'c.production_clock_set'),
      location('runtimes/th12/th12_web/cpp/game/GameSession.cpp', 'pump_stage_loading(stage_load_clock()'),
      location('runtimes/th12/th12_web/cpp/game/StagedLoaderPrototype.hpp', 'deadline=now+minimum'),
      location('runtimes/th12/th12_web/cpp/game/StagedLoaderPrototype.hpp', 'actions.prepare_scene()'),
      location('runtimes/th12/th12_web/cpp/sdl/Application.cpp', 'SDL_GetTicksNS'),
      location('runtimes/th12/th12_web/cpp/sdl/Application.cpp', 'stage_uploads.advance'),
    ]
    plan = {'prepared':True, 'executed':False, 'noNativeProcessStart':True,
      'experiment':'Timestamp one original next-stage worker and the corresponding Player boundaries, without deriving schedule from the observed5/15/etc windows.',
      'requiredEvents':[{'address':'0x4365c5','event':'main-thread loader launch request'},
        {'address':'0x435ab0','event':'worker entry and first-slot read'},
        {'address':'0x435b0f','event':'Sleep60 call entry'}, {'address':'0x435b11','event':'Sleep60 returned'},
        {'address':'0x435f32','event':'Replay initialization call'}, {'address':'0x435f3d','event':'HUD load call'},
        {'address':'0x435f4b','event':'Stage load call'}, {'address':'0x435f66','event':'Enemy constructor call'},
        {'address':'0x4228de','event':'owner publication store'}, {'address':'0x4228e4','event':'nextId1 store'},
        {'address':'0x44dbd0','event':'Player entry'}],
      'recordForEveryEvent':['threadId','eventOrdinal','externalMonotonicTimestamp','debuggerStopAndResumeTimestamps','mainCallbackOrdinal','firstCaptureFile','SupervisorFlags'],
      'requiredHostFacts':['actual Sleep entry/return, no fabricated return', 'actual allocator and CPU decode interval',
        'actual graphics preparation calls/completions', 'same monotonic domain for main and worker timestamps'],
      'boundedOriginalAlternative':'Existing unmodified guard/Replay prefix units establish call requests and stores only. A same-clock complete worker experiment cannot be claimed from these because Sleep/Win32 thread/D3D/resource host completions were not executed or recorded.',
      'portableCompanion':'Use generic externally scheduled phase events with the same explicit monotonic clock; never feed Native captured5/15/etc callback windows or returned values into production.',
      'futureChildPrerequisite':'Only an explicitly permitted private original child may run; prove its private config music/effects bytes0x22/0x23 are both0 before launch, and leave H:/Games user config/save untouched.'}
    plan_path = OUT / 'bounded-worker-experiment-plan.json'
    plan_path.write_text(json.dumps(plan, indent=2) + '\n')
    bind(plan_path)
    bind(OUT / 'attempt01-report-path-failure/audit.py')
    bind(OUT / 'attempt01-report-path-failure/failure.json')
    bind(OUT / 'attempt02-newline-failure/audit.py')
    bind(OUT / 'attempt02-newline-failure/failure.json')
    result = {'loadingHostClockAuditVerified':True, 'productionChanged':False, 'nativeEquivalent':False, 'completeGame':False,
      'actualRetailProcessesStarted':0, 'replayCallbacksExecuted':0, 'originalInstructionExecutionPerformed':False,
      'productionCoreFiles':267, 'loadingWindows':windows, 'rngDifferencesRetained':10, 'nextIdDifferencesRetained':57,
      'fullDetailDifferencesRemain':65, 'actualNativeCapture':{'kind':'Real hidden retail child with debugger before-Player snapshots',
        'capturedCallbacks':90793, 'aggregateElapsedSeconds':native['elapsedSeconds'], 'perCallbackOrWorkerTimestamps':False,
        'controlledHostClock':False, 'musicEffectsConfigurationBytes':list(configuration[0x22:0x24]),
        'caseInitialization':native['caseInitialization'], 'scope':native['scope']},
      'separateControlledHostPrefixes':host_receipts, 'originalInstructions':instructions, 'sourceLocations':source_locations,
      'provenDifferences':['Current fixture samples one exact60Hz monotonic value per whole game callback. Its CPU/headless-ready phases run under that same unchanged clock sample.',
        'Original worker explicitly requests Sleep60 only after its real first copy slot becomes negative; Replay reset precedes HUD/Stage work and owner publication precedes ECL parse.',
        'The long Native oracle has real OS threads/API/resource work and debugger stops, but records only callback-state changes, not worker/Sleep elapsed intervals.',
        'The512 prefix controlled QPC/heap/GPU host receipts do not contain the cross-stage worker; their command model cannot be promoted into the90793 Native timing domain.'],
      'notProven':['Which OS scheduling, debugger stop, allocator or GPU interval accounts for each remaining2-callback reset difference.',
        'A constant extra wait or phase frame count corresponding to57 nextId differences.',
        'Raw owner-pointer lifetime or complete Native wall-clock equivalence from nextId observations alone.'],
      'nextIndependentExperiment':plan,
      'officialReferences':['https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-sleep',
        'https://learn.microsoft.com/en-us/windows/win32/debug/debugging-events'],
      'bindings':BINDINGS, 'bindingCount':len(BINDINGS), 'toolSha256':bind(Path(__file__))['sha256'],
      'scope':'Read-only original bytes and bounded windows extracted from existing frozen traces, never a new90793-frame run. Declared production ns are not Native timestamps. No window fitting, reseeding, masks, simulated Native Sleep/allocator/GPU results or production changes. The real controlled-worker timing experiment is prepared, not executed; original game execution remains forbidden for this task.'}
    result['bindingCount'] = len(BINDINGS)
    DOC.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'auditVerified':True, 'windows':len(windows), 'rngDifferences':10, 'nextIdDifferences':57,
      'bindings':len(BINDINGS), 'report':DOC.relative_to(ROOT).as_posix(), 'sha256':bind(DOC)['sha256']}))


if __name__ == '__main__':
    main()
