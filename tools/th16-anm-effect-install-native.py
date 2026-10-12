"""Retail TH16 effect-1 initializer and callback row; particle execution is excluded."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,CODE,HEAP,STACK,LOOP=0x70001000,0x70003000,0x70008000,0x7001f000,0x45fb9a
def main():
 img,t,d=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000);m.mem_write(0x477fa7,b'\xb8'+struct.pack('<I',HEAP)+b'\xc3')
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 rows=[]
 for flags in (0,7,0xffffffff,0xab123457):
  for flags2 in (0,0xffffffff,0x78345678):
   for refs in (0,1,2,3,65535):
    m.mem_write(VM,bytes(0x700));m.mem_write(HEAP,b'\xa5'*0x193c);put(VM+0x28,CODE);put(VM+0x4a0,1);put(VM+0x530,flags);put(VM+0x534,flags2)
    m.mem_write(CODE,struct.pack('<hHhHi',508,12,0,refs,10000 if refs&1 else 1))
    for reg,v in ((UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE)):m.reg_write(reg,v)
    m.emu_start(t[508],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
    assert get(VM+0x5b8)==HEAP
    words=list(struct.unpack('<'+'I'*(0x193c//4),m.mem_read(HEAP,0x193c)));words[0x1934//4]=0
    rows.append(dict(flags=flags,flags2=flags2,refs=refs,size=get(VM+0x5bc),afterFlags=get(VM+0x530),afterFlags2=get(VM+0x534),selectors=[get(VM+0x5c4+n*4) for n in range(6)],words=words))
 out=ROOT/'artifacts/th16/effect-install-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),scope='Retail opcode508, factory418af0 and initializer405670 execute for effect1 from the original table4a2250. Malloc returns a fixed pointer; original memset executes. All 6,460 bytes (0x193c) compared with timer rate-pointer relocation normalized. Production stops before first particle callback; particle pre-update, deletion, interruption, sprite callbacks, particles and gameplay are explicitly unimplemented and excluded.',rows=rows),separators=(',',':'))+'\n');print(len(rows),'native effect installation cases')
if __name__=='__main__':main()
