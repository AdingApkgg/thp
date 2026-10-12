"""Measure D16 writes for authored constant screen-depth quads on installed HAL."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/stage-gpu-stream-replay/depth-quantization';OUT.mkdir(exist_ok=True)
base=ROOT/'tools/th14-stage-depth-readback-native.py';s=base.read_text()
s=s.replace("OUT=ROOT/'artifacts/th14/stage-gpu-stream-replay/depth-reference'","REFERENCE=ROOT/'artifacts/th14/stage-gpu-stream-replay/depth-reference';OUT=ROOT/'artifacts/th14/stage-gpu-stream-replay/depth-quantization'")
s=s.replace("(OUT/'reference.json')","(REFERENCE/'reference.json')").replace("(OUT/'nvapi_interface.h')","(REFERENCE/'nvapi_interface.h')")
s=s.replace('for fmt in (114,21):','for fmt in (114,):')
anchor='            for value in (0,.25,.5,.75,1):';assert anchor in s
s=s.replace(anchor,'''            words={0,0x3f800000,0x3f000000,0x3e800000,0x3f400000,0x3f666666}
            for k in (0,1,2,32,100,1000,16000,32767,32768,50000,59818,60027,62314,65534):
                for bias in (0,.25,.5,.75,1):
                    v=max(0,min(1,(k+bias)/65535));w=struct.unpack('<I',struct.pack('<f',v))[0]
                    for d in (-2,-1,0,1,2):
                        if 0<=w+d<=0x3f800000:words.add(w+d)
            values=[struct.unpack('<f',struct.pack('<I',w))[0] for w in sorted(words)]
            for value in values:''')
anchor="                call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,2,0,value,0]);r=copy(device,depth,None,tex,None,0);sample=dict(clearDepth=value,copyStatus=r);row['samples'].append(sample)"
assert anchor in s
s=s.replace(anchor,'''
                call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,3,0,1,0])
                for key,v in ((7,1),(14,1),(15,0),(22,1),(23,8),(27,0),(28,0),(137,0)):call(device,'IDirect3DDevice9','SetRenderState',[U,U],[key,v])
                for key,v in ((1,2),(2,0),(4,2),(5,0)):call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[0,key,v])
                call(device,'IDirect3DDevice9','SetFVF',[U],[0x44])
                z=struct.unpack('<I',struct.pack('<f',value))[0];fword=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
                quad=(U*20)(fword(0),fword(0),z,fword(1),0xffffffff,fword(64),fword(0),z,fword(1),0xffffffff,fword(0),fword(64),z,fword(1),0xffffffff,fword(64),fword(64),z,fword(1),0xffffffff)
                call(device,'IDirect3DDevice9','BeginScene',[],[]);call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,C.byref(quad),20]);call(device,'IDirect3DDevice9','EndScene',[],[])
                r=copy(device,depth,None,tex,None,0);sample=dict(inputDepth=value,inputWord=z,copyStatus=r);row['samples'].append(sample)
''')
anchor="                (OUT/('probe-%d-%s.bin'%(fmt,str(value)))).write_bytes(raw)";assert anchor in s
s=s.replace(anchor,"                assert all(raw[i:i+4]==raw[:4] for i in range(0,len(raw),4));sample['d16']=round(sample['firstFloat']*65535)")
s=s.replace("(OUT/'probe.json')","(OUT/'native.json')").replace("print(json.dumps(rows))","print('Measured D16 constant-depth quad writes',len(rows[-1]['samples']))")
s=s.replace('Hidden own 64x64 D16 surface clear and NVAPI capability/readback probe. No game draws or retail depth capture; failed conversions retained.','Hidden own 64x64 D16 surface with constant screen-depth quad writes. Float32 neighbor inputs, all readback pixels uniform, installed NVAPI conversion. No world gradients, retail game framebuffer or cross-device equivalence.')
generated=ROOT/'tools/th14-stage-depth-quantization-hal.py';generated.write_text(s)
runpy.run_path(str(generated),run_name='__main__')
sha=lambda b:hashlib.sha256(b).hexdigest();n=json.loads((OUT/'native.json').read_bytes());samples=n['rows'][-1]['samples']
import math
models={name:sum(fn(r['inputDepth'])!=r['d16'] for r in samples) for name,fn in {'floor':lambda z:math.floor(z*65535),'nearest':lambda z:math.floor(z*65535+.5),'tiesDown':lambda z:math.ceil(z*65535-.5)}.items()}
(OUT/'generation.json').write_text(json.dumps(dict(generatorSha256=sha(Path(__file__).read_bytes()),baseSha256=sha(base.read_bytes()),generatedSha256=sha(generated.read_bytes()),nativeSha256=sha((OUT/'native.json').read_bytes()),samples=len(samples),mismatches=models),indent=2)+'\n')
print(models)
