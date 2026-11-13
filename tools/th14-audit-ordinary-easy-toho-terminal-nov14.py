"""Compare a current early endpoint with retained native replay evidence.

This is a terminal gameplay comparison, not whole-trace or ordinary native UI acceptance.
"""
from pathlib import Path
import hashlib, json, struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-difficulties-nov14'
N = R / 'artifacts/th14/mode-coverage-oct29/marisaa-easy-toho-native'
A = H / 'marisaa-easy-full-alternate-v2'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
n, a = load(N / 'report.json'), load(A / 'report.json')
manifest_path = R / 'artifacts/th14/native-campaign-assets/57d84a5cbe82-b1d9e367e7e5/manifest.json'
manifest = load(manifest_path)
assert sha(manifest_path) == n['referenceArchiveManifestSha256']
assert manifest['changedEntries'] == ['demo0.rpy']
assert n['sourceFullReplaySha256'] == manifest['replaySha256'] == load(A / 'plan.json')['sourceReplaySha256']
assert n['sourceFullReplaySha256'] == sha(R / 'artifacts/th14/mode-coverage-oct29/marisaa-easy-toho/th14_ud0925.rpy')
assert n['executableSha256'] == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert n['childExited'] and not n['error'] and n['observedForcedReplayEndMenu']
assert n['configuredMusicAndSoundVolumeZero'] and n['rngOrCounterWrites'] == n['instructionBytesPatched'] == 0
assert n['gameStateWordWrites'] == 1 and n['caseInitialization']['attractBitClearOnly']
assert not n['caseInitialization']['gameplayRngOrHealthOrInputOrCounterWrites']
assert sha(N / 'observer-source.py') == n['sourceSha256']
assert a['retired'] and not a['exception'] and not a['passed'] and a['outcome'] == 'natural-game-over'
assert not load(A / 'platform.json')['audibleOutput']
data = (N / 'selected-state.u32').read_bytes()
assert len(data) == n['callbacks'] * 128 and sha(N / 'selected-state.u32') == n['selectedSha256']
native = struct.unpack('<32I', data[-128:])
tape = load(A / 'observations-summary.json')
current = tape['last'][1:32]  # Current observer additionally prefixes the callback index.
indices = list(range(21)) + list(range(25, 31))
assert all(native[i] == current[i] for i in indices)
terminal = n['terminalMenuSamples'][-1]
assert [terminal['stage'], terminal['controlFrame'], terminal['score'], terminal['lives'], terminal['lifeState']] == [5, 7565, 26014792, 0xffffffff, 2]
result = dict(passed=True, limitedTerminalGameplayComparison=True,
              terminalGameplayWordsCompared=len(indices), terminalGameplayWordsDifferent=0,
              stage=5, controlFrame=7565, score=260147920, lives=-1, lifeState=2,
              nativeCallbacks=n['callbacks'], ordinaryCallbacks=tape['callbacks'],
              nativeInstructionBytesPatched=0, nativeAttractFlagClearedAsDeclared=True,
              nativeGameplayRngHealthOrCounterWrites=False, nativeReplayDemoInputReplacedOnly=True,
              currentMode='ordinary', referenceMode='declared-warm-replay',
              callbackTimingOrWholeTraceAccepted=False, originalOrdinaryUiAccepted=False,
              clearAccepted=False, completeGame=False,
              evidence={p.relative_to(R).as_posix(): sha(p) for p in [manifest_path, N / 'report.json',
                        N / 'selected-state.u32', A / 'report.json', A / 'observations-summary.json']})
existing_path = R / 'artifacts/th14/behavior-application-nov13/marisaa-easy-existing-native-comparison.json'
existing = load(existing_path)
monster = H / 'marisaa-easy-full-monster-v3'
monster_report, monster_tape = load(monster / 'report.json'), load(monster / 'observations-summary.json')
primary_input = R / 'artifacts/th14/royalflare-coverage-matrix-oct16/inputs/marisaa-easy.rpy'
assert sha(primary_input) == existing['inputSha256'] == load(monster / 'plan.json')['sourceReplaySha256']
assert existing['nativeSelectedHashVerified'] and existing['nativeAlsoEndedEarly']
assert not monster_report['passed'] and monster_report['retired'] and not monster_report['exception']
assert monster_report['outcome'] == 'natural-game-over'
monster_current = monster_tape['last'][1:32]
assert all(existing['nativeFinalPlayerRow'][i] == monster_current[i] for i in indices)
result['monsterTerminal'] = dict(sameInputAsPrimaryCoverage=True,
    reusedPreviouslyHashVerifiedNativeTerminal=True, terminalGameplayWordsCompared=len(indices),
    terminalGameplayWordsDifferent=0, stage=monster_current[30], controlFrame=monster_current[0],
    score=monster_current[12] * 10, nativeCallbacks=existing['nativeCallbacks'],
    ordinaryCallbacks=monster_tape['callbacks'], originalReferenceDiagnosticTiming=True,
    ordinaryNativeUiOrWholeTraceAccepted=False, clearAccepted=False)
for p in [existing_path, monster / 'report.json', monster / 'observations-summary.json']:
    result['evidence'][p.relative_to(R).as_posix()] = sha(p)
(H / 'toho-terminal-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
