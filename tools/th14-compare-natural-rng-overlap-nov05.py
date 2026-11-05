"""Test one proof-bound logical RNG delivery, retaining every original gate.

This diagnostic advances Initialize readiness after the retained seed read and
before its stale store. Its counter/global-copy timing is not the exact native
instruction schedule. It supplies no original seed or per-frame state values.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-native-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main(case):
    if case == 'on':
        prior = json.loads((H / 'overlap-off/result.json').read_bytes())
        assert prior['strictDriverExitCode'] == prior['rawVerifierExitCode'] == 0
    parent = H / 'comparison-driver/driver-off.mjs'
    raw = parent.read_bytes()
    assert SHA(raw) == '8e7d54cf1dd3899abcb7f581905ea7fe19b8366c761468c0c2254636a9cf1d5e'
    source = raw.decode()
    changes = []

    def replace(before, after):
        nonlocal source
        assert source.count(before) == 1, (before[:100], source.count(before))
        source = source.replace(before, after)
        changes.append((before, after))

    anchor = "const replayStoreEvents=stageEvents('replay-rng-store-events.jsonl');"
    replace(anchor, '''const overlapPath=resolve(root,'artifacts/th14/original-nine-shot-native-nov05/natural-overlap.json');
const overlapBytes=read(overlapPath),overlap=JSON.parse(overlapBytes);
assert(overlap.verifiedNaturalSeedReadSpansReplayStore&&overlap.proposedDeliveryIsFiniteLogicalOrderDiagnostic);
assert(!overlap.independentTimingAccepted&&!overlap.seedsProvidedToPortableEngine);
assert.equal(overlap.verifierSha256,sha(read(resolve(root,'tools/th14-natural-rng-overlap-nov05.py'))));
for(const[name,row]of Object.entries(overlap.evidenceBindings))assert.equal(sha(read(resolve(root,name))),row.sha256);
assert.equal(overlap.evidenceBindings[relative(root,resolve(nativeHome,'report.json')).replaceAll('\\\\','/')]?.sha256,sha(read(resolve(nativeHome,'report.json'))));
''' + anchor)
    anchor = '  const delta=(after[22]-rng[2][1])>>>0;'
    # The frozen source has one-space indentation at this line.
    if anchor not in source:
        anchor = ' const delta=(after[22]-rng[2][1])>>>0;'
    replace(anchor, ''' if(stage===overlap.stage){
  assert.equal(callback,overlap.precedingPlayerCallbacks);assert.equal(firstScriptReadPoint,1);
  const pumpNs=overlap.observedPumpNs,readyNs=overlap.initializeReadyReceiptNs;
  assert.equal(stores[2].hostMonotonicNs,readyNs);
  assert(pumpNs<overlap.firstReadReceiptNs&&overlap.firstReadReceiptNs<overlap.scriptSeedStoreReceiptNs);
  assert(overlap.scriptSeedStoreReceiptNs<overlap.firstMainStoreReceiptNs&&overlap.firstMainStoreReceiptNs<readyNs);
  assert.equal(phaseInputs.find(row=>row.stage===stage&&row.phase==='Initialize').readyNs,readyNs);
  assert.equal(c.observed_first_script_read_window(stage,callback,baseNow+BigInt(pumpNs)-playerOrigin,baseNow+BigInt(readyNs)-playerOrigin,1),1);
  firstScriptReadWindows.push({stage,callback,pumpNs,readyNs,actualSeedReadSpansReplayStore:true,
   overlapProofSha256:sha(overlapBytes),finiteLogicalOrderDiagnostic:true,exactExecutionTimesRecovered:false,
   counterClearAndGlobalsCopyAtExactNativeMainInstruction:false,originalRngValuesProvidedToEngine:false});
  continue;
 }
''' + anchor)
    if case == 'on':
        replace('c.shot_lifetime_install(0)', 'c.shot_lifetime_install(1)')
    restored = source
    for before, after in reversed(changes):
        assert restored.count(after) == 1
        restored = restored.replace(after, before)
    assert restored.encode() == raw
    out = H / ('overlap-'+case)
    assert not out.exists()
    out.mkdir()
    driver = out / 'driver.mjs'
    driver.write_text(source, encoding='utf8', newline='\n')
    subprocess.run(['C:/nvm4w/nodejs/node.exe', '--check', str(driver)], check=True,
                   capture_output=True, timeout=30)
    argv = list(json.loads((H / 'comparison-off/plan.json').read_bytes())['argv'])
    argv[2] = str(driver)
    argv[argv.index('--output')+1] = str(out / 'model')
    argv += ['--first-script-read-point', '1']
    (out / 'plan.json').write_text(json.dumps(dict(argv=argv, parentDriverSha256=SHA(raw),
        driverSha256=SHA(driver.read_bytes()), exactReversalRestoresParent=True,
        allOriginalFinalGatesPreserved=True, finiteLogicalOrderDiagnostic=True,
        exactNativeCounterAndSnapshotInstructionPlacementAccepted=False,
        originalValuesProvidedToEngine=False, productionChanged=False, completeGame=False), indent=2)+'\n')
    start = time.monotonic()
    with (out / 'driver.log').open('wb') as log:
        child = subprocess.run(argv, cwd=R, stdout=log, stderr=subprocess.STDOUT,
                               timeout=240, creationflags=subprocess.CREATE_NO_WINDOW)
    code = None
    if (out / 'model/report.json').exists():
        native = argv[argv.index('--native')+1]
        build = argv[argv.index('--build')+1]
        with (out / 'verify.log').open('wb') as log:
            checker = subprocess.run([sys.executable, '-X', 'utf8',
                str(R / 'tools/th14-verify-native-campaign.py'), '--native', native,
                '--model', str(out / 'model'), '--build', build, '--prefix', '35000',
                '--output', str(out / 'raw-verified.json')], cwd=R,
                stdout=log, stderr=subprocess.STDOUT, timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW)
        code = checker.returncode
    result = dict(case=case, strictDriverExitCode=child.returncode, rawVerifierExitCode=code,
        elapsedSeconds=time.monotonic()-start, finiteLogicalOrderDiagnostic=True,
        exactNativeScheduleAccepted=False, originalSeedValuesProvidedToEngine=False,
        independentTimingAccepted=False, productionChanged=False, completeGame=False)
    if case == 'on' and child.returncode == code == 0:
        for name in ['selected-state.u32','full-camera.u32','replay-cursor.u32','portable-hud.u32']:
            assert (out / 'model' / name).read_bytes() == (H / 'overlap-off/model' / name).read_bytes()
        result['readonlyProbeTransparentForCapturedState'] = True
    (out / 'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    return 0 if child.returncode == code == 0 else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['off','on'], required=True)
    raise SystemExit(main(parser.parse_args().case))
