"""Cross-check independent original-width D3D9 hardware fog against x64 reference.

No original process or visible window. All input floats are serialized once;
the x86 helper only submits their exact bits. No renderer production changes.
"""
import hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/gpu-stage-fog32'
sha=lambda b:hashlib.sha256(b).hexdigest()
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 native_path=ROOT/'artifacts/th14/gpu-stage-fog/native.json';native_bytes=native_path.read_bytes();native=json.loads(native_bytes)
 old_pixels=(native_path.parent/'native.bgra').read_bytes();assert sha(old_pixels)==native['pixelsSha256'];assert native['behaviorFlags']==64 and len(native['cases'])==7104
 for name,h in native['tools'].items():assert sha((ROOT/'tools'/name).read_bytes())==h
 request=bytearray(b'TH14FOG\0'+struct.pack('<I',len(native['cases']))+struct.pack('<16I',*native['texture']))
 colors=[0xc8b56e29,0x795ac4e8,0xea28cf7b,0x467c318e]
 for i,(x,y,z,u,v) in enumerate([(-.65,.65,1,-.25,-.125),(.65,.65,1,1.25,-.125),(-.65,-.65,2,-.25,1.125),(.65,-.65,2,1.25,1.125)]):request.extend(struct.pack('<3fI2f',x,y,z,colors[i],u,v))
 for case in native['cases']:
  scale=case['scale'];world=[[f32(v*scale) if i%4<3 else v for i,v in enumerate(m)] for m in native['worldMatrices']][case['world']]
  view=[[f32(v*scale) if i in (12,13,14) else v for i,v in enumerate(m)] for m in native['viewMatrices']][case['view']]
  projection=native['projectionMatrices'][case['projection']].copy()
  if case['projection']==0:projection[0]=projection[5]=f32(1/scale);projection[10]=f32(1/f32(f32(9.9)*scale))
  else:projection[14]=f32(-scale/f32(9.9))
  request.extend(struct.pack('<64f',*world,*view,*projection,*native['textureMatrix']))
  request.extend(struct.pack('<5I3f',case['fog'],case['range'],case['point'],case['textureTransform'],case['color'],case['near'],case['far'],case['density']))
 assert len(request)==12+64+96+7104*288
 requests=OUT/'requests.bin';requests.write_bytes(request);helper=OUT/'fog32.exe';reports=[]
 for precision in [24,53,64]:
  output=OUT/f'readback-{precision}.bin';subprocess.run([str(helper),str(requests),str(output),str(precision)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
  data=output.read_bytes();count,create_cw,reset_cw,vendor,device=struct.unpack_from('<5I',data);assert count==7104 and len(data)==20+count*4096;assert create_cw==0x7f;assert reset_cw&0x300=={24:0,53:0x200,64:0x300}[precision]
  pixels=data[20:];differences=[]
  for index in range(count):
   offset=index*4096;actual=pixels[offset:offset+4096];expected=old_pixels[offset:offset+4096]
   if actual!=expected:
    bad=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b];j=bad[0];differences.append(dict(index=index,channels=len(bad),maxDelta=max(abs(actual[i]-expected[i]) for i in bad),first=dict(x=j//4%32,y=j//128,channel=j%4,x86=actual[j],x64=expected[j])))
  report=dict(precision=precision,createFpcw=create_cw,postResetFpcw=reset_cw,cases=count,bytes=len(pixels),pixelsSha256=sha(pixels),x64PixelsSha256=sha(old_pixels),exactCases=count-len(differences),differences=differences,vendorId=vendor,deviceId=device)
  reports.append(report);print(json.dumps({k:v for k,v in report.items() if k!='differences'}),flush=True)
 result=dict(passed=all(not r['differences'] for r in reports),completeGame=False,nativeEquivalent=False,reports=reports,requestSha256=sha(request),nativeReferenceSha256=sha(native_bytes),helperSha256=sha(helper.read_bytes()),helperSourceSha256=sha((ROOT/'tools/th14-stage-fog32-helper.cpp').read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),d3d9Sha256=sha(Path('C:/Windows/SysWOW64/d3d9.dll').read_bytes()),x64D3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()),scope='7104 independent hidden D3D9 HAL hardware vertex-processing scenes, same serialized matrix/vertex/texture/state bits as original STD endpoint x64 reference. x86 default device PC24 and controlled post-device PC53/PC64 compared strictly; excludes actual retail draw loop, driver portability, whole frame/audio/natural clear.')
 (ROOT/'docs/porting/th14-gpu-stage-fog32-observed-oct12.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
 if not result['passed']:raise RuntimeError('x86 and x64 reference pixels differ; preserve report and inspect before production changes')
if __name__=='__main__':main()
