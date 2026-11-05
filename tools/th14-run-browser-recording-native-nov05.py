"""Quiet bounded preflight then separate natural original playback of browser slot02."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,sys,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/browser-recording-native-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()


def main(case):
    observer=H/'observer/observer.py';prep=json.loads((observer.parent/'prepared.json').read_bytes())
    assert SHA(observer.read_bytes())==prep['observerSha256']
    if case=='natural':
        prior=json.loads((H/'preflight/verified.json').read_bytes());assert prior['verifiedNativePreflight']and prior['observerSha256']==prep['observerSha256']
    assets=R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-ec04b9bea043'
    manifest=json.loads((assets/'manifest.json').read_bytes());assert SHA((assets/'manifest.json').read_bytes())==prep['assetManifestSha256']
    assert manifest['passed'] and manifest['replaySha256']=='ec04b9bea043c092e4f7b2fd18f379cb38419c5597ed7d640193fbefc344434a'
    out=H/case;assert not out.exists();out.mkdir()
    count=1200 if case=='preflight' else 8000;seconds=240
    argv=[sys.executable,'-X','utf8',str(observer),'--assets',str(assets),'--output',str(out/'native'),
        '--config',str(R/'artifacts/th14/combat-pool-oct25/native-config.bin'),'--character','0','--subtype','1','--difficulty','1',
        '--publication-cutoff','1000','--combat-schema','3','--maximum-callbacks',str(count),'--max-seconds',str(seconds),
        '--maximum-startup-seconds','90','--minimum-free-gib','100','--maximum-capture-gib','0.5',
        '--scene-camera-events','--controller-phase-events','--camera-write-events','--worker-rng-events','--worker-main-context',
        '--worker-main-stack-bytes','2048','--stage-object-vm-window-events','--worker-active-vm-snapshot','--live-callbacks','1,1000']
    plan=dict(argv=argv,maximumCallbacks=count,maximumSeconds=seconds,maximumStartupSeconds=90,
        minimumFreeGiB=100,maximumObservationMiB=512,intactBrowserReplay=True,declaredFramesNotCallbackCount=True,
        quiet=True,noComputerUseOrD3d9HelpersDuringCapture=True,noAutomaticNextCase=True,
        observerSha256=prep['observerSha256'],originalGameMemoryMutationsUnchanged=True,
        naturalPlaybackAccepted=False,completeGame=False)
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    def budget():return storage.check_budget(out,100*1024**3,512*1024**2)
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
        naturalPlaybackAccepted=False,completeGame=False)
    (out/'process-end.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    return 0 if guard is None and child.returncode in (0,1)else 2


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=['preflight','natural'],required=True)
    raise SystemExit(main(p.parse_args().case))
