"""432/433 with actual 421aa0 manager-list lookup and raw XYZ copying."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,manager,owner,stack=0x70000000,0x70030000,0x70034000,0x7003f000;m.mem_map(base,0x40000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 # Control only the wrapper that chooses the argument; execute the actual
 # integer global getter 42a920 for -9909 (parent id) on every command.
 wrapper=b'\xb9'+struct.pack('<I',owner)+b'\x68'+struct.pack('<i',-9909)
 wrapper+=b'\xe8'+struct.pack('<i',0x42a920-(0x42c1d0+len(wrapper)+5))+b'\xc2\x04\x00'
 m.mem_write(0x42c1d0,wrapper)
 cases=[]
 for op in (432,433):
  for count in range(5):
   for index in (0,7,-1,42,17,-2147483648,2147483647):
    m.mem_write(base,bytes(0x3e000));put(0x4db544,manager);put(manager+0xd0,base+0x10000+0x14d8 if count else 0)
    initial=[(0x80000000,0x7fc01234,0x41234567,0xabcdef01,0)[i%5] for i in range(52)]
    # Populate the four 0x44-byte Movement records using the production prefix.
    fields=(0,4,8,0x34,0x38,0x3c,0x18,0x1c,0x20,0x24,0x28,0x2c,0x40)
    for j,off in enumerate((0,0x44,0x88,0xcc)):
     for k,f in enumerate(fields):put(base+off+f,initial[j*13+k])
    records=[]
    for j in range(count):
     p=base+0x10000+j*0x6000;id=(7,-1,7,42)[j];xyz=[0x3f800000+j,0x7fc00000+j if j==2 else 0x42c80000+j,0x80000000+j]
     put(p+0x11e4,id);m.mem_write(p+0x1234,struct.pack('<III',*xyz));put(p+0x14d8,p);put(p+0x14dc,p+0x6000+0x14d8 if j+1<count else 0);records.append([id,*xyz])
    put(stack,base+0x35000);put(stack+4,index);m.reg_write(UC_X86_REG_ESP,stack)
    m.emu_start(0x421aa0,base+0x35000,count=1000);found=m.reg_read(UC_X86_REG_EAX)
    put(owner+0x11e8,index)
    if found:
     m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);put(base+0x40ec,owner);put(owner+4,owner+0x100)
     m.emu_start(0x4271eb if op==432 else 0x4271fc,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
    result=[get(base+off+f) for off in (0,0x44,0x88,0xcc) for f in fields]
    cases.append(dict(op=op,id=index,initial=initial,records=records,found=int(bool(found)),result=result))
 out=ROOT/'artifacts/th14/enemy-position-copy-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases))+'\n',encoding='utf8');print(f'{len(cases)} retail enemy position copy/lookup cases.')
if __name__=='__main__':main()
