"""Diagnostic unique stage/frame pairing; physical-order strict gates stay intact."""
from pathlib import Path
import argparse,collections,hashlib,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda data:hashlib.sha256(data).hexdigest()

def main(home,native,output,live):
 home=home.resolve();native=native.resolve();output=output.resolve()
 assert all(path.is_relative_to(R/'artifacts/th14')for path in [home,native,output])and not output.exists()
 plan_raw=(home/'plan.json').read_bytes();plan=json.loads(plan_raw)
 progress_raw=(home/('progress.json'if live else 'report.json')).read_bytes();progress=json.loads(progress_raw)
 assert progress['terminal'] is (not live)
 native_raw=(native/'report.json').read_bytes();original=json.loads(native_raw)
 assert original['childExited'] and not original['error']
 assert original['sourceFullReplaySha256']==plan['bindings']['replaySha256']
 model_raw=(home/'observations.u32').read_bytes();expected=(native/'selected-state.u32').read_bytes()
 assert len(expected)==original['callbacks']*128 and SHA(expected)==original['selectedSha256']
 camera=(native/'world-camera.raw').read_bytes();tail=(native/'world-camera-tail.u32').read_bytes();hud=(native/'hud-score.u32').read_bytes()
 assert len(camera)==original['callbacks']*292 and len(tail)==len(hud)==original['callbacks']*8
 complete,partial=divmod(len(model_raw),456)
 if not live:assert not partial and complete==progress['callbacks']
 count=min(progress['callbacks'],complete);models=collections.defaultdict(list);references=collections.defaultdict(list)
 for index in range(count):
  row=struct.unpack_from('<32I',model_raw,index*456+4);models[(row[30],row[0])].append((index+1,row))
 for index in range(original['callbacks']):
  row=struct.unpack_from('<32I',expected,index*128);references[(row[30],row[0])].append((index+1,row))
 counts=collections.Counter();stages=collections.Counter();ambiguous=[];shots=[];first={};pairs=0
 camera_counts=collections.Counter();hud_counts=collections.Counter();first_camera={};first_hud={}
 offsets=collections.defaultdict(collections.Counter)
 for key in sorted(models.keys()&references.keys()):
  a=models[key];b=references[key]
  if len(a)!=1 or len(b)!=1:
   ambiguous.append(dict(stage=key[0],frame=key[1],modelRows=len(a),nativeRows=len(b)));continue
  pairs+=1;stages[key[0]]+=1;offsets[key[0]][a[0][0]-b[0][0]]+=1
  actual=a[0][1];expected_row=b[0][1]
  for field in range(32):
   if actual[field]!=expected_row[field]:
    counts[field]+=1;first.setdefault(field,dict(stage=key[0],frame=key[1],modelCallback=a[0][0],nativeCallback=b[0][0]))
  if actual[26]!=expected_row[26]:shots.append(dict(stage=key[0],frame=key[1],modelCallback=a[0][0],nativeCallback=b[0][0],modelCount=actual[26],nativeCount=expected_row[26]))
  model_index=a[0][0]-1;native_index=b[0][0]-1
  camera_actual=struct.unpack_from('<75I',model_raw,model_index*456+33*4)
  camera_expected=struct.unpack_from('<73I',camera,native_index*292)+struct.unpack_from('<2I',tail,native_index*8)
  hud_actual=struct.unpack_from('<2I',model_raw,model_index*456+108*4);hud_expected=struct.unpack_from('<2I',hud,native_index*8)
  for values,reference,counter,firsts in [(camera_actual,camera_expected,camera_counts,first_camera),(hud_actual,hud_expected,hud_counts,first_hud)]:
   for field,(left,right)in enumerate(zip(values,reference)):
    if left!=right:
     counter[field]+=1;firsts.setdefault(field,dict(stage=key[0],frame=key[1],modelCallback=a[0][0],nativeCallback=b[0][0]))
 result=dict(schema='th14/independent-session-unique-stage-frame-pairs/1',
  verifiedDiagnosticPairing=True,liveSnapshotOnly=live,modelCallbacksInSnapshot=count,
  nativeCallbacks=original['callbacks'],uniquePairs=pairs,pairedByStage=dict(stages),ambiguousFrameKeysExcluded=ambiguous,
  differenceCounts=dict(counts),firstByField=first,shotCountDifferences=shots,
  camera75DifferenceCounts=dict(camera_counts),camera75FirstByField=first_camera,hudDifferenceCounts=dict(hud_counts),hudFirstByField=first_hud,
  observedCallbackOffsetCounts={stage:dict(value)for stage,value in offsets.items()},
  primaryNativeReference=SHA(native_raw)==plan['bindings']['nativeReportSha256'],
  ambiguousLoadingOrSlowdownFramesNotAccepted=True,rawStrictGatesSuperseded=False,
  engineStateOrTimingChanged=False,originalValuesProvidedToEngine=False,
  exactSchedulingAccepted=False,wholeReplayAccepted=False,completeGame=False,nativeEquivalent=False,
  bindings=dict(planSha256=SHA(plan_raw),modelProgressOrReportSha256=SHA(progress_raw),modelSnapshotSha256=SHA(model_raw),
   modelSnapshotBytes=len(model_raw),nativeReportSha256=SHA(native_raw),nativeSelectedSha256=SHA(expected),
   nativeCameraSha256=SHA(camera),nativeCameraTailSha256=SHA(tail),nativeHudSha256=SHA(hud)),
  toolSha256=SHA(Path(__file__).read_bytes()))
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(verifiedDiagnosticPairing=True,live=live,pairs=pairs,stages=sorted(stages),
  fields=sorted(counts),cameraFields=sorted(camera_counts),hudFields=sorted(hud_counts),shotCountDifferences=len(shots),rawStrictGatesSuperseded=False,completeGame=False)))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['run','native','output']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--live',action='store_true');a=p.parse_args();main(a.run,a.native,a.output,a.live)
