"""Select real portrait lifecycle frames for controlled offscreen raster tests."""
import hashlib,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/dialogue-panel-gpu';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
proof_path=ROOT/'docs/porting/th14-dialogue-panel-geometry-verified-oct12.json';proof=json.loads(proof_path.read_text(encoding='utf-8'));assert proof['passed']
native_path=ROOT/'artifacts/th14/dialogue-panel-geometry-native.json';native_bytes=native_path.read_bytes();assert sha(native_bytes)==proof['nativeProofSha256'];native=json.loads(native_bytes)
for path,h in proof['sourceHashes'].items():assert sha((ROOT/'runtimes/th12/th12_web'/path).read_bytes())==h,path
for key,path in [('fixtureSha256','runtimes/th12/th12_web/tests/cpp/th14-dialogue-panel-geometry-fixture.cpp'),('toolSha256','tools/th14-dialogue-panel-geometry-check.mjs'),('nativeToolSha256','tools/th14-dialogue-panel-geometry-native.py')]:assert sha((ROOT/path).read_bytes())==proof[key]
extraction=Path(json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text())['extraction']);cases=[];offset=0;textures={}
for name,h in native['resourceHashes'].items():
 data=(extraction/name).read_bytes();assert sha(data)==h;chunk=0;records=[]
 while True:
  width,height,fmt=struct.unpack_from('<HHH',data,chunk+10);tex=struct.unpack_from('<I',data,chunk+28)[0]+chunk;assert data[chunk+32] and data[tex:tex+4]==b'THTX';pixel_format,pw,ph,size=struct.unpack_from('<HHHI',data,tex+6);assert pixel_format==fmt and fmt in (1,3,5,7);assert pw<=width and ph<=height
  bpp={1:4,3:2,5:2,7:1}[fmt];raw=data[tex+16:tex+16+size];assert len(raw)==pw*ph*bpp;out_bpp=4 if fmt==7 else bpp;pixels=bytearray(width*height*out_bpp)
  for y in range(ph):
   row=raw[y*pw*bpp:(y+1)*pw*bpp]
   if fmt==7:row=b''.join(bytes([v,v,v,255]) for v in row)
   pixels[y*width*out_bpp:y*width*out_bpp+pw*out_bpp]=row
  texture_file=name+'.'+str(len(records))+'.pixels';(OUT/texture_file).write_bytes(pixels);records.append(dict(file=texture_file,width=width,height=height,format={1:21,3:23,5:26,7:21}[fmt],pitch=width*out_bpp,bytes=len(pixels),sha256=sha(pixels),sourceFormat=fmt,pixelWidth=pw,pixelHeight=ph))
  stride=struct.unpack_from('<I',data,chunk+36)[0]
  if not stride:break
  chunk+=stride
 textures[name]=records
for row_index,row in enumerate(native['rows']):
 for frame in sorted(set([0,12,45,60,90,len(row['frames'])-1])):
  if frame>=len(row['frames']):continue
  source=row['frames'][frame];vertices=[v for d in source['draws'] for v in d['vertices']]
  if vertices:
   left=max(0,math.floor(min(v[0] for v in vertices))-2);top=max(0,math.floor(min(v[1] for v in vertices))-2);right=min(640,math.ceil(max(v[0] for v in vertices))+3);bottom=min(480,math.ceil(max(v[1] for v in vertices))+3)
   if left>=right or top>=bottom:left=top=0;right=bottom=1
  else:left=top=0;right=bottom=1
  crop=[left,top,right-left,bottom-top];size=crop[2]*crop[3]*4
  cases.append(dict(index=len(cases),row=row_index,input=row['input'],filename=native['roots'][row['input'][0]][0],frame=frame,events=[dict(frame=e['frame'],label=e['label']) for e in row['events'] if e['frame']<=frame],crop=crop,offset=offset,size=size,draws=source['draws']));offset+=size
report=dict(prepared=True,completeGame=False,nativeEquivalent=False,cases=cases,bytes=offset,textures=textures,resourceHashes=native['resourceHashes'],nativeGeometrySha256=sha(native_bytes),geometryProofSha256=sha(proof_path.read_bytes()),nativeExecutableSha256=native['executableSha256'],nativeD3dxSha256=native['d3dxSha256'],prepareToolSha256=sha(Path(__file__).read_bytes()),scope='Six selected frames per288 real panel lifecycle routes, widths32/128/384 at rates0.5/1/1.25, deferred/synchronous labels and two sequences. Actual original recorded vertices/materials submitted to HAL; port regenerates every preceding frame through actual AnmManager factories and ANM and production AnmRenderer, then current production SDL/WebGL Renderer. Original embedded THTX pixels independently parsed, padded at top left with zero bytes in declared surface format, grayscale expanded to BGRA. Controlled alpha threshold1, non-fog/depth-test-disabled screen pipeline, no original full texture loader/batch implementation/full MSG/world/whole-game raster claim. Native shared screen vertex RHW initialized1.')
(OUT/'prepared.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('Prepared panel GPU',len(cases),offset,'bytes',sum(len(v) for v in textures.values()),'textures')
