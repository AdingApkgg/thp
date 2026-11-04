"""Run one bounded, hidden, muted TH14 register-read observation.

Prefix stops are explicitly diagnostic. The35000-callback case requires an
independently checked1200-callback preflight; no cases chain automatically.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, sys, time

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/script-rng-read-generation-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=['preflight','prefix'],required=True);p.add_argument('--profile',choices=['rotating-pump'],default='rotating-pump');a=p.parse_args()
    out=H/(a.case+'-'+a.profile);assert not out.exists()
    prepared=json.loads((H/('observer-'+a.profile)/'prepared.json').read_bytes());observer=H/('observer-'+a.profile)/'observer.py'
    assert prepared['observerSha256']==SHA(observer.read_bytes())
    if a.case=='prefix':
        prior=json.loads((H/('preflight-'+a.profile)/'verified.json').read_bytes())
        assert prior['verifiedNativePreflight']and prior['observerSha256']==prepared['observerSha256']
    assets=R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'
    manifest=json.loads((assets/'manifest.json').read_bytes())
    assert manifest['passed']and manifest['replaySha256']=='c48412a95f0fe9f685d97574e8ab0655d41e44ff9c41fda7bf788589b1b29c74'
    count=1200 if a.case=='preflight'else 35000;seconds=240 if a.case=='preflight'else 1800
    argv=[sys.executable,'-X','utf8',str(observer),'--assets',str(assets),'--output',str(out/'native'),
        '--config',str(R/'artifacts/th14/combat-pool-oct25/native-config.bin'),'--character','0','--subtype','1','--difficulty','1',
        '--publication-cutoff','1000','--combat-schema','3','--maximum-callbacks',str(count),'--max-seconds',str(seconds),
        '--maximum-startup-seconds','90','--minimum-free-gib','100','--maximum-capture-gib','0.5',
        '--scene-camera-events','--controller-phase-events','--camera-write-events','--worker-rng-events','--worker-main-context',
        '--worker-main-stack-bytes','2048','--stage-object-vm-window-events','--worker-active-vm-snapshot',
        '--live-callbacks','1,1000'if a.case=='preflight'else'1,1000,26000,34000']
    out.mkdir(parents=True)
    (out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    plan=dict(argv=argv,observerSha256=prepared['observerSha256'],selection=[0,1,1,1],maximumCallbacks=count,
        maximumSeconds=seconds,maximumStartupSeconds=90,maximumObservationMiB=512,minimumFreeGiB=100,
        diagnosticPrefixOnly=True,physicalAudioRequested=False,noComputerUseOrD3d9HelpersDuringCapture=True,
        noAutomaticNextCase=True,hardwareBreakpointsOnly=True,exceptionGateWaived=False,
        independentTimingAccepted=False,nativeValuesProvidedToEngine=False,completeGame=False)
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    def budget():return storage.check_budget(out/'native'if(out/'native').exists()else out,100*1024**3,512*1024**2)
    budget();start=time.monotonic();guard=None
    with(out/'native.log').open('wb')as log:
        child=subprocess.Popen(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        (out/'process-start.json').write_text(json.dumps(dict(observerPid=child.pid,startedUnixNs=time.time_ns()))+'\n')
        while child.poll()is None:
            try:budget()
            except RuntimeError:guard='storage-budget'
            if time.monotonic()-start>seconds+30:guard='outer-wall-budget'
            if guard:child.terminate();child.wait(timeout=30);break
            time.sleep(1)
    result=dict(exitCode=child.returncode,guardStop=guard,elapsedSeconds=time.monotonic()-start,
                diagnosticPrefixOnly=True,independentTimingAccepted=False,completeGame=False)
    (out/'process-end.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    # The underlying observer returns1 at a deliberate prefix stop. This does
    # not qualify any native or model fields; the separate checker must do so.
    return 0 if guard is None and child.returncode in (0,1)else 2

if __name__=='__main__':raise SystemExit(main())
