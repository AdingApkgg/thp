"""Read unblended shape interpolation in actual native/portable RGBA32F targets."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'artifacts/th14/gpu-original-shapes/float';OUT.mkdir(parents=True,exist_ok=True)
prepared=json.loads((ROOT/'artifacts/th14/gpu-original-shapes/prepared.json').read_bytes())
for row in prepared['cases']:row['offset']*=4;row['size']*=4
prepared['bytes']*=4;prepared['scope']='Unblended RGBA32F output isolates source color interpolation; not the blended RGBA8 shape acceptance test.'
prepared['prepareToolSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(OUT/'prepared.json').write_text(json.dumps(prepared,indent=2)+'\n',encoding='utf8')
native=(ROOT/'tools/th14-gpu-original-shapes-native.py').read_text(encoding='utf8')
native=native.replace("OUT=ROOT/'artifacts/th14/gpu-original-shapes'","OUT=ROOT/'artifacts/th14/gpu-original-shapes/float'")
assert native.count('[640,480,21,')==2
native=native.replace('[640,480,21,','[640,480,116,').replace('(27,1)','(27,0)')
native=native.replace('lock.bits+y*lock.pitch+left*4,width*4','lock.bits+y*lock.pitch+left*16,width*16')
native=native.replace("OUT/'native.bgra'","OUT/'native.rgba32f'")
native=native.replace('report=dict(generated=True,','report=dict(generated=True,outputFormat="A32B32G32R32F",outputByteOrder="RGBA float32 little endian",blendingEnabled=False,')
native=native.replace('controlled blend/alpha and disabled fog/depth','unblended RGBA32F source color interpolation with alpha test and disabled fog/depth')
(ROOT/'tools/th14-gpu-original-shapes-float-native.py').write_text(native,encoding='utf8')
fixture=(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-original-shapes-fixture.cpp').read_text(encoding='utf8')
fixture=fixture.replace('640*480*4','640*480*16').replace('PixelFormat::Bgra8,2560','PixelFormat::Bgra8,10240')
fixture=fixture.replace('r.pipeline().depthTest=false','r.pipeline().blend=false;r.pipeline().depthTest=false')
fixture=fixture.replace('y*crop[2]*4','y*crop[2]*16').replace('crop[0])*4','crop[0])*16').replace('crop[2]*4);','crop[2]*16);')
(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-original-shapes-float-fixture.cpp').write_text(fixture,encoding='utf8')
print('Prepared native and production-geometry unblended RGBA32F shape fixtures')
