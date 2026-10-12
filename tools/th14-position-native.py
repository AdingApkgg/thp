"""Execute TH14's position resolver and quad query with controlled display globals.

Only the security-cookie check is replaced. The original parent recursion,
trigonometry, SSE rounding and resolution/origin selection execute unmodified.
This does not assert the D3D draw path or initialization of those display globals.
"""
import hashlib
import importlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,STACK,RETURN,OUT=0x70000000,0x7003f000,0x70030000,0x70020000
VMS=[BASE+i*0x1000 for i in range(3)]


def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first)
        m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(BASE,0x40000);m.mem_write(0x4854a0,b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def floats(p,v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def read(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,4*n)))
    def run(address):
        m.mem_write(OUT,bytes(48));m.mem_write(STACK,struct.pack('<II',RETURN,OUT))
        m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VMS[0])
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(address,RETURN,count=100000)
        assert m.reg_read(UC_X86_REG_EIP)==RETURN
    def setup(depth,flags,parent_flags,sample,scale,mode=0,anchor=0):
        m.mem_write(BASE,bytes(0x3000));nodes=[]
        origins=[320+sample*7,16-sample*3,427-sample*11,37+sample*13]
        floats(0x4f7a6c,[scale])
        for address,v in zip((0x4f7a88,0x4f7a8c,0x4f7a80,0x4f7a84),origins):put(address,v)
        for i,vm in enumerate(VMS):
            f=flags if i==0 else parent_flags
            vectors=[[17.25+i*10+sample/7,-32.5+sample*10,41.125],[-12.5+i,61.25+sample,-10.75],[.25,19.5-i,2.625]]
            rotation=[.125,.5,-.75+i*.625+sample/9]
            size=[31.75+sample*.2,47.625-sample*.3]
            pivot=[2.3,-7.1]
            scales=[1.1+i*.13,-.625+sample*.1,.75+i*.15,1.25-i*.07]
            for offset,v in zip((0x59c,0x3c,0x4ec),vectors):floats(vm+offset,v)
            floats(vm+0x48,rotation);floats(vm+0x60,scales);floats(vm+0x80,size);floats(vm+0x90,pivot)
            put(vm+0x1c,f);put(vm+0x594,VMS[i+1] if i<depth else 0)
            put(vm+0x18,(mode<<25)|((anchor%3)<<21)|((anchor//3)<<23))
            nodes.append(dict(flags=f,position=vectors[0],script=vectors[1],child=vectors[2],rotation=rotation,
                size=size,pivot=pivot,scale=scales[:2],extra=scales[2:]))
        return dict(depth=depth,nodes=nodes,displayScale=scale,origins=origins,mode=mode,anchor=anchor)
    cases=[]
    for depth in range(3):
        for resolution in range(8):
            for origin in range(4):
                for relation in (0,0x8000,0x400000,0x408000):
                    for sample,scale in enumerate((.75,1.,2.)):
                        flags=(resolution<<19)|(origin<<17)|relation
                        parent_flags=(((resolution+1)%8)<<19)|(((origin+1)%4)<<17)|(0x400000 if sample==2 else 0)
                        row=setup(depth,flags,parent_flags,sample,scale)
                        run(0x435490);row['result']=read(OUT,3);cases.append(row)
    quads=[]
    for mode in range(4):
        for anchor in range(9):
            for resolution in range(8):
                for relation in (0,0x8000,0x400000,0x408000):
                    sample=(mode+anchor+resolution)%3;depth=sample
                    flags=(resolution<<19)|((anchor%4)<<17)|relation
                    row=setup(depth,flags,(1<<19)|(1<<17),sample,(.75,1.,2.)[sample],mode,anchor)
                    run(0x479560);row['result']=read(OUT,12);quads.append(row)
    out=ROOT/'artifacts/th14/position-native.json'
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,quads=quads),indent=2)+'\n',encoding='utf-8')
    print(f'Observed {len(cases)} TH14 native positions and {len(quads)} quad queries.')


if __name__=='__main__':main()
