"""Observe TH14 ring allocation commands and original geometry updates.

Allocation is a recorded boundary returning a pre-mapped buffer; cookie checks
are stubbed. Vertex generation and referenced argument helpers are original code.
No renderer or device submission is replaced with an asserted result.
"""
import hashlib
import importlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,VM,PARENT,GEOM,CODE,STACK,RETURN=0x70000000,0x70001000,0x70002000,0x70010000,0x70008000,0x7003f000,0x70030000


def main():
    img,handlers,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(BASE,0x40000);m.mem_write(0x4854a0,b'\xc3');m.mem_write(0x485540,b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def floats(p,v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def read(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    def call(addr):
        put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VM)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(addr,RETURN,count=500000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
    allocations=[];allocated=[]
    def boundary(machine,address,size,user):
        if address==0x485540:
            allocated.append(get(machine.reg_read(UC_X86_REG_ESP)+4));machine.reg_write(UC_X86_REG_EAX,GEOM)
        elif address==0x47007e:machine.emu_stop()
    m.hook_add(UC_HOOK_CODE,boundary,begin=0x485540,end=0x485540)
    m.hook_add(UC_HOOK_CODE,boundary,begin=0x47007e,end=0x47007e)
    for op in (600,601,602,609,610):
        for count in (2,5,17):
            for refs in (0,1):
                for mode in (0,31):
                    m.mem_write(VM,bytes(0x700));put(VM+0x18,7|(mode<<25));put(VM+0x4ac,count)
                    m.mem_write(CODE,struct.pack('<HHhHi',op,12,0,refs,10000 if refs else count))
                    allocated.clear();put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK)
                    m.reg_write(UC_X86_REG_EDI,VM);m.reg_write(UC_X86_REG_EBX,CODE)
                    m.emu_start(handlers[op],RETURN,count=10000)
                    assert m.reg_read(UC_X86_REG_EIP)==0x47007e and len(allocated)==1
                    allocations.append(dict(op=op,count=count,refs=refs,initialMode=mode,mode=(get(VM+0x18)>>25)&31,bytes=allocated[0]))
    cases=[]
    for mode in (9,13,14,23,24):
        for count in (2,5,17):
            for resolution in range(8):
                for color_mode in range(4):
                    sample=(count+resolution+color_mode)%3;display_scale=(.75,1.,2.)[sample]
                    flags=(resolution<<19)|((sample+1)<<17)|(0x400000 if sample==2 else 0)
                    row=dict(mode=mode,count=count,flags=flags,colorMode=color_mode,displayScale=display_scale,
                        position=[17.3,-7.2,9.1],script=[-4.25,3.6,8.5],child=[.1,2.25,3.5],
                        rotation=[(2.75,-3.25,7.25)[sample],.125,(.35,-4.5,8.1)[sample]],scale=[9.3+sample,31.7-sample],
                        variables=[2.5+sample*.75,7.3+sample*.4,23.5-sample*2,.3-sample*1.7],
                        parent=sample==2,parentPosition=[4.5,7.75,-12.3],parentRotation=[.5,.75,-.625],
                        uv=[.125,.25,.825,.375],uvOffset=[-.13,1.1],primary=0xab123456,secondary=0x78345678,uvCycles=sample-1)
                    m.mem_write(VM,bytes(0x700));m.mem_write(PARENT,bytes(0x700));m.mem_write(GEOM,bytes(0x4000))
                    put(VM+0x18,7|(mode<<25)|(color_mode<<17));put(VM+0x1c,flags);put(VM+0x5b4,GEOM)
                    put(VM+0x4ac,count);put(VM+0x4b0,row['uvCycles']);put(VM+0x534,row['primary']);put(VM+0x538,row['secondary'])
                    for offset,key in ((0x59c,'position'),(0x3c,'script'),(0x4ec,'child'),(0x48,'rotation'),(0x60,'scale'),(0x4bc,'variables'),(0x3b8,'uv'),(0x88,'uvOffset')):floats(VM+offset,row[key])
                    if row['parent']:
                        put(VM+0x594,PARENT);put(PARENT+0x1c,0x20000)
                        floats(PARENT+0x59c,row['parentPosition']);floats(PARENT+0x48,row['parentRotation'])
                    floats(0x4f7a6c,[display_scale]);put(0x4f7a88,320);put(0x4f7a8c,16);put(0x4f7a80,427);put(0x4f7a84,37)
                    call(0x473310);stride=24 if mode>=23 else 28
                    row['vertices']=[dict(position=read(GEOM+i*stride,3),rhw=None if stride==24 else read(GEOM+i*stride+12,1)[0],
                        color=get(GEOM+i*stride+stride-12),uv=read(GEOM+i*stride+stride-8,2)) for i in range(count*2)]
                    cases.append(row)
    output=ROOT/'artifacts/th14/rings-native.json'
    output.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),allocations=allocations,cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'Observed {len(allocations)} TH14 ring allocations and {len(cases)} vertex buffers.')


if __name__=='__main__':main()
