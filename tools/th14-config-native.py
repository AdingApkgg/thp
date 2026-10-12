"""Execute the retail 4454b8 option/signature/size validation branch only."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in im.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,im.data[raw:raw+n])
 m.mem_map(0x70000000,0x10000);stack=0x7000f000;frame=0x70008000
 initial=bytes.fromhex(json.loads((ROOT/'artifacts/th14/replay-writer-native.json').read_text(encoding='utf-8'))['configs'][0]['config'])
 cases=[]
 def check(data,size):
  m.mem_write(0x4d9134,data);m.mem_write(frame-8,struct.pack('<I',size));m.mem_write(stack,bytes(4));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,frame)
  # Stop at the accepted controller-copy branch or rejected reset branch.
  m.emu_start(0x4454b8,0x445501,count=100)
  ip=m.reg_read(UC_X86_REG_EIP)
  # Invalid paths cannot run the reset/log functions in this validation proof.
  assert ip in (0x445501,0x44552d),hex(ip)
  cases.append(dict(data=data.hex(),size=size,accepted=ip==0x445501))
 # A code hook stops before the rejection's filesystem/log delivery.
 from unicorn import UC_HOOK_CODE
 m.hook_add(UC_HOOK_CODE,lambda uc,a,n,u:uc.emu_stop(),begin=0x44552d,end=0x44552d)
 for offset in range(0x1c,0x22):
  for value in range(256):
   data=bytearray(initial);data[offset]=value;check(bytes(data),92)
 for signature in (0,0x140001,0x140002,0x140003,0xffffffff):
  for size in (0,4,91,92,93,100):
   data=bytearray(initial);struct.pack_into('<I',data,0,signature);check(bytes(data),size)
 (ROOT/'artifacts/th14/config-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8')
 print(f'{len(cases)} native config validation cases')
if __name__=='__main__':main()
