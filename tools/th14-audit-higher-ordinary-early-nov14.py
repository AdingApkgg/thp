"""Retain differences against existing native replay terminals without normalizing them."""
from pathlib import Path
import hashlib, json, struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-difficulties-nov14'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
cases = [
    ('marisaa-hard', 'retail-marisaa-hard-callback-rng-hardware-oct26',
     'd95704789da54f5c66c94106b2b9a626ab5ec89cb4ffdad6d06a606ff7c51b7b'),
    ('marisab-lunatic', 'retail-marisab-lunatic-exit-boundary-hardware-oct26',
     '5b5792fcecbab5c3fca8e94fb0b1ec7752e0122ce9e53404bb7a9ebaaa0ff9fb')]
indices = list(range(21)) + list(range(25, 31))
rows = []
for key, directory, report_hash in cases:
    n = R / 'artifacts/th14' / directory
    a = H / (key + '-full-v2')
    nr, cr = load(n / 'report.json'), load(a / 'report.json')
    assert sha(n / 'report.json') == report_hash
    assert nr['childExited'] and not nr['error'] and nr['observedForcedReplayEndMenu']
    assert nr['instructionBytesPatched'] == nr['rngOrCounterWrites'] == 0
    assert nr['configuredMusicAndSoundVolumeZero']
    assert sha(n / 'observer-source.py') == nr['sourceSha256']
    assert cr['retired'] and not cr['passed'] and not cr['exception']
    assert cr['outcome'] == 'natural-game-over' and cr['noRngStateWrites']
    assert nr['sourceFullReplaySha256'] == load(a / 'plan.json')['sourceReplaySha256']
    assert not load(a / 'platform.json')['audibleOutput']
    raw = (n / 'selected-state.u32').read_bytes()
    assert len(raw) == nr['callbacks'] * 128 and sha(n / 'selected-state.u32') == nr['selectedSha256']
    native = list(struct.unpack('<32I', raw[-128:]))
    tape = load(a / 'observations-summary.json')
    current = tape['last'][1:32]
    differences = [dict(field=i, native=native[i], ordinary=current[i])
                   for i in indices if native[i] != current[i]]
    rows.append(dict(key=key, sourceReplaySha256=nr['sourceFullReplaySha256'],
        originalAlsoEndedEarly=True, currentClearAccepted=False,
        originalMode='diagnostic replay', currentMode='ordinary',
        sameOriginalOrdinaryStartupAndTimeline=False, wholeTraceCompared=False,
        nativeCallbacks=nr['callbacks'], ordinaryCallbacks=tape['callbacks'],
        nativeTerminalSelected32=native, ordinaryTerminalSelected31=current,
        terminalGameplayFieldsCompared=len(indices), differentTerminalFields=differences,
        allTerminalGameplayFieldsEqual=not differences, diagnosticsRetained=True,
        productionDefectCauseEstablished=False, silent=True, completeGame=False,
        evidence={p.relative_to(R).as_posix(): sha(p) for p in [n / 'report.json',
                  n / 'selected-state.u32', a / 'report.json', a / 'observations-summary.json']}))
(H / 'higher-early-native-audit.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps([dict(key=r['key'], differentTerminalFields=r['differentTerminalFields'],
                       currentClearAccepted=False) for r in rows]))
