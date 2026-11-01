"""Run the unchanged campaign checks with the actually observed passive VM-return clock.

This supplies only a host time at an existing production poll. Native VM, RNG,
handles and pixels are evidence, never game operands. No original is launched.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[1]
S=lambda raw:hashlib.sha256(raw).hexdigest()

def prepare(native,proof_path,output):
    native=native.resolve(strict=True);proof_path=proof_path.resolve(strict=True);output=output.resolve()
    assert native.is_relative_to(R/'artifacts/th14')and proof_path.is_relative_to(R/'artifacts/th14')and output.is_relative_to(R/'artifacts/th14')and not output.exists()
    verifier=R/'tools/th14-passive-vm-return-evidence-nov01.py'
    spec=importlib.util.spec_from_file_location('passive_return_observation',verifier);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    proof=json.loads(proof_path.read_bytes());assert proof==module.evidence(native)
    assert proof['verifiedFinitePassiveNormalVmReturnObservation']and proof['returnEventsDeliveredAfterRestore']==1
    run=json.loads((native/'report.json').read_bytes());assert run['callbacks']==48000 and not run['error']and run['diagnosticPrefixOnly']
    restore=next(e for e in run['transitionEvents']if e.get('normalVmCallWindowAtSeedRestore',{}).get('callReturnEdgeDeliveryPending'))
    window=restore['normalVmCallWindowAtSeedRestore'];entry=window['activeCall'];snapshot=window['activeVmSnapshot']
    assert restore['pc']==0x456133 and window['mainPcAtRestore']==0x47e660 and entry['file']==5 and entry['script']==4
    assert snapshot['callIdentityStillMatches']and snapshot['identity']==dict(handle=entry['handle'],file=entry['file'],script=entry['script'])
    assert not window['withinVmMethodAtRestore']and window['returnWatchStatusBitAtRestore']
    observation=dict(callback=restore['precedingPlayerCallbacks'],readyNs=restore['hostMonotonicNs'],stage=restore['stage'],
        originalPc=window['mainPcAtRestore'],file=entry['file'],script=entry['script'],retainedBaseline=False,
        passiveOriginalReturnPcActuallyObserved=True,normalRegistryEntryProjection=False,originalInstructionRngOrCounterWrites=False,
        nativeReportSha256=S((native/'report.json').read_bytes()),passiveProofSha256=S(proof_path.read_bytes()),
        originalIndependentThreadTimingAcceptance=False,exactIndividualSeedStorePcSimultaneityNotClaimed=True)
    build_path=R/'artifacts/th14/reimub-normal-construction-current-oct30/observer/observer-build.json'
    build=json.loads(build_path.read_bytes());assert S((build_path.parent/'observer.wasm').read_bytes())==build['wasmSha256']
    for row in build['objectBindings']:assert S(Path(row['path']).read_bytes())==row['sha256']
    base_path=R/'tools/th14-compare-native-campaign.mjs';base=base_path.read_text()
    assert base.count("const root=resolve(import.meta.dirname,'..')")==1 and base.count('let normalVmBoundary=null;')==1
    script=base.replace("const root=resolve(import.meta.dirname,'..')","const root="+json.dumps(R.as_posix()))
    injection="""const passiveReturnClock=JSON.parse(read(resolve(import.meta.dirname,'return-clock-observation.json')));
assert(prefix===48000 && schedulerPhases==='observed' && !normalBoundary && !options.has('normal-vm-boundary-observation'));
assert.equal(sha(read(resolve(nativeHome,'report.json'))),passiveReturnClock.nativeReportSha256);
normalVmBoundary=passiveReturnClock;
assert.equal(c.observed_normal_vm_clock(normalVmBoundary.callback,baseNow+BigInt(normalVmBoundary.readyNs)-playerOrigin,normalVmBoundary.file,normalVmBoundary.script),1);
"""
    script=script.replace('let normalVmBoundary=null;','let normalVmBoundary=null;\n'+injection)
    script=script.replace("normalVmBoundary.retainedBaseline?'controlled-vm-return-baseline':'controlled-vm-return'","normalVmBoundary.retainedBaseline?'controlled-vm-return-baseline':'passive-observed-vm-return'")
    output.mkdir(parents=True);(output/'compare.mjs').write_text(script);(output/'return-clock-observation.json').write_text(json.dumps(observation,indent=2)+'\n')
    command=['C:/nvm4w/nodejs/node.exe',str(output/'compare.mjs'),'--native',native.relative_to(R).as_posix(),'--assets',run['observerOptions']['assets'],
        '--build',build_path.relative_to(R).as_posix(),'--output',(output/'model').relative_to(R).as_posix(),'--selection','1,0,0,1','--prefix','48000','--scheduler-phases','observed']
    plan=dict(declaredUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),argv=command,producerSha256=S(Path(__file__).read_bytes()),
        comparisonBaseSha256=S(base_path.read_bytes()),comparisonGeneratedSha256=S((output/'compare.mjs').read_bytes()),nativeProofSha256=S(proof_path.read_bytes()),
        maximumWallSeconds=300,maximumObservationBytes=128*1024**2,minimumFreeBytes=100*1024**3,physicalAudioDevicesOpened=0,
        originalProcessesStarted=0,productionGameplayModified=False,onlyObservedHostClockAndBoundaryProvided=True,
        productionNormalVmReturnPollUsed=True,independentSchedulingAccepted=False,completeGame=False,nativeEquivalent=False)
    (output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');return command,plan

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    command,plan=prepare(a.native,a.proof,a.output);output=a.output.resolve();assert shutil.disk_usage(R).free>=plan['minimumFreeBytes']
    started=time.monotonic();stop=None
    with (output/'compare.log').open('wb')as log:
        child=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT)
        (output/'process-start.json').write_text(json.dumps(dict(pid=child.pid,argv=command),indent=2)+'\n');print(json.dumps(dict(comparisonPid=child.pid)),flush=True)
        while child.poll()is None:
            if time.monotonic()-started>plan['maximumWallSeconds']:stop='declared-wall-budget'
            if shutil.disk_usage(R).free<plan['minimumFreeBytes']:stop='minimum-free-space'
            if sum(p.stat().st_size for p in output.rglob('*')if p.is_file())>plan['maximumObservationBytes']:stop='declared-output-budget'
            if stop:child.terminate();child.wait(timeout=30);break
            time.sleep(1)
        result=dict(pid=child.pid,exitCode=child.returncode,guardStop=stop,elapsedSeconds=time.monotonic()-started,
            strictPassed=child.returncode==0 and stop is None,completeGame=False,nativeEquivalent=False)
        (output/'process-end.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    sys.exit(child.returncode or int(stop is not None))
if __name__=='__main__':main()
