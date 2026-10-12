"""Run retail TH13 transform instructions and 2-D quad generation in Unicorn.

Only the security-cookie check and allocator are replaced. Instruction helpers,
interpolation, per-frame updates, parent transforms and trigonometry are native.
"""
import importlib
import json
import struct
import hashlib
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,PARENT,CODE,OUT,STACK,RETURN=0x70000000,0x70001000,0x70002000,0x70003000,0x7001f000,0x70010000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(13)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(VM,0x20000);m.mem_map(0,4096);m.mem_write(0x47a09f,b'\xc3')
    geometry=VM+0x6000;allocated=0
    m.mem_write(0x47a0ed,b'\xc3')
    def allocator(machine,address,size,user):
        nonlocal allocated
        allocated=struct.unpack('<I',m.mem_read(m.reg_read(UC_X86_REG_ESP)+4,4))[0]
        assert allocated<=4096
        m.mem_write(geometry,bytes(4096));m.reg_write(UC_X86_REG_EAX,geometry)
    m.hook_add(UC_HOOK_CODE,allocator,begin=0x47a0ed,end=0x47a0ed)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def floats(p,v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def read(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    def run(address,registers):
        put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK)
        for reg,value in registers:m.reg_write(reg,value)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(address,RETURN,count=100000)
        assert m.reg_read(UC_X86_REG_EIP)==RETURN,hex(m.reg_read(UC_X86_REG_EIP))
    def reset():
        m.mem_write(VM,bytes(0x4000));put(VM+0x18,7);put(VM+0x28,CODE)
        floats(VM+0x60,[1,1,1.25,.75,0,0,1.5,.5]);floats(VM+0x90,[3.25,-5])
        floats(VM+0x3c,[3,5,8]);floats(VM+0x574,[11.25,-7.5,10])
        put(VM+0x528,0xab123456);put(VM+0x544,0x4c0a28);put(VM+0x548,1);floats(0x4c0a28,[1])
    def values():return dict(extra=read(VM+0x68,2),texture=read(VM+0x78,2),pivot=read(VM+0x90,2),scroll=read(VM+0x3d8,2),alpha=m.mem_read(VM+0x52b,1)[0],position=read(VM+0x3c,3),physical=read(VM+0x574,3),size=read(VM+0x80,2),mode=(struct.unpack('<I',m.mem_read(VM+0x18,4))[0]>>25)&31,uvOffset=read(VM+0x88,2))
    cases=[]
    for op in (417,422,425,426,427,428,429,430,433,434,435,436,603,604,605,606,607,608):
        for references in (0,1,2,3):
            for sample,(x,y) in enumerate(((.25,-.5),(2.5,3.75),(-1.25,.125),(0,0))):
                reset();floats(VM+0x4bc,[x,y,0,0]);put(VM+0x4ac,8)
                if op==422:
                    args=b'';refs=0
                elif op==417:
                    args=struct.pack('<ii',37,10000 if references&2 else 8)
                    refs=references&2
                elif op in (604,605):
                    args=struct.pack('<fi',10004. if references&1 else x,10000 if references&2 else 8);refs=references
                elif op in (427,428):
                    args=struct.pack('<iif',10000 if references&1 else 8,sample,10004. if references&2 else x)
                    refs=(references&1)|((references&2)<<1)
                elif op in (430,433,435):
                    args=struct.pack('<iiff',8,sample,10004. if references&1 else x,10005. if references&2 else y)
                    refs=references<<2
                elif op in (425,426):
                    args=struct.pack('<f',10004. if references&1 else x);refs=references&1
                else:
                    args=struct.pack('<ff',10004. if references&1 else x,10005. if references&2 else y);refs=references
                m.mem_write(CODE,struct.pack('<hHhH',op,8+len(args),0,refs)+args+struct.pack('<hHhH',0,8,30000,0))
                timeline=[]
                for frame in range(10):
                    run(0x462450,[(UC_X86_REG_ECX,VM)]);assert m.reg_read(UC_X86_REG_EAX)==0
                    timeline.append(values())
                cases.append(dict(op=op,refs=refs,args=list(struct.unpack('<'+'I'*(len(args)//4),args)),x=x,y=y,timeline=timeline))
    quads=[]
    for mode in range(4):
        for ax in range(3):
            for ay in range(3):
                for parent in (0,1,2):
                    reset();m.mem_write(OUT,bytes(48))
                    put(VM+0x18,7|(mode<<25)|(ax<<21)|(ay<<23));put(VM+0x1c,0x10000 if parent==2 else 0)
                    floats(VM+0x60,[1.5,.625,.75,1.25]);floats(VM+0x80,[31.5,27.25])
                    floats(VM+0x3c,[3.25,-9.5,.125]);floats(VM+0x574,[127.25,200.75,.375]);floats(VM+0x4e0,[4.5,2.25,.25]);floats(VM+0x50,[.375])
                    if parent:
                        put(VM+0x570,PARENT);put(PARENT+0x1c,0x40000)
                        floats(PARENT+0x574,[11.25,-7.5,10]);floats(PARENT+0x60,[.5,2,1.25,.75]);floats(PARENT+0x50,[-.625])
                    run(0x46aca0,[(UC_X86_REG_ECX,VM),(UC_X86_REG_EAX,OUT)])
                    quads.append(dict(mode=mode,ax=ax,ay=ay,parent=parent,vertices=read(OUT,12)))
    uv_quads=[];manager=VM+0x4000
    for sx,sy in ((1,1),(2.5,.75),(-1.25,0)):
        for ox,oy in ((0,0),(.125,-.25)):
            reset();floats(VM+0x78,[sx,sy]);floats(VM+0x88,[ox,oy])
            uv=[.125,.25,.75,.375,.25,.875,.875,1];floats(VM+0x3b8,uv)
            m.mem_write(0x4e47d8,bytes(112));put(STACK,RETURN);put(STACK+4,0)
            m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EAX,VM);m.reg_write(UC_X86_REG_ECX,manager)
            m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
            m.emu_start(0x467350,0x4675bb,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x4675bb
            uv_quads.append(dict(scale=[sx,sy],offset=[ox,oy],input=uv,output=[v for i in range(4) for v in read(0x4e47ec+i*28,2)]))
    rings=[]
    for op in (600,601,602):
        for count in (4,8):
            for parent in (0,1,2):
                for color_mode in range(4):
                    reset();put(VM+0x18,7|(color_mode<<17));put(VM+0x1c,0x10000 if parent==2 else 0)
                    put(VM+0x528,0x9f123456);put(VM+0x52c,0x6134abcd)
                    put(VM+0x4ac,count);put(VM+0x4b0,3);floats(VM+0x60,[5.5,24.25]);floats(VM+0x48,[2.5,0,.375])
                    floats(VM+0x3b8,[.125,.25,.75,.375]);floats(VM+0x88,[.125,-.25]);floats(VM+0x4e0,[4.5,2.25,.25])
                    if parent:
                        put(VM+0x570,PARENT);put(PARENT+0x1c,0x40000);floats(PARENT+0x574,[11.25,-7.5,10])
                    refs=int(count==8);m.mem_write(CODE,struct.pack('<hHhHIhHhH',op,12,0,refs,10000 if refs else count,0,8,30000,0))
                    allocated=0;run(0x462450,[(UC_X86_REG_ECX,VM)]);assert m.reg_read(UC_X86_REG_EAX)==0
                    rings.append(dict(op=op,count=count,parent=parent,colorMode=color_mode,allocation=allocated,
                                      vertices=[list(struct.unpack('<4fI2f',m.mem_read(geometry+i*28,28))) for i in range(count*2)]))
    motion=[]
    for rate in (.5,1.,2.):
        for independent_time in (0,1):
            for camera in (0,1):
                reset();put(VM+0x18,7|(camera<<15));put(VM+0x1c,independent_time<<8);floats(0x4c0a28,[rate])
                floats(0x4dcbf0,[.25,-.75,.125]);floats(VM+0x70,[.125,-.25]);floats(VM+0x3d8,[.25,-.375]);floats(VM+0x54,[0,0,.125])
                m.mem_write(CODE,struct.pack('<hHhH',0,8,30000,0));timeline=[]
                for frame in range(6):
                    run(0x462450,[(UC_X86_REG_ECX,VM)]);assert m.reg_read(UC_X86_REG_EAX)==0
                    timeline.append(read(VM+0x574,3)+read(VM+0x60,2)+read(VM+0x48,3)+read(VM+0x88,2)+read(VM+0x540,1)+read(0x4c0a28,1))
                motion.append(dict(rate=rate,independentTime=independent_time,camera=camera,timeline=timeline))
    ribbons=[]
    for seed in (0,12345,65535):
        for rate in (.5,1.,2.):
            reset();floats(VM,[17.25,-9.5,.125]);floats(0x4c0a28,[rate]);m.mem_write(0x4dc31c,struct.pack('<HHI',seed,0,0));m.mem_write(0x4e49ed,b'\0')
            m.mem_write(CODE,struct.pack('<hHhHIhHhH',508,12,0,0,5,0,8,30000,0));allocated=0
            run(0x462450,[(UC_X86_REG_ECX,VM)]);assert allocated==0x418
            initial=dict(phase=read(geometry+0x400,1)[0],position=read(VM+0x574,3),layer=struct.unpack('<I',m.mem_read(VM+0x24,4))[0])
            timeline=[]
            for frame in range(36):
                run(0x462450,[(UC_X86_REG_ECX,VM)]);assert m.reg_read(UC_X86_REG_EAX)==0
                timeline.append(dict(vertices=[list(struct.unpack('<3fI2f',m.mem_read(geometry+i*24,24))) for i in range(32)],steps=read(geometry+0x300,48),timer=read(geometry+0x40c,1)[0],rng=list(struct.unpack('<HHI',m.mem_read(0x4dc31c,8)))))
            ribbons.append(dict(seed=seed,rate=rate,initial=initial,timeline=timeline))
    out=ROOT/'artifacts/th13/transform-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,quads=quads,uvQuads=uv_quads,rings=rings,motion=motion,ribbons=ribbons),indent=2)+'\n',encoding='utf-8')
    print(f'Observed {len(cases)} transform timelines and {len(quads)} native quads.')
if __name__=='__main__':main()
