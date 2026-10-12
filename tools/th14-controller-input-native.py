"""Retail 4018b0 DirectInput consumer with controlled successful device delivery."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in im.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,im.data[raw:raw+n])
 end,device,table,poll,getstate,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x70004000,0x7000f000;m.mem_map(end,0x10000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));word=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 put(device,table);put(table+0x64,poll);put(table+0x24,getstate);put(0x4d8f84,device);put(0x4d9684,0x800)
 m.mem_write(poll,b'\x31\xc0\xc2\x04\x00');m.mem_write(getstate,b'\x31\xc0\xc2\x0c\x00');m.mem_write(0x4854a0,b'\xc3')
 state=bytes(0x110)
 def hook(uc,a,n,u):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x48f980:m.mem_write(word(sp+4),bytes(word(sp+12)));m.reg_write(UC_X86_REG_EAX,word(sp+4))
  else:m.mem_write(word(sp+12),state)
 m.mem_write(0x48f980,b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=0x48f980,end=0x48f980);m.hook_add(UC_HOOK_CODE,hook,begin=getstate,end=getstate)
 rows=[]
 for mapping,mask,threshold,held in itertools.product(((0,1,2,5,-1,-1,-1,-1,-1,3),(3,0,1,2,4,5,6,7,8,9),(-1,1,1,1,0,0,0,0,0,0),(127,126,125,124,0,0,0,0,8,9)),range(64),((600,600),(250,1000),(-1,0)),(0,0x20000)):
  for x,y in ((0,0),(-600,-600),(600,600),(-601,601),(601,-601),(-250,1000),(251,-1001)):
   cfg=bytearray(92);struct.pack_into('<10h',cfg,4,*mapping);struct.pack_into('<2h',cfg,0x18,*threshold);m.mem_write(0x4d6aac,bytes(cfg[4:24]));m.mem_write(0x4d9134,bytes(cfg))
   buttons=bytearray(128)
   for i in range(128):buttons[i]=255 if (i<6 and mask&(1<<i)) or (i>=124 and mask&(1<<(127-i))) or i in (8,9) else 127
   state=struct.pack('<ii',x,y)+bytes(40)+bytes(buttons)+bytes(96)
   assert len(state)==0x110
   put(stack,end);put(stack+4,held);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x4018b0,end,count=2000);assert m.reg_read(UC_X86_REG_EIP)==end
   rows.append(dict(config=cfg.hex(),buttons=buttons.hex(),x=x,y=y,held=held,result=m.reg_read(UC_X86_REG_EAX)))
 (ROOT/'artifacts/th14/controller-input-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} native DirectInput samples')
if __name__=='__main__':main()
