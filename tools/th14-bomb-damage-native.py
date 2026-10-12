"""Retail six Bomb damage virtuals and 451430 with active/inactive Bombs.
Damage-area ownership, movement and startup are excluded; geometry/math run natively.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
TABLES=[0x4bd850,0x4bd834,0x4bd818,0x4bd7fc,0x4bd7e0,0x4bd7c4]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
    end,player,bomb,resource,p,sizeptr,flag,last,stack=0x70000000,0x70001000,0x70020000,0x70021000,0x70022000,0x70022020,0x70022040,0x70022060,0x700ff000
    m.mem_map(end,0x100000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
    def boundary(machine,a,size,user):
        if a==0x48f980:
            sp=m.reg_read(UC_X86_REG_ESP);dest=get(sp+4);m.mem_write(dest,bytes(get(sp+12)));m.reg_write(UC_X86_REG_EAX,dest)
    for a in (0x403cd0,0x403df0,0x48f980):
        m.mem_write(a,b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
    def call(entry,args):
        put(stack,end)
        for n,v in enumerate(args):put(stack+4+n*4,v)
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bomb)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.emu_start(entry,end,count=200000);assert m.reg_read(UC_X86_REG_EIP)==end
        return m.reg_read(UC_X86_REG_EAX)
    direct=[]
    for selection,position,size in itertools.product(range(6),(0,0xdead0000,p),(0,0xdead1000,sizeptr)):
        entry=img.u32(TABLES[selection]+12)
        value=call(entry,[position,size]);assert m.reg_read(UC_X86_REG_ESP)==stack+12
        direct.append(dict(selection=selection,entry=entry,position=position,size=size,damage=value))
    rows=[]
    for selection,active,advanced,occupied in itertools.product(range(6),(0,1),(0,1),(0,1)):
        m.mem_write(player,bytes(0x19000));m.mem_write(bomb,bytes(0x100));put(bomb,TABLES[selection]);put(bomb+0x40,active)
        put(0x4db67c,player);put(0x4db52c,bomb);put(player+0x688,resource);put(player+0x68c,10-advanced);put(player+0x690,10);put(resource+0x28,220);put(0x4f5830,0)
        m.mem_write(p,struct.pack('<fff',0,0,0));m.mem_write(sizeptr,struct.pack('<ff',16,16));put(flag,77);m.mem_write(last,struct.pack('<fff',111,222,333))
        if occupied:
            a=player+0xde18
            for off,v in ((0x10,3),(0x14,bits(48)),(0x70,30),(0x74,29),(0x78,bits(29)),(0x84,150),(0x8c,9999999),(0x90,1)):put(a+off,v)
        m.reg_write(UC_X86_REG_XMM3,0)
        damage=call(0x451430,[p,sizeptr,0,flag,last,0,0,0])
        rows.append(dict(args=[selection,active,advanced,occupied],result=[damage,get(flag),get(0x4f5830)]))
    circles=[]
    for radius,x,ticked,advanced,rate in itertools.product((0.,32.,126.),(0.,16.,40.,134.,160.),(0,1),(0,1),(.5,1.,1.25)):
        m.mem_write(player,bytes(0x19000));m.mem_write(bomb,bytes(0x100));put(bomb,TABLES[3]);put(bomb+0x40,1)
        put(0x4db67c,player);put(0x4db52c,bomb);put(player+0x688,resource);put(player+0x68c,10-advanced);put(player+0x690,10);put(resource+0x28,220);put(0x4f5830,0);put(0x4d8f58,bits(rate))
        m.mem_write(p,struct.pack('<fff',0,0,0));m.reg_write(UC_X86_REG_XMM2,bits(radius));m.reg_write(UC_X86_REG_XMM3,0)
        # 450130 uses ECX=player, unlike the Bomb virtual/collector calls.
        put(stack,end);put(stack+4,p);put(stack+8,0);put(stack+12,90);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.emu_start(0x450130,end,count=200000);area=m.reg_read(UC_X86_REG_EAX);assert area==player+0xde18;put(area+0x10,get(area+0x10)|4)
        if ticked:
            put(stack+0x1c,256);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBX,player+0xde90);m.reg_write(UC_X86_REG_EDI,player);m.reg_write(UC_X86_REG_EAX,256)
            m.emu_start(0x44e005,0x44e0fa,count=200000)
        m.mem_write(p,struct.pack('<fff',x,0,0));m.mem_write(sizeptr,struct.pack('<ff',16,16));put(flag,77);m.reg_write(UC_X86_REG_XMM3,0)
        damage=call(0x451430,[p,sizeptr,0,flag,last,0,0,0])
        circles.append(dict(args=[radius,x,ticked,advanced,rate],result=[damage,get(0x4f5830),get(area+0x10)&1,get(flag)]))
    report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),direct=direct,rows=rows,circles=circles,scope=__doc__.strip())
    (ROOT/'artifacts/th14/bomb-damage-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(f'{len(direct)} retail direct virtual calls, {len(rows)} active-Bomb collector cases and {len(circles)} actual Bomb-circle allocation/collector cases.')
if __name__=='__main__':main()
