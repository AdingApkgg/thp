"""Retail 502/503 handler bodies; argument resolver and ANM lookup are sinks."""
import importlib,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    base,stack=0x70000000,0x7000f000;m.mem_map(base,0x10000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    argument=0;calls=[]
    def boundary(machine,address,size,user):
        if address==0x42c1d0:machine.reg_write(UC_X86_REG_EAX,argument)
        else:
            handle=get(machine.reg_read(UC_X86_REG_ECX))
            if handle:calls.append([handle,int(address==0x47f520)])
    for address,cleanup in ((0x42c1d0,4),(0x47f560,0),(0x47f520,0)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    cases=[]
    for opcode,entry in ((502,0x42771a),(503,0x427753)):
        for flags in (0,1,32,33,0xffffffff,0xdeadbeef):
            for argument in (0,1,32,33,0xffffffff,0x80000000):
                for pattern in range(3):
                    m.mem_write(base,bytes(0x5000));put(base+0x4054,flags)
                    handles=[0 if pattern==0 or pattern==2 and n%2==0 else 100+n for n in range(16)]
                    for n,v in enumerate(handles):put(base+0x124+n*4,v)
                    m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack);calls.clear();m.emu_start(entry,0x429c28,count=10000)
                    assert m.reg_read(UC_X86_REG_EIP)==0x429c28
                    cases.append(dict(opcode=opcode,flags=flags,bits=argument,pattern=pattern,handles=handles,result=get(base+0x4054),calls=list(calls)))
    out=ROOT/'artifacts/th14/enemy-flags-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} native TH14 enemy flag/visibility cases observed.')
if __name__=='__main__':main()
