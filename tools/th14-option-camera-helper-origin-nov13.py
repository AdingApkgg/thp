"""Evaluate real camera helpers on the retained current transition poses."""
from pathlib import Path
import hashlib
import json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/option-refresh-oracle-nov13/current-replay'
q = json.loads((H / 'qualified.json').read_bytes())
assert q['allChildrenWorkersHostsGpuAndClockRetired']
assert q['firstRawDifferences']['camera75']['cppCallback'] == 30828
parent = R / 'tools/th14-menu-camera-derived-native-nov06.py'
source = parent.read_text(encoding='utf8')
cut = "model=ROOT/'artifacts/th14/file-wait-poll-nov06/menu-campaign-real'"
assert source.count(cut) == 1
source = source[:source.index(cut)]
source += r'''
H=ROOT/'artifacts/th14/option-refresh-oracle-nov13/current-replay'
N=ROOT/'artifacts/th14/low-pause-input-key-native-nov09/input-key-prefix'
nb=(N/'world-camera.raw').read_bytes();nt=(N/'world-camera-tail.u32').read_bytes()
cb=(H/'current-prefix/observations.u32').read_bytes()
assert len(nb)==35000*292 and len(nt)==35000*8 and len(cb)==35000*456
native=lambda i:nb[(i-1)*292:i*292]+nt[(i-1)*8:i*8]
current=lambda i:cb[(i-1)*456+132:(i-1)*456+432]
pose=lambda raw:raw[:96]+raw[224:]
cache=lambda raw:raw[96:224]
first=30828
assert all(pose(native(i))==pose(current(i))for i in range(1,35001))
poses={}
for i in range(first-300,first+1):
 poses.setdefault(pose(native(i)),dict(raw=native(i),callbacks=[]))['callbacks'].append(i)
def compute(entry,raw):
 m.mem_write(CAMERA,raw);matrices.clear();run(entry,[CAMERA])
 if entry==0x446250:
  assert not matrices
  run(0x4461e0,[CAMERA])
 assert [kind for kind,_ in matrices]==[2,3]
 output=bytes(m.mem_read(CAMERA,300))
 assert [output[96:160],output[160:224]]==[v for _,v in matrices]
 return output
targets={name:dict(cacheSha256=sha(cache(getter(first))),matches=[])
         for name,getter in [('native',native),('currentCpp',current)]}
inputs=bytearray();outputs=bytearray();cases=0;controls=0
for item in poses.values():
 for mode,entry in [('screen',0x446250),('perspective',0x446400)]:
  output=compute(entry,item['raw']);cases+=1;inputs.extend(item['raw']);outputs.extend(output)
  for name,getter in [('native',native),('currentCpp',current)]:
   if cache(output)==cache(getter(first)):
    targets[name]['matches'].append(dict(case=cases,mode=mode,poseCallbacks=item['callbacks']))
  if cases<=2:
   changed=bytearray(item['raw']);fov=struct.unpack_from('<f',changed,0x54)[0]
   struct.pack_into('<f',changed,0x54,fov*.875)
   assert cache(compute(entry,bytes(changed)))!=cache(output)
   controls+=1
service.stdin.close();service.wait(timeout=10);assert service.returncode==0,service.stderr.read()
(OUT/'inputs.u32').write_bytes(inputs);(OUT/'outputs.u32').write_bytes(outputs)
paths=[Path(__file__),ROOT/'tools/th14-menu-camera-derived-native-nov06.py',service_source,
       H/'qualified.json',H/'camera-measured-lineage.json',H/'current-prefix/observations.u32',
       N/'world-camera.raw',N/'world-camera-tail.u32']
result=dict(finiteCandidateAnalysisOnly=True,firstDifferentCallback=first,
 windowPrecedingCallbacks=300,uniquePoses=len(poses),actualOriginalHelperCases=cases,
 negativeFovControls=controls,targets=targets,actualWindowsX86D3dxServices=True,
 serviceExitCode=service.returncode,serviceControlfp=service_controlfp,serviceExited=True,
 serviceExeSha256=sha(service_exe.read_bytes()),originalExecutableSha256=sha(image.data),
 d3dxSha256=sha(dll.data),inputsSha256=sha(inputs),outputsSha256=sha(outputs),
 originalHelperEntries=['446250','446400','4461e0'],newGameOrGpuOrAudioStarted=False,
 physicalCopyTimestampOrWriterProven=False,productionChanged=False,wholeCameraGapClosed=False,
 completeGame=False,bindings={p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in paths})
(OUT/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','targets']}))
print(json.dumps(dict(targetModes={name:sorted(set(m['mode']for m in v['matches']))for name,v in targets.items()},
 targetMatchingCases={name:len(v['matches'])for name,v in targets.items()})))
'''
exec(compile(source, __file__, 'exec'), globals())
