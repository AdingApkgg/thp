"""Retail TH16 child factory, binder and first update with bounded synthetic templates.

Allocator and registry insertion are controlled; original resource template copy,
cleanup, creation/linking and child's interpreter execute. Resource compilation
into templates and actual registry implementation are not tested here.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
PARENT,CHILD,CODE,CHILDCODE,FILE,TEMPLATES,MANAGER,SCRIPTS,STACK,RETURN=0x70001000,0x70002000,0x70003000,0x70004000,0x70005000,0x70006000,0x70010000,0x70009000,0x7003f000,0x70000000
def main():
    img,table,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x40000);slot=MANAGER+0x184f4f0;m.mem_map(slot&~4095,4096);m.mem_write(0x47499b,b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def real(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    registry=[];first_parent=[]
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x46f600:m.reg_write(UC_X86_REG_EAX,CHILD)
        elif address==0x46f2e0:m.reg_write(UC_X86_REG_EAX,CHILD)
        elif address in (0x46e7d0,0x46e890,0x46e940,0x46ea00):
            out=get(sp+4);assert get(sp+8)==CHILD;put(out,123);m.reg_write(UC_X86_REG_EAX,out);registry.append(hex(address))
        elif address==0x45f980 and m.reg_read(UC_X86_REG_ECX)==CHILD:first_parent.append(get(CHILD+0x5b0)==PARENT)
        elif address==0x45fb9a and m.reg_read(UC_X86_REG_EBX)==PARENT:m.emu_stop()
    for address,cleanup in ((0x46f600,0),(0x46f2e0,0),(0x46e7d0,8),(0x46e890,8),(0x46e940,8),(0x46ea00,8)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    for address in (0x45f980,0x45fb9a):m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    def command(op,*args,refs=0):return struct.pack('<hHhH',op,8+len(args)*4,0,refs)+b''.join(struct.pack('<I',v&0xffffffff) for v in args)
    put(0x4c0f48,MANAGER);put(slot+8,FILE);put(FILE+0x10c,TEMPLATES);put(FILE+0x120,SCRIPTS);put(SCRIPTS+4,CHILDCODE)
    cases=[]
    for op in range(500,507):
        for refs in (0,7 if op in (505,506) else 1):
            for inherited in (0,1):
                for layer in (0,7,42):
                    for program in (0,1,2):
                        for p in (PARENT,CHILD):m.mem_write(p,bytes(0x700))
                        registry.clear();first_parent.clear();put(PARENT+0x530,7);put(PARENT+0x534,inherited<<25);put(PARENT+0x18,27);put(PARENT+0x1c,2);put(PARENT+0x28,CODE);put(PARENT+0x4a0,1);put(PARENT+0x588,PARENT)
                        m.mem_write(PARENT+0x4a0,struct.pack('<iiii',1,6,9,12));floats(PARENT+0x4b0,.25,-.5,.75,1);m.mem_write(PARENT+0x4c0,struct.pack('<iiIIIIII',17,-19,0x11223344,0x55667788,0x80000000,0xffffffff,0x3f800000,256))
                        floats(PARENT+0x5e0,12,21,34);floats(PARENT+0x2c,3,5,8);floats(PARENT+0x38,.25,.5,.75)
                        args=[10000 if refs else 1]
                        if op in (505,506):args += [struct.unpack('<I',struct.pack('<f',v))[0] for v in ((10004.,10005.) if refs else (.25,-.5))]
                        m.mem_write(CODE,command(op,*args,refs=refs))
                        script=command(304,layer)
                        if program==2:script+=command(509)
                        if program:script+=command(400,*[struct.unpack('<I',struct.pack('<f',v))[0] for v in ((10004.,10005.,10006.) if program==2 else (10.5,-11.25,12.75))],refs=7 if program==2 else 0)
                        script+=command(2)+command(-1);m.mem_write(CHILDCODE,script)
                        template=TEMPLATES+0x5fc;m.mem_write(template,bytes(0x5fc));put(template+0x530,7);put(template+0x1c,2);put(template+0x24,1);put(template+0x28,0);floats(template+0x50,1,1);put(template+0x520,0xffffffff)
                        floats(0x4a5788,1);m.mem_write(0x4c10b6,b'\0');put(FILE+0x134,0)
                        for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,PARENT),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                        m.emu_start(table[op],RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x45fb9a,(op,hex(m.reg_read(UC_X86_REG_EIP)))
                        assert len(first_parent)==1
                        cases.append(dict(op=op,refs=refs,inherited=inherited,layer=layer,program=program,registry=registry[:],parentBeforeFirstUpdate=first_parent[0],parent=get(CHILD+0x5b0)==PARENT,transformParent=get(CHILD+0x5ac)==PARENT,childFlag=bool(get(CHILD+0x530)&0x400),flag10=bool(get(CHILD+0x534)&0x400),flag25=bool(get(CHILD+0x534)&0x2000000),linked=get(PARENT+0x58c)==CHILD+0x578,stopped=get(CHILD+0x28)==0xffffffff,position=real(CHILD+0x5e0,3),script=real(CHILD+0x2c,3),child=real(CHILD+0x4e0,3),rotation=real(CHILD+0x38,3),actualLayer=get(CHILD+0x18),variables=list(struct.unpack('<16I',m.mem_read(CHILD+0x4a0,64)))))
    out=ROOT/'artifacts/th16/child-native.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),factory='0x46ed60',binder='0x407b20',scope=__doc__,cases=cases),indent=2)+'\n',encoding='utf-8');print(f'{len(cases)} native TH16 child factory/binder/first-update cases')
if __name__=='__main__':main()
