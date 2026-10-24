"""Actual44e005 active stationary-area loop, including unmodified403cd0/403df0/floor.

Synthetic finite positions/clock inputs; no live process state injection. The
original instructions and math services are not patched. This is a bounded
instruction control, not whole-game equivalence.
"""
from pathlib import Path
import hashlib,importlib,itertools,json,random,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
OFFSETS=[0x10,0x14,0x18,0x1c,0x20,0x2c,0x30,0x34,0x70,0x74,0x78,0x84,0x88,0x8c,0x90,0x94]
def main():
    img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
    end,player,stack=0x70000000,0x70010000,0x700ff000;m.mem_map(end,0x100000);a=player+0xde18
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    positions=[(-106.8515625,74.9765625),(0.,0.),(-0.,-0.),(-192.,480.),(192.,-32.),(-.0078125,.0078125),(-6.73,6.73),(1.0000001192092896,-1.0000001192092896)]
    rng=random.Random(0x44e005)
    positions += [(rng.randint(-24576,24576)/128,rng.randint(-4096,61440)/128) for _ in range(192)]
    rows=[]
    for (x,y),rate,flags in itertools.product(positions,(0.,.5,1.,1.25),(0,1,3)):
        m.mem_write(player,bytes(0x19000));m.mem_write(stack-0x3000,bytes(0x3100));floats(0x4d8f58,rate)
        # Movement at area+2c is stationary, mode0; the active-area loop still snaps XY.
        put(a+0x10,flags);floats(a+0x14,32,16,.37,0);floats(a+0x2c,x,y,.25)
        for off,value in [(0x70,30),(0x74,30),(0x78,bits(30.)),(0x7c,0x4d8f58),(0x84,150),(0x88,3900),(0x8c,9999999),(0x90,1),(0x94,148)]:put(a+off,value)
        frames=[]
        for _ in range(4):
            put(stack+0x1c,1);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBX,a+0x78);m.reg_write(UC_X86_REG_EDI,player);m.reg_write(UC_X86_REG_EAX,1)
            m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
            m.emu_start(0x44e005,0x44e0fa,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x44e0fa
            frames.append([get(a+o) for o in OFFSETS])
        rows.append(dict(input=[bits(x),bits(y),bits(rate),flags],frames=frames))
    out=ROOT/'artifacts/th14/damage-area-snap-oct25';out.mkdir(exist_ok=True)
    report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),originalEntry='44e005..44e0fa;403cd0;403df0;4040dc..40415f',originalInstructionsOrMathPatched=False,offsets=OFFSETS,rows=rows,finiteInputsOnly=True,completeGame=False,nativeEquivalent=False)
    (out/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(json.dumps(dict(cases=len(rows),frames=len(rows)*4,originalInstructionsOrMathPatched=False)))
if __name__=='__main__':main()
