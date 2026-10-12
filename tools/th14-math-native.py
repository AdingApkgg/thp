"""Native TH14 ANM arithmetic, random, and branch observations at dispatch boundaries."""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,CODE,STACK,RETURN=0x70001000,0x70002000,0x7001f000,0x70000000


def main():
    img,table,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x20000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
    def real(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    cases=[]
    for op in [*range(100,132),*range(200,214)]:
        for sample,(a,b) in enumerate(((7,3),(-7,3),(7,-3),(-7,-3),(1,1),(0,1))):
            for refs_variant in (0,1,2,7):
                for visual in (0,1):
                    seed=(0,1,12345,32768,54321,65535)[sample]
                    m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(128))
                    for off,v in [(0x18,7),(0x1c,visual<<9),(0x28,CODE),(0x38,CODE),(0x554,0x4d8f58),(0x558,1)]:put(VM+off,v)
                    ints=[a,b,2,9];floats=[a/8,b/8,.5,.75]
                    m.mem_write(VM+0x4ac,struct.pack('<4i',*ints));m.mem_write(VM+0x4bc,struct.pack('<4f',*floats))
                    m.mem_write(0x4db508,struct.pack('<HHI',seed,0,0));m.mem_write(0x4db510,struct.pack('<HHI',54321,0,0));m.mem_write(0x4f5815,b'\0')
                    args=[];refs=0
                    def add(kind,value,var,bit=None):
                        nonlocal refs
                        if refs_variant&(1<<(len(args) if bit is None else bit)):
                            refs|=1<<len(args);value=var
                        args.append(struct.pack('<'+kind,value))
                    if op<=121:
                        kind='f' if op%2 else 'i';initial=floats[0] if kind=='f' else a
                        add(kind,initial,10004. if kind=='f' else 10000)
                        add(kind,floats[1] if kind=='f' else b,10005. if kind=='f' else 10001)
                        if op>=112:add(kind,.5 if kind=='f' else 2,10006. if kind=='f' else 10002)
                    elif op in (122,123):
                        kind='i' if op==122 else 'f'
                        add(kind,a if kind=='i' else floats[0],10000 if kind=='i' else 10004.)
                        add(kind,b if kind=='i' else floats[1],10001 if kind=='i' else 10005.)
                    elif op<=128:
                        add('f',floats[0],10004.);add('f',floats[1],10005.)
                    elif op==129:add('f',floats[0],10004.)
                    elif op in (130,131):
                        add('f',0.,10006.);add('f',0.,10007.)
                        add('f',floats[0],10004.,0);add('f',floats[1],10005.,1)
                    elif op==200:args=[struct.pack('<i',64),struct.pack('<i',12)]
                    elif op==201:
                        add('i',a,10000);args.extend((struct.pack('<i',64),struct.pack('<i',12)))
                    else:
                        kind='f' if op%2 else 'i'
                        add(kind,floats[0] if kind=='f' else a,10004. if kind=='f' else 10000)
                        add(kind,floats[1] if kind=='f' else b,10005. if kind=='f' else 10001)
                        args.extend((struct.pack('<i',64),struct.pack('<i',12)))
                    raw=b''.join(args);length=8+len(raw)
                    m.mem_write(CODE,struct.pack('<hHhH',op,length,0,refs)+raw)
                    m.mem_write(CODE+length,struct.pack('<hHhH',0,8,30000,0));m.mem_write(CODE+64,struct.pack('<hHhH',0,8,30000,0))
                    m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EBP,STACK)
                    m.reg_write(UC_X86_REG_EDI,VM);m.reg_write(UC_X86_REG_EBX,CODE)
                    m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
                    try:m.emu_start(table[op],0x47007e,count=100000)
                    except Exception as ex:raise RuntimeError((op,a,b,refs,hex(m.reg_read(UC_X86_REG_EIP)))) from ex
                    assert m.reg_read(UC_X86_REG_EIP)==0x47007e,(op,hex(m.reg_read(UC_X86_REG_EIP)))
                    cases.append(dict(op=op,refs=refs,args=list(struct.unpack('<'+'I'*len(args),raw)),initialInts=ints,initialFloats=floats,
                        seed=seed,visual=visual,integers=words(VM+0x4ac,4),floats=real(VM+0x4bc,4),outputArgs=words(CODE+8,len(args)),
                        next=m.reg_read(UC_X86_REG_EAX)-CODE,timer=real(VM+0x550,1)[0],
                        rngSeed=words(0x4db508,1)[0]&65535,rngCalls=words(0x4db50c,1)[0],visualCalls=words(0x4db514,1)[0]))
    out=ROOT/'artifacts/th14/math-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} original TH14 arithmetic/random/branch cases observed.')


if __name__=='__main__':main()
