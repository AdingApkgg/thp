"""Execute retail rectangle/circle bodies on captured stage-3 boundary queries.

The supplied PlayerCollision shape is the declared input, including its already
scaled radius. This does not prove original bullet trajectories or scheduling.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import struct
import sys

R=Path(__file__).resolve().parents[1]
SHA=lambda data:hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14') and not out.exists()
    run=json.loads((args.run/'report.json').read_bytes())
    assert run['retired'] and run['passed'] and not run['exception'] and not run['errors']
    capture=(args.run/'stage3-collision-queries.u32').read_bytes()
    assert capture and len(capture)%(42*4)==0 and len(capture)<=4096*42*4
    rows=list(struct.iter_unpack('<42I',capture))
    assert all(r[0]==0x47525a33 and r[1]==3 and r[5] in (0,2) and not r[6]&4 for r in rows)
    sys.path[:0]=[str(R/'tools/tmp/th14-analysis-python'),str(R/'tools')]
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_EAX,UC_X86_REG_XMM2,UC_X86_REG_MXCSR
    image=importlib.import_module('th-anm-handlers').handlers(14)[0]
    assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,address,size,offset,length in image.sections:
        first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first)
        m.mem_write(address,image.data[offset:offset+length])
    end,player,hud,pos,sizeptr,header,stack=[0x70000000+n for n in (0,0x1000,0x20000,0x21000,0x22000,0x23000,0x3f000)]
    m.mem_map(end,0x40000)
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    real=lambda bits:struct.unpack('<f',struct.pack('<I',bits))[0]
    hit_calls=[]
    def hit_boundary(machine,pc,length,data):
        sp=machine.reg_read(UC_X86_REG_ESP);hit_calls.append(True)
        machine.reg_write(UC_X86_REG_EAX,0);machine.reg_write(UC_X86_REG_ESP,sp+4);machine.reg_write(UC_X86_REG_EIP,get(sp))
    m.hook_add(UC_HOOK_CODE,hit_boundary,begin=0x44f7a0,end=0x44f7a0)
    put(0x4db67c,player);put(player+0x688,header);put(0x4db550,hud)
    mismatches=[];nearest=[]
    for index,row in enumerate(rows):
        hit_calls.clear()
        for off,value in ((0x5e0,row[25]),(0x5e4,row[26]),(0x630,row[27]),(0x634,row[28]),
                          (0x63c,row[29]),(0x640,row[30]),(0x684,row[32]),(0x182c4,row[33]),(0x182d4,0)):
            put(player+off,value)
        put(header+4,row[31]);put(hud+0x194,row[34]);put(pos,row[14]);put(pos+4,row[15])
        put(sizeptr,row[22]);put(sizeptr+4,row[23]);put(stack,end);put(stack+4,pos)
        circle=bool(row[6]&0x10)
        put(stack+8,0 if circle else sizeptr)
        if not circle:put(stack+12,0)
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player)
        m.reg_write(UC_X86_REG_XMM2,row[22]);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.emu_start(0x44efa0 if circle else 0x44ee80,end,count=10000)
        assert m.reg_read(UC_X86_REG_EIP)==end
        actual=m.reg_read(UC_X86_REG_EAX)
        record=dict(index=index,controlFrame=row[2],slot=row[3],bulletAge=row[4],portResult=row[5],nativeResult=actual,
                    circle=circle,margin=real(row[39]),position=[real(row[14]),real(row[15])],
                    player=[real(row[25]),real(row[26])],velocity=[real(row[17]),real(row[18])],
                    speed=real(row[20]),angle=real(row[21]),radiusOrWidth=real(row[22]),
                    sprite=row[11],color=row[12],activeTransforms=row[8])
        nearest.append(record)
        if actual!=row[5] or hit_calls:mismatches.append(record)
    nearest.sort(key=lambda r:abs(r['margin']))
    q=dict(passed=not mismatches,cases=len(rows),circleCases=sum(bool(r[6]&0x10) for r in rows),
           eligiblePortGrazeQueries=sum(r[5]==2 for r in rows),mismatchCount=len(mismatches),mismatches=mismatches,
           closestBoundaryQueries=nearest[:20],captureBytes=len(capture),captureSha256=SHA(capture),
           nativeExecutableSha256=SHA(image.data),instructionBytesPatched=0,
           alreadyScaledPlayerRadiusDeclared=True,hitApplicationControlledBoundary=True,
           originalTrajectoryOrPlayerTimelineAccepted=False,currentExtraGrazeExplained=False,
           sourceStateFedBack=False,gameLogicChanged=False,completeGame=False,toolSha256=SHA(Path(__file__).read_bytes()))
    out.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k not in ('closestBoundaryQueries','mismatches')}))


if __name__=='__main__':
    main()
