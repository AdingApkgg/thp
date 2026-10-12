"""TH14 enemy ANM commands, native creation/first-update and position sync.

ECL argument reads, allocation, ANM resource binding and registry lookup are
controlled boundaries. The command bodies and native ANM interpreter execute.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE=0x70000000
ENEMY,OWNER,CONTEXT,MANAGER,FILE,OLD,VM,CODE,STACK=tuple(BASE+n for n in (0x1000,0x6000,0x7000,0x9000,0xa000,0xb000,0xc000,0xd000,0x3f000))

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(BASE,0x40000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
    args=[];registry=[];reads=[];bindings=[];handles={}
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x483f30:
            index=get(sp+4);reads.append(index);m.reg_write(UC_X86_REG_EAX,args[index]&0xffffffff)
        elif address==0x483fc0:
            index=get(sp+4);reads.append(index);m.reg_write(UC_X86_REG_XMM0,args[index]&0xffffffff)
        elif address==0x47fcb0:m.reg_write(UC_X86_REG_EAX,VM)
        elif address==0x40af00:
            assert get(sp+4)==VM and m.reg_read(UC_X86_REG_ECX)==FILE
            bindings.append(get(sp+8));put(VM+0x18,7);put(VM+0x1c,0x800000)
            put(VM+0x28,CODE);put(VM+0x38,CODE);put(VM+0x30,FILE)
            put(VM+0x554,0x4d8f58);put(VM+0x558,1);floats(VM+0x60,1,1,1,1)
            floats(VM+0x4e0,1,3.1415927410125732);put(VM+0x4e8,65536);put(VM+0x580,VM)
        elif address in (0x47e890,0x47e950):
            assert get(sp+8)==VM;out=get(sp+4);put(out,200);m.reg_write(UC_X86_REG_EAX,out);registry.append(hex(address))
        elif address==0x47f0a0:
            m.reg_write(UC_X86_REG_EAX,handles.get(get(sp+4),0))
        elif address==0x47f420:m.reg_write(UC_X86_REG_EAX,handles.get(get(m.reg_read(UC_X86_REG_ECX)),0))
    for address,cleanup in ((0x483f30,4),(0x483fc0,4),(0x47fcb0,0),(0x40af00,8),(0x47e890,8),(0x47e950,8),(0x47f0a0,4),(0x47f420,0)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    def command(op,*args):return struct.pack('<hHhH',op,8+4*len(args),0,0)+b''.join(struct.pack('<I',v&0xffffffff) for v in args)
    f32=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
    def reset():
        m.mem_write(BASE,bytes(0x3e000));registry.clear();reads.clear();bindings.clear()
        handles.clear();handles.update({100:OLD,200:VM})
        put(ENEMY+0x40ec,OWNER);put(OWNER+4,CONTEXT);put(0x4db544,MANAGER);put(MANAGER+0xa4,FILE)
        put(OLD+0x18,7);put(OLD+0x580,OLD);put(OLD+0x30,FILE)
        floats(0x4d8f58,1);m.mem_write(0x4f5815,b'\0')
        m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EBP,STACK)
        m.reg_write(UC_X86_REG_EDI,ENEMY);m.reg_write(UC_X86_REG_EDX,OWNER)
        m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
    cases=[]
    for op,entry in ((303,0x42a3e0),(306,0x42590a),(307,0x4256a9),(308,0x425793),(313,0x425a6a),(316,0x425b19),(318,0x4259f6)):
        for slot in ((0,7,15) if op not in (307,308,318) else (0,)):
            for hidden in (0,1):
                for facing in (-8,1,17):
                    for program in (0,1,2):
                        for script in ((-1,1) if op==303 else (-1,0,2) if op==316 else (1,)):
                            reset();args[:]=[1 if op in (307,308) else slot,script]
                            if op==316:put(STACK+0x1c,ENEMY)
                            if op==307:floats(ENEMY+0x44,12.25,-14.5,4.75)
                            put(ENEMY+0x124+slot*4,100);put(ENEMY+0x264,1);put(ENEMY+0x268,8)
                            put(ENEMY+0x26c,9);put(ENEMY+0x270,10);put(ENEMY+0x274,-1);put(ENEMY+0x27c,facing)
                            put(ENEMY+0x4054,hidden*32|(0x100000 if op==318 else 0));floats(ENEMY+0x3f58,31,37)
                            code=b''
                            if program:code+=command(304,8 if program==1 else 28)
                            if program==2:code+=command(400,*map(f32,(3.25,-7.5,9.125)))+command(404,*map(f32,(2.5,-3.25)))
                            code+=command(2)+command(-1);m.mem_write(CODE,code)
                            if op==303:put(STACK,BASE);m.reg_write(UC_X86_REG_ECX,ENEMY)
                            end=BASE if op==303 else 0x429c28;m.emu_start(entry,end,count=50000)
                            assert m.reg_read(UC_X86_REG_EIP)==end
                            cases.append(dict(op=op,slot=slot,hidden=hidden,facing=facing,program=program,script=script,
                                state=[get(ENEMY+0x4054),*words(ENEMY+0x264,5),*words(ENEMY+0x3f58,2)],
                                oldDeleted=bool(get(OLD+0x1c)&32),handle=get(ENEMY+0x124+slot*4),reads=reads[:],bindings=bindings[:],registry=registry[:],
                                vm=[get(VM+0x24),get(VM+0x1c)&0x60220,get(VM+0x18)&2,*words(VM+0x59c,3),*words(VM+0x3c,3),*words(VM+0x60,2)] if bindings else []))
    offsets=[]
    for slot in (0,1,7,15):
      for x in (f32(-999999.),f32(-24.25),0x80000000,0,f32(4096.),0x7fc01234,0x7f800000):
       for y in (f32(-999999.),f32(-8.5),0,f32(39.25),0xff800000):
        reset();args[:]=[slot,x,y];put(STACK+0x1c,ENEMY)
        for n in range(16):floats(ENEMY+0x164+n*12,float(n)*-.25,float(n)*.5,99.)
        m.emu_start(0x4253c0,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        offsets.append(dict(slot=slot,x=x,y=y,reads=reads[:],result=words(ENEMY+0x164,48)))
    angled=[]
    for file in (0,1,3):
      for program in (0,1,2):
       for p in ((0.,0.,0.),(12.25,-14.5,4.75),(-192.,-8.,0.)):
        for angle in (f32(-999999.),f32(-3.25),f32(-0.),f32(0.),f32(6.5),0x7fc01234,0x7f800000):
         reset();args[:]=[file,1,angle];put(MANAGER+0xa0+file*4,FILE);floats(ENEMY+0x44,*p)
         code=b''
         if program:code+=command(304,8 if program==1 else 28)
         if program==2:code+=command(400,*map(f32,(3.25,-7.5,9.125)))+command(401,*map(f32,(.25,-.5,2.25)))+command(404,*map(f32,(2.5,-3.25)))
         m.mem_write(CODE,code+command(2)+command(-1));m.emu_start(0x4257cf,0x429c28,count=50000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
         angled.append(dict(file=file,program=program,position=p,angle=angle,reads=reads[:],bindings=bindings[:],registry=registry[:],vm=[get(VM+0x24),get(VM+0x1c)&0x60220,get(VM+0x18)&6,*words(VM+0x59c,3),*words(VM+0x3c,3),*words(VM+0x60,2),get(VM+0x50)]))
    offset_effects=[]
    for file in (0,1,3):
      for program in (0,1,2):
       for p in ((0.,0.,0.),(12.25,-14.5,4.75),(-192.,-8.,0.)):
        for angle in (f32(-999999.),f32(-3.25),f32(-0.),f32(0.),f32(6.5),0x7fc01234,0x7f800000):
         reset();args[:]=[file,1,f32(-23.25),f32(11.5),angle];put(MANAGER+0xa0+file*4,FILE);floats(ENEMY+0x44,*p)
         code=b''
         if program:code+=command(304,8 if program==1 else 28)
         if program==2:code+=command(400,*map(f32,(3.25,-7.5,9.125)))+command(401,*map(f32,(.25,-.5,2.25)))+command(404,*map(f32,(2.5,-3.25)))
         m.mem_write(CODE,code+command(2)+command(-1));m.emu_start(0x425581,0x429c28,count=50000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
         offset_effects.append(dict(file=file,program=program,position=p,angle=angle,reads=reads[:],bindings=bindings[:],registry=registry[:],vm=[get(VM+0x24),get(VM+0x1c)&0x60220,get(VM+0x18)&6,*words(VM+0x59c,3),*words(VM+0x3c,3),*words(VM+0x60,2),get(VM+0x50)]))
    positions=[]
    for world in (0,1):
        for rotation in (0,1):
            for velocity in range(3):
                for parent in (-1,0,7,15):
                    reset();handles.clear();put(ENEMY+0x4054,world*0x4000000)
                    floats(ENEMY+0x44,12.25,-14.5,4.75);floats(ENEMY+0x78,*((2.,3.,0.),(0.,0.,0.),(-3.,-4.,0.))[velocity]);floats(ENEMY+0x120,.875)
                    for n in range(16):
                        vm=BASE+0x10000+n*0x700;handles[100+n]=vm;put(ENEMY+0x124+n*4,100+n)
                        floats(ENEMY+0x164+n*12,n*.25,n*-.5,n*.75);put(ENEMY+0x224+n*4,parent if n==7 else -1)
                        put(vm+0x18,3);put(vm+0x1c,rotation*0x40);floats(vm+0x59c,100+n,200+n,300+n)
                        floats(vm+0x3c,1.25+n,2.5+n,3.75+n);floats(vm+0x50,-.625)
                    m.reg_write(UC_X86_REG_ESI,ENEMY);m.emu_start(0x42488a,0x4249fd,count=100000)
                    assert m.reg_read(UC_X86_REG_EIP)==0x4249fd
                    positions.append(dict(world=world,rotation=rotation,velocity=velocity,parent=parent,angle=get(ENEMY+0x120),
                        vms=[[*words(BASE+0x10000+n*0x700+0x59c,3),get(BASE+0x10000+n*0x700+0x50),get(BASE+0x10000+n*0x700+0x18)&4] for n in range(16)]))
    directions=[]
    for prior in (-1,0,1):
        for vx in (-.1,-.03,-.02,0,.02,.03,.1):
            for facing in (-8,1,17):
                reset();put(ENEMY+0x4054,0x100000);put(ENEMY+0x124,100);put(ENEMY+0x270,0)
                put(ENEMY+0x274,prior);put(ENEMY+0x27c,facing);floats(ENEMY+0x78,vx)
                floats(OLD+0x3c,3.25,-7.5,9.125);m.mem_write(CODE,command(2)+command(-1))
                m.emu_start(0x42348c,0x42369e,count=100000)
                assert m.reg_read(UC_X86_REG_EIP)==0x42369e
                directions.append(dict(prior=prior,vx=vx,facing=facing,direction=get(ENEMY+0x274),handle=get(ENEMY+0x124),
                    bindings=bindings[:],registry=registry[:],oldDeleted=bool(get(OLD+0x1c)&32),
                    vm=[get(VM+0x24),get(VM+0x1c)&0x60220,*words(VM+0x59c,3)] if bindings else []))
    logos=[]
    for mode in (-1,0,8,9):
        for flags in (0,0x20,0x40,0xff):
            for program in (0,1,2):
                reset();put(0x4db550,MANAGER);put(MANAGER+0x148,FILE);put(0x4d964c,mode);put(0x4f58b8,flags)
                code=b''
                if program:code+=command(304,8 if program==1 else 28)
                if program==2:code+=command(400,*map(f32,(3.25,-7.5,9.125)))+command(404,*map(f32,(2.5,-3.25)))
                m.mem_write(CODE,code+command(2)+command(-1));m.emu_start(0x425577,0x429c28,count=100000)
                assert m.reg_read(UC_X86_REG_EIP)==0x429c28
                logos.append(dict(mode=mode,flags=flags,program=program,bindings=bindings[:],registry=registry[:],
                    vm=[get(VM+0x24),get(VM+0x1c)&0x60220,get(VM+0x18)&2,*words(VM+0x59c,3),*words(VM+0x3c,3),*words(VM+0x60,2)] if bindings else []))
    rotations=[]
    for selected in (-1,0,8,15,16):
      for present in (0,1):
       for angle in (-999999.,-3.25,-1.,0.,6.5):
        reset();args[:]=[selected,f32(angle)];put(CONTEXT+4,CODE);put(CODE+4,319)
        put(ENEMY+0x124+max(0,selected)*4,100);put(OLD+0x18,0x202);floats(OLD+0x50,.75)
        if not present:handles.clear()
        m.emu_start(0x425420,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        rotations.append(dict(slot=selected,present=present,angle=angle,reads=reads[:],result=[get(OLD+0x18),get(OLD+0x50),get(ENEMY+0x124+max(0,selected)*4)]))
    scales=[]
    for op in (329,335):
     for selected in (-1,0,8,15,16):
      for present in (0,1):
       for x,y in ((f32(-999999.),f32(1.5)),(f32(-1.),f32(0.)),(f32(-0.),f32(-0.)),(f32(0.),f32(0.)),(f32(.5),f32(.75)),(f32(4.),f32(-2.)),(0x7fc01234,f32(1.)),(0x7f800000,0xff800000)):
        reset();args[:]=[selected,x,y];put(CONTEXT+4,CODE);put(CODE+4,op);put(ENEMY+0x124+max(0,selected)*4,100)
        put(OLD+0x18,0x202);floats(OLD+0x60,1.25,-2.5,3.75,-4.25)
        if not present:handles.clear()
        m.emu_start(0x425420,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        scales.append(dict(op=op,slot=selected,present=present,x=x,y=y,reads=reads[:],result=[get(OLD+0x18),*words(OLD+0x60,4),get(ENEMY+0x124+max(0,selected)*4)]))
    colors=[]
    for op in (325,327,331,336):
     for selected in (-1,0,8,15,16):
      for present in (0,1):
       for value in (-2147483648,-257,-1,0,117,255,256,2147483647):
        reset();args[:]=[selected,value,value+1,value-1];put(CONTEXT+4,CODE);put(CODE+4,op);put(ENEMY+0x124+max(0,selected)*4,100)
        put(OLD+0x18,0x602);put(OLD+0x534,0x75214365);put(OLD+0x538,0xc987a9cb);put(OLD+0x24,7)
        if not present:handles.clear()
        m.emu_start(0x425420,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        colors.append(dict(op=op,slot=selected,present=present,value=value,reads=reads[:],result=[get(OLD+0x18),*words(OLD+0x534,2),get(OLD+0x24),get(ENEMY+0x124+max(0,selected)*4)]))
    alpha_timelines=[]
    for op in (328,332):
     for mode in (-1,*range(32),32):
      for duration in (-3,0,1,35):
       for rate in (.5,1.,1.25):
        for start,target in ((0,255),(255,-1),(117,-2147483648)):
         reset();args[:]=[0,duration,mode,target];put(CONTEXT+4,CODE);put(CODE+4,op);put(ENEMY+0x124,100);put(OLD+0x18,0x60007)
         floats(0x4d8f58,rate);put(OLD+0x534,(start<<24)|0x214365);put(OLD+0x538,(start<<24)|0x87a9cb)
         offset=0x14c if op==328 else 0x328;put(OLD+offset+8,23);put(OLD+offset+12,-47)
         m.emu_start(0x425420,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28 and reads==[0,3,2,1]
         def alpha_snapshot():return [*words(OLD+0x534,2),get(OLD+0x18)&0x60008,*words(OLD+offset,4),*words(OLD+offset+0x14,3),get(OLD+offset+0x28),get(OLD+offset+0x2c)]
         frames=[alpha_snapshot()]
         for j in range(int(max(duration,0)/rate)+4):
          put(STACK,BASE);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,OLD);m.emu_start(0x473af0,BASE,count=10000);assert m.reg_read(UC_X86_REG_EIP)==BASE;frames.append(alpha_snapshot())
         alpha_timelines.append(dict(op=op,mode=mode,duration=duration,rate=rate,start=start,target=target,frames=frames))
    rgb_timelines=[]
    for mode in (-1,*range(32),32):
     for duration in (-3,0,1,35):
      for rate in (.5,1.,1.25):
       for target in ((0,0,0),(255,255,255),(-1,-2147483648,256)):
        reset();args[:]=[0,duration,mode,*target];put(CONTEXT+4,CODE);put(CODE+4,326);put(ENEMY+0x124,100);put(OLD+0x18,7)
        floats(0x4d8f58,rate);put(OLD+0x534,0x75214365);put(OLD+0x538,0xc987a9cb)
        for n in range(6):put(OLD+0x10c+n*4,23+n*17)
        m.emu_start(0x425420,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28 and reads==[0,3,4,5,2,1]
        def rgb_snapshot():return [*words(OLD+0x534,2),get(OLD+0x18)&8,*words(OLD+0xf4,12),*words(OLD+0x130,3),get(OLD+0x144),get(OLD+0x148)]
        frames=[rgb_snapshot()]
        for j in range(int(max(duration,0)/rate)+4):
         put(STACK,BASE);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,OLD);m.emu_start(0x473af0,BASE,count=10000);assert m.reg_read(UC_X86_REG_EIP)==BASE;frames.append(rgb_snapshot())
        rgb_timelines.append(dict(mode=mode,duration=duration,rate=rate,target=target,frames=frames))
    scale_timelines=[]
    for mode in (-1,*range(32),32):
     for duration in (-3,0,1,35):
      for rate in (.5,1.,1.25):
       for target in ((2.75,-1.125),(-999999.,.5)):
        reset();args[:]=[0,duration,mode,*map(f32,target)];put(CONTEXT+4,CODE);put(CODE+4,330);put(ENEMY+0x124,100);put(OLD+0x18,7)
        floats(0x4d8f58,rate);floats(OLD+0x60,1.25,-2.5);floats(OLD+0x214,.25,-.5,.75,-1.25)
        m.emu_start(0x425420,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28 and reads==[0,4,3,2,1]
        def snapshot():return [*words(OLD+0x60,2),get(OLD+0x18)&8,*words(OLD+0x204,8),*words(OLD+0x22c,3),get(OLD+0x240),get(OLD+0x244)]
        frames=[snapshot()]
        for j in range(int(max(duration,0)/rate)+4):
         put(STACK,BASE);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,OLD);m.emu_start(0x473af0,BASE,count=10000);assert m.reg_read(UC_X86_REG_EIP)==BASE;frames.append(snapshot())
        scale_timelines.append(dict(mode=mode,duration=duration,rate=rate,target=target,frames=frames))
    out=ROOT/'artifacts/th14/enemy-animation-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),offsets=offsets,rgbTimelines=rgb_timelines,colors=colors,alphaTimelines=alpha_timelines,scaleTimelines=scale_timelines,scales=scales,angled=angled,offsetEffects=offset_effects,rotations=rotations,cases=cases,positions=positions,directions=directions,logos=logos),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} animation commands, {len(positions)} slot-position and {len(directions)} direction cases observed.')
if __name__=='__main__':main()
