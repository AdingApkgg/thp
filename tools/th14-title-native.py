"""Observe retail TH14 main-menu input and routing, with ANM/audio sinks.

The native cursor, state transitions and mode-bit setters execute unchanged.
Animation/sound delivery is a boundary; this is not a visual equivalence test.
"""
import hashlib
import importlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
MENU, STACK, RETURN = 0x70000000, 0x7002f000, 0x70030000

def main():
    img, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, n in img.sections:
        first = base & ~4095
        m.mem_map(first, ((base + size + 4095) & ~4095) - first)
        m.mem_write(base, img.data[raw:raw+n])
    m.mem_map(MENU, 0x31000)
    def put(p, v): m.mem_write(p, struct.pack('<I', v & 0xffffffff))
    def get(p): return struct.unpack('<I', m.mem_read(p, 4))[0]
    sounds = []
    unlocked = 0
    def boundary(machine, address, size, user):
        sp = machine.reg_read(UC_X86_REG_ESP)
        if address == 0x46e3d0: sounds.append(get(sp+4))
        if address == 0x459220: machine.reg_write(UC_X86_REG_EAX, unlocked)
        if address in (0x4590b0,0x41eea0):
            out=get(sp+4);put(out,0);machine.reg_write(UC_X86_REG_EAX,out)
        if address == 0x458e40: put(machine.reg_read(UC_X86_REG_ECX)+0x2c8+get(sp+4)*4,0)
    for address, cleanup in ((0x46e3d0,8),(0x459220,0),(0x458fa0,12),(0x458ef0,12),(0x47f140,8),(0x47f1b0,8),
                             (0x4590b0,12),(0x458e40,4),(0x420d20,0),(0x41eea0,16),(0x445840,0)):
        m.mem_write(address, b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    cases = []
    inputs = [(0,0),(16,0),(32,0),(48,0),(0,16),(0,32),(0,48),(2,0),(256,0),(1,0),(0x80000,0),(17,0),(33,0),(3,0),(0x102,0),(0x80003,0)]
    for unlocked in (0,1):
        for selected in range(10):
            for substate, timer, pressed, repeat in [(2,17,p,r) for p,r in inputs]+[(4,t,0,0) for t in (19,20)]:
                m.mem_write(MENU, bytes(0x10000))
                for offset,value in ((0x1c,1),(0x24,substate),(0x28,selected),(0x30,10),(0xf8,1),(0x2b8,timer),(0x2c0,0x4d8f58),(0x2c4,1)):
                    put(MENU+offset,value)
                if not unlocked: put(MENU+0xb8,1);put(MENU+0xfc,1)
                put(0x4d5984,1);put(0x4f5834,1);put(0x4f58b8,0)
                put(0x4d6884,pressed);put(0x4d6880,repeat)
                put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,MENU)
                m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
                sounds.clear();m.emu_start(0x45a0f0,RETURN,count=100000)
                assert m.reg_read(UC_X86_REG_EIP)==RETURN
                cases.append(dict(kind=1,unlocked=unlocked,selected=selected,substate=substate,timer=timer,pressed=pressed,repeat=repeat,
                    resultSelected=get(MENU+0x28),resultScreen=get(MENU+0x1c),resultSubstate=get(MENU+0x24),
                    difficulty=get(0x4f5834),flags=get(0x4f58b8)&48,sounds=list(sounds)))
    selection_cases=[]
    inputs += [(64,0),(128,0),(192,0),(0,64),(0,128),(0,192),(65,0),(129,0),(66,0),(130,0)]
    for kind,entry in ((5,0x45d5d0),(6,0x45dba0),(7,0x45e1c0)):
        for difficulty in (1,4):
            for character in (range(3) if kind==7 else (0,)):
                count=(1 if difficulty==4 else 4) if kind==5 else 3 if kind==6 else 2
                for selected in range(count):
                    for substate,timer,pressed,repeat in [(2,17,p,r) for p,r in inputs]+[(s,t,0,0) for s,t in ((3,9),(3,10),(3,13),(3,14),(3,39),(3,40),(4,5),(4,6))]:
                        m.mem_write(MENU,bytes(0x10000))
                        for offset,value in ((0x1c,kind),(0x24,substate),(0x28,selected),(0x30,count),(0xf8,kind!=5),(0x2b8,timer),(0x2c0,0x4d8f58),(0x2c4,1),(0xb4,1),(0x34,0),(0x74,10),(0x59fc,1)):
                            put(MENU+offset,value)
                        for address,value in ((0x4d5984,difficulty),(0x4f5834,difficulty),(0x4f58b8,0),(0x4f5828,character),(0x4f582c,0),(0x4db6ac,0),(0x4db6a8,0),(0x4d6884,pressed),(0x4d6880,repeat)):
                            put(address,value)
                        put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,MENU)
                        sounds.clear();m.emu_start(entry,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
                        selection_cases.append(dict(kind=kind,difficulty=difficulty,character=character,selected=selected,substate=substate,timer=timer,pressed=pressed,repeat=repeat,
                            state=[get(MENU+0x1c),get(MENU+0x24),get(MENU+0x28),get(MENU+0x30),get(0x4f5834),get(0x4f5828),get(0x4f582c)],sounds=list(sounds)))
    out=ROOT/'artifacts/th14/title-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,selectionCases=selection_cases),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} original TH14 main-menu and {len(selection_cases)} selection input/routing cases observed.')

if __name__=='__main__': main()
