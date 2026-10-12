"""Retail help manager 437c40, with resource/PNG/ANM/audio boundaries.

The original control flow and cursor/timer routines run unchanged. The page
delivery boundary is already completed when testing substate 3; no threading,
D3DX resampling or GPU pixels are part of this proof.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,HELP,RESOURCE,TEXTURE,OBJECT,VTABLE,STACK=0x70000000,0x70001000,0x70004000,0x70005000,0x70006000,0x70007000,0x70010000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
    m.mem_map(BASE,0x20000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<i',m.mem_read(p,4))[0]
    scripts=[];sounds=[];labels={};requests=[];positions=[]
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x438120:
            out,script=get(sp+4),get(sp+8);scripts.append(script);position=get(sp+12);positions.append([get(position+i*4)&0xffffffff for i in range(3)] if position else [0,0,0]);put(out,100+script);labels[script]=0;m.reg_write(UC_X86_REG_EAX,out)
        elif address in (0x47f1b0,0x47f140):labels[get(sp+4)-100]=get(sp+8)
        elif address==0x46e3d0:sounds.append(get(sp+4))
        elif address==0x445b00:requests.append(get(HELP+0x28))
    for address,cleanup in ((0x438120,16),(0x47f1b0,8),(0x47f140,8),(0x46e3d0,8),(0x47f910,0),(0x47c8b0,24),(0x445b00,4),(0x485ddf,0)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    m.mem_write(BASE+0x8000,b'\xc2\x04\x00')
    rows=[]
    for phase,substate in ((0,0),(1,0),(1,1),(1,3),(1,4),(1,5),(2,0)):
        for timer in (0,19,20,29,30):
            for selected in range(7):
                for (pressed,repeat),origin in itertools.product(((0,0),(1,0),(2,0),(256,0),(16,0),(32,0),(0,16),(0,32)),(0,128)):
                    m.mem_write(BASE,bytes(0x8000));scripts.clear();sounds.clear();labels.clear();requests.clear();positions.clear()
                    for p,v in ((HELP+0x10,phase),(HELP+0x14,timer-1),(HELP+0x18,timer),(HELP+0x28,selected),(HELP+0x30,7),(HELP+0xf8,1),(HELP+0x130,RESOURCE),(HELP+0x138,substate),(RESOURCE+0x124,TEXTURE),(TEXTURE+0x18,OBJECT),(OBJECT,VTABLE),(VTABLE+0x24,BASE+0x8000),(0x4d6884,pressed),(0x4d6880,repeat)):
                        put(p,v)
                    for i in range(10):put(HELP+0x100+i*4,100+i);labels[i]=0
                    m.mem_write(HELP+0x12c,struct.pack('<f',float(origin)))
                    m.mem_write(HELP+0x1c,struct.pack('<f',float(timer)));m.mem_write(0x4d8f58,struct.pack('<f',1));put(STACK,BASE)
                    m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,HELP)
                    m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
                    m.emu_start(0x437c40,BASE,count=100000);assert m.reg_read(UC_X86_REG_EIP)==BASE,hex(m.reg_read(UC_X86_REG_EIP))
                    rows.append(dict(phase=phase,substate=substate,timer=timer,selected=selected,pressed=pressed,repeat=repeat,origin=origin,positions=positions[:],result=[get(HELP+0x10),get(HELP+0x138),get(HELP+0x18),get(HELP+0x28),get(HELP+0x128),requests[-1] if requests else -1],scripts=scripts[:],sounds=sounds[:],labels=[labels[i] for i in range(10)]))
    out=ROOT/'artifacts/th14/manual-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf-8')
    print(f'{len(rows)} retail help-manager state/input cases.')
if __name__=='__main__':main()
