"""Independently compare retained full-session observations to the original.

Live snapshots are explicitly incomplete and never accept a replay or schedule.
The comparison includes all 32 selected words, 75 camera words and two HUD words.
"""
from pathlib import Path
import argparse,collections,hashlib,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda data:hashlib.sha256(data).hexdigest()

def main(home,native,output,live,comparison_only=False):
 home=home.resolve();native=native.resolve();output=output.resolve()
 assert all(path.is_relative_to(R/'artifacts/th14')for path in [home,native,output]) and not output.exists()
 bindings={}
 def raw(path):
  data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
 def read(path):return json.loads(raw(path))
 plan=read(home/'plan.json');original=read(native/'report.json')
 report=read(home/('progress.json'if live else 'report.json'))
 assert report['terminal'] is (not live)
 assert original['childExited'] and not original['error']
 primary_reference=plan['bindings']['nativeReportSha256']==SHA(raw(native/'report.json'))
 assert primary_reference or comparison_only,'A different native run must be explicitly comparison-only'
 assert original['sourceFullReplaySha256']==plan['bindings']['replaySha256']
 expected=raw(native/'selected-state.u32');camera=raw(native/'world-camera.raw');tail=raw(native/'world-camera-tail.u32');hud=raw(native/'hud-score.u32')
 assert SHA(expected)==original['selectedSha256'] and len(expected)==original['callbacks']*128
 assert len(camera)==original['callbacks']*292 and len(tail)==len(hud)==original['callbacks']*8
 data=raw(home/'observations.u32');stride=114*4;full_rows,partial=divmod(len(data),stride)
 if not live:assert partial==0 and full_rows==report['callbacks']
 count=min(report['callbacks'],full_rows)
 assert count>0
 selected_counts=collections.Counter();camera_counts=collections.Counter();hud_counts=collections.Counter()
 stages=collections.Counter();first=None;first_stage={}
 compared=min(count,original['callbacks']);last_stage=0
 for index in range(count):
  row=struct.unpack_from('<114I',data,index*stride);assert row[0]==index+1
  stage=row[31];assert last_stage<=stage<=6 and stage>=1;last_stage=stage;stages[stage]+=1
  if index>=compared:continue
  expected_selected=struct.unpack_from('<32I',expected,index*128)
  differences=[n for n,(a,b)in enumerate(zip(row[1:33],expected_selected))if a!=b]
  selected_counts.update(differences)
  if differences:
   item=dict(callback=index+1,stage=stage,fields=differences)
   if first is None:first=item
   first_stage.setdefault(stage,item)
  expected_camera=struct.unpack_from('<73I',camera,index*292)+struct.unpack_from('<2I',tail,index*8)
  camera_counts.update(n for n,(a,b)in enumerate(zip(row[33:108],expected_camera))if a!=b)
  expected_hud=struct.unpack_from('<2I',hud,index*8)
  hud_counts.update(n for n,(a,b)in enumerate(zip(row[108:110],expected_hud))if a!=b)
 def string_keys(value):return {str(k):v for k,v in sorted(value.items())}
 if not live and primary_reference:
  assert string_keys(selected_counts)==report['differenceCounts']
  assert string_keys(camera_counts)==report['camera75DifferenceCounts']
  assert string_keys(hud_counts)==report['hudDifferenceCounts']
  assert first==report['firstDifference'] and compared==report['nativeComparedCallbacks']
  assert string_keys(stages)==report['stageCounts']
  assert SHA(data)==report['observationsSha256']
 event_path=home/'delivery-events.u32';groups={}
 if event_path.exists():
  events=raw(event_path);assert len(events)%48==0
  for row in struct.iter_unpack('<12I',events):
   kind,stage,generation,detail,*_=row;assert kind in [1,2,3,4,5,6]
   group=groups.setdefault(generation,dict(stage=stage,kinds=[],operations=[],resourceFinished=False,cancelled=False))
   assert group['stage']==stage;group['kinds'].append(kind)
   if kind in [3,4]:group['operations'].append(detail)
   if kind==6:group['resourceFinished']=True
   if kind==5:group['cancelled']=True
  for group in groups.values():
   operations=group['operations'];assert operations==list(range(len(operations))) and len(operations)<=4
   if group['resourceFinished']:assert operations==[0,1,2,3]
 else:assert last_stage==1
 complete_groups=sum(group['resourceFinished']for group in groups.values())
 strict=compared==original['callbacks'] and not selected_counts and not camera_counts and not hud_counts
 if not live and primary_reference:assert report['strictOriginalPrefixPassed']==strict
 result=dict(schema='th14/independent-full-session-raw-comparison/1',
  rawDataStructureAndReportedComparisonVerified=True,liveSnapshotOnly=live,runTerminal=not live,
  primaryDriverComparisonRecomputed=primary_reference,additionalComparisonOnlyReference=not primary_reference,
  primaryStrictGatesSuperseded=False,
  callbacksVerified=count,completeRowsObserved=full_rows,unverifiedPartialTailBytes=partial,
  nativeComparedCallbacks=compared,nativeCapturedCallbacks=original['callbacks'],
  selectedWordCount=32,cameraWordCount=75,hudWordCount=2,
  selectedDifferenceCounts=string_keys(selected_counts),camera75DifferenceCounts=string_keys(camera_counts),hudDifferenceCounts=string_keys(hud_counts),
  firstDifference=first,firstByStage=first_stage,stageCounts=string_keys(stages),
  deliveryGroups=groups,fullResourceOwnersFinishedWithFourOperations=complete_groups,
  strictOriginalPrefixPassed=strict,coldNativeBootstrapReproduced=False,
  independentNativeSchedulingAccepted=False,wholeReplayAccepted=False,completeGame=False,nativeEquivalent=False,
  evidenceBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()))
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(rawDataVerified=True,liveSnapshotOnly=live,callbacks=count,stages=sorted(stages),
  fourStepResourceCompletions=complete_groups,selectedDifferenceFields=len(selected_counts),
  cameraDifferenceFields=len(camera_counts),hudDifferenceFields=len(hud_counts),strictOriginalPrefixPassed=strict,completeGame=False)))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['run','native','output']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--live',action='store_true')
 p.add_argument('--comparison-only-reference',action='store_true',help='Compare the same replay against another immutable native run without replacing the primary driver gates')
 a=p.parse_args();main(a.run,a.native,a.output,a.live,a.comparison_only_reference)
