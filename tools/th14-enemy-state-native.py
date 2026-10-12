"""Retail TH14 field setters; argument reads and memset are explicit boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    base,stack=0x70000000,0x7000f000;m.mem_map(base,0x10000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    offsets=[0x4054,0x110,0x114,0x118,0x11c,0x3f60,0x3f64,0x3f68,0x3f6c,0x3f74,0x3f78,0x3f7c,0x3f80,*range(0x3f90,0x3fc8,4),0x3fc8,0x3fcc]
    args=[];reads=[]
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x48f980:
            p,value,n=(get(sp+v) for v in (4,8,12));m.mem_write(p,bytes([value&255])*n);m.reg_write(UC_X86_REG_EAX,p)
        elif address in (0x42c1f0,0x42c250):
            reads.append('destination');m.reg_write(UC_X86_REG_EAX,base+0x5000)
        else:
            index=get(sp+4);reads.append(index);m.reg_write(UC_X86_REG_XMM0 if address in (0x42c230,0x483fc0) else UC_X86_REG_EAX,args[index]&0xffffffff)
    for address,cleanup in ((0x483f30,4),(0x48f980,0),(0x42c230,4),(0x42c1d0,4),(0x42c1f0,4),(0x42c250,4)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    cases=[];f32=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    for op,entry in ((500,0x42767e),(501,0x4276a5),(504,0x42720d),(505,0x427260),(506,0x427792),(507,0x4277aa),(508,0x4277ca),(510,0x427820),(511,0x427834),(524,0x4294cf),(544,0x428a27)):
        for n in range(28):
            m.mem_write(base,bytes(0x5000));reads.clear()
            initial=[0x800000 if n%4==0 else 0xffffffff if n%4==1 else 0x20000 if n%4==2 else 0]+[0x10000000+k*0x1000+n for k in range(1,len(offsets))]
            for offset,value in zip(offsets,initial):put(base+offset,value)
            put(0x4f5828+0x84,n%3);put(0x4f5828+0x8c,100+n)
            args[:]=[f32((n-12)*.75),f32(100-n*2.5),f32(n*.5),f32(-n*.5)]
            if op==507:args[:]=[n%14,0x80000000+n*971]
            elif op in (510,511,524,544):args[:]=[n%3 if n%2 else 0xffffffff-n*7711]
            m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(entry,0x429c28,count=10000)
            assert m.reg_read(UC_X86_REG_EIP)==0x429c28
            cases.append(dict(op=op,n=n,initial=initial,args=args[:],result=[get(base+offset) for offset in offsets]+[get(0x4f5828+0x84),get(0x4f5828+0x8c)],reads=reads[:]))
    assignments=[]
    for op,entry in ((535,0x42792d),(536,0x4279ae)):
        for difficulty in (-2147483648,-1,0,1,2,3,4,127,2147483647):
            for n in range(8):
                reads.clear();args[:]=[64 if op==535 else f32(64),*[(0x80000000+n*7711+j*97813)&0xffffffff if op==535 else f32((n-4)*(j+.75)) for j in range(4)]]
                put(base+0x5000,0x12345678);put(0x4f5834,difficulty)
                m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(entry,0x429c28,count=10000)
                assert m.reg_read(UC_X86_REG_EIP)==0x429c28
                assert reads==[1,2,3,4,'destination'],reads
                assignments.append(dict(op=op,difficulty=difficulty,args=args[:],result=get(base+0x5000),reads=reads[:]))
    bosses=[];manager,owner=base+0x6000,base+0x7000
    for flags in (0,0x80000,0x800000,0xffffffff):
        for manager_flags in (0,1,0xa5a5a5a5):
            for selected in (-2,-1,0,1,7,8,9,15):
                for prior in (0,3,7,8,15):
                    m.mem_write(base,bytes(0x8000));reads.clear();args[:]=[selected]
                    put(0x4db544,manager);put(base+0x4054,flags);put(base+0x4064,prior);put(base+0x40ec,owner);put(manager+0x9c,manager_flags)
                    for n in range(16):put(manager+0x5c+n*4,owner if flags&0x800000 and n==prior else 0x77770000+n*4)
                    m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x42787d,0x429c28,count=10000)
                    assert m.reg_read(UC_X86_REG_EIP)==0x429c28
                    values=[get(manager+0x5c+n*4) for n in range(16)]
                    bosses.append(dict(flags=flags,managerFlags=manager_flags,selected=selected,prior=prior,result=[get(base+0x4054),get(base+0x4064),get(manager+0x9c),*[0 if v==0 else 1 if v==owner else 2+n for n,v in enumerate(values)]]))
    boss_waits=[]
    for pattern in range(256):
        m.mem_write(base,bytes(0x8000));reads.clear();put(0x4db544,manager)
        for n in range(8):put(manager+0x5c+n*4,owner if pattern&(1<<n) else 0)
        before=bytes(m.mem_read(manager,0x100))
        m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x42886e,0x429c2a,count=1000)
        assert m.reg_read(UC_X86_REG_EIP)==0x429c2a
        assert bytes(m.mem_read(manager,0x100))==before and not reads
        result=m.reg_read(UC_X86_REG_EAX);boss_waits.append(dict(pattern=pattern,result=-1 if result==0xffffffff else result))
    dialogue_waits=[]
    for present in (0,1):
      for signal in (0,1,2,0x80000000,0xffffffff):
        m.mem_write(base,bytes(0x8000));reads.clear();put(0x4db550,manager);put(manager+0x194,owner if present else 0);put(owner+0x180,signal)
        m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x428847,0x429c2a,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c2a
        result=m.reg_read(UC_X86_REG_EAX);assert not reads
        dialogue_waits.append(dict(present=present,signal=signal,result=-1 if result==0xffffffff else result))
    phase_counts=[]
    for value in (-2147483648,-100,-1,0,1,2,3,7,9,10,11,100,2147483647):
        m.mem_write(base,bytes(0x8000));reads.clear();args[:]=[value];put(0x4db550,manager);put(manager+0x158,37)
        m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x429708,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28 and reads==[0]
        phase_counts.append(dict(value=value,result=get(manager+0x158)))
    clear_callbacks=[]
    for prior in (0,0x42c8a0,0x42cc70,0xffffffff):
      for mode in (0,1,2,-1):
        m.mem_write(base,bytes(0x8000));reads.clear();args[:]=[0];put(base+0x410c,prior);put(base+0x4110,mode)
        m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x4275e5,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28 and reads==[0]
        clear_callbacks.append(dict(prior=prior,mode=mode,result=[get(base+0x410c),get(base+0x4110)]))
    rewinds=[]
    assert img.u32(0x429c50+img.read(0x429ef4+548-300,1)[0]*4)==0x429812
    for difficulty in (-2147483648,-1,0,1,2,3,4,2147483647):
      for time in (-4096.5,-.0,.125,12345.5,16777216.):
       for counts in ((-1,-2,-3,-4),(0,1,2,3),(-2147483648,2147483647,16777217,-16777217),(71,83,97,101)):
        m.mem_write(base,bytes(0x8000));reads.clear();args[:]=list(counts)
        put(base+0x40ec,base+0x6000);put(base+0x6004,base+0x7000);put(base+0x7000,f32(time));put(0x4f5834,difficulty)
        m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(0x429812,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28 and reads==[0,1,2,3]
        rewinds.append(dict(difficulty=difficulty,time=f32(time),counts=[v&0xffffffff for v in counts],result=get(base+0x7000),reads=reads[:]))
    timers=[]
    for flags in (0,1,2,3,0xa5a5a5a5,0xffffffff):
        for pointer in (0,base+0x5004,0x4d8f58):
            m.mem_write(base,bytes(0x5000));reads.clear()
            for offset,value in ((0,111),(4,222),(8,f32(333.5)),(12,pointer),(16,flags)):put(base+0x2bc+offset,value)
            m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x4289b9,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
            result=[get(base+0x2bc+v) for v in (0,4,8,16)];p=get(base+0x2bc+12);result.append(0 if p==0 else 1 if p==base+0x5004 else 2)
            assert reads==[];timers.append(dict(flags=flags,pointer=0 if not pointer else 1 if pointer==base+0x5004 else 2,result=result))
    interrupts=[];marks=[]
    for slot in range(8):
        for health in (-1,0,1,9000):
            for time in (-1,0,120,3600):
                m.mem_write(base,bytes(0x8000));reads.clear();args[:]=[slot,health,time];put(0x4f58b8,0);put(base+0x40ec,base+0x7000)
                m.mem_write(base+0x6020,b'next_phase\0');offset=base+0x7000+0x525c+slot*16
                # Owner contains the table; reserve enough mapped memory for it.
                for j,v in enumerate((100,200,0x77770001,0x77770002)):put(offset+j*4,v)
                m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESI,base+0x6000);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x4286b7,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
                values=[get(offset+j*4) for j in range(4)];values[2:]=[1 if p==base+0x6020 else 2 if p==0x77770001 else 3 for p in values[2:]]
                interrupts.append(dict(slot=slot,health=health,time=time,result=values,reads=reads[:]))
    timeout_names=[]
    for slot in range(8):
        m.mem_write(base,bytes(0x8000));reads.clear();args[:]=[slot];put(base+0x40ec,base+0x7000)
        m.mem_write(base+0x6018,b'next_timeout\0');offset=base+0x7000+0x525c+slot*16
        for j,v in enumerate((100,200,0x77770001,0x77770002)):put(offset+j*4,v)
        m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESI,base+0x6000);m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(0x42878c,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        values=[get(offset+j*4) for j in range(4)];values[2:]=[1 if p==base+0x6018 else 2 if p==0x77770001 else 3 for p in values[2:]]
        timeout_names.append(dict(slot=slot,result=values,reads=reads[:]))
    for boss in range(3):
        for slot in range(4):
            for health in (-2147483648,-1,0,1,9000,2147483647):
                for value in (-3.5,0,4500.25):
                    m.mem_write(base,bytes(0x8000));reads.clear();args[:]=[slot,f32(value),0xff00aa55]
                    put(0x4db550,base+0x7000);put(base+0x3f78,health);put(base+0x4064,boss)
                    m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x42759b,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
                    p=base+0x7000+0x1b8+boss*0x54+slot*8
                    marks.append(dict(boss=boss,slot=slot,health=health,value=value,type=0xff00aa55,result=[get(p),get(p+4)],reads=reads[:]))
    death_sounds=[]
    assert img.u32(0x429c50+92*4)==0x42537c
    for value in (-2147483648,-1,0,3,4,36,2147483647):
        m.mem_write(base,bytes(0x5000));args[:]=[value];reads.clear();put(base+0x3fe8,123)
        m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,base+0x5000);m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(0x42537c,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        death_sounds.append(dict(value=value,result=get(base+0x3fe8)))
    rates=[]
    assert img.u32(0x429c50+img.read(0x429ef4+547-300,1)[0]*4)==0x42978d
    for value in (0,0x80000000,1,0x3effffff,0x3f000000,0x3f7fffff,0x3f800000,0x3f800001,0x3fa00000,0xbf800000,0x7f800000,0xff800000,0x7fc12345):
        reads.clear();args[:]=[value];put(0x4d8f58,0x12345678)
        m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(0x42978d,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28 and reads==[0]
        rates.append(dict(value=value,result=get(0x4d8f58)))
    callback_setters=[]
    for index in range(7):
      for prior in (0,0xffffffff):
       for mode in (0,1,-1):
        reads.clear();args[:]=[index];put(base+0x410c,prior);put(base+0x4110,mode)
        m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(0x4275e5,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        ptr=get(base+0x410c);assert ptr==img.u32(0x4d4cec+index*4)
        callback_setters.append(dict(index=index,prior=prior,mode=mode,result=[index,get(base+0x4110)]))
    hitbox_angles=[]
    assert img.u32(0x429c50+img.read(0x429ef4+564-300,1)[0]*4)==0x4276ee
    for value in (0,0x80000000,1,0x3effffff,0x3f800000,0xbf800000,0x40490fdb,0x40c90fdb,0x7f800000,0xff800000,0x7fc12345):
        reads.clear();args[:]=[value];put(base+0x120,0x12345678)
        m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(0x4276ee,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28 and reads==[0]
        hitbox_angles.append(dict(value=value,result=get(base+0x120)))
    health_bits=[]
    assert img.u32(0x429c50+img.read(0x429ef4+568-300,1)[0]*4)==0x4289cb
    for flags in (0,1,2,3,0x80000000,0xa5a5a5a5,0xffffffff):
      for value in (-2147483648,-3,-2,-1,0,1,2,3,2147483647):
        reads.clear();args[:]=[value];put(base+0x3f8c,flags)
        m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(0x4289cb,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28 and reads==[0]
        health_bits.append(dict(flags=flags,value=value,result=get(base+0x3f8c)))
    out=ROOT/'artifacts/th14/enemy-state-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),hitboxAngles=hitbox_angles,healthBits=health_bits,rates=rates,callbackSetters=callback_setters,rewinds=rewinds,deathSounds=death_sounds,clearCallbacks=clear_callbacks,phaseCounts=phase_counts,dialogueWaits=dialogue_waits,bossWaits=boss_waits,timeoutNames=timeout_names,cases=cases,assignments=assignments,bosses=bosses,timers=timers,interrupts=interrupts,marks=marks),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} retail TH14 field-setter cases and {len(assignments)} difficulty assignments observed.')
if __name__=='__main__':main()
