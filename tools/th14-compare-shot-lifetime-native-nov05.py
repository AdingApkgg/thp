"""Run unchanged strict gates plus optional output-only per-slot observation."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/shot-lifetime-native-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest()


def main(case):
    native=H/'prefix-slots-v2/native'
    ended=json.loads((native.parent/'process-end.json').read_bytes())
    report=json.loads((native/'report.json').read_bytes())
    assert ended['exitCode']==1 and ended['guardStop']is None
    assert report['callbacks']==35000 and report['childExited'] and not report['error'] and not report['debugErrors']
    assert report['shotLifetimeReadOnly'] and report['configuredMusicAndSoundVolumeZero']
    out=H/('comparison-'+case);assert not out.exists();out.mkdir()
    proof=H/'native-register-proof.json'
    if case=='off':
        assert not proof.exists()
        subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-shot-lifetime-register-evidence-nov05.py'),
            '--native',str(native),'--output',str(proof)],check=True,cwd=R,timeout=60)
    else:
        prior=json.loads((H/'comparison-off/result.json').read_bytes())
        assert prior['strictDriverExitCode']==0 and prior['rawVerifierExitCode']==0
    source=H/'comparison-driver-v2'/('driver-off.mjs'if case=='off'else'driver.mjs')
    prepared=json.loads((source.parent/'prepared.json').read_bytes())
    assert SHA(source.read_bytes())==prepared['disabledDriverSha256'if case=='off'else'driverSha256']
    build=R/'artifacts/th14/shot-lifetime-nov05/build-retry1/observer-build.json'
    events=[json.loads(x)for x in (native/'script-rng-access-events.jsonl').read_bytes().splitlines()]
    first=min(x['precedingPlayerCallbacks']for x in events);last=max(x['precedingPlayerCallbacks']for x in events)+1
    argv=['C:/nvm4w/nodejs/node.exe','--no-warnings',str(source),'--native',str(native),
        '--assets',str(R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),
        '--build',str(build),'--output',str(out/'model'),'--prefix','35000','--selection','0,1,1,1',
        '--scheduler-phases','observed','--rng-audit-first',str(first),'--rng-audit-last',str(last),
        '--native-read-evidence',str(proof),'--supervisor-pass-evidence',str(proof.with_name(proof.stem+'-timeline.json')),
        '--supervisor-resource-pump','enabled']
    (out/'plan.json').write_text(json.dumps(dict(argv=argv,driverSha256=SHA(source.read_bytes()),
        allOriginalComparisonsAndFinalGatesUnchanged=True,onlyOutputObserverAndProvenanceChanged=True,
        noNativeValuesSuppliedToEngine=True,ordinaryIndependentTimingAccepted=False,completeGame=False),indent=2)+'\n')
    start=time.monotonic()
    with(out/'driver.log').open('wb')as log:
        process=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
    raw_code=None
    if (out/'model/report.json').exists():
        with(out/'verify.log').open('wb')as log:
            verify=subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-campaign.py'),
                '--native',str(native),'--model',str(out/'model'),'--build',str(build),'--prefix','35000',
                '--output',str(out/'raw-verified.json')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=60)
        raw_code=verify.returncode
    result=dict(case=case,strictDriverExitCode=process.returncode,rawVerifierExitCode=raw_code,
        elapsedSeconds=time.monotonic()-start,allOriginalFinalGatesUnchanged=True,completeGame=False)
    if case=='on' and process.returncode==0:
        equal=[]
        for name in ['selected-state.u32','full-camera.u32','replay-cursor.u32','portable-hud.u32']:
            data=(out/'model'/name).read_bytes()
            assert data==(H/'comparison-off/model'/name).read_bytes()
            equal.append(dict(file=name,bytes=len(data),sha256=SHA(data)))
        result['probeTransparentForCapturedState']=equal
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return 0 if process.returncode==0 and raw_code==0 else 2


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=['off','on'],required=True)
    raise SystemExit(main(p.parse_args().case))
