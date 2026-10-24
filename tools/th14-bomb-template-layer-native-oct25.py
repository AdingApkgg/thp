"""Observe requested template-preserving ANM layers in all six retail Bomb startups.

This is native-only evidence for implementation work, NOT a port pass.
Allocation, ANM factories, audio, HUD and damage-area factories are boundaries.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,PLAYER,BOMB,SPELL,ENEMY,HUD,RESOURCE,STACK=0x70000000,0x70001000,0x70021000,0x70023000,0x70025000,0x70027000,0x70029000,0x700ff000
TABLES=[0x4bd850,0x4bd834,0x4bd818,0x4bd7fc,0x4bd7e0,0x4bd7c4]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
    m.mem_map(BASE,0x100000);events=[];allocated=[];areas=[];created=[]
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def point(p):return [get(p+i*4) for i in range(3)]
    def alloc(size):
        p=BASE+0x40000+len(allocated)*0x1000;assert size<=0x1000;allocated.append([p,size]);m.mem_write(p,bytes(size));return p
    def sink(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address in (0x485540,0x4854af,0x401570):m.reg_write(UC_X86_REG_EAX,alloc(0x100 if address==0x401570 else get(sp+4)))
        elif address==0x48f980:
            p,value,n=get(sp+4),get(sp+8),get(sp+12);m.mem_write(p,bytes([value&255])*n);m.reg_write(UC_X86_REG_EAX,p)
        elif address==0x47ed10:
            row=dict(kind='animation',script=get(sp+8),position=point(get(sp+12)),rotation=get(sp+16),layer=get(sp+20))
            created.append(row);events.append(row);put(get(sp+4),len(created));m.reg_write(UC_X86_REG_EAX,get(sp+4))
        elif address in (0x46e3d0,0x46e470):events.append(dict(kind='sound',id=get(sp+4),positional=address==0x46e470))
        elif address==0x434fd0:events.append(dict(kind='hud',stock=get(sp+4),fragments=get(sp+8)))
        elif address in (0x450130,0x450270):
            p=alloc(0xa4);areas.append(p);put(p+0x10,1);put(p+0x74,0);put(p+0x78,0);put(p+0x7c,0x4d8f58);put(p+0x80,1)
            put(p+0x84,get(sp+12 if address==0x450270 else sp+8));put(p+0x8c,get(sp+16 if address==0x450270 else sp+12))
            events.append(dict(kind='rectangle' if address==0x450270 else 'circle',position=point(get(sp+4)),extent=m.reg_read(UC_X86_REG_XMM2)&0xffffffff,growth=m.reg_read(UC_X86_REG_XMM3)&0xffffffff,args=[get(sp+4+i*4) for i in range(1,4 if address==0x450270 else 3)]));m.reg_write(UC_X86_REG_EAX,p)
    for a,cleanup in ((0x485540,0),(0x4854af,0),(0x4855d2,0),(0x401570,4),(0x401120,8),(0x48f980,0),(0x47ed10,28),(0x46e3d0,8),(0x46e470,4),(0x434fd0,8),(0x450130,12),(0x450270,16)):
        m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
    m.mem_write(0x4854a0,b'\xc3');rows=[]
    for selection,flags,elapsed in itertools.product(range(6),(0,1,0x23),(0,59,60,120)):
        m.mem_write(BASE,bytes(0xf0000));events.clear();allocated.clear();areas.clear();created.clear()
        for p,v in ((0x4db67c,PLAYER),(0x4db52c,BOMB),(0x4db534,SPELL),(0x4db544,ENEMY),(0x4db550,HUD),
                    (BOMB,TABLES[selection]),(PLAYER+0x10,RESOURCE),(PLAYER+0x182d0,1),(PLAYER+0x182c4,10),
                    (SPELL+0x7c,flags),(SPELL+0x28,elapsed),(SPELL+0x80,12345),(ENEMY+0x14,7),(ENEMY+0x18,9),
                    (0x4f5870,3),(0x4f5874,4),(0x4d8f58,0x3f800000),(STACK,BASE)):
            put(p,v)
        m.mem_write(PLAYER+0x5e0,struct.pack('<fff',12.25,400.,3.))
        m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.emu_start(0x412110,BASE,count=100000);assert m.reg_read(UC_X86_REG_EIP)==BASE,(selection,hex(m.reg_read(UC_X86_REG_EIP)))
        rows.append(dict(selection=selection,spellFlags=flags,spellElapsed=elapsed,entry=img.u32(TABLES[selection]),events=events[:],
                         stock=get(0x4f5870),active=get(BOMB+0x40),spellResult=[get(SPELL+0x7c),get(SPELL+0x80)],
                         enemyCounters=[get(ENEMY+0x14),get(ENEMY+0x18)],playerFlags=get(PLAYER+0x182d4),invulnerability=get(PLAYER+0x182c4),
                         position=point(BOMB+0x624),areaState=[[get(p+o) for o in (0x10,0x74,0x84,0x8c,0x90,0xa0)] for p in areas]))
    report=dict(date='2026-10-25',toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),targetInstructionBytesPatched=0,declaredServiceStubAddresses=[hex(a)for a in(0x485540,0x4854af,0x4855d2,0x401570,0x401120,0x48f980,0x47ed10,0x46e3d0,0x46e470,0x434fd0,0x450130,0x450270,0x4854a0)],nativeOnly=True,portVerified=False,executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,
                scope=__doc__.strip())
    out=ROOT/'artifacts/th14/bomb-template-layer-oct25/unit/native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(nativeCases=len(rows),allAnimationLayersMinusOne=all(e['layer']==0xffffffff for row in rows for e in row['events'] if e['kind']=='animation'))))
if __name__=='__main__':main()
