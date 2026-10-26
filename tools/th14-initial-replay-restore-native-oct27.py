"""Execute the ordinary replay worker branch and its real stage restoration.

Declared virtual memory inputs only. No original process, GUI, audio, native
game state injection into the port, or full replay acceptance is involved.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import itertools
import json
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
    out.mkdir(parents=True);sys.path.insert(0,str(ROOT/'tools'))
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_WRITE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EBX,UC_X86_REG_EIP
    image=importlib.import_module('th-anm-handlers').handlers(14)[0]
    decoded=args.decoded.resolve(strict=True).read_bytes();count=struct.unpack_from('<I',decoded,0x78)[0]
    assert 1<=count<=7;headers=[];offset=0x94
    for _ in range(count):
        header=decoded[offset:offset+0xdc];assert len(header)==0xdc
        stage,seed=struct.unpack_from('<HH',header);frames,size=struct.unpack_from('<II',header,4)
        assert 1<=stage<=7 and size>=frames*6;headers.append((stage,seed,header));offset+=0xdc+size
    assert offset==len(decoded)
    machine=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,address,size,file_offset,length in image.sections:
        first=address&~4095;machine.mem_map(first,((address+size+4095)&~4095)-first)
        machine.mem_write(address,image.data[file_offset:file_offset+length])
    base=0x70000000;machine.mem_map(base,0x10000);manager=base+0x100;sheet=base+0x1000;stack=base+0xf000
    def put(address,value):machine.mem_write(address,struct.pack('<I',value&0xffffffff))
    def words(address,count):return list(struct.unpack('<'+'I'*count,machine.mem_read(address,count*4)))
    writes=[]
    def observe(machine,access,address,size,value,user):
        if 0x4db508<=address<0x4db518 or 0x4f5828<=address<0x4f5898:
            writes.append(dict(pc=machine.reg_read(UC_X86_REG_EIP),address=address,bytes=size,value=value&((1<<(size*8))-1)))
    machine.hook_add(UC_HOOK_MEM_WRITE,observe)
    cases=[]
    for (stage,seed,header),old_script,old_game,calls,flags in itertools.product(headers,[0,1,0x5d12,0xffff],[0,0xffff],[0,0xfffffffe],[2,0x12,0x22]):
        machine.mem_write(manager,bytes(0x400));put(manager+0x10,1);put(0x4db688,manager);put(0x4f58a4,stage);put(0x4f58b8,flags)
        machine.mem_write(sheet,header);record=manager+(stage*5+0x19)*8
        put(record,0x71234560);put(record+8,0x72345670);put(record+0x10,sheet)
        machine.mem_write(0x4db508,struct.pack('<HHIHHI',old_script,0xa5a5,calls,old_game,0x5a5a,calls))
        machine.mem_write(0x4f5828,bytes.fromhex('efbeadde')*28)
        writes.clear();machine.reg_write(UC_X86_REG_ESP,stack);machine.reg_write(UC_X86_REG_EBX,base+0x3000)
        # Stop at the real return site, before unrelated HUD/camera services.
        machine.emu_start(0x435ed0,0x435f37,count=1000);assert machine.reg_read(UC_X86_REG_EIP)==0x435f37
        actual=words(0x4db508,4);expected=[seed|(0xa5a5<<16),calls,seed|(0x5a5a<<16),0]
        assert actual==expected and bytes(machine.mem_read(0x4f5828,0x70))==header[0x14:0x84]
        assert words(record+4,1)==[0x71234560]and words(record+0xc,1)==[0x72345670]and words(record+0x14,1)==[0xffffffff]
        assert [row['address']for row in writes[:3]]==[0x4db510,0x4db508,0x4db514]
        assert len(writes)==31 and [row['address']for row in writes[3:]]==list(range(0x4f5828,0x4f5898,4))
        cases.append(dict(stage=stage,seed=seed,flags=flags,initialScriptSeed=old_script,initialGameSeed=old_game,initialCalls=calls,
            rngWords=actual,globalsSha256=SHA(header[0x14:0x84]),writeSequence=[row.copy()for row in writes]))
    report=dict(schema='th14/ordinary-initial-replay-restore-native/1',completed=True,cases=cases,caseCount=len(cases),
        decodedSha256=SHA(decoded),decodedFile=str(args.decoded),executableSha256=SHA(image.data),
        branchAddress=0x435ed0,restoreAddress=0x456050,stopAddress=0x435f37,
        originalInstructionSlices=[dict(address=address,bytes=len(raw),sha256=SHA(raw))for address,raw in
            [(0x435ed0,image.read(0x435ed0,0x80)),(0x456050,image.read(0x456050,0xeb))]],
        bothSeedsRestored=True,scriptCallCountPreserved=True,gameCallCountReset=True,all28GlobalsCopied=True,
        originalInstructionsModified=False,originalProcessLaunched=False,ordinaryMenuInitializationAccepted=False,
        declaredVirtualAbiInputsOnly=True,toolSha256=SHA(Path(__file__).read_bytes()),completeGame=False,nativeEquivalent=False)
    (out/'native.json').write_text(json.dumps(report,indent=2)+'\n');(out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in report.items()if k not in ['cases','originalInstructionSlices']}),flush=True)


if __name__=='__main__':main()
