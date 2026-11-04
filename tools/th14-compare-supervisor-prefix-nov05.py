"""Compare the fixed-pass recording; keep every failed gate and raw difference."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,sys,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/supervisor-pass-rng-nov05';SHA=lambda b:hashlib.sha256(b).hexdigest()
def main(native,out,pump_mode):
    assert native.is_relative_to(H)and out.is_relative_to(H)and not out.exists()
    end=json.loads((native.parent/'process-end.json').read_bytes());nreport=json.loads((native/'report.json').read_bytes())
    assert end['exitCode']==1 and end['guardStop']is None and nreport['callbacks']==35000 and nreport['childExited']and not nreport['error']and not nreport['debugErrors']
    out.mkdir();(out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    def run(label,argv):
        started=time.monotonic()
        with(out/(label+'.log')).open('wb')as log:p=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
        result=dict(exitCode=p.returncode,elapsedSeconds=time.monotonic()-started,argv=argv,logSha256=SHA((out/(label+'.log')).read_bytes()))
        (out/(label+'-process.json')).write_text(json.dumps(result,indent=2)+'\n');return p.returncode
    proof=out/'native-register-proof.json'
    assert run('native-evidence',[sys.executable,'-X','utf8',str(R/'tools/th14-supervisor-rng-read-evidence-nov05.py'),'--native',str(native),'--output',str(proof)])==0
    accesses=[json.loads(line)for line in (native/'script-rng-access-events.jsonl').read_bytes().splitlines()]
    first=min(row['precedingPlayerCallbacks']for row in accesses);last=max(row['precedingPlayerCallbacks']for row in accesses)+1
    driver_home=H/'comparison-driver-v6';driver=driver_home/'driver.mjs';prepared=json.loads((driver_home/'prepared.json').read_bytes())
    assert SHA(driver.read_bytes())==prepared['driverSha256']
    assert prepared['parentDriverSha256']=='d3e1bcdf456e3339b16bce7ea00d6e1c42d4656d33cd042804ac8ba6cd4d18bd'
    assert prepared['toolSha256']==SHA((driver_home/'prepare-tool.py').read_bytes())==SHA((R/'tools/th14-prepare-supervisor-comparison-nov05.py').read_bytes())
    assert prepared['allFinalGatesByteIdentical']and not prepared['representativePreviousPlayerClockFallbackAdded']
    build=H/'resource-clock-build-retry1/observer-build.json';b=json.loads(build.read_bytes())
    base=R/'artifacts/th14/script-rng-read-generation-nov05/portable-audit-build/observer-build.json'
    assert json.loads(base.read_bytes())['wasmSha256']=='b129d06717e7e09f0d5fa4e8090993bc3177c88fa74bbc77fa254a52580eefef'
    assert b['baseBuildSha256']==SHA(base.read_bytes()) and b['clockOnlySupervisorPumpObservationCallAdded'] and not b['rootProductionSourcesModified']
    assert b['buildToolSha256']==SHA((build.parent/'build-tool.py').read_bytes())==SHA((R/'tools/th14-build-supervisor-resource-clock-nov05.py').read_bytes())
    model=out/'model';argv=['C:/nvm4w/nodejs/node.exe','--no-warnings',str(driver),'--native',str(native),
        '--assets',str(R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),'--build',str(build),'--output',str(model),
        '--prefix','35000','--selection','0,1,1,1','--scheduler-phases','observed','--rng-audit-first',str(first),'--rng-audit-last',str(last),
        '--native-read-evidence',str(proof),'--supervisor-pass-evidence',str(proof.with_name(proof.stem+'-timeline.json')),
        '--supervisor-resource-pump',pump_mode]
    (out/'plan.json').write_text(json.dumps(dict(argv=argv,driverSha256=prepared['driverSha256'],buildReportSha256=SHA(build.read_bytes()),
        observerSha256=nreport['sourceSha256'],nativeReportSha256=SHA((native/'report.json').read_bytes()),
        noOriginalRngOrMatrixValuesProvidedToEngine=True,noRepresentativePreviousPlayerClockFallback=True,allFinalComparisonGatesUnchanged=True,
        mainCameraVmControllerWatchesDeliberatelyGivenUp=True,ordinaryIndependentTimingAccepted=False,completeGame=False),indent=2)+'\n')
    code=run('comparison',argv)
    if not(model/'report.json').exists():
        result=dict(comparisonPreparedOrExecutedCompletely=False,comparisonExitCode=code,failureRetained=True,completeGame=False)
        (out/'comparison-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return 2
    raw_code=run('raw-verifier',[sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-campaign.py'),'--native',str(native),'--model',str(model),
        '--build',str(build),'--prefix','35000','--output',str(out/'raw-verified.json')])
    nr=(native/'selected-state.u32').read_bytes();pr=(model/'selected-state.u32').read_bytes();assert len(nr)==len(pr)==35000*128
    counts={}
    for n,p in zip(struct.iter_unpack('<32I',nr),struct.iter_unpack('<32I',pr)):
        for field,(x,y)in enumerate(zip(n,p)):
            if x!=y:counts[field]=counts.get(field,0)+1
    portable=(model/'rng-register-audit.u32').read_bytes();assert len(portable)%64==0
    prows=[row for row in struct.iter_unpack('<16I',portable)if row[3]==0]
    differences=dict(callback=0,point=0,actualInstructionValue=0,sampledScriptCalls=0)
    for n,p in zip(accesses,prows):
        kind=n['instructionContract']['kind'];expected=[n['precedingPlayerCallbacks'],1 if kind.startswith('mix')else 4,
            n['valueRetainedByTrappedInstruction'],struct.unpack_from('<I',bytes.fromhex(n['rngHexAtObservation']),4)[0]]
        actual=[p[0],p[2],p[4],p[5]]
        for key,x,y in zip(differences,expected,actual):differences[key]+=x!=y
    rng_equal=len(prows)>=len(accesses)and not any(differences.values())
    report=json.loads((model/'report.json').read_bytes());assert report['supervisorPassMode']and not report['originalSourceReadPcObserved']
    assert report['supervisorClockInputCount']==34000
    generic=json.loads((out/'raw-verified.json').read_bytes())if raw_code==0 else None
    result=dict(comparisonPreparedOrExecutedCompletely=True,comparisonExitCode=code,rawVerifierExitCode=raw_code,callbacks=35000,
        actualSupervisorClockInputs=report['supervisorClockInputCount'],stateDifferenceCounts=counts,all32StateFieldsEqual=not counts,
        nativeInstructionAccesses=len(accesses),portableScriptRows=len(prows),matchedObservedInstructionSequence=rng_equal,
        instructionDifferenceCounts=differences,extraPortableRowsNotAccepted=max(0,len(prows)-len(accesses)),missingPortableRows=max(0,len(accesses)-len(prows)),
        cameraComparison=json.loads((model/'full-camera-report.json').read_bytes())if(model/'full-camera-report.json').exists()else None,
        allExistingComparisonGatesPassed=code==0 and raw_code==0,
        vm303Rows=generic['vm303Rows']if generic else None,combatCheckpoints=generic['combatCheckpoints']if generic else None,
        noOriginalRngOrMatrixValuesProvidedToEngine=True,noRepresentativeFrameEntryFallback=True,
        strictSceneWhitelistChanged=False,oldDefaultFailureClosed=False,ordinaryIndependentTimingAccepted=False,completeGame=False)
    (out/'comparison-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='cameraComparison'}))
    return 0 if result['allExistingComparisonGatesPassed']else 2
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--pump-clock',choices=['enabled','disabled'],required=True);a=p.parse_args()
    raise SystemExit(main(a.native.resolve(),a.output.resolve(),a.pump_clock))
