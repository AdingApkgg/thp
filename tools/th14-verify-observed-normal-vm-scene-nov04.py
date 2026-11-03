"""Apply the existing Scene assertions to the independently bound VM-input adapter."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, struct
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()
p=argparse.ArgumentParser(description=__doc__)
for name in ['native','model','build','normal-vm-inputs','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();n=a.native.resolve();m=a.model.resolve();out=a.output.resolve()
assert all(path.is_relative_to(R/'artifacts/th14')for path in(n,m,out))and not out.exists()
base=R/'tools/th14-verify-native-scene-boundaries-nov03.py'
assert sha(base.read_bytes())=='1d5eb0a1c8769542ca8e4bcfc42a38a6c0262ba939306dc588eec6a877a864e4'
spec=importlib.util.spec_from_file_location('vm_input_contract',R/'tools/th14-normal-vm-input-contract-nov04.py');contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
bound=contract.validate(n,m,a.build,a.normal_vm_inputs)
# Retain every original Scene payload, coverage, source and clock assertion.
native_raw=(n/'report.json').read_bytes();native=json.loads(native_raw);model_raw=(m/'report.json').read_bytes();model=json.loads(model_raw);selected=(n/'selected-state.u32').read_bytes();count=model['callbacks']
assert model['schedulerPhases']=='observed'and model['completed']and len(selected)==native['callbacks']*128 and len(selected)>=count*128 and sha(selected)==native['selectedSha256']
assert model['comparisonToolSha256']==bound['reviewedDriverSha256']
first=struct.unpack_from('<I',selected,120)[0];last=first;active=set()
for i in range(count):
    stage=struct.unpack_from('<I',selected,i*128+120)[0];frame=struct.unpack_from('<I',selected,i*128)[0];assert 1<=stage<=7 and stage>=last;last=stage
    if stage!=first and frame>0:active.add(stage)
eventfile=n/'scene-camera-copy-events.jsonl';raw=eventfile.read_bytes()if eventfile.exists()else b'';events=[json.loads(x)for x in raw.splitlines()if x]
if raw:assert native['sceneCameraCopyEventsSha256']==sha(raw)
else:assert not native.get('sceneCameraCopyEventsSha256')
inputs=[x for x in model['observedPhaseInputs']if x['phase']=='Scene'];assert len(inputs)==len({x['stage']for x in inputs})and active<={x['stage']for x in inputs}
for item in inputs:
    candidates=[e for e in events if e['stage']==item['stage']and e['event']=='scene-camera-copy-before'];assert len(candidates)==1;event=candidates[0]
    assert event['readOnly']and event['pc']==0x40d435 and item['completionSource']=='original40d435BeforeSceneCameraCopy'and item['readyNs']==event['hostMonotonicNs']
result=dict(passed=True,scope='Existing Scene payload and clock checks plus a regenerated driver and independently verified original VM-input contract.',
    activeLaterStages=sorted(active),sceneInputs=len(inputs),driverSha256=model['comparisonToolSha256'],
    nativeReportSha256=sha(native_raw),nativeSceneEventsSha256=sha(raw)if raw else None,modelReportSha256=sha(model_raw),
    baseVerifierSha256=sha(base.read_bytes()),observedVmInputContract=bound,verifierSha256=sha(Path(__file__).read_bytes()),completeGame=False,nativeEquivalent=False)
out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result))
