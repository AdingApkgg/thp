"""Validate the reviewed adapter, original VM identity and actual loader readiness."""
from pathlib import Path
import hashlib, importlib.util, json, struct
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,R/'tools'/file);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def validate(native,model,build_path,proof_path):
    native=native.resolve(strict=True);model=model.resolve(strict=True);build_path=build_path.resolve(strict=True);proof_path=proof_path.resolve(strict=True)
    assert all(path.is_relative_to(R/'artifacts/th14')for path in(native,model,build_path,proof_path))
    proof_bytes=proof_path.read_bytes();proof=json.loads(proof_bytes)
    verifier=module('observed_normal_vm_input_proof','th14-observed-normal-vm-inputs-nov04.py')
    assert proof==verifier.verify(native),'Original VM-input proof changed'
    generator=module('observed_normal_vm_input_driver','th14-prepare-normal-vm-boundary-driver-nov04.py')
    driver=generator.driver_source();report_bytes=(model/'report.json').read_bytes();report=json.loads(report_bytes)
    assert report['comparisonToolSha256']==sha(driver),'Unreviewed observed-VM scheduler driver'
    assert report['vmBoundaryDriverGeneratorSha256']==sha((R/'tools/th14-prepare-normal-vm-boundary-driver-nov04.py').read_bytes())
    assert report['hostNormalBoundaryMode']=='observed-vm-return' and report['diagnosticPrefixOnly'] and report['callbacks']==proof['callbacks']
    observed=report['normalVmInputObservation'];assert observed['sha256']==sha(proof_bytes) and (R/observed['path']).resolve()==proof_path
    assert observed['inputs']==proof['inputs'] and report['normalVmBoundaryFailed']==0
    assert not report['vmCallbackPointersWrapped'] and not report['ordinaryIndependentThreadTimingAcceptance']
    assert report['noRngSerialCounterHealthOrInputWrites'] and report['noPerFrameStateOverrides']
    states=report['normalVmBoundaryStates'];assert len(states)==len(proof['inputs'])==2
    stores=[json.loads(line)for line in(native/'replay-rng-store-events.jsonl').read_bytes().splitlines()]
    for state,input in zip(states,proof['inputs'],strict=True):
        assert len(state)==17 and state[0]==1
        assert state[5:9]==[input['handle'],input['file'],input['script'],input['callback']]
        assert state[9]==2 and state[14]==0xffffffff and state[15:17]==[1,1]
        original=next(row for row in stores if row['stage']==input['stage']and row['pc']==0x45610f)
        words=struct.unpack('<HHIHHI',bytes.fromhex(original['rngHex']))
        assert state[1:5]==[words[0],words[2],words[3],words[5]],'Computed pre-restore RNG state does not match'
        initialized=[row for row in report['observedPhaseInputs']if row['phase']=='Initialize'and row['stage']==input['stage']]
        assert len(initialized)==1 and initialized[0]['readyNs']==input['readyNs'] and initialized[0]['completionSource']=='original456133AfterSeedsRestoredBeforeGlobalsCopy'
    build=json.loads(build_path.read_bytes());assert build['wasmSha256']==report['wasmSha256']==sha((build_path.parent/'observer.wasm').read_bytes())
    assert len(build['objectBindings'])==141 and build['all141CoreObjectsRecompiled']
    fixture=Path(build['fixtureGraphRoot']);assert fixture.read_bytes()==(R/'runtimes/th12/th12_web/tests/cpp/th14-normal-vm-boundary-fixture-nov04.cpp').read_bytes()
    for row in build['objectBindings']:assert sha(Path(row['path']).read_bytes())==row['sha256']
    for path,digest in build['fixtureDependencyHashes'].items():assert sha(Path(path).read_bytes())==digest
    return dict(verifiedObservedVmInputContract=True,nativeInputProofSha256=sha(proof_bytes),modelReportSha256=sha(report_bytes),
        reviewedDriverSha256=sha(driver),driverGeneratorSha256=report['vmBoundaryDriverGeneratorSha256'],
        matchedVmIdentities=2,allInputsDelivered=True,workerReadyAndDeadlineSatisfied=True,
        sameStoppedDebugEventClockUsed=True,nativeRngOrSerialStateOverridden=False,
        ordinaryIndependentThreadTimingAccepted=False,completeGame=False,nativeEquivalent=False,
        contractVerifierSha256=sha(Path(__file__).read_bytes()))
