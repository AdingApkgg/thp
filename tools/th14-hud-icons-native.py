"""Retail 46fe50 on the original front.anm icon scripts, including fades.

Only the security cookie check and sprite resource binding are replaced.
Native instruction dispatch, interrupts, interpolators and clocks execute.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
VM,CODE,STACK,RETURN=0x70001000,0x70003000,0x7001f000,0x70000000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    source=ROOT/'artifacts/archive-differential/th14-bBPoO0/front.anm'
    bodies={slot:body for slot,_,body in importlib.import_module('th-anm-script-dump').scripts(source.read_bytes())}
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        begin=base&~4095;m.mem_map(begin,((base+size+4095)&~4095)-begin);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x20000);m.mem_write(0x4854a0,b'\xc3');m.mem_write(0x46f1e0,b'\xc2\x08\x00')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    sprite=[-1]
    def bind(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP);sprite[0]=get(sp+8)
    m.hook_add(UC_HOOK_CODE,bind,begin=0x46f1e0,end=0x46f1e0)
    rows=[]
    for slot in range(29,45):
        for early in (False,True):
            m.mem_write(VM,bytes(0x1000));m.mem_write(CODE,bodies[slot]);sprite[0]=-1
            for off,v in ((0x18,6),(0x1c,0x200),(0x28,CODE),(0x38,CODE),(0x534,0xffffffff),
                          (0x548,-999999),(0x554,0x4d8f58),(0x558,1)):
                put(VM+off,v)
            m.mem_write(VM+0x60,struct.pack('<ff',1.,1.))
            m.mem_write(0x4d8f58,struct.pack('<f',1.))
            # Full, empty and every fragment frame, then a stock change while visible.
            schedule={1:2,122:3,123:7,124:8,125:9,126:10,127:11,128:12,160:2} if early else {121:2,122:3,123:7,124:8,125:9,126:10,127:11,128:12,160:2}
            frames=[]
            for frame in range(181):
                if frame in schedule:put(VM+0x4a0,schedule[frame])
                put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VM)
                m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f)
                m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
                m.emu_start(0x46fe50,RETURN,count=100000)
                assert m.reg_read(UC_X86_REG_EIP)==RETURN,(slot,frame,hex(m.reg_read(UC_X86_REG_EIP)))
                assert m.reg_read(UC_X86_REG_EAX)==0,(slot,frame)
                frames.append([sprite[0],get(VM+0x534),get(VM+0x24),get(VM+0x1c),get(VM+0x18)&1,
                               get(VM+0x54c),get(VM+0x550),*[get(VM+off) for off in (0x3c,0x40,0x44)]])
            rows.append(dict(slot=slot,early=early,schedule=schedule,frames=frames))
    out=ROOT/'artifacts/th14/hud-icons-native.json'
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),rows=rows))+'\n',encoding='utf8')
    print(f'{len(rows)*181} original-resource native icon frames.')

if __name__=='__main__':main()
