"""Check observed-input rejection and compile the shared VM API for four titles."""
from pathlib import Path
import argparse, concurrent.futures, copy, hashlib, importlib.util, json, os, subprocess, time
R=Path(__file__).resolve().parents[1]
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def load_module(name,file):
    spec=importlib.util.spec_from_file_location(name,R/'tools'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);a=p.parse_args()
    home=a.candidate.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14')
    out=home/'api-checks';out.mkdir();started=time.monotonic()
    contract=load_module('normal_vm_contract','th14-normal-vm-input-contract-nov04.py')
    proof_path=home/'observed-inputs.json';proof=json.loads(proof_path.read_bytes())
    native=R/proof['native'];model=home/'public-observed-run/model';build_path=home/'build/typed/observer-build.json'
    positive=contract.validate(native,model,build_path,proof_path);assert positive['verifiedObservedVmInputContract']
    report=json.loads((model/'report.json').read_bytes());controls=[]
    # These change acceptance inputs, not any engine or original recording bytes.
    for key in ('early-clock','wrong-handle','unreviewed-driver','not-worker-ready','wrong-identity','proposed-mode','wrong-original-record'):
        directory=out/key;directory.mkdir();changed_report=copy.deepcopy(report);changed_proof=copy.deepcopy(proof)
        use_proof=proof_path;use_native=native
        if key=='early-clock':
            changed_proof['inputs'][0]['readyNs']-=611900
        elif key=='wrong-handle':
            changed_proof['inputs'][0]['handle']+=1
        elif key=='unreviewed-driver':
            changed_report['comparisonToolSha256']='0'*64
        elif key=='not-worker-ready':
            changed_report['normalVmBoundaryStates'][0][15]=0
        elif key=='wrong-identity':
            changed_report['normalVmBoundaryStates'][0][5]+=1
        elif key=='proposed-mode':
            changed_report['hostNormalBoundaryMode']='proposed'
        else:
            use_native=R/'artifacts/th14/replay-rng-store-trace-nov04/native'
        if changed_proof!=proof:
            use_proof=directory/'inputs.json';use_proof.write_bytes((json.dumps(changed_proof,indent=2)+'\n').encode())
        (directory/'report.json').write_bytes((json.dumps(changed_report,indent=2)+'\n').encode())
        try:
            contract.validate(use_native,directory,build_path,use_proof)
        except (AssertionError,FileNotFoundError)as error:
            controls.append(dict(key=key,rejected=True,errorType=type(error).__name__,message=str(error)))
        else:
            raise AssertionError('Invalid input accepted: '+key)
    (out/'input-controls.json').write_bytes((json.dumps(dict(positive=positive,negativeControls=controls),indent=2)+'\n').encode())
    core=json.loads((home/'build/ordinary/observer-build.json').read_bytes());source=Path(core['sourceSnapshotRoot'])
    compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    assert sha(compiler.read_bytes())==core['compilerSha256']
    def check(pair):
        title,name=pair;unit=source/'th12_web/cpp/game'/name
        flags=[flag for flag in core['flags']if not flag.startswith('-DPORT_TITLE=')]
        command=[str(compiler),*flags,'-DPORT_TITLE='+str(title),'-fsyntax-only',str(unit)]
        result=subprocess.run(command,cwd=R,env={**os.environ,'TEMP':str(out),'TMP':str(out)},capture_output=True,timeout=90)
        (out/f'th{title}-{name}.log').write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,(title,name,result.stderr.decode(errors='replace')[-2000:])
        return dict(title=title,source=name,sourceSha256=sha(unit.read_bytes()),exitCode=result.returncode,argv=command)
    pairs=[(title,name)for title in(12,13,14,16)for name in('AnmManager.cpp','GameBattle.cpp','GameSession.cpp')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:cases=list(pool.map(check,pairs))
    result=dict(passed=True,cases=cases,negativeControls=controls,positiveObservedInputContractPassed=True,
        compilerSha256=core['compilerSha256'],toolSha256=sha(Path(__file__).read_bytes()),
        contractVerifierSha256=sha((R/'tools/th14-normal-vm-input-contract-nov04.py').read_bytes()),
        elapsedSeconds=time.monotonic()-started,completeGame=False,nativeEquivalent=False)
    (out/'report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,syntaxChecks=len(cases),negativeControls=len(controls))),flush=True)


if __name__=='__main__':main()
