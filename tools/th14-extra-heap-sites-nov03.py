"""Execute original alternate heap call sequences up to synthetic OS boundaries."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EBP,UC_X86_REG_EIP,UC_X86_REG_ESI,UC_X86_REG_ESP
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));p=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(p.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
for pc,raw in [(0x485538,'ff15e4114b00'),(0x494fbb,'ff15e4114b00'),(0x494ea5,'ff1550104b00')]:assert p.read(pc,6).hex()==raw
pe=struct.unpack_from('<I',p.data,0x3c)[0];directory=p.image_base+struct.unpack_from('<I',p.data,pe+0x18+0x68)[0];resolved={}
for j in range(200):
 oft,_,_,name,first=struct.unpack('<5I',p.read(directory+j*20,20))
 if not any([oft,name,first]):break
 dll=p.cstring(p.image_base+name)
 for k in range(1000):
  value=p.u32(p.image_base+(oft or first)+k*4)
  if not value:break
  va=p.image_base+first+k*4
  if va in (0x4b1050,0x4b11e4):assert not value&0x80000000 and va not in resolved;resolved[va]=(dll,p.cstring(p.image_base+value+2))
assert resolved=={0x4b1050:('KERNEL32.dll','HeapReAlloc'),0x4b11e4:('KERNEL32.dll','HeapAlloc')}
cases=[]
for kind,start,ret,request in [('alternate',0x48552c,0x48553e,0),('alternate',0x48552c,0x48553e,57),('zeroed',0x494fa2,0x494fc1,57),('reallocate',0x494e94,0x494eab,57)]:
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,va,size,offset,count in p.sections:
  page=va&~4095;m.mem_map(page,((va+size+4095)&~4095)-page);m.mem_write(va,p.data[offset:offset+count])
 m.mem_map(0x70000000,0x100000);sp=0x700ff000;frame=0x700f0000;stub=0x70004000;heap=0x70003000;old=0x70005000;result=0x70006000
 m.mem_write(0x4b11e4,struct.pack('<I',stub));m.mem_write(0x4b1050,struct.pack('<I',stub));m.mem_write(0x4dafec,struct.pack('<I',heap));m.mem_write(frame+8,struct.pack('<2I',old if kind=='reallocate' else request,1));m.reg_write(UC_X86_REG_EBP,frame);m.reg_write(UC_X86_REG_ESP,sp);m.reg_write(UC_X86_REG_EAX,heap);m.reg_write(UC_X86_REG_ESI,request)
 m.emu_start(start,stub,count=100);assert m.reg_read(UC_X86_REG_EIP)==stub;at=m.reg_read(UC_X86_REG_ESP);argc=5 if kind=='reallocate' else 4;args=struct.unpack('<'+'I'*argc,m.mem_read(at,argc*4));size=max(request,1);assert args==(ret,heap,0,old,size) if kind=='reallocate' else args==(ret,heap,8 if kind=='zeroed' else 0,size)
 m.reg_write(UC_X86_REG_EAX,result);m.reg_write(UC_X86_REG_ESP,at+argc*4);m.emu_start(ret,ret,count=1);assert m.reg_read(UC_X86_REG_EIP)==ret and m.reg_read(UC_X86_REG_EAX)==result
 if kind in ('zeroed','reallocate'):assert m.reg_read(UC_X86_REG_ESI)==size
 cases.append(dict(site=kind,syntheticRequestedBytes=request,heapRequestedBytes=size,heapFlags=8 if kind=='zeroed' else 0,returnBoundaryReached=True))
result=dict(verifiedOriginalExtraHeapCallBoundaries=True,originalExecutableSha256=sha(p.data),actualOriginalInstructionsExecuted=True,cases=cases,alternateZeroRequestNormalizedToOne=True,operatingSystemHeapFunctionsExecuted=False,nativeValuesProvidedToEngine=False,productionCodeChanged=False,completeGame=False,nativeEquivalent=False,toolSha256=sha(Path(__file__).read_bytes()))
q=argparse.ArgumentParser(description=__doc__);q.add_argument('--check',action='store_true');q.add_argument('--output',type=Path,default=R/'docs/porting/th14-extra-heap-sites-nov03.json');a=q.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(R/'artifacts/th14');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
