"""Observe TH14 position/color/transform timelines in the original interpreter.

Only the security-cookie check is replaced; all instruction helpers, timer and
interpolation code run directly from the pinned executable.
"""
import hashlib
import importlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,CODE,STACK,RETURN=0x70001000,0x70002000,0x7001f000,0x70000000


def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        begin=base&~4095;m.mem_map(begin,((base+size+4095)&~4095)-begin)
        m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x20000);m.mem_write(0x4854a0,b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def read(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def reset(x,y,z):
        m.mem_write(VM,bytes(0x700));put(VM+0x18,7);put(VM+0x1c,0x800000);put(VM+0x28,CODE)
        floats(VM+0x60,1,1,1.25,.75,0,0,1.5,.5);floats(VM+0x90,3.25,-5)
        floats(VM+0x3c,3,5,8);floats(VM+0x59c,11.25,-7.5,10)
        put(VM+0x534,0xab123456);put(VM+0x538,0x78345678)
        put(VM+0x554,0x4d8f58);put(VM+0x558,1);floats(0x4d8f58,1)
        floats(VM+0x4bc,x,y,z,.125)
        for i,v in enumerate((8,37,201,77)):put(VM+0x4ac+i*4,v)
    def values():
        return dict(extra=read(VM+0x68,2),texture=read(VM+0x78,2),pivot=read(VM+0x90,2),
            scroll=read(VM+0x3d8,2),position=read(VM+0x3c,3),physical=read(VM+0x59c,3),
            rotation=read(VM+0x48,3),scale=read(VM+0x60,2),uvOffset=read(VM+0x88,2),
            primary=get(VM+0x534),secondary=get(VM+0x538),timer=read(VM+0x550,1)[0],
            size=read(VM+0x80,2),mode=(get(VM+0x18)>>25)&31,counter=get(VM+0x4ac))
    cases=[]
    ops=[400,401,402,404,406,407,408,409,410,412,413,414,415,416,417,420,422,425,426,427,428,429,430,433,434,435,436,603,604,605,606,607,608]
    for op in ops:
        for sample,(x,y,z) in enumerate(((.25,-.5,.75),(2.5,3.75,-1.25),(-1.25,.125,2),(0,0,0))):
            for refs_variant in (0,1,2,7):
                reset(x,y,z)
                args=[];refs=0
                def add(kind,value,var):
                    nonlocal refs
                    if refs_variant&(1<<(len(args)%3)):
                        refs|=1<<len(args);value=var
                    args.append(struct.pack('<'+kind,value))
                if op in (400,401,415):
                    for i,v in enumerate((x,y,z)):add('f',v,10004.+i)
                elif op in (402,416,429,434,436,603,606,607,608):
                    for i,v in enumerate((x,y)):add('f',v,10004.+i)
                elif op in (404,406):
                    for i,v in enumerate((37,201,77)):add('i',v,10001+i)
                elif op in (407,410,412,430,433,435,408,413,409,414,427,428):
                    add('i',8,10000)
                    args.append(struct.pack('<i',sample))
                    if op in (408,413):
                        for i,v in enumerate((37,201,77)):add('i',v,10001+i)
                    elif op in (409,414):add('i',37,10001)
                    elif op in (427,428):add('f',x,10004.)
                    else:
                        for i,v in enumerate((x,y,z) if op in (407,410) else (x,y)):add('f',v,10004.+i)
                elif op==417:
                    args.append(struct.pack('<i',37));add('i',8,10000)
                elif op in (425,426):add('f',x,10004.)
                elif op in (604,605):add('f',x,10004.);add('i',8,10000)
                elif op==420:
                    add('i',8,10000)
                    for i,v in enumerate((x,y,z)*3):add('f',v,10004.+i%3)
                raw=b''.join(args)
                m.mem_write(CODE,struct.pack('<hHhH',op,8+len(raw),0,refs)+raw+struct.pack('<hHhH',0,8,30000,0))
                timeline=[]
                for frame in range(10):
                    put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VM)
                    m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
                    try:m.emu_start(0x46fe50,RETURN,count=100000)
                    except Exception as ex:raise RuntimeError((op,sample,refs,frame,hex(m.reg_read(UC_X86_REG_EIP)))) from ex
                    assert m.reg_read(UC_X86_REG_EIP)==RETURN,(op,frame,hex(m.reg_read(UC_X86_REG_EIP)))
                    assert m.reg_read(UC_X86_REG_EAX)==0,(op,frame)
                    timeline.append(values())
                cases.append(dict(op=op,refs=refs,args=list(struct.unpack('<'+'I'*len(args),raw)),x=x,y=y,z=z,timeline=timeline))
    out=ROOT/'artifacts/th14/transform-native.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} original TH14 transform timelines, {len(cases)*10} frames observed.')


if __name__=='__main__':main()
