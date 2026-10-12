"""Observe original TH13 ANM handlers in Unicorn, with no game/OS stubs.

Ordinary handlers stop at the next dispatch boundary. Stop/delete instructions
run the full interpreter entry and return, with only the security-cookie check
stubbed. No instruction semantics are substituted.
"""
import importlib
import json
import struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
VM=0x70001000
CODE=0x70002000
STACK=0x7001f000
RETURN=0x70000000
LOOP=0x4624fd
DEFAULT_OPS=[313,314,315,316,317,318,439,440,441,509,609,610,612,613,614,617,618,628,633,634]


def main():
    img,handlers,default=importlib.import_module('th-anm-handlers').handlers(13)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        begin=base&~4095;length=((base+size+4095)&~4095)-begin
        m.mem_map(begin,length)
        m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x20000)
    m.mem_write(0x47a09f,b'\xc3')  # security cookie, no game-state behavior
    stop_at_loop=False
    def boundary(machine,address,size,user):
        if stop_at_loop and address==LOOP:machine.emu_stop()
    m.hook_add(UC_HOOK_CODE,boundary,begin=LOOP,end=LOOP)
    def put(p,value):m.mem_write(p,struct.pack('<I',value&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def flt(p):return struct.unpack('<f',m.mem_read(p,4))[0]
    observations=[]
    for op in [1,2,6,302,304,306,309,310,312,403,405,423,424,431,432,437,438,507]+DEFAULT_OPS:
        for value in ([0,1,2,3,15,16,18,19,20,21,31,255,256,-1] if op==302 else [0,1,2,3,18,19,255,256,-1]):
            for variant in range(2):
                # Native masks differ from canonical masks. Compare named fields.
                flags=7|(0xc0009000 if variant else 0x40000000)
                flags2=0x840000 if variant else 0x800000
                refs=(3 if op==312 else 1) if variant and op in (6,306,312,403,405,432,437,507) else 0
                m.mem_write(VM,bytes(0x700))
                for off,val in [(0x18,flags),(0x1c,flags2),(0x24,27),(0x28,CODE),
                                (0x528,0xab123456),(0x52c,0x78345678),(0x4ac,value),(0x4b0,value^2),
                                (0x544,0x4c0a28),(0x548,1)]:put(VM+off,val)
                m.mem_write(VM+0x60,struct.pack('<ff',1.,-2.5))
                m.mem_write(0x4c0a28,struct.pack('<f',1.))
                arg=10000 if refs else value
                arg2=10001 if refs&2 else value^2
                m.mem_write(CODE,struct.pack('<hHhHII',op,16 if op==312 else 12,0,refs,arg&0xffffffff,arg2&0xffffffff))
                m.reg_write(UC_X86_REG_ESP,STACK)
                m.reg_write(UC_X86_REG_EBP,STACK)
                m.reg_write(UC_X86_REG_EBX,VM)
                m.reg_write(UC_X86_REG_EDI,CODE)
                m.reg_write(UC_X86_REG_FPCW,0x37f)
                m.reg_write(UC_X86_REG_FPSW,0)
                m.reg_write(UC_X86_REG_FPTAG,0xffff)
                if op in (1,2):
                    stop_at_loop=False
                    put(STACK,RETURN);m.reg_write(UC_X86_REG_ECX,VM)
                    m.emu_start(0x462450,RETURN,count=100000)
                    assert m.reg_read(UC_X86_REG_EIP)==RETURN
                    status=m.reg_read(UC_X86_REG_EAX)
                    # A stopped TH13 VM remains stopped on the next call as well.
                    m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VM)
                    m.emu_start(0x462450,RETURN,count=100000)
                    assert m.reg_read(UC_X86_REG_EIP)==RETURN
                    next_status=m.reg_read(UC_X86_REG_EAX)
                else:
                    stop_at_loop=True
                    if op in DEFAULT_OPS:assert handlers.get(op,default)==default
                    m.emu_start(handlers.get(op,default),LOOP,count=100000)
                    assert m.reg_read(UC_X86_REG_EIP)==LOOP,(op,value,variant,hex(m.reg_read(UC_X86_REG_EIP)))
                    status=0;next_status=None
                observations.append(dict(op=op,value=value,variant=variant,refs=refs,arg=arg,arg2=arg2,
                    status=status,nextStatus=next_status,stopped=get(VM+0x28)==0,
                    primary=get(VM+0x528),secondary=get(VM+0x52c),layer=get(VM+0x24),flags2=get(VM+0x1c),
                    scaleY=flt(VM+0x64),flipY=bool(get(VM+0x18)&0x1000),
                    visible=bool(get(VM+0x18)&1),scaleDirty=bool(get(VM+0x18)&8),
                    flag15=bool(get(VM+0x18)&0x8000),addressV=get(VM+0x18)>>30,drawingMode=(get(VM+0x18)>>25)&31,vertexColorMode=(get(VM+0x18)>>17)&3,
                    timerFraction=flt(VM+0x540)))
    polar=[]
    stop_at_loop=True
    for seed in (0,1,12345,32768,65535):
        for low,high in ((0.,1.),(48.,64.),(-10.,20.),(3.25,3.25),(20.,-5.)):
            for refs in (0,3,7,11,15):
                for visual in (0,1):
                    m.mem_write(VM,bytes(0x700));put(VM+0x28,CODE)
                    # TH13 visual-RNG selection lives in flags2 bit 9; opcode
                    # 131 ignores it and explicitly addresses the script RNG.
                    put(VM+0x1c,0x200 if visual else 0)
                    m.mem_write(VM+0x4bc,struct.pack('<4f',low,0.,0.,high))
                    args=(10005.,10006.,10004. if refs&4 else low,10007. if refs&8 else high)
                    m.mem_write(CODE,struct.pack('<hHhH4f',131,24,0,refs,*args))
                    m.mem_write(0x4dc31c,struct.pack('<HHI',seed,0,0))
                    m.mem_write(0x4e49ed,b'\0') # lock inactive in this isolated single-thread probe
                    m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EBP,STACK)
                    m.reg_write(UC_X86_REG_EBX,VM);m.reg_write(UC_X86_REG_EDI,CODE)
                    put(STACK+0x18,CODE)
                    m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0)
                    m.reg_write(UC_X86_REG_FPTAG,0xffff)
                    m.emu_start(handlers[131],LOOP,count=100000)
                    assert m.reg_read(UC_X86_REG_EIP)==LOOP
                    x=flt(VM+0x4c0 if refs&1 else CODE+8)
                    y=flt(VM+0x4c4 if refs&2 else CODE+12)
                    polar.append(dict(seed=seed,low=low,high=high,refs=refs,visual=visual,x=x,y=y,
                                      rngSeed=get(0x4dc31c)&65535,rngCalls=get(0x4dc320)))
    report={'scope':'Original handler state only; renderer behavior is not asserted.',
            'game':'th13','executableSha256':__import__('hashlib').sha256(img.data).hexdigest(),
            'cases':observations,'polar':polar}
    out=ROOT/'artifacts/th13/anm-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'{len(observations)} original TH13 ANM state cases and {len(polar)} random-polar cases observed.')


if __name__=='__main__':main()
