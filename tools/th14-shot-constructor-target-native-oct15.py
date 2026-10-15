"""Original 453540 with a live hit receiver, including an unlinked constructor."""
import hashlib, importlib, itertools, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/shot-constructor-target-native-oct15.json'
def main():
    assert not OUT.exists()
    img=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert hashlib.sha256(img.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    end,obj,spec,player,enemy,area,target,rect,stack=0x70000000,0x70001000,0x70002000,0x70010000,0x70040000,0x70053000,0x70054000,0x70054020,0x700ff000
    m.mem_map(end,0x100000)
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
    events=[]
    def observe(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x47f140:events.append([1,get(sp+8)])
        elif address==0x46e470:events.append([4,get(sp+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
        elif address==0x42c810:events.append([5,m.reg_read(UC_X86_REG_XMM1)&0xffffffff])
    for address,cleanup in ((0x47f140,8),(0x46e470,4),(0x42c810,0)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE,observe,begin=address,end=address)
    cases=[]
    for mode,shape,dx,dy in itertools.product((0,1,2),(0,1),(-40.,0.,8.),(-120.,0.,40.)):
        m.mem_write(obj,bytes(0x100));m.mem_write(enemy,bytes(0x6000));m.mem_write(player,bytes(0x19000));m.mem_write(area,bytes(0xa4));events.clear()
        for p,v in ((0x4db67c,player),(0x4db544,enemy if mode==1 else 0),(obj+0xbc,spec),(obj+0x10,3),(obj+0x14,77),(obj+0x18,9),(obj+0x1c,10),(obj+0x98,1),(obj+0x9c,enemy if mode else 0),(obj+0xa0,19 if mode else 0),(obj+0xc0,area),(obj+0xac,19),(spec+0x4c,bits(.05)),(player+0x18350,8),(enemy+0x11e4,19),(enemy+0x11ec,13),(area+0x10,1),(area+0x28,bits(12)),(area+0x9c,enemy if mode else 0),(obj+0x6c,bits(8)),(obj+0x70,bits(-1.5707963705062866)),(stack,end),(stack+4,rect if shape else 0),(stack+8,0),(stack+12,bits(10))):put(p,v)
        for address,values in ((obj+0x54,(12.25,300.5,3.)),(enemy+0x1234,(32.25,180.5,2.)),(obj+0xc4,(-20.,120.,1.)),(target,(12.25+dx,300.5+dy,0.)),(rect,(24.,40.))):
            for i,v in enumerate(values):put(address+i*4,bits(v))
        for reg,value in ((UC_X86_REG_ESP,stack),(UC_X86_REG_ECX,obj),(UC_X86_REG_EDX,target),(UC_X86_REG_MXCSR,0x1f80),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)):m.reg_write(reg,value)
        m.emu_start(0x453540,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
        result=[get(obj+o) for o in (0x10,0x6c,0x54,0x58,0x5c)]+[get(player+0x18350),get(area+0x10),int(get(obj+0x9c)!=0),get(obj+0xa0)]+[get(obj+o) for o in (0xc4,0xc8,0xcc)]+[get(enemy+0x11ec),get(player+0x184b8),m.reg_read(UC_X86_REG_EAX)]
        args=[0,10,10,7,8,8,3,4,mode,1,1,1,0,13,1,bits(.75),bits(1.3),bits(1.),1,4,3,1,shape,bits(dx),bits(dy),bits(10),bits(12),1]
        cases.append(dict(args=args,result=result,events=events[:]))
    OUT.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=cases,nativeEquivalent=False,scope='Original hit callback with recorded animation/sound/slowdown boundaries. Mode 2 retains a live receiver outside the enemy manager. No whole game or physical device claim.'),indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases),unlinkedConstructorCases=sum(c['args'][8]==2 for c in cases))))
if __name__=='__main__':main()
