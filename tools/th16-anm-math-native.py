"""Retail TH16 assignment and explicit three-operand arithmetic with valid operands."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,CODE,STACK,RETURN,LOOP=0x70001000,0x70003000,0x7001f000,0x70000000,0x45fb9a
def main():
    img,table,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x20000)
    ints=[23,-11,0x40000001,-99];floats=[1.5,-2.75,.125,448];rows=[]
    for op in range(100,122):
        real=bool(op&1);count=2 if op<112 else 3;division=op in (108,109,110,111,118,119,120,121)
        for a in (-2147483648,-257,-1,0,1,19,255,2147483647):
            for b in ((0,) if count==2 else (-7,-1,0,1,3,16)):
                for refs in range(8):
                    second=floats[2] if real and refs&4 else ints[2] if refs&4 else b
                    first=floats[1] if real and refs&2 else ints[1] if refs&2 else a
                    if count==2:second=first;first=floats[0] if real and refs&1 else ints[0] if refs&1 else -3
                    if division and (second==0 or not real and first==-2147483648 and second==-1):continue
                    m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64));m.mem_write(VM+0x28,struct.pack('<I',CODE));m.mem_write(VM+0x530,struct.pack('<I',7));m.mem_write(VM+0x4a0,struct.pack('<iiii',*ints));m.mem_write(VM+0x4b0,struct.pack('<ffff',*floats))
                    m.mem_write(CODE,struct.pack('<hHhH',op,8+count*4,0,refs));args=[10004 if real and refs&1 else 10000 if refs&1 else -3,10005 if real and refs&2 else 10001 if refs&2 else a,10006 if real and refs&4 else 10002 if refs&4 else b]
                    for i,v in enumerate(args[:count]):m.mem_write(CODE+8+i*4,struct.pack('<f' if real else '<i',v))
                    for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                    m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP,(op,a,b,refs,hex(m.reg_read(UC_X86_REG_EIP)))
                    def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
                    rows.append(dict(op=op,a=a,b=b,refs=refs,words=words(VM+0x4a0,4)+words(VM+0x4b0,4)+words(CODE+8,count),advance=words(VM+0x28,1)[0]-CODE))
    trig=[]
    for op in range(124,129):
        for a in (-1024,-33.25,-3.1415927410125732,-1,-.125,-0.0,0.0,1e-45,.125,.5,1,3.1415927410125732,33.25,1024):
            if op==127 and abs(a)>1:continue
            for refs in range(4):
                m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64));m.mem_write(VM+0x28,struct.pack('<I',CODE));m.mem_write(VM+0x530,struct.pack('<I',7));m.mem_write(VM+0x4b0,struct.pack('<ffff',1.5,a,.125,448))
                m.mem_write(CODE,struct.pack('<hHhHff',op,16,0,refs,10004 if refs&1 else -3,10005 if refs&2 else a))
                for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP,(op,a,refs,hex(m.reg_read(UC_X86_REG_EIP)))
                trig.append(dict(op=op,aBits=struct.unpack('<I',struct.pack('<f',a))[0],refs=refs,words=list(struct.unpack('<IIII',m.mem_read(VM+0x4b0,16)))+list(struct.unpack('<II',m.mem_read(CODE+8,8)))))
    randoms=[]
    for op in (122,123):
        for a in (-2147483648,-257,-1,0,1,3,255,2147483647):
            for refs in range(4):
                for seed in (0,1,12345,65535):
                    m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64));m.mem_write(VM+0x28,struct.pack('<I',CODE));m.mem_write(VM+0x530,struct.pack('<I',7));m.mem_write(VM+0x4a0,struct.pack('<iiii',23,a,0,0));m.mem_write(VM+0x4b0,struct.pack('<ffff',1.5,a,.125,448));m.mem_write(0x4a6d80,struct.pack('<HHI',seed,0,0));m.mem_write(0x4c10b6,b'\0')
                    m.mem_write(CODE,struct.pack('<hHhH',op,16,0,refs))
                    m.mem_write(CODE+8,struct.pack('<ff' if op==123 else '<ii',(10004 if op==123 else 10000) if refs&1 else -3,(10005 if op==123 else 10001) if refs&2 else a))
                    for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                    m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                    randoms.append(dict(op=op,a=a,refs=refs,seed=seed,rngSeed=struct.unpack('<H',m.mem_read(0x4a6d80,2))[0],rngCalls=struct.unpack('<I',m.mem_read(0x4a6d84,4))[0],words=list(struct.unpack('<IIIIIIII',m.mem_read(VM+0x4a0,32)))+list(struct.unpack('<II',m.mem_read(CODE+8,8)))))
    polar=[]
    for low,high in ((0,1),(-1,3),(-257,4096),(1.5,-2.75)):
        for refs in range(16):
            for seed in (0,1,12345,65535):
                m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64));m.mem_write(VM+0x28,struct.pack('<I',CODE));m.mem_write(VM+0x530,struct.pack('<I',7));m.mem_write(VM+0x4b0,struct.pack('<ffff',1.5,-2.75,.125,448));m.mem_write(0x4a6d80,struct.pack('<HHI',seed,0,0));m.mem_write(0x4c10b6,b'\0')
                m.mem_write(CODE,struct.pack('<hHhHffff',131,24,0,refs,10004 if refs&1 else -3,10005 if refs&2 else -7,10006 if refs&4 else low,10007 if refs&8 else high))
                for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                m.emu_start(table[131],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                polar.append(dict(low=low,high=high,refs=refs,seed=seed,rngSeed=struct.unpack('<H',m.mem_read(0x4a6d80,2))[0],rngCalls=struct.unpack('<I',m.mem_read(0x4a6d84,4))[0],words=list(struct.unpack('<IIII',m.mem_read(VM+0x4b0,16)))+list(struct.unpack('<IIII',m.mem_read(CODE+8,16)))))
    fixed_polar=[]
    for angle in (-3.1415927410125732,-.75,-0.0,0.0,.5,3.1415927410125732):
        for radius in (-257,-1,0,1,33.25,4096):
            for refs in range(16):
                m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64));m.mem_write(VM+0x28,struct.pack('<I',CODE));m.mem_write(VM+0x530,struct.pack('<I',7));m.mem_write(VM+0x4b0,struct.pack('<ffff',1.5,-2.75,.125,448))
                m.mem_write(CODE,struct.pack('<hHhHffff',130,24,0,refs,10004 if refs&1 else -3,10005 if refs&2 else -7,10006 if refs&4 else angle,10007 if refs&8 else radius))
                for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                m.emu_start(table[130],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                fixed_polar.append(dict(angle=angle,radius=radius,refs=refs,words=list(struct.unpack('<IIII',m.mem_read(VM+0x4b0,16)))+list(struct.unpack('<IIII',m.mem_read(CODE+8,16)))))
    branches=[]
    integer_bits=[v&0xffffffff for v in (-2147483648,-257,-1,0,1,23,2147483647)]
    float_bits=[0xff800000,0x7f800000,0x7fc00000,0x80000000,0,0xc0300000,0x3fc00000,1,0x80000001]
    for op in range(202,214):
        real=bool(op&1);values=float_bits if real else integer_bits
        for a in values:
            for b in values:
                for refs in range(16):
                    m.mem_write(VM,bytes(0x700));m.mem_write(VM+0x28,struct.pack('<I',CODE));m.mem_write(VM+0x4a0,struct.pack('<iiii',23,-11,0,0));m.mem_write(VM+0x4b0,struct.pack('<ffff',1.5,-2.75,0,0));m.mem_write(VM+0x540,struct.pack('<iifII',18,19,19.25,0,1))
                    bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
                    first=(bits(10004) if real else 10000) if refs&1 else a;second=(bits(10005) if real else 10001) if refs&2 else b
                    m.mem_write(CODE,struct.pack('<hHhHIIII',op,24,0,refs,first,second,48,27))
                    for reg,v in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
                    m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                    pointer=struct.unpack('<I',m.mem_read(VM+0x28,4))[0]
                    branches.append(dict(op=op,aBits=a,bBits=b,refs=refs,words=[pointer if pointer==48 else pointer-CODE]+list(struct.unpack('<III',m.mem_read(VM+0x540,12)))))
    out=ROOT/'artifacts/th16/anm-math-native.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),handlers={str(op):hex(table[op]) for op in (*range(100,122),*range(122,129),130,131,*range(202,214))},scope='Retail assignment, in-place and explicit three-operand arithmetic plus twelve comparison branches at next dispatch; exact output words, immediate and first-four-variable references. Includes signed overflow, finite arithmetic and comparison NaNs, infinities, signed zeros and subnormals. Branch offset/time references are ignored as in retail. Global retail RNG executes with mutex disabled. Random integer zero bound preserves the RNG; signed bounds use unsigned modulo. Finite sine/cosine/tangent/arccosine/arctangent execute their original CRT helpers (arccosine within its real domain). Excludes division/remainder by zero, signed INT_MIN/-1, intrinsic nonfinite inputs, animation and gameplay equivalence.',cases=rows,branches=branches,trig=trig,randoms=randoms,polar=polar,fixedPolar=fixed_polar),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} native TH16 ANM arithmetic cases; {len(branches)} comparison branch cases')
if __name__=='__main__':main()
