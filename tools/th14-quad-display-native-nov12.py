"""Actual TH14 flat/rotated draw helpers over declared display inputs."""
from pathlib import Path
import hashlib,importlib,itertools,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/quad-display-space-nov12';rotations='--rotations'in sys.argv;H=H/'rotations'if rotations else H;assert not H.exists();H.mkdir()
P=R/'artifacts/th14/mode8-display-space-nov12';meta=json.loads((P/'native.json').read_bytes());inputs=(P/'inputs.bin').read_bytes();assert hashlib.sha256(inputs).hexdigest()==meta['inputSha256']
sys.path.insert(0,str(R/'tools'));image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert hashlib.sha256(image.data).hexdigest()==meta['executableSha256']
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,offset,n in image.sections:
 first=va&~4095;m.mem_map(first,((va+size+4095)&~4095)-first);m.mem_write(va,image.data[offset:offset+n])
B=0x70000000;VM=B+0x1000;PARENT=B+0x3000;OUTPUT=B+0x7000;STACK=B+0xff000;STOP=B+0xfe000;m.mem_map(B,0x100000);m.mem_write(0x4854a0,b'\xc3')
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
rows=[];expected=bytearray();selected_inputs=bytearray();anchors=[(0,0),(1,2),(2,1)]
for index,row in enumerate(meta['rows']):
 if row['dirty'] or row['freeze']:continue
 raw=bytearray(inputs[index*meta['inputStrideBytes']:(index+1)*meta['inputStrideBytes']]);assert len(raw)==3000
 # New declared finite sprite dimensions; not measurements from a game run.
 struct.pack_into('<2f',raw,32+0x80,*(([137.25,61.125],[.1,13.3])[row['sample']]))
 if rotations:
  struct.pack_into('<f',raw,32+0x50,[.375,-.625][row['sample']]);struct.pack_into('<f',raw,32+1484+0x50,[-.25,.75][row['sample']])
 selected_index=len(selected_inputs)//3000;selected_inputs.extend(raw)
 width,height,scale,ox,oy,sx,sy,parent=struct.unpack_from('<8I',raw)
 for address,value in [(0x4f7a64,width),(0x4f7a68,height),(0x4f7a6c,scale),(0x4f7a80,ox),(0x4f7a84,oy),(0x4f7a88,sx),(0x4f7a8c,sy)]:put(address,value)
 for mode,anchor in itertools.product(range(4),range(3)):
  m.mem_write(VM,bytes(raw[32:32+1484]));m.mem_write(PARENT,bytes(raw[32+1484:]));put(VM+0x594,PARENT if parent else 0)
  flags=struct.unpack_from('<I',raw,32+0x18)[0];ax,ay=anchors[anchor];put(VM+0x18,(flags&~((31<<25)|(3<<21)|(3<<23)))|(mode<<25)|(ax<<21)|(ay<<23))
  before=bytes(m.mem_read(VM,1484));m.mem_write(OUTPUT,bytes(48));m.mem_write(STACK,struct.pack('<6I',STOP,VM,OUTPUT,OUTPUT+12,OUTPUT+24,OUTPUT+36))
  for reg,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_MXCSR,0x1f80),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:m.reg_write(reg,value)
  entry=0x4766e0 if mode in [1,3] else 0x476100;m.emu_start(entry,STOP,count=100000)
  assert m.reg_read(UC_X86_REG_EIP)==STOP and bytes(m.mem_read(VM,1484))==before
  expected.extend(m.mem_read(OUTPUT,48));rows.append(dict(input=selected_index,mode=mode,anchor=anchor,width=width,height=height))
assert len(rows)==6912 and len(selected_inputs)==576*3000
(H/'inputs.bin').write_bytes(selected_inputs);(H/'outputs.u32').write_bytes(expected)
for name in ['AnmRenderer.cpp']:
 dest=H/'baseline-source'/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes((R/'runtimes/th12/th12_web/cpp/game'/name).read_bytes())
j=dict(cases=len(rows),inputs=576,inputStrideBytes=3000,outputWords=12,rows=rows,inputSha256=hashlib.sha256(selected_inputs).hexdigest(),outputSha256=hashlib.sha256(expected).hexdigest(),baseInputSha256=meta['inputSha256'],toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),executableSha256=meta['executableSha256'],originalEntries=['476100','4766e0'],declaredInputs=True,allRotationsZero=not rotations,declaredLocalZRotations=[.375,-.625]if rotations else [0],declaredParentZRotations=[-.25,.75]if rotations else [0],threeAnchorCombinations=anchors,geometryOnly=True,cookieReturnService='4854a0',newOriginalGameProcesses=0,newGpuRuns=0,audibleOutput=False,completeGame=False)
(H/'native.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(dict(cases=len(rows),inputs=576,comparedWords=len(rows)*12)))
