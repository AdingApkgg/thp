"""Execute both real TH14 ECL -9988 getters with distinct phase/lifetime clocks."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]


def main():
    image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in image.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,image.data[raw:raw+n])
    base=0x70000000;m.mem_map(base,0x20000);enemy=base+0x1000;stack=base+0x1f000;result=base+0x100
    floating_return=base+0x800
    m.mem_write(floating_return,b'\xd9\x1d'+struct.pack('<I',result))
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    rows=[]
    for phase in (-1,0,1,5399,5400,7200,2147483647):
        for fractional in (-.5,0.,.5,5399.75,5400.25,7200.5):
            for lifetime in (120,20000):
                m.mem_write(enemy,bytes(0x6000))
                put(enemy+0x14b0,phase);put(enemy+0x14b4,bits(fractional))
                put(enemy+0x14c4,lifetime);put(enemy+0x14c8,bits(lifetime+.25))
                values=[]
                for address,floating in ((0x42a920,False),(0x42b230,True)):
                    target=floating_return+6 if floating else base
                    put(stack,floating_return if floating else base);put(stack+4,-9988)
                    m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy)
                    m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPTAG,0xffff)
                    m.emu_start(address,target,count=1000)
                    assert m.reg_read(UC_X86_REG_EIP)==target,(hex(address),phase,fractional,hex(m.reg_read(UC_X86_REG_EIP)))
                    values.append(struct.unpack('<I',m.mem_read(result,4))[0] if floating else m.reg_read(UC_X86_REG_EAX))
                rows.append(dict(phaseCurrent=phase,phaseFractionalBits=bits(fractional),lifetimeCurrent=lifetime,lifetimeFractionalBits=bits(lifetime+.25),integer=values[0],floating=values[1]))
    output=ROOT/'artifacts/th14/ecl-phase-clock';output.mkdir(parents=True,exist_ok=True)
    (output/'native.json').write_text(json.dumps(dict(cases=rows,executableSha256=hashlib.sha256(image.data).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
    print('Original getter cases:',len(rows))


if __name__=='__main__':main()
