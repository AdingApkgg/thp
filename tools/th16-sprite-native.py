"""Execute TH16's retail sprite dispatcher and complete binder on valid synthetic banks."""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,CODE,FILE,FALLBACK,SPRITES,ALT,MANAGER,STACK,RETURN=0x70001000,0x70002000,0x70003000,0x70003400,0x70004000,0x70005000,0x70010000,0x7003f000,0x70000000
def main():
    img,table,_=importlib.import_module('th-anm-handlers').handlers(16)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x40000)
    bank_slot=MANAGER+0x184f4f0;m.mem_map(bank_slot&~4095,4096)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def real(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    for file,sprites in ((FILE,SPRITES),(FALLBACK,ALT)):put(file+0x108,1);put(file+0x11c,sprites)
    put(0x4c0f48,MANAGER);put(bank_slot+8,FILE);put(0x4a6d98,MANAGER);put(MANAGER+0x19240,FALLBACK)
    callback=0x7002b000;m.mem_write(callback,bytes.fromhex('8bc283c001c3'));put(0x491b20,callback)
    for bank,indices in ((SPRITES,range(4)),(ALT,[258])):
        for i in indices:
            w,h=(31.5+i,17.25+i) if bank==SPRITES else (1.,1.)
            floats(bank+i*68+0x1c,256,512,.125,.25,.75,.875,h,w,1,1)
    rows=[]
    plans=[(300,value,refs,cb,frame,1,12345) for value in (-123,-1,0,1,2) for refs in (0,1) for cb in (0,1) for frame in (0,17,32760)]
    plans += [(301,value,refs,cb,17,bound,seed) for value in (-3,0) for refs in range(4) for cb in (0,1) for bound in (1,3) for seed in (0,1,12345,65535)]
    for op,value,refs,cb,frame,bound,seed in plans:
                    m.mem_write(VM,bytes(0x700));put(VM+0x530,6);put(VM+0x28,CODE);put(VM+0x1c,2);put(VM+0x4a0,value);put(VM+0x544,frame);put(VM+0x5dc,cb)
                    put(VM+0x4a4,bound);m.mem_write(0x4a6d80,struct.pack('<HHI',seed,0,0));m.mem_write(0x4c10b6,b'\0')
                    m.mem_write(CODE,struct.pack('<hHhHii',op,12 if op==300 else 16,0,refs,10000 if refs&1 else value,10001 if refs&2 else bound))
                    m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EBX,VM);m.reg_write(UC_X86_REG_EDI,CODE)
                    m.emu_start(table[op],0x45fb9a,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x45fb9a
                    index=get(VM+0x20)
                    rows.append(dict(op=op,value=value,refs=refs,callback=cb,frame=frame,bound=bound,seed=seed,rngSeed=get(0x4a6d80)&65535,rngCalls=get(0x4a6d84),index=index,fallback=index==258,ownerUnchanged=get(VM+0x1c)==2,visible=bool(get(VM+0x530)&1),spriteFrame=get(VM+0x494),size=real(VM+0x70,2),uv=real(VM+0x3a8,8),matrix=real(VM+0x3d0,16),transform=real(VM+0x410,16),uvMatrix=real(VM+0x450,16)))
    out=ROOT/'artifacts/th16/sprite-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),handlers={str(op):hex(table[op]) for op in (300,301)},binder='0x45edb0',rng='0x402be0',scope='Retail opcodes 300/301 and complete sprite binder on synthetic valid resource banks. Callback is a controlled input-plus-one function. Actual global RNG executes with mutex disabled, positive bounds 1/3 and four seeds. Index selection, ASCII fallback, owner, timer stamp, sizes, UV and matrices; no renderer, invalid-bank, zero range or gameplay claim.',cases=rows),indent=2)+'\n',encoding='utf-8')
    print(f'{len(rows)} native TH16 sprite cases')
if __name__=='__main__':main()
