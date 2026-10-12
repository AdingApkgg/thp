"""Retail TH16 45f980 on the original front.anm icon scripts, including fades.

Only the security cookie check and sprite resource binding are replaced.
Native instruction dispatch, interrupts, interpolators and clocks execute.
"""
import hashlib, importlib, itertools, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
VM,CODE,STACK,RETURN=0x70001000,0x70003000,0x7001f000,0x70000000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(16)
    source=ROOT/'artifacts/th16/front-corpus/front.anm'
    bodies={slot:body for slot,_,body in importlib.import_module('th-anm-script-dump').scripts(source.read_bytes())}
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        begin=base&~4095;m.mem_map(begin,((base+size+4095)&~4095)-begin);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x2000000);m.mem_write(0x47499b,b'\xc3');m.mem_write(0x45edb0,b'\xc2\x08\x00')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    sprite=[-1]
    def bind(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP);sprite[0]=get(sp+8)
    m.hook_add(UC_HOOK_CODE,bind,begin=0x45edb0,end=0x45edb0)
    rows=[]
    for slot in range(30,46):
        for early in (False,True):
            m.mem_write(VM,bytes(0x1000));m.mem_write(CODE,bodies[slot]);sprite[0]=-1
            # TH16 stores a script byte offset and resolves script base via the manager.
            for off,v in ((0x18,0xffffffff),(0x1c,5),(0x24,slot),(0x28,0),(0x530,7),(0x534,0x400),(0x520,0xffffffff),(0x540,-999999),(0x550,1),(0x554,-1),(0x564,1)):
                put(VM+off,v)
            m.mem_write(VM+0x50,struct.pack('<ff',1.,1.));put(0x4a5788,0x3f800000);put(0x490eb0,0x4a5788)
            put(0x4c0f48,0x70020000);put(0x70020000+5*4+0x184f4f0,0x70010000);put(0x70010000+0x120,0x70011000);put(0x70011000+slot*4,CODE)
            # Full, empty and every fragment frame, then a stock change while visible.
            schedule={1:2,122:3,123:7,124:8,125:9,126:10,127:11,128:12,160:2} if early else {121:2,122:3,123:7,124:8,125:9,126:10,127:11,128:12,160:2}
            frames=[]
            for frame in range(181):
                if frame in schedule:put(VM+0x490,schedule[frame])
                put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VM)
                m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f)
                m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
                m.emu_start(0x45f980,RETURN,count=100000)
                assert m.reg_read(UC_X86_REG_EIP)==RETURN,(slot,frame,hex(m.reg_read(UC_X86_REG_EIP)))
                assert m.reg_read(UC_X86_REG_EAX)==0,(slot,frame)
                if frame==0:put(VM+0x490,4);put(VM+0x534,get(VM+0x534)&~0xc000)
                frames.append([sprite[0],get(VM+0x520),get(VM+0x18),get(VM+0x534),get(VM+0x530)&1,
                               get(VM+0x544),get(VM+0x548),*[get(VM+off) for off in (0x2c,0x30,0x34)]])
            rows.append(dict(slot=slot,early=early,schedule=schedule,frames=frames))
    stocks=[];gui=0x70080000;icons=[0x70090000+n*0x800 for n in range(16)]
    for n,p in enumerate(icons):put(gui+0x54+n*4,p)
    for count,fragments,difficulty,extend in itertools.product(range(9),(0,1,4,123,499999,1000000,0xffffffff),(1,4),(0,1,5)):
        for p in icons:put(p+0x490,77);put(p+0x5d0,0)
        put(0x4a57b4,difficulty);put(0x4a57fc,extend)
        for entry,n in ((0x42c280,count),(0x42c390,8-count)):
            put(STACK,RETURN);put(STACK+4,n);put(STACK+8,fragments);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,gui);m.emu_start(entry,RETURN,count=10000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
        stocks.append(dict(count=count,fragments=fragments,difficulty=difficulty,extend=extend,output=[get(p+0x490) for p in icons]))
    out=ROOT/'artifacts/th16/hud-icons-native.json'
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),rows=rows,stocks=stocks))+'\n',encoding='utf8')
    print(f'{len(rows)*181} original-resource native icon frames.')

if __name__=='__main__':main()
