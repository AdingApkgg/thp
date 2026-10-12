"""TH14 sprite binding, including the native negative-index ASCII fallback.

Original binding and dispatch code execute in Unicorn with synthetic resources.
The optional callback is a tiny test function returning its input plus one.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,CODE,FILE,FALLBACK,SPRITES,ALT,MANAGER,STACK,RETURN=0x70001000,0x70002000,0x70003000,0x70003400,0x70004000,0x70005000,0x70010000,0x7003f000,0x70000000


def main():
    img,table,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x40000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def real(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    for file,sprites in ((FILE,SPRITES),(FALLBACK,ALT)):
        put(file+0x108,1);put(file+0x11c,sprites)
    put(0x4db520,MANAGER);put(MANAGER+0x191e4,FALLBACK)
    # mov eax,edx; add eax,1; ret -- exercise the native callback calling convention.
    callback=0x7002b000;m.mem_write(callback,bytes.fromhex('8bc283c001c3'))
    for bank,indices in ((SPRITES,range(4)),(ALT,[258])):
        for i in indices:
            p=bank+i*72;w,h=(31.5+i,17.25+i) if bank==SPRITES else (1.,1.)
            floats(p+0x1c,256,512,.125,.25,.75,.875,h,w,1,1)
    plans=[(300,value,refs,cb,frame,1,12345) for value in (-123,-1,0,1,2) for refs in (0,1) for cb in (0,1) for frame in (0,17)]
    plans += [(301,value,refs,cb,17,bound,seed) for value in (-3,0) for refs in range(4) for cb in (0,1) for bound in (1,3) for seed in (0,1,12345,65535)]
    cases=[]
    for op,value,refs,cb,frame,bound,seed in plans:
                    m.mem_write(VM,bytes(0x700));put(VM+0x18,6);put(VM+0x28,CODE);put(VM+0x30,FILE)
                    put(VM+0x4ac,value);put(VM+0x4b0,bound);put(VM+0x54c,frame);put(VM+0x5ac,callback if cb else 0)
                    m.mem_write(0x4db508,struct.pack('<HHI',seed,0,0));m.mem_write(0x4f5815,b'\0')
                    m.mem_write(CODE,struct.pack('<hHhHii',op,12 if op==300 else 16,0,refs,10000 if refs&1 else value,10001 if refs&2 else bound))
                    m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EDI,VM);m.reg_write(UC_X86_REG_EBX,CODE)
                    m.emu_start(table[op],0x47007e,count=100000)
                    assert m.reg_read(UC_X86_REG_EIP)==0x47007e
                    pointer=get(VM+0x2c)
                    cases.append(dict(op=op,value=value,refs=refs,callback=cb,frame=frame,bound=bound,seed=seed,
                        rngSeed=get(0x4db508)&65535,rngCalls=get(0x4db50c),
                        index=struct.unpack('<h',m.mem_read(VM+0x34,2))[0],fallback=pointer>=ALT,
                        ownerUnchanged=get(VM+0x30)==FILE,visible=bool(get(VM+0x18)&1),spriteFrame=get(VM+0x4a4),
                        size=real(VM+0x80,2),uv=real(VM+0x3b8,8),matrix=real(VM+0x3e0,16),
                        transform=real(VM+0x420,16),uvMatrix=real(VM+0x460,16)))
    out=ROOT/'artifacts/th14/sprite-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} original TH14 sprite bindings observed.')


if __name__=='__main__':main()
