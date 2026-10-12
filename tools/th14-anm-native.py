"""Execute retail TH14 ANM handlers. Only the security-cookie check is replaced.

State probes stop at the next dispatch boundary, before animation/timer updates.
Delete/stop probes execute the complete entry twice to observe lifetime behavior.
"""
import hashlib
import importlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
VM, CODE, STACK, RETURN = 0x70001000, 0x70002000, 0x7001f000, 0x70000000
LOOP = 0x47007e
OPS = [1,2,6,302,303,304,305,306,307,308,309,310,311,312,313,314,315,403,405,421,423,424,431,432,437,438,507]
VALUES = [0,1,2,3,15,16,18,19,20,21,22,23,24,29,31,32,34,35,255,256,-1]


def main():
    img, table, default = importlib.import_module('th-anm-handlers').handlers(14)
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        begin=base&~4095
        m.mem_map(begin, ((base+size+4095)&~4095)-begin)
        m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x20000)
    m.mem_write(0x4854a0,b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def flt(p):return struct.unpack('<f',m.mem_read(p,4))[0]
    defaults=[op for op in (0,313,314,315,316,317,318,439,440,441,611,612,613,614,617,618,628,633,634) if table.get(op,default)==default]
    cases=[]
    for op in OPS+defaults:
        for value in VALUES:
            for variant in (0,1):
                for refs in (0,3 if op==312 else 1):
                    flags2=0xbc0000 if variant else 0x820000
                    flags=7|(0xc0009000 if variant else 0x40000000)
                    m.mem_write(VM,bytes(0x700))
                    for off,v in [(0x18,flags),(0x1c,flags2),(0x24,27),(0x28,CODE),
                                  (0x534,0xab123456),(0x538,0x78345678),(0x4ac,value),(0x4b0,value^2),
                                  (0x554,0x4d8f58),(0x558,1)]:put(VM+off,v)
                    m.mem_write(VM+0x60,struct.pack('<ff',1.,-2.5))
                    m.mem_write(0x4d8f58,struct.pack('<f',1.))
                    arg=10000 if refs else value
                    arg2=10001 if refs&2 else value^2
                    m.mem_write(CODE,struct.pack('<hHhHII',op,16 if op==312 else 12,0,refs,arg&0xffffffff,arg2&0xffffffff))
                    m.reg_write(UC_X86_REG_ESP,STACK)
                    m.reg_write(UC_X86_REG_EBP,STACK)
                    m.reg_write(UC_X86_REG_EDI,VM)
                    m.reg_write(UC_X86_REG_EBX,CODE)
                    m.reg_write(UC_X86_REG_XMM1,0xbf800000)
                    m.reg_write(UC_X86_REG_FPCW,0x37f)
                    m.reg_write(UC_X86_REG_FPSW,0)
                    m.reg_write(UC_X86_REG_FPTAG,0xffff)
                    if op in (1,2):
                        statuses=[]
                        for _ in range(2):
                            put(STACK,RETURN)
                            m.reg_write(UC_X86_REG_ESP,STACK)
                            m.reg_write(UC_X86_REG_ECX,VM)
                            m.emu_start(0x46fe50,RETURN,count=100000)
                            assert m.reg_read(UC_X86_REG_EIP)==RETURN
                            statuses.append(m.reg_read(UC_X86_REG_EAX))
                        status,next_status=statuses
                    else:
                        m.emu_start(table.get(op,default),LOOP,count=100000)
                        assert m.reg_read(UC_X86_REG_EIP)==LOOP,(op,value,variant,refs,hex(m.reg_read(UC_X86_REG_EIP)))
                        status,next_status=0,None
                    cases.append(dict(op=op,value=value,variant=variant,refs=refs,arg=arg,arg2=arg2,
                        initialFlags2=flags2,status=status,nextStatus=next_status,
                        stopped=get(VM+0x28)==0,primary=get(VM+0x534),secondary=get(VM+0x538),
                        layer=get(VM+0x24),flags2=get(VM+0x1c),scaleY=flt(VM+0x64),
                        flipY=bool(get(VM+0x18)&0x1000),visible=bool(get(VM+0x18)&1),
                        scaleDirty=bool(get(VM+0x18)&8),flag15=bool(get(VM+0x18)&0x8000),
                        addressV=get(VM+0x18)>>30,drawingMode=(get(VM+0x18)>>25)&31,
                        vertexColorMode=(get(VM+0x18)>>17)&3,timerFraction=flt(VM+0x550),
                        blendMode=(get(VM+0x18)>>5)&15,depthDisabled=bool(get(VM+0x18)&0x2000),
                        flipX=bool(get(VM+0x18)&0x800),scaleX=flt(VM+0x60),
                        anchorX=(get(VM+0x18)>>21)&3,anchorY=(get(VM+0x18)>>23)&3))
    out=ROOT/'artifacts/th14/anm-native.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(game='th14',scope='Selected native instruction state; no renderer or complete-game equivalence.',
        executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,defaultOpcodes=defaults),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} original TH14 ANM state cases observed.')


if __name__=='__main__':main()
