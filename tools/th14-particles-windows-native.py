"""Run TH14 effect 7 with real VM/interpolation and D3DX normalization.

Allocation, script binding and animation registries are controlled boundaries.
Child scripts idle after their first update. Normalization executes in the
actual pinned Windows x86 DLL through the declared vector-service boundary;
Unicorn's reciprocal-square-root instruction model is not used for it.
The fixture supplies parent/child update order; it does not prove the scheduler.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,CODE,CHILDCODE,GEOM,FILE,MANAGER,STACK,RETURN,CHILDREN=0x70001000,0x70002000,0x70003000,0x70004000,0x70008000,0x70009000,0x7003f000,0x70000000,0x71000000
DLL_SHA='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'


def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/d3dx9_43.dll')
    assert hashlib.sha256(dll.data).hexdigest()==DLL_SHA,'D3DX executable differs from pinned native oracle'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for binary in (img,dll):
        for _,base,size,raw,n in binary.sections:
            first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,binary.data[raw:raw+n])
    m.mem_map(RETURN,0x40000);m.mem_map(CHILDREN,0x100000);m.mem_map(0,4096)
    m.mem_write(0x4854a0,b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def read(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
    def run(address,vm=VM,args=(),edx=0):
        m.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),RETURN,*args))
        m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,vm);m.reg_write(UC_X86_REG_EDX,edx)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(address,RETURN,count=5000000);assert m.reg_read(UC_X86_REG_EIP)==RETURN,hex(m.reg_read(UC_X86_REG_EIP))
        return m.reg_read(UC_X86_REG_EAX)
    # Initialize the real DLL dispatch table via its SSE2 table installer.
    run(0x101bc521,args=(0x101ca068,));assert get(0x101ca084)==0x101bca21
    put(0x4b12b8,0x100301d9)
    vectors=importlib.import_module('th14-d3dx-windows').WindowsVectors(m,0x100301d9,ROOT/'artifacts/th14/particles-windows-worker')
    active={};scripts={};allocated=[];next_child=0
    def boundary(machine,address,size,user):
        nonlocal next_child
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x485540:
            n=get(sp+4);assert n==0x193c;allocated.append(n);m.mem_write(GEOM,bytes(n));m.reg_write(UC_X86_REG_EAX,GEOM)
        elif address==0x47fcb0:
            p=CHILDREN+next_child*0x1000;next_child+=1;assert next_child<=200
            m.mem_write(p,bytes(0x700));m.reg_write(UC_X86_REG_EAX,p)
        elif address==0x40af00:
            p=get(sp+4);script=get(sp+8);assert script in (151,152);scripts[p]=script
            put(p+0x18,7);put(p+0x1c,0x800000);put(p+0x28,CHILDCODE);put(p+0x38,CHILDCODE)
            put(p+0x554,0x4d8f58);put(p+0x558,1);floats(p+0x60,[1,1,1,1]);put(p+0x534,0xffffffff)
            put(p+0x568,0x4d8f58);put(p+0x56c,1)
        elif address==0x47e890:
            output=get(sp+4);p=get(sp+8);identity=(p-CHILDREN)//0x1000+1;active[identity]=p
            put(output,identity);m.reg_write(UC_X86_REG_EAX,output)
        elif address==0x47f0a0:m.reg_write(UC_X86_REG_EAX,active.get(get(sp+4),0))
    for address,cleanup in ((0x485540,0),(0x47fcb0,0),(0x40af00,8),(0x47e890,8),(0x47f0a0,4)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    cases=[]
    for seed in (0,12345):
        for rate in (.5,1.,2.):
            for slowdown in (0.,.25):
                active.clear();scripts.clear();allocated.clear();next_child=0;m.mem_write(VM,bytes(0x700))
                put(0x4db53c,MANAGER);put(MANAGER+0x10,FILE);put(0x4f56cc,MANAGER)
                put(VM+0x18,7);put(VM+0x1c,0x800000);put(VM+0x28,CODE);put(VM+0x38,CODE)
                put(VM+0x554,0x4d8f58);put(VM+0x558,1);floats(VM+0x60,[1,1,1,1]);floats(VM+0x598,[slowdown])
                floats(VM+0x59c,[17.25,-9.5,.125]);floats(VM+0x48,[.125,-.25,.35]);floats(VM+0x4d4,[.75])
                put(VM+0x4ac,8);put(VM+0x534,0xab123456);floats(0x4d8f58,[rate]);m.mem_write(0x4f5815,b'\0')
                m.mem_write(0x4db510,struct.pack('<HHI',seed,0,0));m.mem_write(0x4db508,struct.pack('<HHI',54321,0,0))
                idle=struct.pack('<hHhHhHhH',0,8,30000,0,-1,8,32767,0)
                m.mem_write(CHILDCODE,struct.pack('<hHhHI',310,12,0,0,1)+idle);m.mem_write(CODE,struct.pack('<hHhHI',508,12,0,0,7)+idle)
                assert run(0x46fe50)==0 and allocated==[0x193c]
                timeline=[]
                for frame in range(72):
                    if frame==45:run(0x408540,edx=1);put(VM+0x4a0,1)
                    if frame==62:
                        for identity in list(active):
                            if identity%3==0:del active[identity]
                    if frame==71:active.clear()
                    status=run(0x46fe50)
                    if frame==70:run(0x408500)
                    children=[]
                    for identity,p in active.items():
                        children.append(dict(id=identity,script=scripts[p],color=get(p+0x534),counter=get(p+0x4ac),slowdown=read(p+0x598,1)[0],
                            age=get(p+0x560),visible=get(p+0x18)&1,stopped=get(p+0x28)==0,position=read(p+0x3c,3),
                            interpolation=read(p+0x9c,12),duration=get(p+0xec),interpolationTimer=read(p+0xe0,1)[0]))
                    timeline.append(dict(status=status,children=children,handles=words(GEOM,200),states=words(GEOM+0x15e0,200),
                        timer=read(GEOM+0x1930,1)[0],centers=read(GEOM+0x1900,9),rng=words(0x4db510,2),rate=read(0x4d8f58,1)[0]))
                    for p in active.values():assert run(0x46fe50,vm=p)==0
                cases.append(dict(seed=seed,rate=rate,slowdown=slowdown,timeline=timeline))
    service=vectors.close()
    out=ROOT/'artifacts/th14/particles-windows-check/native.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),d3dxSha256=DLL_SHA,normalizationService=service,cases=cases),separators=(',',':'))+'\n',encoding='utf-8')
    print(f'Observed {len(cases)} TH14 effect-7 timelines / {len(cases)*72} frames with native D3DX SSE2 normalization.')


if __name__=='__main__':main()
