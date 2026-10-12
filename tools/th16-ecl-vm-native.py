"""Run the retail TH16 VM on synthetic valid instructions, without enemy systems."""
import importlib,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,CODE,STACK,RETURN=0x70000000,0x70010000,0x700ff000,0x700fe000
def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(BASE,0x100000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def instruction(op,args,refs=0,cleanup=0,time=0,difficulty=255):return struct.pack('<iHHHBBI',time,op,16+len(args)*4,refs,difficulty,len(args),cleanup)+struct.pack('<'+'I'*len(args),*[v&0xffffffff for v in args])
    cases=[]
    def run(op,args,refs=0,cleanup=0,time=128,rate=1,stack=None,difficulty=255,seed=0):
        initial=[0]*192
        for i in range(16):initial[i*2:i*2+2]=[ord('i') if i%2==0 else ord('f'),i+1 if i%2==0 else bits(i+.25)]
        initial[128:132]=[bits(12.75),bits(-3.5),123,456]
        if stack:initial[:len(stack)]=stack
        code=instruction(op,args,refs,cleanup,difficulty=difficulty)+instruction(0,[],time=2147483647)
        m.mem_write(BASE,bytes(0x2000));m.mem_write(BASE+12,struct.pack('<192I',*initial));m.mem_write(CODE,bytes(16)+code)
        put(BASE,bits(time));put(BASE+4,0);put(BASE+8,0);put(BASE+0x100c,128);put(BASE+0x1020,255);put(STACK,RETURN);put(BASE+0x1018,BASE+0x2000);put(BASE+0x2000+0x11f8,BASE+0x4000);put(BASE+0x4000+0x8c,BASE+0x5000);put(BASE+0x5000+4,CODE)
        m.reg_write(UC_X86_REG_ECX,BASE);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_XMM1,bits(rate))
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(0x472030,RETURN,count=20000);assert m.reg_read(UC_X86_REG_EIP)==RETURN,(op,hex(m.reg_read(UC_X86_REG_EIP)))
        top=get(BASE+0x100c);assert top<=768
        cases.append(dict(opcode=op,seed=seed,code=code.hex(),time=bits(time),rate=bits(rate),initial=initial,rng=[0,0],output=dict(result=m.reg_read(UC_X86_REG_EAX),time=get(BASE),offset=get(BASE+8),top=top,stack=list(struct.unpack('<192I',m.mem_read(BASE+12,768))))))
    for op in (0,22,30,31,23,24):
        for value in (1,17,200,-8,16777217):
            for rate in (.5,1,2):
                run(op,[bits(value+.25) if op==24 else value] if op in (23,24) else [],cleanup=16,rate=rate)
    for op in (23,24,42,44):
        for index in (-1,-2,-3,-16,512):
            for cleanup in (0,8,16):run(op,[bits(index) if op in (24,44) else index],refs=1,cleanup=cleanup)
    for op in (43,45,78):
        for cleanup in (0,8,16):run(op,[bits(512) if op==45 else 512],refs=1,cleanup=cleanup)
    for op in [*range(50,79),83,84,88]:
        for kind in (ord('i'),ord('f')):
            for n in range(4):
                stack=[]
                for i in range(16):stack.extend([kind,i+1+n if kind==ord('i') else bits(i*.5+1.25+n)])
                if op==78:run(op,[512],refs=1,stack=stack)
                else:run(op,[],stack=stack)
    for op in (85,86,87):
        for n in range(12):
            args=[bits(512),bits(3+n*.375),bits(4-n*.125)]
            if op==87:args.extend([bits(n*1.25+50),bits(2+n*.625)])
            run(op,args,refs=1,cleanup=16)
    path=ROOT/'artifacts/th16/ecl-vm-native.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} retail TH16 VM cases observed.')
if __name__=='__main__':main()
