"""TH14 ANM wait/interrupt/return lifecycle using the full native interpreter."""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
VM,CODE,STACK,RETURN=0x70001000,0x70002000,0x7001f000,0x70000000


def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x20000);m.mem_write(0x4854a0,b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def real(p):return struct.unpack('<f',m.mem_read(p,4))[0]
    cases=[]
    for wait in (3,4):
        for rate in (.5,1,2):
            for request in (7,8,-1):
                for fallback in (False,True):
                    def command(op,time,*args):return struct.pack('<hHhH',op,8+4*len(args),time,0)+b''.join(struct.pack('<i',v) for v in args)
                    code=command(403,0,37)+command(wait,0)+command(5,10,7)+command(403,10,201)+command(7,12)
                    if fallback:code+=command(5,20,-1)+command(403,20,77)+command(2,21)
                    code+=command(-1,32767)
                    m.mem_write(VM,bytes(0x700));m.mem_write(CODE,code)
                    for off,v in [(0x18,7),(0x1c,0x800000),(0x28,CODE),(0x38,CODE),(0x534,0xab123456),(0x554,0x4d8f58),(0x558,1)]:put(VM+off,v)
                    m.mem_write(0x4d8f58,struct.pack('<f',rate));timeline=[]
                    for frame in range(20):
                        pending=request if frame==4 else 8 if frame==12 else 0
                        if pending:put(VM+0x4a0,pending)
                        put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VM)
                        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
                        m.emu_start(0x46fe50,RETURN,count=100000)
                        assert m.reg_read(UC_X86_REG_EIP)==RETURN
                        timeline.append(dict(pending=pending,status=m.reg_read(UC_X86_REG_EAX),
                            instruction=get(VM+0x28)-CODE if get(VM+0x28) else -1,
                            visible=bool(get(VM+0x18)&1),waiting=bool(get(VM+0x18)&0x4000),
                            primary=get(VM+0x534),timer=real(VM+0x550),savedTimer=real(VM+8),
                            savedInstruction=get(VM+0x14)-CODE if get(VM+0x14) else -1))
                    cases.append(dict(wait=wait,rate=rate,request=request,fallback=fallback,timeline=timeline))
    out=ROOT/'artifacts/th14/flow-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} original TH14 interrupt timelines ({len(cases)*20} frames) observed.')


if __name__=='__main__':main()
