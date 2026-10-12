"""Execute the TH14 effect-8 registration and pre-update through the real VM.

Only allocation and security-cookie checking are replaced. The original effect
table, initialization, RNG, trigonometry, timer and stopped-VM callbacks run.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,CODE,GEOM,STACK,RETURN=0x70001000,0x70002000,0x70004000,0x7001f000,0x70000000


def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x20000);m.mem_map(0,4096)
    m.mem_write(0x4854a0,b'\xc3');m.mem_write(0x485540,b'\xc3')
    allocated=[]
    def allocator(machine,address,size,user):
        n=struct.unpack('<I',m.mem_read(m.reg_read(UC_X86_REG_ESP)+4,4))[0]
        assert n==0xa20;allocated.append(n);m.mem_write(GEOM,bytes(n));m.reg_write(UC_X86_REG_EAX,GEOM)
    m.hook_add(UC_HOOK_CODE,allocator,begin=0x485540,end=0x485540)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def read(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    def run():
        put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VM)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(0x46fe50,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
        assert m.reg_read(UC_X86_REG_EAX)==0
    cases=[]
    for seed in (0,12345,65535):
        for rate in (.5,1.,2.):
            for independent in (0,1):
                m.mem_write(VM,bytes(0x700));put(VM+0x18,7);put(VM+0x1c,0x800000|(independent<<8))
                put(VM+0x28,CODE);put(VM+0x38,CODE);put(VM+0x554,0x4d8f58);put(VM+0x558,1)
                floats(VM+0x60,[1,1,1,1]);floats(VM,[17.25,-9.5,.125]);floats(0x4d8f58,[rate])
                m.mem_write(0x4db508,struct.pack('<HHI',seed,0,0));m.mem_write(0x4f5815,b'\0')
                m.mem_write(CODE,struct.pack('<hHhHIhHhH',508,12,0,0,8,0,8,30000,0));allocated.clear()
                run();assert allocated==[0xa20]
                initial=dict(phase=read(GEOM+0xa08,1)[0],position=read(VM+0x59c,3),layer=get(VM+0x24))
                timeline=[]
                for frame in range(48):
                    if frame==24:put(VM+0x28,0)
                    if frame==36:floats(GEOM+0x964,[.125])
                    run()
                    timeline.append(dict(vertices=[list(struct.unpack('<3fI2f',m.mem_read(GEOM+i*24,24))) for i in range(80)],
                        steps=read(GEOM+0x780,120),angles=read(GEOM+0x960,2),timer=read(GEOM+0xa14,1)[0],
                        timerCurrent=get(GEOM+0xa10),timerPrevious=get(GEOM+0xa0c),rate=read(0x4d8f58,1)[0],rng=list(struct.unpack('<HHI',m.mem_read(0x4db508,8)))))
                cases.append(dict(seed=seed,rate=rate,independent=independent,initial=initial,timeline=timeline))
    out=ROOT/'artifacts/th14/ribbon-native.json'
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'Observed {len(cases)} TH14 effect-8 timelines / {len(cases)*48} frames.')


if __name__=='__main__':main()
