"""Execute TH14's four ANM variable accessor functions without semantic stubs."""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,PARENT,ARG,STACK,RETURN=0x70001000,0x70002000,0x70003000,0x7001f000,0x70000000


def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x20000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    cases=[]
    for kind,address in enumerate((0x46fae0,0x46f770,0x46fd60,0x46fc50)):
        for value in [*range(9999,10038),2,-1,10004.75]:
            if kind in (0,2) and not isinstance(value,int):continue
            for bound in (0,1,256,-5):
                for parent in (0,1,2):
                    m.mem_write(VM,bytes(0x700));m.mem_write(PARENT,bytes(0x700))
                    for i,v in enumerate((-11,24,-31,55)):put(VM+0x4ac+i*4,v)
                    floats(VM+0x4bc,.5,-2.25,3.75,9.125,5.5,-6.25,7.75)
                    put(VM+0x4d8,17);put(VM+0x4dc,-19);floats(VM+0x4e0,1.25,-3.5);put(VM+0x4e8,bound)
                    floats(VM+0x3c,3,5,8);floats(VM+0x48,.25,.5,.375)
                    put(VM+0x594,PARENT if parent else 0);floats(PARENT+0x50,-.625 if parent==1 else 7.125)
                    floats(0x4d9514,16,24,32);floats(0x4d9550,.5,-.25,1);floats(0x4d9538,-7,13,42)
                    m.mem_write(0x4db508,struct.pack('<HHI',12345,0,0));m.mem_write(0x4db510,struct.pack('<HHI',54321,0,0));m.mem_write(0x4f5815,b'\0')
                    put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VM)
                    m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
                    if kind==0:put(STACK+4,value)
                    elif kind==1:m.reg_write(UC_X86_REG_XMM1,struct.unpack('<I',struct.pack('<f',value))[0])
                    else:
                        m.mem_write(ARG,struct.pack('<i' if kind==2 else '<f',value));put(STACK+4,ARG)
                    m.emu_start(address,RETURN,count=100000)
                    assert m.reg_read(UC_X86_REG_EIP)==RETURN,(kind,value)
                    result=m.reg_read(UC_X86_REG_EAX)
                    if kind==1:result=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM0)&0xffffffff))[0]
                    elif kind>=2:
                        if result==ARG:result=-1
                        elif VM+0x4ac<=result<=VM+0x4e8:result=(result-VM-0x4ac)//4
                        elif VM+0x3c<=result<=VM+0x50:result=16+(result-VM-0x3c)//4
                        else:raise ValueError(hex(result))
                    cases.append(dict(kind=kind,value=value,bound=bound,parent=parent,result=result,
                        scriptSeed=get(0x4db508)&65535,scriptCalls=get(0x4db50c),visualSeed=get(0x4db510)&65535,visualCalls=get(0x4db514)))
    # Cover the complete 16-bit seed space. Fixed seeds missed the signed RNG's
    # separate SSE rounding before subtraction, observable in long effects.
    rng_samples=[];m.mem_write(VM,bytes(0x700));floats(VM+0x4e0,1,1)
    for seed in range(65536):
        row=[]
        for variable in (10011.,10012.):
            m.mem_write(0x4db508,struct.pack('<HHI',seed,0,0));put(STACK,RETURN)
            m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VM)
            m.reg_write(UC_X86_REG_XMM1,struct.unpack('<I',struct.pack('<f',variable))[0])
            m.emu_start(0x46f770,RETURN,count=1000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
            row.append(struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM0)&0xffffffff))[0])
        row.extend((get(0x4db508)&65535,get(0x4db50c)));rng_samples.append(row)
    out=ROOT/'artifacts/th14/variables-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,rngSamples=rng_samples),separators=(',',':'))+'\n',encoding='utf-8')
    print(f'{len(cases)} original TH14 variable-access cases and {len(rng_samples)*2} RNG results observed.')


if __name__=='__main__':main()
