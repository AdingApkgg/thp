"""Execute retail TH16 position, rotation, scale, alpha and RGB setters."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,CODE,STACK,RETURN,LOOP=0x70001000,0x70003000,0x7001f000,0x70000000,0x45fb9a
def main():
    img,table,default=importlib.import_module('th-anm-handlers').handlers(16)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,count in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+count])
    m.mem_map(RETURN,0x20000);m.mem_write(0x47499b,b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    ops=(400,401,402,403,404,405,406)
    rows=[]
    for op in ops:
        for value in (-257,-1,0,1,3,255,256,4096):
            for child in (0,1):
                for refs in range(8):
                    m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64))
                    put(VM+0x28,CODE);put(VM+0x530,7|(0x400 if child else 0));put(VM+0x520,0xab123456);put(VM+0x524,0x78345678)
                    m.mem_write(VM+0x50,struct.pack('<ff',1,-2.5))
                    for i,v in enumerate((-257,255,4096,13)):put(VM+0x4a0+i*4,v)
                    m.mem_write(VM+0x4b0,struct.pack('<ffff',-1.25,.125,448,-99))
                    real=op in (400,401,402);count=2 if op==402 else 1 if op in (403,405) else 3;size=8+4*count
                    m.mem_write(CODE,struct.pack('<hHhH',op,size,0,refs))
                    for i in range(count):
                        val=10004+i if real and refs&(1<<i) else 10000+i if refs&(1<<i) else value+i*7
                        m.mem_write(CODE+8+i*4,struct.pack('<f' if real else '<i',val))
                    for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                    m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                    offsets=[0x2c,0x30,0x34,0x4e0,0x4e4,0x4e8,0x38,0x3c,0x40,0x50,0x54]
                    rows.append(dict(op=op,value=value,child=child,refs=refs,words=[get(VM+0x520),get(VM+0x524),get(VM+0x530)&12,get(VM+0x28)-CODE]+[get(VM+o) for o in offsets]))
    interpolation=[]
    for duration in (-1,0,1,7,32,99):
        for mode in (-1,0,1,7,8,16,17,18,255):
            for child in (0,1):
                for refs in range(32):
                    m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64))
                    put(VM+0x28,CODE);put(VM+0x530,7|(0x400 if child else 0));put(VM+0x4a0,duration)
                    m.mem_write(VM+0x2c,struct.pack('<fff',1.5,-2.75,3.25));m.mem_write(VM+0x4e0,struct.pack('<fff',-9.5,0.125,448))
                    m.mem_write(VM+0x4b0,struct.pack('<fff',0.5,-33.25,1024));m.mem_write(0x4d9dc4,struct.pack('<fff',4.5,-5.75,6.25))
                    m.mem_write(CODE,struct.pack('<hHhHii',407,28,0,refs,10000 if refs&1 else duration,mode))
                    for i,v in enumerate((12.5,-13.25,14.75)):m.mem_write(CODE+16+i*4,struct.pack('<f',10004+i if refs&(4<<i) else v))
                    for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                    m.emu_start(table[407],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                    offsets=list(range(0x8c,0xbc,4))+[0xc8,0xcc,0xd0,0xdc,0xe0]
                    interpolation.append(dict(duration=duration,mode=mode,child=child,refs=refs,words=[get(VM+o) for o in offsets]))
    hermite=[]
    for duration in (-1,0,1,7,32,99):
        for child in (0,1):
            for refs in range(1024):
                m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64))
                put(VM+0x28,CODE);put(VM+0x530,7|(0x400 if child else 0));put(VM+0x4a0,duration)
                m.mem_write(VM+0x2c,struct.pack('<fff',1.5,-2.75,3.25));m.mem_write(VM+0x4e0,struct.pack('<fff',-9.5,.125,448))
                m.mem_write(VM+0x4b0,struct.pack('<ffff',.5,-33.25,1024,-.0))
                m.mem_write(CODE,struct.pack('<hHhHi',420,48,0,refs,10000 if refs&1 else duration))
                for i,v in enumerate((12.5,-13.25,14.75,-15.5,16.25,-17.75,18.5,-19.25,20.75)):
                    m.mem_write(CODE+12+i*4,struct.pack('<f',10004+i%4 if refs&(2<<i) else v))
                for reg,v in [(UC_X86_REG_ESI,256),(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                m.emu_start(table[420],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                offsets=list(range(0x8c,0xbc,4))+[0xc8,0xcc,0xd0,0xdc,0xe0]
                hermite.append(dict(duration=duration,child=child,refs=refs,words=[get(VM+o) for o in offsets]))
    texture=[]
    for op in (429,430):
        for duration in (-1,0,1,19):
            for mode in (-1,0,1,7,8,16,17,18,255):
                for refs in range(16):
                    m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64));put(VM+0x28,CODE);put(VM+0x530,7)
                    put(VM+0x4a0,duration);m.mem_write(VM+0x4b0,struct.pack('<ffff',.5,-33.25,1024,-.0));m.mem_write(VM+0x68,struct.pack('<ff',1.5,-2.75))
                    for i in range(4):m.mem_write(VM+0x28c+i*4,struct.pack('<f',9+i))
                    m.mem_write(CODE,struct.pack('<hHhH',op,16 if op==429 else 24,0,refs))
                    if op==429:
                        for i,v in enumerate((12.5,-13.25)):m.mem_write(CODE+8+i*4,struct.pack('<f',10004+i if refs&(1<<i) else v))
                    else:
                        m.mem_write(CODE+8,struct.pack('<ii',10000 if refs&1 else duration,mode))
                        for i,v in enumerate((12.5,-13.25)):m.mem_write(CODE+16+i*4,struct.pack('<f',10004+i if refs&(4<<i) else v))
                    for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                    m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                    offsets=[0x68,0x6c]+list(range(0x27c,0x29c,4))+[0x2a4,0x2a8,0x2ac,0x2b8,0x2bc,0x530]
                    texture.append(dict(op=op,duration=duration,mode=mode,refs=refs,words=[get(VM+o) for o in offsets]))
    polar_interpolation=[]
    for duration in (-1,0,1,19):
        for mode in (-1,0,1,7,8,16,255):
            for child in (0,1):
                for refs in range(16):
                    m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64))
                    put(VM+0x28,CODE);put(VM+0x530,7|(0x400 if child else 0));put(VM+0x4a0,duration)
                    m.mem_write(VM+0x2c,struct.pack('<fff',1.5,-2.75,3.25));m.mem_write(VM+0x4e0,struct.pack('<fff',-9.5,.125,448));m.mem_write(VM+0x4b0,struct.pack('<ffff',.5,-33.25,1024,-.0));m.mem_write(0x4d9dc4,struct.pack('<fff',4.5,-5.75,6.25))
                    m.mem_write(CODE,struct.pack('<hHhHiiff',433,24,0,refs,10000 if refs&1 else duration,mode,10004 if refs&4 else -.75,10005 if refs&8 else 33.25))
                    for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                    m.emu_start(table[433],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                    offsets=list(range(0x8c,0xbc,4))+[0xc8,0xcc,0xd0,0xdc,0xe0]
                    polar_interpolation.append(dict(duration=duration,mode=mode,child=child,refs=refs,words=[get(VM+o) for o in offsets]))
    other=[]
    configs={408:(0xe4,3,0x120,0x134,False),409:(0x13c,1,0x150,0x164,False),410:(0x16c,3,0x1a8,0x1bc,True),412:(0x1f4,2,0x21c,0x230,True),413:(0x2c0,3,0x2fc,0x310,False),414:(0x318,1,0x32c,0x340,False)}
    for op,(start,width,timer,end,real) in configs.items():
        for duration in (-1,0,1,19):
            for mode in (-1,0,1,7,8,16,17,18,255):
                for value in (-257,-1,0,255,256):
                    for refs in range(32):
                        m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64));put(VM+0x28,CODE);put(VM+0x530,7|0x60000)
                        put(VM+0x520,0xab123456);put(VM+0x524,0x78345678)
                        m.mem_write(VM+0x38,struct.pack('<fff',1.5,-2.75,3.25));m.mem_write(VM+0x50,struct.pack('<ff',1,-2.5));m.mem_write(0x4d9dc4,bytes(12))
                        for i in range(4):put(VM+0x4a0+i*4,duration if i==0 else value+(i-1)*7)
                        m.mem_write(VM+0x4b0,struct.pack('<fff',value,value+7,value+14))
                        for i in range(width*2):m.mem_write(VM+start+(2*width+i)*4,struct.pack('<f' if real else '<i',9+i))
                        size=16+width*4;m.mem_write(CODE,struct.pack('<hHhHii',op,size,0,refs,10000 if refs&1 else duration,mode))
                        for i in range(width):m.mem_write(CODE+16+i*4,struct.pack('<f' if real else '<i',(10004+i if real else 10001+i) if refs&(4<<i) else value+i*7))
                        for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                        m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                        offsets=list(range(start,start+width*16,4))+[timer,timer+4,timer+8,end,end+4]
                        other.append(dict(op=op,duration=duration,mode=mode,value=value,refs=refs,words=[get(VM+o) for o in offsets]+[get(VM+0x530)&12,(get(VM+0x530)>>17)&3]))
    lifecycle=[]
    for op in (-1,1,2):
        for flags in (0,1,6,7,0x8007):
            for clock in (0,7,19):
                m.mem_write(VM,bytes(0x700));put(VM+0x28,CODE);put(VM+0x530,flags)
                for offset,v in ((0x540,clock-1),(0x544,clock),(0x548,struct.unpack('<I',struct.pack('<f',clock+.25))[0])):put(VM+offset,v)
                m.reg_write(UC_X86_REG_EBX,VM);m.reg_write(UC_X86_REG_ESP,STACK);m.emu_start(table[op],0x462c92,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x462c92
                lifecycle.append(dict(op=op,flags=flags,clock=clock,status=m.reg_read(UC_X86_REG_EAX),words=[get(VM+0x530)&1,int(get(VM+0x28)==0xffffffff),get(VM+0x540),get(VM+0x544),get(VM+0x548)]))
    velocity=[]
    for op in (415,416,425,426):
        for value in (-257,-1,0,1,3,255,256,4096):
            for refs in range(8):
                for flags2 in (0,0xffffffff,0x78345678,0x820100):
                    m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64));put(VM+0x28,CODE);put(VM+0x530,7);put(VM+0x534,flags2)
                    for offset,val in ((0x44,1.5),(0x48,-2.75),(0x4c,3.25),(0x60,.25),(0x64,-.125),(0x3c8,4.5),(0x3cc,-5.75)):m.mem_write(VM+offset,struct.pack('<f',val))
                    m.mem_write(VM+0x4b0,struct.pack('<ffff',-1.25,.125,448,-99))
                    width=3 if op==415 else 2 if op==416 else 1;size=8+width*4;m.mem_write(CODE,struct.pack('<hHhH',op,size,0,refs))
                    for i in range(width):m.mem_write(CODE+8+i*4,struct.pack('<f',10004+i if refs&(1<<i) else value+i*7))
                    for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                    m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                    velocity.append(dict(op=op,value=value,refs=refs,flags2=flags2,words=[get(VM+o) for o in (0x44,0x48,0x4c,0x60,0x64,0x3c8,0x3cc,0x534)]+[get(VM+0x530)&12]))
    jumps=[]
    for offset in (16,24,32,48):
        for time in (-32768,-100,-1,0,1,19,32760):
            for refs in (0,1,2,3,255):
                for flags in (0,1,0x12345678,0xffffffff):
                    m.mem_write(VM,bytes(0x700));put(VM+0x28,CODE);put(VM+0x550,flags)
                    put(VM+0x540,18);put(VM+0x544,19);m.mem_write(VM+0x548,struct.pack('<f',19.25))
                    m.mem_write(CODE,struct.pack('<hHhHii',200,16,0,refs,offset,time))
                    for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE)]:m.reg_write(reg,v)
                    m.emu_start(table[200],0x45fba0,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x45fba0
                    jumps.append(dict(offset=offset,time=time,refs=refs,flags=flags,words=[get(VM+o) for o in (0x28,0x540,0x544,0x548,0x550)]))
    counters=[]
    for value in (-2147483648,-1,0,1,2,3,19,2147483647):
        for refs in (0,1,3,7):
            for time in (-32768,-1,0,27):
                m.mem_write(VM,bytes(0x700));put(VM+0x28,CODE);put(VM+0x4a0,value);put(VM+0x550,1);put(VM+0x540,18);put(VM+0x544,19);m.mem_write(VM+0x548,struct.pack('<f',19.25))
                m.mem_write(CODE,struct.pack('<hHhHiii',201,20,0,refs,10000 if refs&1 else value,40,time))
                for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE)]:m.reg_write(reg,v)
                m.emu_start(table[201],LOOP,count=10000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                pointer=get(VM+0x28)
                counters.append(dict(value=value,refs=refs,time=time,words=[get(VM+0x4a0),get(CODE+8),pointer if pointer==40 else pointer-CODE,get(VM+0x540),get(VM+0x544),get(VM+0x548)]))
    report=dict(title=16,scope='Retail setter, velocity and interpolator initialization at next dispatch, jump/timer state before target resolution, counter branch state after decrement, plus stop/delete state and return before epilogue. Variable references use the first four variables only. Production fixtures stop before animation tail for initialization comparisons. Jump targets are valid forward in-script offsets; jump reference flags are ignored as in retail. Counter includes signed wrapping and ignored target/time reference flags. No native animation tail, post-stop interrupt resumption, sprite binding, renderer or gameplay equivalence claim.',executableSha256=hashlib.sha256(img.data).hexdigest(),handlers={str(op):hex(table[op]) for op in (*ops,407,420,429,430,433,*configs,-1,1,2,415,416,425,426,200,201)},cases=rows,interpolation=interpolation,otherInterpolation=other,hermite=hermite,texture=texture,polarInterpolation=polar_interpolation,lifecycle=lifecycle,velocity=velocity,jumps=jumps,counters=counters)
    out=ROOT/'artifacts/th16/anm-basic-native.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} TH16 native basic ANM cases; {len(interpolation)} position-interpolator cases')
if __name__=='__main__':main()
