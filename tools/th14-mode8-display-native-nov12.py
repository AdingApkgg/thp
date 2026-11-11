"""Actual mode8 matrix producer slices, with declared display/VM inputs."""
from pathlib import Path
import hashlib,importlib,itertools,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/mode8-display-space-nov12'
assert not H.exists();H.mkdir()
sys.path.insert(0,str(R/'tools'))
image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert hashlib.sha256(image.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,n in image.sections:
 first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[raw:raw+n])
B=0x70000000;VM=B+0x1000;PARENT=B+0x3000;STACK=B+0xff000;FRAME=STACK-0x800
m.mem_map(B,0x100000);m.mem_write(0x4854a0,b'\xc3')
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
floats=lambda p,a:m.mem_write(p,struct.pack('<'+'f'*len(a),*a))
word=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
def setup_vm(at,resolution,origin,dirty,freeze,sample,parent=False):
 m.mem_write(at,bytes(1484));put(at+0x18,3|dirty|(0x10000 if freeze else 0))
 put(at+0x1c,(resolution<<19)|(origin<<17))
 floats(at+0x3c,[3.125,-5.25,1.75] if not parent else [-.125,.75,2.])
 floats(at+0x59c,[11.25,21.125,-7.5] if not parent else [31.25,-17.5,4.])
 floats(at+0x4ec,[.0625,-.5,1.125]);floats(at+0x90,[1.125,-.75])
 floats(at+0x60,[1.25,.75] if not sample else [.3,-1.125]);floats(at+0x68,[.625,1.5])
 sprite=[0.125,0.0625,0,0,-.03125,.1875,0,0,0,0,1,0,.5,-.25,0,1]
 cache=[.375,0.03125,0,0,-.125,.25,0,0,0,0,1,0,3.5,-7.25,0,1]
 floats(at+0x3e0,sprite);floats(at+0x420,cache)
rows=[];inputs=bytearray();outputs=bytearray()
for width,height in [(480,360),(640,480),(800,600),(801,623),(960,720),(1280,960)]:
 scale=struct.unpack('<f',struct.pack('<f',width/640.))[0]
 # Execute the actual primary-origin scalar producer, stopping before pops.
 put(0x4f7a64,width);put(0x4f7a68,height);floats(0x4f7a6c,[scale])
 for reg,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,FRAME),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,value)
 m.emu_start(0x4468eb,0x44690e,count=1000)
 origin_x=word(0x4f7a80);origin_y=m.reg_read(UC_X86_REG_EAX)
 put(0x4f7a84,origin_y)
 # The other origin's actual scalar producer has no calls.
 m.emu_start(0x446c72,0x446cb6,count=1000)
 scaled_x,scaled_y=word(0x4f7a88),word(0x4f7a8c)
 for res,origin,dirty,freeze,parent,sample in itertools.product(range(8),range(3),[0,4,8,12],[0,1],[0,1],[0,1]):
  setup_vm(VM,res,origin,dirty,freeze,sample)
  setup_vm(PARENT,(res+1)%5,0,0,0,0,True)
  if parent:put(VM+0x594,PARENT)
  metadata=[width,height,word(0x4f7a6c),origin_x,origin_y,scaled_x,scaled_y,parent]
  raw=bytes(m.mem_read(VM,1484));parent_raw=bytes(m.mem_read(PARENT,1484))
  inputs.extend(struct.pack('<8I',*metadata)+raw+parent_raw)
  m.mem_write(FRAME-0x200,bytes(0x300));put(FRAME-0xd8,0)
  for reg,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,FRAME),(UC_X86_REG_EBX,VM),
   (UC_X86_REG_EAX,word(VM+0x18)),(UC_X86_REG_MXCSR,0x1f80),(UC_X86_REG_FPCW,0x37f),
   (UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:m.reg_write(reg,value)
  # Rebuild/cache/translate, including the real4352b0 parent/origin helper.
  m.emu_start(0x477c64,0x4780a8,count=100000)
  assert m.reg_read(UC_X86_REG_EIP)==0x4780a8
  # Real unscaled Z overwrite; stop before the first device dereference.
  m.emu_start(0x4781af,0x4781de,count=1000)
  assert m.reg_read(UC_X86_REG_EIP)==0x4781de
  out=bytes(m.mem_read(FRAME-0xcc,64))+bytes(m.mem_read(VM+0x420,64))+struct.pack('<I',word(VM+0x18)&12)
  assert len(out)==33*4;outputs.extend(out)
  rows.append(dict(width=width,height=height,resolution=res,origin=origin,dirty=dirty,freeze=freeze,parent=parent,sample=sample))
for name,data in [('inputs.bin',inputs),('outputs.u32',outputs)]: (H/name).write_bytes(data)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['AnmProjection.cpp','AnmProjection.hpp','AnmRenderer.cpp']:
 src=R/'runtimes/th12/th12_web/cpp/game'/name;dest=H/'baseline-source'/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(src.read_bytes())
report=dict(cases=len(rows),rows=rows,inputStrideBytes=8*4+2*1484,outputWords=33,
 actualOriginalMatrixSlices=['477c64..4780a8','4781af..4781de'],
 actualOriginProducerSlices=['4468eb..44690e','446c72..446cb6'],
 declaredVmInputs=True,allRotationsZero=True,realParentAndOriginHelper=True,
 materialTextureAndGpuNotExecuted=True,cookieReturnService='4854a0',
 inputSha256=sha(H/'inputs.bin'),outputSha256=sha(H/'outputs.u32'),
 executableSha256=hashlib.sha256(image.data).hexdigest(),toolSha256=sha(Path(__file__)),
 sourceBaseline={p.name:sha(p) for p in (H/'baseline-source').iterdir()},newOriginalGameProcesses=0,audibleOutput=False,completeGame=False)
(H/'native.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),actualOriginalInstructions=True,inputBytes=len(inputs),outputBytes=len(outputs))))
