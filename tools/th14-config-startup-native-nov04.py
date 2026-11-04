"""Execute TH14's config rejection/reset/join instructions with declared I/O."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EBP,UC_X86_REG_EIP

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14') and not out.exists();out.mkdir(parents=True)
    image,*_=importlib.import_module('th-anm-handlers').handlers(14)
    assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert image.read(0x44553f,10)==bytes.fromhex('b934914d00e89721ffff')
    machine=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,offset,length in image.sections:
        start=base&~4095;machine.mem_map(start,((base+size+4095)&~4095)-start);machine.mem_write(base,image.data[offset:offset+length])
    machine.mem_map(0x70000000,0x10000);stack=0x7000e000;frame=0x70008000
    events=[]
    def u32(address):return struct.unpack('<I',machine.mem_read(address,4))[0]
    def hook(uc,address,size,user):
        if address not in [0x403100,0x48f980]:return
        sp=uc.reg_read(UC_X86_REG_ESP);return_address=u32(sp)
        if address==0x48f980:
            destination,value,length=(u32(sp+4*n) for n in [1,2,3]);assert length==92 and value==0
            uc.mem_write(destination,bytes(length));events.append('memset-92')
        else:events.append('log')
        uc.reg_write(UC_X86_REG_ESP,sp+4);uc.reg_write(UC_X86_REG_EIP,return_address)
    machine.hook_add(UC_HOOK_CODE,hook)
    default=bytearray(92);struct.pack_into('<I',default,0,0x140002)
    controller=struct.pack('<10h',0,1,2,5,-1,-1,-1,-1,-1,3)
    default[4:24]=controller;struct.pack_into('<HH',default,0x18,600,600)
    for offset,value in [(0x1d,1),(0x1e,1),(0x1f,5),(0x21,2),(0x22,100),(0x23,80),(0x25,2),(0x39,1)]:default[offset]=value
    struct.pack_into('<II',default,0x28,0x80000000,0x80000000)
    candidates=[]
    for offset in range(0x1c,0x22):
        for value in range(256):
            candidate=bytearray(default);candidate[offset]=value;candidates.append((f'option-{offset:02x}-{value}',bytes(candidate),92,False))
    for signature in [0,0x140001,0x140002,0x140003,0xffffffff]:
        for length in [0,4,91,92,93,100]:
            candidate=bytearray(default);struct.pack_into('<I',candidate,0,signature);candidates.append((f'signature-{signature:08x}-size-{length}',bytes(candidate),length,False))
    modified=bytearray(default);modified[0x22]=37;modified[0x23]=53;modified[0x50:]=bytes(range(12))
    candidates += [('valid-user-options',bytes(modified),92,False),('missing-file',bytes(default),0,True)]
    rows=[];limits=[2,3,2,6,3,3]
    for label,candidate,length,missing in candidates:
        machine.mem_write(0x4d9134,candidate);machine.mem_write(0x4d6aac,controller)
        machine.mem_write(frame-8,struct.pack('<I',length));machine.mem_write(stack,bytes(32))
        machine.reg_write(UC_X86_REG_EBP,frame);machine.reg_write(UC_X86_REG_ESP,stack)
        events.clear();machine.emu_start(0x445496 if missing else 0x4454b8,0x445549,count=256)
        assert machine.reg_read(UC_X86_REG_EIP)==0x445549
        valid=not missing and length==92 and candidate[:4]==default[:4] and all(candidate[0x1c+n]<limit for n,limit in enumerate(limits))
        actual=bytes(machine.mem_read(0x4d9134,92));expected=candidate if valid else bytes(default)
        assert actual==expected,label
        assert events==([] if valid else ['log','memset-92']),label
        actual_controller=bytes(machine.mem_read(0x4d6aac,20));assert actual_controller==(candidate[4:24] if valid else controller)
        rows.append(dict(case=label,inputHex=candidate.hex(),declaredSize=length,missing=missing,accepted=valid,outputHex=actual.hex(),events=list(events),joinedOrdinaryStartup=True))
    result=dict(schema='th14/native-config-startup/1',cases=rows,executableSha256=SHA(image.data),
        branchSha256=SHA(image.read(0x445496,0xb3)),resetSha256=SHA(image.read(0x4376e0,0x79)),
        verifierSha256=SHA(Path(__file__).read_bytes()),resetIsActualRetailInstructions=True,
        controllerInputDeclared=True,crtMemsetAndLogBoundariesStubbed=True,
        fileSystemOrOrdinaryOriginalUiExecuted=False,completeGame=False,nativeEquivalent=False)
    (out/'native.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(cases=len(rows),rejected=sum(not r['accepted']for r in rows),allJoinedStartup=True)))

if __name__=='__main__':main()
