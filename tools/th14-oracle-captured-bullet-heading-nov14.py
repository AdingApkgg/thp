"""Rebuild headings with retail ETEX 40000 for captured boundary-query angles.

This is a fresh controlled heading operation. A stored velocity need not equal
this operation after other transforms, and original trajectories are not proved.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import struct
import sys

R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert a.output.resolve().is_relative_to(R/'artifacts/th14') and not a.output.exists()
    raw=a.capture.read_bytes();assert raw and len(raw)%(42*4)==0
    rows=list(struct.iter_unpack('<42I',raw));assert all(r[0]==0x47525a33 for r in rows)
    sys.path[:0]=[str(R/'tools/tmp/th14-analysis-python'),str(R/'tools')]
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_MXCSR,UC_X86_REG_FPCW,UC_X86_REG_FPSW,UC_X86_REG_FPTAG
    image=importlib.import_module('th-anm-handlers').handlers(14)[0]
    assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,address,size,offset,length in image.sections:
        first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first);m.mem_write(address,image.data[offset:offset+length])
    base=0x70000000;bullet=base+0x1000;player=base+0x4000;stack=base+0x1f000;m.mem_map(base,0x20000)
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    boundaries=[]
    def boundary(machine,pc,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP);boundaries.append(pc)
        machine.reg_write(UC_X86_REG_EAX,0);machine.reg_write(UC_X86_REG_ESP,sp+4+(8 if pc==0x46e3d0 else 0));machine.reg_write(UC_X86_REG_EIP,get(sp))
    for pc in (0x4854a0,0x46e3d0):m.hook_add(UC_HOOK_CODE,boundary,begin=pc,end=pc)
    results=[]
    for index,r in enumerate(rows):
        m.mem_write(bullet,bytes(0x3000));put(0x4db67c,player)
        put(player+0x5e0,r[25]);put(player+0x5e4,r[26]);put(player+0x5e8,0)
        for off,value in ((0xbc0,r[14]),(0xbc4,r[15]),(0xbc8,r[16]),(0xbd8,r[20]),(0xbdc,r[21])):put(bullet+off,value)
        put(bullet+0xc20,0);put(bullet+0xc04,0)
        t=bullet+0xc28;put(t,r[21]);put(t+4,r[20]);put(t+0x20,0x40000);put(t+0x24,0)
        put(0x4d8f58,0x3f800000);put(stack,base)
        m.reg_write(UC_X86_REG_ECX,bullet);m.reg_write(UC_X86_REG_ESP,stack)
        m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        boundaries.clear();m.emu_start(0x418140,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
        result=dict(index=index,controlFrame=r[2],slot=r[3],age=r[4],activeTransforms=r[8],
                    angleBits=r[21],speedBits=r[20],capturedVelocityBits=list(r[17:20]),
                    freshRetailVelocityBits=[get(bullet+off) for off in (0xbcc,0xbd0,0xbd4)],
                    freshRetailAngleBits=get(bullet+0xbdc),freshRetailSpeedBits=get(bullet+0xbd8))
        result['storedVelocityMatchesFreshHeading']=result['capturedVelocityBits']==result['freshRetailVelocityBits']
        results.append(result)
    q=dict(cases=len(results),storedVelocityMatchesFreshHeading=sum(r['storedVelocityMatchesFreshHeading'] for r in results),
           rows=results,captureSha256=SHA(raw),instructionBytesPatched=0,
           declaredCookieAndSoundBoundaries=True,originalTrajectoryAccepted=False,
           differentStoredVelocityDoesNotAloneProveBug=True,gameLogicChanged=False,completeGame=False,
           toolSha256=SHA(Path(__file__).read_bytes()))
    a.output.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k!='rows'}))


if __name__=='__main__':
    main()
