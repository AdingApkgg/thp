"""Run TH13's character-selection input handler with ANM/audio sinks.

Only the selection state, transition and sound sequence are asserted here.
Animation lookup/interrupt calls are boundaries, not animation equivalence.
"""
import importlib
import json
import hashlib
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
MENU,VM,CHILDREN,STACK,RETURN=0x70000000,0x70010000,0x70011000,0x7002f000,0x70030000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(13)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first)
        m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(MENU,0x31000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    sounds=[]
    def boundary(machine,address,size,user):
        if address==0x460bc0:sounds.append(machine.reg_read(UC_X86_REG_EDX))
        elif address==0x46fb90:machine.reg_write(UC_X86_REG_EAX,VM)
        elif address==0x470530:put(machine.reg_read(UC_X86_REG_EBX),2000+machine.reg_read(UC_X86_REG_EDI))
    for a,cleanup in ((0x460bc0,0),(0x46fb90,4),(0x470530,0),(0x46fc30,4),(0x46fca0,4),(0x43af70,4)):
        m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
    cases=[]
    for difficulty in (1,4):
        for selected in range(4):
            for pressed,repeat in ((0,0),(64,0),(128,0),(192,0),(0,64),(0,128),(2,0),(1,0),(129,0),(65,0)):
                m.mem_write(MENU,bytes(0x10000));m.mem_write(VM,bytes(0x3000))
                for off,v in ((0x1c,6),(0x24,2),(0x28,selected),(0x30,4),(0xf8,1),(0x2b8,17),(0x2c0,0x4c0a28),(0x2c4,1)):
                    put(MENU+off,v)
                put(MENU+0x2c8+(130 if difficulty==4 else 129)*4,1000)
                # The original searches the VM child list for arrow scripts.
                put(VM+0x55c,VM);put(VM+0x560,CHILDREN+0x700)
                for i,script in enumerate((85,86)):
                    child=CHILDREN+i*0x1000;node=child+0x700
                    m.mem_write(child+0x4aa,struct.pack('<h',script));put(child+0x530,2000+script)
                    put(node,child);put(node+4,CHILDREN+0x1700 if i==0 else 0)
                put(0x4be7c4,difficulty);put(0x4be830,0)
                put(0x4e49fc,pressed);put(0x4e49f8,repeat)
                m.mem_write(STACK,struct.pack('<II',RETURN,MENU));m.reg_write(UC_X86_REG_ESP,STACK)
                m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
                sounds.clear();m.emu_start(0x451450,RETURN,count=100000)
                assert m.reg_read(UC_X86_REG_EIP)==RETURN
                cases.append(dict(difficulty=difficulty,selected=selected,pressed=pressed,repeat=repeat,
                    resultSelected=get(MENU+0x28),substate=get(MENU+0x24),sounds=list(sounds)))
    out=ROOT/'artifacts/th13/title-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} original TH13 character-selection input cases observed.')
if __name__=='__main__':main()
