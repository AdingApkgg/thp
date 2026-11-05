"""Expand the retained original A trajectory with read-only shot snapshots.

Uses the exact accepted A driver and all its gates. Only adds output probes;
reuses the existing observation Wasm and never launches an original process.
This does not retroactively supply missing original A VM snapshots.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-model-nov05/retry1'
A = R / 'artifacts/th14/script-rng-read-generation-nov05/portable-player-pump-ready-at-pump'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main(case):
    assert shutil.disk_usage(R).free > 100*1024**3
    accepted = json.loads((A / 'comparison-result.json').read_bytes())
    assert accepted['verifiedFiniteUnanchoredComparison']
    if case == 'on':
        assert json.loads((H / 'off/result.json').read_bytes())['allExistingPayloadsByteIdentical']
    parent = R / 'tools/th14-compare-native-player-pump-ready-nov05.mjs'
    raw = parent.read_bytes()
    assert SHA(raw) == 'd3e1bcdf456e3339b16bce7ea00d6e1c42d4656d33cd042804ac8ba6cd4d18bd'
    source = raw.decode()
    changes = []

    def replace(before, after):
        nonlocal source
        assert source.count(before) == 1, (before[:80], source.count(before))
        source = source.replace(before, after)
        changes.append((before, after))

    # This derivative lives under artifacts rather than the parent's tools/.
    replace("const root=resolve(import.meta.dirname,'..')", 'const root='+json.dumps(str(R)))
    replace('function compare(index){', '''const lifetimeSnapshots=[];
function retainLifetime(index){
 if(c.shot_lifetime_meta(0)!==index+1)return;
 const meta=Array.from({length:6},(_,word)=>c.shot_lifetime_meta(word)>>>0);
 assert.equal(meta[3],96);assert.equal(meta[4],256);assert(lifetimeSnapshots.length<64);
 const data=Buffer.from(new Uint8Array(c.memory.buffer,c.shot_lifetime_data(),256*96*4));
 const name='shot-lifetime-'+(index+1)+'.u32';write(resolve(out,name),data,{flag:'wx'});
 lifetimeSnapshots.push({callback:meta[0],stage:meta[1],stageFrame:meta[2],stride:96,slots:256,file:name,bytes:data.length,sha256:sha(data)});
 write(resolve(out,'shot-lifetime-index.json'),JSON.stringify({readOnly:true,originalValuesProvidedToEngine:false,snapshots:lifetimeSnapshots})+'\\n');
}
function compare(index){''')
    replace('rows.push(...row);for(let k=0;k<32;k++){',
            'rows.push(...row);retainLifetime(index);for(let k=0;k<32;k++){')
    replace('initialCreationCount=c.observed_creation_count();compare(0);',
            f'initialCreationCount=c.observed_creation_count();assert.equal(c.shot_lifetime_install({int(case == "on")}),1);compare(0);')
    restored = source
    for before, after in reversed(changes):
        assert restored.count(after) == 1
        restored = restored.replace(after, before)
    assert restored.encode() == raw

    out = H / case
    assert not out.exists()
    out.mkdir(parents=True)
    driver = out / 'driver.mjs'
    driver.write_text(source, encoding='utf8', newline='\n')
    subprocess.run(['C:/nvm4w/nodejs/node.exe', '--check', str(driver)], check=True,
                   capture_output=True, timeout=30)
    build = R / 'artifacts/th14/shot-lifetime-nov05/build-retry1/observer-build.json'
    build_info = json.loads(build.read_bytes())
    assert build_info['wasmSha256'] == '1fcd416817b86822182429e12431f97475180f6c41a3a8a24e0641636076ecc6'
    assert SHA((build.parent / 'observer.wasm').read_bytes()) == build_info['wasmSha256']
    for row in build_info['objectBindings']:
        assert SHA(Path(row['path']).read_bytes()) == row['sha256']
    plan = json.loads((A / 'plan.json').read_bytes())
    argv = list(plan['argv'])
    argv[2] = str(driver)
    argv[argv.index('--output')+1] = str(out / 'model')
    argv[argv.index('--build')+1] = str(build)
    native = Path(argv[argv.index('--native')+1])
    (out / 'plan.json').write_text(json.dumps(dict(
        argv=argv, parentStrictDriverSha256=SHA(raw), driverSha256=SHA(driver.read_bytes()),
        exactReversalRestoresParent=True, allOriginalGatesPreserved=True,
        existingWasmReused=True, originalProcessLaunched=False,
        nativeValuesSuppliedToEngine=False, completeGame=False), indent=2)+'\n')
    started = time.monotonic()
    with (out / 'driver.log').open('wb') as log:
        process = subprocess.run(argv, cwd=R, stdout=log, stderr=subprocess.STDOUT,
                                 timeout=240, creationflags=subprocess.CREATE_NO_WINDOW)
    result = dict(case=case, driverExitCode=process.returncode,
                  elapsedSeconds=time.monotonic()-started, completeGame=False)
    (out / 'result.json').write_text(json.dumps(result, indent=2)+'\n')
    assert process.returncode == 0, 'Retained comparison failure; no gate was relaxed'
    with (out / 'raw-verifier.log').open('wb') as log:
        verifier = subprocess.run([sys.executable, '-X', 'utf8',
            str(R / 'tools/th14-verify-native-campaign.py'), '--native', str(native),
            '--model', str(out / 'model'), '--build', str(build), '--prefix', '35000',
            '--output', str(out / 'raw-verified.json')], cwd=R, check=False,
            stdout=log, stderr=subprocess.STDOUT, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW)
    assert verifier.returncode == 0
    # All generated binary observations, sampled VM arrays and combat objects
    # must equal the previously accepted trajectory, not merely each other.
    names = sorted({p.name for p in (A / 'model').glob('*.u32')} |
                   {p.name for p in (A / 'model').glob('portable-live-*.json')} |
                   {p.name for p in (A / 'model').glob('combat-[0-9]*.json')})
    assert len(names) > 300
    for name in names:
        assert (out / 'model' / name).read_bytes() == (A / 'model' / name).read_bytes(), name
    snapshots = json.loads((out / 'model/shot-lifetime-index.json').read_bytes())['snapshots'] if case == 'on' else []
    assert len(snapshots) == (55 if case == 'on' else 0)
    size = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    assert size < 80*1024**2
    result.update(rawVerifierExitCode=0, allExistingPayloadsByteIdentical=True,
                  payloadFiles=len(names), callbacks=35000, snapshots=len(snapshots),
                  outputBytes=size, strictDriverParentSha256=SHA(raw),
                  driverSha256=SHA(driver.read_bytes()), buildSha256=SHA(build.read_bytes()),
                  oldOriginalAVmSnapshotsAdded=False, originalNineDifferencesClosed=False,
                  independentTimingAccepted=False, productionChanged=False,
                  toolSha256=SHA(Path(__file__).read_bytes()))
    (out / 'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['off', 'on'], required=True)
    main(parser.parse_args().case)
