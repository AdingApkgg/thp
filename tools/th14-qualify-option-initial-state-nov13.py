"""Bind the narrow option initialization fix without claiming full-game parity."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import os

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/option-refresh-oracle-nov13'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
bindings = {}

def read(name):
    path = H / name
    bindings[path.relative_to(R).as_posix()] = sha(path)
    return json.loads(path.read_bytes())

native = read('native.json')
baseline = read('result.json')
candidate = read('candidate-result.json')
edit = read('candidate-edits.json')
provider = read('candidate-providers/build.json')
component = read('candidate-component/build.json')
controls = read('other-title-controls/result.json')
retained = read('retained-shot-inputs.json')
assert native['actualFullConstructor'] and native['actualFullInitialize']
assert native['graphicsOrAudioDevicesOpened'] == 0
assert len(native['rows']) == 6
assert not baseline['passed'] and baseline['differentWords'] == 1056
assert (candidate['selections'], candidate['steps'], candidate['comparedWords'],
        candidate['differentWords']) == (6, 90, 183060, 0)
assert candidate['passed'] and candidate['normalAccessControl']
assert candidate['platformCalls'] == 0 and controls['passed']
assert len(controls['pairs']) == 3 and all(p['identical'] for p in controls['pairs'])
assert sha(H / 'baseline-PlayerFrame.cpp') == edit['beforeSha256']
assert sha(R / edit['path']) == edit['afterSha256']
for name, digest in provider['sourceBindings'].items():
    assert sha(R / name) == digest, name
for name, digest in component['objectBindings'].items():
    assert sha(R / name) == digest, name
assert sha(H / 'candidate-component/probe.wasm') == component['wasmSha256']
assert candidate['bindings']['native'] == sha(H / 'native.json')
assert candidate['bindings']['build'] == sha(H / 'candidate-component/build.json')
assert candidate['bindings']['runner'] == sha(R / 'tools/th14-run-option-initial-state-candidate-nov13.mjs')
assert native['toolSha256'] == sha(R / 'tools/th14-option-refresh-native-nov13.py')
assert provider['gameUnitsCompiled'] == 1 and provider['gameObjectsReused'] == 140
fields = Counter(d['field'] for row in baseline['rows'] for d in row['differences'])
assert all(f.startswith('history') or (f.startswith('option') and f.endswith('.word0x60'))
           for f in fields), fields
for case in retained['cases']:
    values = list(case['nativeSamples'].values())
    assert all(s['unique'] for s in values)
    assert len({s['shotCount'] for s in values}) == 1
protected = R / 'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp'
assert sha(protected) == 'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
summary = dict(
    schema='thp/th14-option-initial-state/1', passed=True,
    sourceBase=edit['gameSourceBase'], sourceChanges=[edit],
    actualRetailFunctions=['44c350', '44c4a0', '44f970', '44cc10', '401280'],
    declaredControlledPowerAndTickSequence=True, focus=0,
    selections=6, steps=90, comparedWords=183060,
    baselineDifferentWords=1056, candidateDifferentWords=0,
    baselineDifferenceFields=dict(fields),
    movementHistoryPointsInitialized=33, inactiveOptionY=-51200,
    actualAnmFactoryInterpreterRegistryAndRetirement=True,
    literalHandlesAndRegistryOrderCompared=True,
    vmRepresentationWords=303, completeRawVmMemoryCompared=False,
    sdkGameUnitsRecompiled=1, sdkGameObjectsVerifiedReused=140,
    normalAccessControl=True, otherTitleObjectPairs=controls['pairs'],
    retailSha256=native['originalSha256'], componentWasmSha256=component['wasmSha256'],
    declaredServices=['resource/CRT/memset/texture boundaries inherited from constructor oracle',
                      '434ef0 HUD display sink'],
    nativeGameProcessStarted=False, audioOrGraphicsDevicesOpened=0,
    newLongReplayRuns=0, browserRuntimeRebuilt=False, deployed=False,
    loading24RngGapClosed=False, historicalShotCountFailuresNotCurrentAcceptance=True,
    ordinaryFlowAccepted=False, physicalLoadingScheduleAccepted=False,
    finalPixelsOrPcmAccepted=False, completeGame=False, evidenceBindings=bindings)
summary['toolSha256'] = sha(Path(__file__))
out = H / 'qualified.json'
assert not out.exists()
out.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf8')
public = R / 'docs/porting/th14-option-initial-state-nov13.json'
assert not public.exists()
public.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf8')
state_path = R / 'artifacts/th14/option-recall-once-nov02/work-state.json'
state = json.loads(state_path.read_bytes())
state['localOptionInitialStateNov13'] = dict(
    status='local-component-and-other-title-controls-passed-not-deployed',
    sourceBase=edit['gameSourceBase'], sourceChanges=[edit],
    home=H.relative_to(R).as_posix(), qualifiedSha256=sha(out),
    comparedWords=183060, differentWords=0, otherTitlePairs=3,
    liveSourceUnchanged='b8e36ef27d96238352f5edaf9b368ca23394ceb3',
    completeGame=False)
state['nextMainlineAction'] = (
    'Option rebuild44f970 and stage reset44cc10 controlled original/current oracle now pass '
    'six selections90steps183060words after initializing33 history points and8 option Y sentinels. '
    'Local PlayerFrame fix is not published or deployed; live source remains b8e36ef2. '
    'Three other-title Frame object pairs are identical. Before another long replay, audit '
    'retained detailed shot snapshots at32912/32922/32928: three original runs agree there, '
    'and later historical C++ selected-state runs already matched counts. Do not label those '
    'old failures current without a current-source counterexample. Physical loading24, '
    'complete-mode/ordinary-save/camera/image/PCM/browser acceptance remain open.')
temp = state_path.with_suffix('.option-init.tmp')
temp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
os.replace(temp, state_path)
print(json.dumps({k:summary[k] for k in ['passed','selections','steps','comparedWords',
                                      'candidateDifferentWords','browserRuntimeRebuilt',
                                      'deployed','completeGame']}))
