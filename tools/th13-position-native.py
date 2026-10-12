"""Run TH13's recursive ANM position resolver and child creation bodies.

The resolver has only the security-cookie check stubbed. Child-creation probes
replace allocation, script binding/updating and registry insertion boundaries;
the parent/copy position handling itself is original code.
"""
import importlib
import json
import struct
import hashlib
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,STACK,RETURN=0x70000000,0x7003f000,0x70030000
VMS=[BASE+i*0x1000 for i in range(3)]
CHILD,MANAGER,OUT=BASE+0x8000,BASE+0x10000,BASE+0x20000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(13)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(BASE,0x40000);m.mem_write(0x47a09f,b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def vector(p):return list(struct.unpack('<3f',m.mem_read(p,12)))
    def run(address,args,registers):
        m.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),RETURN,*args));m.reg_write(UC_X86_REG_ESP,STACK)
        for reg,value in registers:m.reg_write(reg,value)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(address,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
    cases=[]
    for depth in range(3):
        for flags in (0,0x40000,0x10000,0x50000):
            for parent_flags in (0,0x40000,0x10000,0x50000):
                for sample in range(5):
                    m.mem_write(BASE,bytes(0x3000));nodes=[]
                    for i,vm in enumerate(VMS):
                        f=flags if i==0 else parent_flags
                        vectors=[[17.25+i*10+sample/4,-32.5+sample*10,41.125],[-12.5+i,61.25+sample,-10.75],[.25,19.5-i,2.625]]
                        for offset,v in zip((0x574,0x3c,0x4e0),vectors):m.mem_write(vm+offset,struct.pack('<3f',*v))
                        put(vm+0x1c,f);put(vm+0x570,VMS[i+1] if i<depth else 0)
                        nodes.append(dict(flags=f,position=vectors[0],script=vectors[1],child=vectors[2]))
                    run(0x466a80,[OUT],[(UC_X86_REG_ECX,VMS[0])])
                    cases.append(dict(depth=depth,nodes=nodes,result=vector(OUT)))
    registry=[]
    def boundary(machine,address,size,user):
        if address==0x4706c0:machine.reg_write(UC_X86_REG_EAX,CHILD)
        elif address==0x462450:machine.reg_write(UC_X86_REG_EAX,0)
        elif address in (0x46f3f0,0x46f4a0,0x46f540,0x46f5f0):
            out=get(machine.reg_read(UC_X86_REG_ESP)+4);put(out,123);machine.reg_write(UC_X86_REG_EAX,out);registry.append(hex(address))
    for address,cleanup in ((0x4706c0,0),(0x403800,4),(0x462450,0),(0x46f3f0,4),(0x46f4a0,4),(0x46f540,4),(0x46f5f0,4)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    spawns=[]
    for detached,flags in ((False,0),(False,4),(False,2),(False,6),(True,0)):
        m.mem_write(VMS[0],bytes(0x700));m.mem_write(CHILD,bytes(0x700));put(VMS[0]+0x24,7)
        for offset,v in ((0x574,[12.,21.,34.]),(0x3c,[3.,5.,8.]),(0x48,[.25,.5,.75])):m.mem_write(VMS[0]+offset,struct.pack('<3f',*v))
        registry.clear()
        if detached:run(0x46fab0,[OUT,0],[(UC_X86_REG_EAX,VMS[0]),(UC_X86_REG_EDI,MANAGER)])
        else:run(0x46f990,[OUT,0,flags],[(UC_X86_REG_ESI,VMS[0]),(UC_X86_REG_EAX,MANAGER)])
        spawns.append(dict(detached=detached,flags=flags,position=vector(CHILD+0x574),child=vector(CHILD+0x4e0),rotation=vector(CHILD+0x48),layer=get(CHILD+0x24),parent=get(CHILD+0x570)==VMS[0],registry=list(registry)))
    out=ROOT/'artifacts/th13/position-native.json'
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,spawns=spawns),indent=2)+'\n',encoding='utf-8')
    print(f'Observed {len(cases)} native positions and {len(spawns)} child-creation variants.')
if __name__=='__main__':main()
