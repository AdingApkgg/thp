"""Retail loader and writer for the actual Launcher-exported score file."""
import hashlib,importlib,json,struct,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 assert len(sys.argv)==4
 source,expected_path,out=map(lambda p:Path(p).resolve(),sys.argv[1:]);assert out.is_relative_to(ROOT);out.mkdir(parents=True,exist_ok=True)
 packed=source.read_bytes();expected=expected_path.read_bytes();assert len(expected)==0x24654
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  begin=b&~4095;m.mem_map(begin,((b+size+4095)&~4095)-begin);m.mem_write(b,img.data[raw:raw+n])
 base,manager,header,heap,stack,ret=0x71000000,0x71001000,0x71040000,0x71100000,0x717fe000,0x717ff000;m.mem_map(base,0x800000);allocation=[heap]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def boundary(uc,a,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x485540:
   p=allocation[0];allocation[0]=(p+get(sp+4)+15)&~15;assert allocation[0]<stack;uc.reg_write(UC_X86_REG_EAX,p)
  elif a==0x487620:
   dst,src,n=(get(sp+i) for i in (4,8,12));uc.mem_write(dst,bytes(uc.mem_read(src,n)));uc.reg_write(UC_X86_REG_EAX,dst)
  elif a==0x48f980:
   dst,value,n=(get(sp+i) for i in (4,8,12));uc.mem_write(dst,bytes([value&255])*n);uc.reg_write(UC_X86_REG_EAX,dst)
 for a in (0x485540,0x487620,0x48f980,0x4855d2):m.mem_write(a,b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 assert len(packed)==struct.unpack_from('<I',packed,4)[0]
 m.mem_write(header,packed);m.mem_write(manager+8,b'\x5a'*len(expected));put(manager,header);put(0x4db68c,manager);put(stack,ret)
 m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager);m.emu_start(0x456de0,ret,count=100000000);assert m.reg_read(UC_X86_REG_EIP)==ret
 raw=bytes(m.mem_read(manager+8,len(expected)));assert raw==expected,'all retail loaded character/settings bytes'
 (out/'retail-loaded.raw').write_bytes(raw)
 allocation[0]=heap;put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager)
 for part in range(30):
  m.emu_start(0x456f60 if part==0 else m.reg_read(UC_X86_REG_EIP),0x457086,count=100000000)
  if m.reg_read(UC_X86_REG_EIP)==0x457086:break
 assert m.reg_read(UC_X86_REG_EIP)==0x457086
 rewritten=bytes(m.mem_read(header,24))+bytes(m.mem_read(m.reg_read(UC_X86_REG_EDI),get(header+16)));(out/'retail-rewritten.dat').write_bytes(rewritten);assert rewritten==packed,'complete retail rewritten file bytes'
 sha=lambda b:hashlib.sha256(b).hexdigest();report=dict(passed=True,nativeExecutableSha256=sha(img.data),inputBytes=len(packed),inputSha256=sha(packed),decodedBytes=len(raw),decodedSha256=sha(raw),rewrittenSha256=sha(rewritten),scope='Actual complete retail456de0 loader and456f60 writer (stopped before OS file write) consume/rewrite the Launcher-exported real browser score. All149076 decoded character/settings bytes and full encoded bytes match production. Allocator/free/memcpy/memset boundaries controlled; no native filesystem/GPU/whole-game equivalence.')
 (out/'native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
