"""Bind TH14 Scene scheduler inputs to original before-copy instruction observations."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest();p=argparse.ArgumentParser(description=__doc__)
for name in ['native','model','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();n=a.native.resolve();m=a.model.resolve();out=a.output.resolve();assert all(x.is_relative_to(R/'artifacts/th14') for x in [n,m,out]) and not out.exists()
native_raw=(n/'report.json').read_bytes();native=json.loads(native_raw);model_raw=(m/'report.json').read_bytes();model=json.loads(model_raw);selected=(n/'selected-state.u32').read_bytes();count=model['callbacks'];assert model['schedulerPhases']=='observed' and model['completed'] and len(selected)==native['callbacks']*128 and len(selected)>=count*128 and sha(selected)==native['selectedSha256']
allowed={sha((R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs').read_bytes()),sha((R/'tools/th14-compare-native-extra-campaign-nov01.mjs').read_bytes())};assert model['comparisonToolSha256'] in allowed,'Unreviewed Scene scheduler driver'
first=struct.unpack_from('<I',selected,120)[0];last=first;active=set()
for i in range(count):
 stage=struct.unpack_from('<I',selected,i*128+120)[0];frame=struct.unpack_from('<I',selected,i*128)[0];assert 1<=stage<=7 and stage>=last;last=stage
 if stage!=first and frame>0:active.add(stage)
eventfile=n/'scene-camera-copy-events.jsonl';raw=eventfile.read_bytes() if eventfile.exists() else b'';events=[json.loads(x) for x in raw.splitlines() if x]
if raw:assert native['sceneCameraCopyEventsSha256']==sha(raw)
else:assert not native.get('sceneCameraCopyEventsSha256')
inputs=[x for x in model['observedPhaseInputs'] if x['phase']=='Scene'];assert len(inputs)==len({x['stage'] for x in inputs}) and active<={x['stage'] for x in inputs},'Missing Scene input for active stage'
for item in inputs:
 candidates=[e for e in events if e['stage']==item['stage'] and e['event']=='scene-camera-copy-before'];assert len(candidates)==1,'Missing unique original Scene before-copy event';event=candidates[0]
 assert event['readOnly'] and event['pc']==0x40d435 and item['completionSource']=='original40d435BeforeSceneCameraCopy' and item['readyNs']==event['hostMonotonicNs'],'Unverified Scene timing source'
result=dict(passed=True,scope='Binds declared Scene input to the original before-copy timestamp and an explicitly reviewed scheduler driver. Does not prove copying was atomic, its per-word ordering, actual independent scheduling or whole gameplay.',activeLaterStages=sorted(active),sceneInputs=len(inputs),driverSha256=model['comparisonToolSha256'],nativeReportSha256=sha(native_raw),nativeSceneEventsSha256=sha(raw) if raw else None,modelReportSha256=sha(model_raw),completeGame=False,nativeEquivalent=False,verifierSha256=sha(Path(__file__).read_bytes()))
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
