"""Execute original TH16 registry layer selection/list insertion, with update/delete sinks."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,NODE,MANAGER,HEADS,STACK,RETURN=0x70001000,0x70002000,0x70003000,0x70004000,0x7001f000,0x70000000
def main():
 img,t,d=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(RETURN,0x20000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 calls=[]
 def hook(machine,address,size,user):calls.append('update' if address==0x45f980 else 'delete')
 m.mem_write(0x45f980,b'\x31\xc0\xc3');m.mem_write(0x46e660,b'\xc2\x08\x00')
 for addr in (0x45f980,0x46e660):m.hook_add(UC_HOOK_CODE,hook,begin=addr,end=addr)
 rows=[]
 for overlay in (0,1):
  for layer in range(43):
   if overlay and layer==31:continue # native layer43 writes beyond the seven-slot scratch table
   for state in (0,0x20,0x40,0x60):
    m.mem_write(VM,bytes(0x700));m.mem_write(MANAGER,bytes(0x100));m.mem_write(HEADS,bytes(43*0x600));m.mem_write(STACK,bytes(512));put(VM+0x18,layer);put(VM+0x534,state);put(NODE,VM);put(NODE+4,0)
    for n in range(43):put(STACK+(n*4-0x70 if overlay else n*4+0x20),HEADS+n*0x600)
    for reg,v in ((UC_X86_REG_ESP,STACK),(UC_X86_REG_EDI,MANAGER),(UC_X86_REG_ESI,NODE)):m.reg_write(reg,v)
    calls.clear();m.emu_start(0x46e570 if overlay else 0x46e3b4,0x46e604 if overlay else 0x46e431,count=100000)
    assert m.reg_read(UC_X86_REG_EIP)==(0x46e604 if overlay else 0x46e431)
    linked=[n for n in range(43) if get(HEADS+n*0x600+0x5a8)==VM]
    rows.append(dict(overlay=overlay,layer=layer,state=state,afterLayer=get(VM+0x18),links=linked,calls=list(calls),count=get(MANAGER+0xd8)))
 out=ROOT/'artifacts/th16/registry-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),scope='Original normal/overlay registry loop, layer alias/default, state-bit update/skip/delete selection and draw-list insertion. Native update and deletion are controlled sinks. One live VM per case; production uses a real stopped script. Native allocator/handle layout, teardown internals, multi-node ordering and overlay layer31 out-of-bounds behavior are excluded.',rows=rows),separators=(',',':'))+'\n');print(len(rows),'native registry cases')
if __name__=='__main__':main()
