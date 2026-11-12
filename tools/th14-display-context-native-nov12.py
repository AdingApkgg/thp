"""Retail reset/Begin global-context writes with declared screen/D3D services."""
from pathlib import Path
import hashlib, importlib, json, struct, sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_ECX, UC_X86_REG_EAX
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-mode-entry-nov12/context-native-v2';H.mkdir(exist_ok=False)
sys.path.insert(0,str(R/'tools'));im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
sha=lambda data:hashlib.sha256(data).hexdigest();assert sha(im.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,off,n in im.sections:
 page=va&~4095;m.mem_map(page,((va+size+4095)&~4095)-page);m.mem_write(va,im.data[off:off+n])
B=0x78000000;MAN=0x79000000;SUP=0x4d8f60;STACK=B+0xf000;STOP=B+0xe000;DEVICE=B+0x1000;VTABLE=B+0x2000
m.mem_map(B,0x10000);m.mem_map(MAN,0x1100000)
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
put(DEVICE,VTABLE);put(SUP+8,DEVICE);put(0x4f56cc,MAN)
services={0x446250:4,0x4461e0:4,0x4854a0:0,B+0x3000:12,B+0x3100:28,B+0x3200:8}
put(VTABLE+0x94,B+0x3000);put(VTABLE+0xac,B+0x3100);put(VTABLE+0xbc,B+0x3200)
counts={}
def service(uc,pc,size,unused):
 counts[hex(pc)]=counts.get(hex(pc),0)+1;sp=m.reg_read(UC_X86_REG_ESP)
 m.reg_write(UC_X86_REG_EAX,0);m.reg_write(UC_X86_REG_EIP,get(sp));m.reg_write(UC_X86_REG_ESP,sp+4+services[pc])
for pc in services:m.hook_add(UC_HOOK_CODE,service,begin=pc,end=pc)
def run(pc,ecx=SUP):
 put(STACK,STOP);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,ecx);m.emu_start(pc,STOP,count=2000);assert m.reg_read(UC_X86_REG_EIP)==STOP
def snapshot():
 words=[get(0x4f7a6c)]
 for p in [0x4f7a88,0x4f7a8c,0x4f7a80,0x4f7a84]:
  value=struct.unpack('<i',m.mem_read(p,4))[0];words.append(struct.unpack('<I',struct.pack('<f',value))[0])
 for p in [0x4d93e8,0x4d9190,0x4d92bc,0x4d9514]:
  words.extend(get(p+224+i*4) for i in range(6));words.extend([get(p+88),get(p+92)])
 return words
rows=[]
for mode in range(6):
 for resource in [0,1]:
  counts.clear();put(0x4f7a54,mode<<2);put(0x4f7a88,-83);put(0x4f7a8c,47);put(SUP+0x1ac,77 if resource else 0);put(SUP+0xa30,0xff000000)
  run(0x46ae40,0x4f5a18);run(0x4465e0);a=snapshot();run(0x446bd0);b=snapshot();run(0x446920);c=snapshot()
  assert a[1:3]==c[1:3] if not resource else b[1:3]==c[1:3]
  assert counts[hex(B+0x3100)]==(2 if resource else 1)
  rows.append(dict(mode=mode,resource=resource,stages=[a,b,c],serviceCalls=dict(counts)))
report=dict(schema='thp/th14-display-context/1',cases=len(rows),rows=rows,wordsPerStage=37,
 screenMatrixMathDeclaredService=True,cachedCameraUploadDeclaredService=True,d3dCallsDeclaredService=True,
 nativeInstructionBytesUnmodified=True,newGameRuns=0,newGpuRuns=0,completeGame=False,
 executableSha256=sha(im.data),toolSha256=sha(Path(__file__).read_bytes()),
 instructionBindings={hex(a):sha(im.read(a,b-a)) for a,b in [(0x46ae40,0x46aeee),(0x4465e0,0x44691a),(0x446bd0,0x446d80)]})
(H/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
