"""Hold all startup inputs fixed and move only Initialize readiness past one pump.

The controls are synthetic legal timing sensitivities, not original observations
or acceptance. Production code and the original strict driver remain unchanged.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,struct,subprocess,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/original-pair-audit-nov05/initialize-controls'
S=R/'artifacts/th14/supervisor-pass-rng-nov05';SHA=lambda data:hashlib.sha256(data).hexdigest()

def main(case):
    assert shutil.disk_usage(R).free>100*1024**3
    origin=R/'artifacts/th14/original-pair-audit-nov05/controls-retry1/baseline'
    proof=json.loads((origin/'result.json').read_bytes());assert proof['baselineSelectedStateByteIdentical']
    source=(origin/'driver.mjs').read_text();assert SHA((origin/'driver.mjs').read_bytes())==proof['diagnosticDriverSha256']
    plan=json.loads((S/'comparison-pump-enabled/plan.json').read_bytes())
    reference=json.loads((S/'comparison-pump-enabled/model/report.json').read_bytes())
    native=Path(plan['argv'][plan['argv'].index('--native')+1])
    rows=[json.loads(line)for line in (native/'supervisor-pass-events.jsonl').read_bytes().splitlines()]
    stages={'baseline':[],'stage2-late':[2],'stage3-late':[3],'stage2-player-late':[2],'stage3-player-late':[3]}[case];deltas={};limits=[]
    boundary_pc=0x44dbd0 if case.endswith('player-late')else 0x47d720
    for stage in stages:
        stamp=next(row['readyNs']for row in reference['observedPhaseInputs']if row['stage']==stage and row['phase']=='Initialize')
        following=min((row for row in rows if row['pc']==boundary_pc and row['hostMonotonicNs']>stamp),key=lambda row:row['hostMonotonicNs'])
        delta=following['hostMonotonicNs']-stamp+1
        later=[row['readyNs']for row in reference['observedPhaseInputs']if row['stage']==stage and row['phase']!='Initialize']
        assert delta>0 and stamp+delta<min(later)
        deltas[stage]=delta;limits.append(dict(stage=stage,delayNs=delta,boundaryPc=hex(boundary_pc),followingBoundaryPrecedingCallbacks=following['precedingPlayerCallbacks'],stillBeforeAllLaterPhaseReadiness=True))
    if case!='baseline':assert json.loads((H/'baseline/result.json').read_bytes())['baselineSelectedStateByteIdentical']
    out=H/case;assert not out.exists();out.mkdir(parents=True)
    (out/'startup-inputs.json').write_bytes((origin/'startup-inputs.json').read_bytes())
    (out/'initialize-deltas.json').write_text(json.dumps(deltas)+'\n')
    marker='const startupInputs=JSON.parse(read(new URL(\'./startup-inputs.json\',import.meta.url)));'
    assert source.count(marker)==1
    source=source.replace(marker,"const controlInitializeDeltas=JSON.parse(read(new URL('./initialize-deltas.json',import.meta.url)));\n"+marker)
    old='c.observed_worker_initialize(stage,baseNow+BigInt(initialized.hostMonotonicNs)-playerOrigin)'
    new='c.observed_worker_initialize(stage,baseNow+BigInt(initialized.hostMonotonicNs)+BigInt(controlInitializeDeltas[stage]??0)-playerOrigin)'
    assert source.count(old)==1;source=source.replace(old,new)
    driver=out/'driver.mjs';driver.write_text(source,encoding='utf8',newline='\n')
    subprocess.run(['C:/nvm4w/nodejs/node.exe','--check',str(driver)],check=True,capture_output=True,timeout=30)
    argv=list(plan['argv']);argv[2]=str(driver);argv[argv.index('--output')+1]=str(out/'model')
    started=time.monotonic()
    with(out/'run.log').open('wb')as log:process=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
    result=dict(case=case,diagnosticOnly=True,syntheticControlNotOriginalObservation=True,exitCode=process.returncode,
        elapsedSeconds=time.monotonic()-started,controlledInitializeReadiness=limits,
        startupInputsUnchanged=True,allOtherClockInputsUnchanged=True,noPerFrameStateOverrides=True,
        nativeRngValuesProvidedToEngine=False,productionOrFixtureRecompiled=False,
        parentDriverSha256=proof['diagnosticDriverSha256'],diagnosticDriverSha256=SHA(driver.read_bytes()),
        originalStrictDriverAndGatesChanged=False,ordinaryIndependentTimingAccepted=False,completeGame=False)
    if process.returncode==0:
        data=(out/'model/diagnostic-state.u32').read_bytes();expected=(origin/'model/diagnostic-state.u32').read_bytes();assert len(data)==len(expected)==35000*128
        counts={};first={}
        for index,(a,b)in enumerate(zip(struct.iter_unpack('<32I',expected),struct.iter_unpack('<32I',data))):
            for field,(x,y)in enumerate(zip(a,b)):
                if x!=y:
                    counts[field]=counts.get(field,0)+1
                    first.setdefault(field,dict(callback=index+1,stage=b[30],stageFrame=b[0]))
        result.update(callbacks=35000,selectedSha256=SHA(data),baselineSelectedStateByteIdentical=data==expected,
            differencesFromSameClockBaseline=counts,firstDifferences=first)
        if case=='baseline':assert data==expected
    size=sum(path.stat().st_size for path in out.rglob('*')if path.is_file());assert size<50*1024**2
    result['outputBytes']=size;(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    if process.returncode:raise SystemExit(process.returncode)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=['baseline','stage2-late','stage3-late','stage2-player-late','stage3-player-late'],required=True);main(p.parse_args().case)
