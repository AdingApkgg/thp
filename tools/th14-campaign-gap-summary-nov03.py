"""Independently count retained selected, camera and HUD differences for a TH14 capture."""
from pathlib import Path
import argparse,collections,hashlib,json,struct
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest();p=argparse.ArgumentParser(description=__doc__)
for x in ['native','model','output']:p.add_argument('--'+x,type=Path,required=True)
a=p.parse_args();N=a.native.resolve();M=a.model.resolve();O=a.output.resolve();assert all(x.is_relative_to(R/'artifacts/th14') for x in [N,M,O]) and not O.exists()
n=json.loads((N/'report.json').read_bytes());m=json.loads((M/'report.json').read_bytes());count=m['callbacks'];assert 0<count<=n['callbacks'] and m['completed'];left=(N/'selected-state.u32').read_bytes();right=(M/'selected-state.u32').read_bytes();assert len(left)>=count*128 and len(right)==count*128 and sha(left)==n['selectedSha256'] and sha(right)==m['selectedSha256'];counts=collections.Counter();first={}
for i in range(count):
 x=struct.unpack_from('<32I',left,i*128);y=struct.unpack_from('<32I',right,i*128)
 for j,(u,v) in enumerate(zip(x,y)):
  if u!=v:counts[str(j)]+=1;first.setdefault(str(j),dict(index=i,stage=x[30],stageFrame=x[0],native=u,portable=v))
assert dict(counts)==m['differenceCounts']
cam=(N/'world-camera.raw').read_bytes();pm=(M/'portable-camera.u32').read_bytes();offsets=[*range(0,88,4),0x104,0x108,0x10c];assert len(cam)>=count*0x124 and len(pm)==count*100;camera=collections.Counter();camera_first={}
for i in range(count):
 for j,off in enumerate(offsets):
  x=struct.unpack_from('<I',cam,i*0x124+off)[0];y=struct.unpack_from('<I',pm,i*100+j*4)[0]
  if x!=y:camera[str(j)]+=1;camera_first.setdefault(str(j),dict(index=i,stage=struct.unpack_from('<I',left,i*128+120)[0],stageFrame=struct.unpack_from('<I',left,i*128)[0],native=x,portable=y))
camera_report=json.loads((M/'camera-report.json').read_bytes());assert dict(camera)==camera_report['counts']
hud=(N/'hud-score.u32').read_bytes();ph=(M/'portable-hud.u32').read_bytes();assert len(hud)>=count*8 and len(ph)==count*8;hud_counts=collections.Counter();hud_first={}
for i in range(count):
 for j in range(2):
  x=struct.unpack_from('<I',hud,i*8+j*4)[0];y=struct.unpack_from('<I',ph,i*8+j*4)[0]
  if x!=y:hud_counts[str(j)]+=1;hud_first.setdefault(str(j),dict(index=i,native=x,portable=y))
live=json.loads((M/'live-report.json').read_bytes());combat=json.loads((M/'combat-snapshots.json').read_bytes())
result=dict(passedIndependentDifferenceCount=True,callbacks=count,selectedDifferenceCounts=dict(counts),selectedFirst=first,cameraDifferenceCounts=dict(camera),cameraFirst=camera_first,hudDifferenceCounts=dict(hud_counts),hudFirst=hud_first,reportedVmValuesEqual=live['allLiveValuesEqual'],reportedCombatWordsEqual=combat['allCapturedCombatWordsEqual'],vmAndCombatReportsNotIndependentlyRecomputedHere=True,sourceReplayEofProved=False,completeGame=False,nativeEquivalent=False,nativeReportSha256=sha((N/'report.json').read_bytes()),modelReportSha256=sha((M/'report.json').read_bytes()),toolSha256=sha(Path(__file__).read_bytes()))
O.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
