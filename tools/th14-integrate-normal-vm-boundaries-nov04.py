"""Promote the six reviewed VM-boundary files after source-bound finite checks."""
from pathlib import Path
import argparse, datetime, hashlib, importlib.util, json
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);a=p.parse_args()
    home=a.candidate.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14')and not(home/'integration.json').exists()
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    prepared=load(home/'prepared.json');core_path=home/'build/ordinary/observer-build.json';core=load(core_path)
    assert len(prepared['changes'])==6 and prepared['preparerSha256']==sha(read(R/'tools/th14-prepare-normal-vm-boundaries-nov04.py'))
    source=Path(core['sourceSnapshotRoot']);assert source==Path(prepared['sourceRoot'])
    assert core['all141CoreObjectsRecompiled']and len(core['objectBindings'])==141
    assert core['wasmSha256']==sha(read(core_path.parent/'observer.wasm'))
    for row in core['objectBindings']:assert sha(read(Path(row['path'])))==row['sha256']
    for name,digest in {**core['sourceHashes'],**core['headerHashes']}.items():assert sha(read(source/name))==digest
    checks=load(home/'api-checks/report.json');protocol=load(home/'protocol-controls-v2/verified.json')
    assert checks['passed']and len(checks['cases'])==12 and len(checks['negativeControls'])==7 and all(x['rejected']for x in checks['negativeControls'])
    assert checks['toolSha256']==sha(read(R/'tools/th14-check-normal-vm-boundaries-nov04.py'))
    assert protocol['verifiedBeforeCallAndAfterReturnFailurePropagation']and len(protocol['cases'])==2
    assert protocol['toolSha256']==sha(read(R/'tools/th14-check-normal-vm-boundary-protocol-nov04.py'))
    for title in(12,13,14,16):
        assert {x['source']for x in checks['cases']if x['title']==title and x['exitCode']==0}=={'AnmManager.cpp','GameBattle.cpp','GameSession.cpp'}
    observed=load(home/'public-observed-run/raw-verified.json')
    assert observed['verifiedFiniteEvidence']and observed['callbacks']==35000 and observed['allSelected32Equal']and observed['allCamera25Equal']and observed['allHud2Equal']
    spec=importlib.util.spec_from_file_location('contract',R/'tools/th14-normal-vm-input-contract-nov04.py');contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
    proof=load(home/'observed-inputs.json')
    validated=contract.validate(R/proof['native'],home/'public-observed-run/model',home/'build/typed/observer-build.json',home/'observed-inputs.json')
    regression=load(home/'current-modes/end.json');assert regression['casesCompleted']==17 and regression['strictV4Passes']==regression['newModelRuns']==16
    callbacks=0
    for row in regression['cases']:
        if not row['strictV4Passed']:
            assert row['key']=='reimub-easy'and row['notRunOnCurrentCore']and row['reportedDebugExceptions']==12
            continue
        assert row['newModelRun']and row['model']['exitCode']==row['verifier']['exitCode']==0
        raw=load(home/'current-modes'/row['key']/'raw-verified.json')
        assert raw['verifiedFiniteEvidence']and raw['wasmSha256']==core['wasmSha256']and raw['callbacks']==row['callbacks']
        for name,binding in raw['bindings'].items():
            data=read(R/name);assert len(data)==binding['bytes']and sha(data)==binding['sha256'],name
        callbacks+=row['callbacks']
    assert callbacks==1379760
    for name,binding in observed['bindings'].items():
        data=read(R/name);assert len(data)==binding['bytes']and sha(data)==binding['sha256'],name
    protected={'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp':'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45',
        'artifacts/th14/vm-return-worker-oct29/work-state.json':'2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'}
    for name,digest in protected.items():assert sha(read(R/name))==digest
    for row in prepared['changes']:
        assert sha(read(R/'runtimes/th12'/row['path']))==row['beforeSha256'],row['path']
        assert sha(read(source/row['path']))==row['afterSha256']
    # All preflight checks finish before the first production mutation.
    backup=home/'before-integration'
    for row in prepared['changes']:
        path=R/'runtimes/th12'/row['path'];saved=backup/row['path'];saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(path.read_bytes())
        path.write_bytes((source/row['path']).read_bytes());assert sha(read(path))==row['afterSha256']
        assert sha(read(saved))==row['beforeSha256']
    for name,digest in protected.items():assert sha((R/name).read_bytes())==digest
    production=home/'production-core';production.mkdir();(production/'observer.wasm').write_bytes((core_path.parent/'observer.wasm').read_bytes())
    report=dict(core,isolatedPrototypeOnly=False,productionIntegrated=True,rootProductionSourcesModified=True,productionSourceMatchVerified=True,
        sourcePublishedCommit=None,sourcePublicationPending=True,parentGameplayCorePublishedCommit='7babb540918c13f7d813eb14ea09db1da2112bcd',
        productionChangedGameFiles=[row['path']for row in prepared['changes']],candidateBuildReport=core_path.relative_to(R).as_posix(),
        candidateBuildReportSha256=sha(core_path.read_bytes()),candidateWasmCopiedByteIdentically=True)
    (production/'observer-build.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
    receipt=dict(integrated=True,changedFiles=prepared['changes'],coreWasmSha256=core['wasmSha256'],all141CoreObjectsRecompiled=True,
        finiteDefaultRegressions=16,finiteDefaultCallbacks=callbacks,observedVmBoundaryCallbacks=35000,observedInputContract=validated,
        otherTitleSyntaxChecks=12,negativeInputControls=7,vmBoundaryFailureControls=2,sourcePublicationPending=True,
        originalInitialReplayStillSynchronous=True,defaultBrowserAllStoresReady=True,ordinaryIndependentThreadTimingAccepted=False,
        protectedFiles=protected,bindings=bindings,completeGame=False,nativeEquivalent=False,
        integrationToolSha256=sha(Path(__file__).read_bytes()),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (home/'integration.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
    print(json.dumps(dict(integrated=True,files=6,wasmSha256=core['wasmSha256'],defaultCallbacks=callbacks,observedCallbacks=35000)),flush=True)


if __name__=='__main__':main()
