"""Execute actual 4222f0 manager reset; only CRT memset is a boundary."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,im.data[raw:raw+n])
 end,obj,stack=0x70000000,0x70001000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 def clear(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);p,n=get(sp+4),get(sp+12);m.mem_write(p,bytes(n));m.reg_write(UC_X86_REG_EAX,p)
 m.mem_write(0x48f980,b'\xc3');m.hook_add(UC_HOOK_CODE,clear,begin=0x48f980,end=0x48f980)
 rows=[]
 for poison in [0,1,0xffffffff,0x80000000,*[i*65537 for i in range(64)]]:
  m.mem_write(obj,bytes(0xe8));put(obj+0xdc,poison);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj)
  m.emu_start(0x4222f0,end,count=1000);assert m.reg_read(UC_X86_REG_EIP)==end
  rows.append(dict(poison=poison,result=[get(obj+0xdc),get(obj+0xd8)],registered=get(0x4db544)==obj))
 out=ROOT/'artifacts/th14/enemy-manager-id-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows)),encoding='utf-8');print(f'{len(rows)} retail manager ID resets')
if __name__=='__main__':main()
