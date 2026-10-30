"""Execute unchanged retail455c20 file-reader/parser with declared file services.

Real file open/read/close, CRT allocation/copy/free and path formatting are
controlled. Both crypto passes, LZSS and all native stage/index stores execute
original instructions. This is not native GUI, scheduling or playback proof.
"""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
    sys.path[:0]=[str(ROOT/'tools/tmp/th14-analysis-python'),str(ROOT/'tools')]
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX,UC_X86_REG_ECX
    image=importlib.import_module('th-anm-handlers').handlers(14)[0]
    assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    rows=[]
    cases=[]
    for index,path in enumerate(a.input):
        path=path.resolve(strict=True);raw=path.read_bytes()
        assert 0x24<=len(raw)<=512*1024 and raw[:6]==b't13r\x02\0'
        packed,unpacked=struct.unpack_from('<II',raw,0x1c)
        assert 0<packed<=len(raw)-0x24 and 0<unpacked<=6*1024**2
        cases.append((f'valid-{index}',path,raw,True))
        if index==0:
            for name,at in [('wrong-magic',0),('wrong-version',4)]:
                changed=bytearray(raw);changed[at]^=1;cases.append((name,path,bytes(changed),False))
    for label,path,data,accepted in cases:
        home=out/label;home.mkdir();m=Uc(UC_ARCH_X86,UC_MODE_32)
        for _,address,size,offset,length in image.sections:
            first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first);m.mem_write(address,image.data[offset:offset+length])
        base=0x70000000;m.mem_map(base,32*1024**2)
        manager,name,stack=base+0x1000,base+0x3000,base+31*1024**2
        heap=[base+0x10000];cursor=[0];events=[]
        def put(address,value):m.mem_write(address,struct.pack('<I',value&0xffffffff))
        def get(address):return struct.unpack('<I',m.mem_read(address,4))[0]
        def allocate(size):
            assert 0<size<=6*1024**2
            address=heap[0];heap[0]+=(size+15)&~15;assert heap[0]<stack-0x10000
            m.mem_write(address,bytes(size));return address
        def finish(result=0,cleanup=0):
            sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EAX,result)
            m.reg_write(UC_X86_REG_ESP,sp+4+cleanup);m.reg_write(UC_X86_REG_EIP,get(sp))
        def service(uc,address,size,user):
            sp=uc.reg_read(UC_X86_REG_ESP);ecx=uc.reg_read(UC_X86_REG_ECX)
            if address==0x4862cd:events.append(dict(service='directory-context',pc=address));finish();return
            if address==0x485ddf:
                m.mem_write(get(sp+4),b'th14_component.rpy\0');events.append(dict(service='format-path',pc=address));finish(18);return
            if address==0x402cc0:events.append(dict(service='exists',pc=address));finish(1);return
            if address==0x402f40:cursor[0]=0;events.append(dict(service='open',pc=address));finish();return
            if address==0x403070:
                assert ecx in (0x24,struct.unpack_from('<I',data,0x1c)[0])and cursor[0]+ecx<=len(data)
                dest=allocate(ecx);m.mem_write(dest,data[cursor[0]:cursor[0]+ecx]);events.append(dict(service='read-owned-buffer',pc=address,offset=cursor[0],bytes=ecx));cursor[0]+=ecx;finish(dest);return
            if address==0x4030d0:events.append(dict(service='close',pc=address));finish();return
            if address==0x485540:events.append(dict(service='allocate',pc=address,bytes=get(sp+4)));finish(allocate(get(sp+4)));return
            if address==0x487620:
                dest,source,count=get(sp+4),get(sp+8),get(sp+12);assert count<=6*1024**2
                m.mem_write(dest,bytes(m.mem_read(source,count)));finish(dest);return
            if address==0x4855d2:finish();return
            raise AssertionError(hex(address))
        for address in [0x4862cd,0x485ddf,0x402cc0,0x402f40,0x403070,0x4030d0,0x485540,0x487620,0x4855d2]:
            m.hook_add(UC_HOOK_CODE,service,begin=address,end=address)
        m.mem_write(name,b'th14_component.rpy\0');put(stack,base);put(stack+4,name)
        # Ordinary file path: do not use the attract archive shortcut.
        put(0x4f58b8,0);put(0x4d0cc0,0xbb40e64e);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager)
        m.emu_start(0x455c20,base,count=50000000)
        assert m.reg_read(UC_X86_REG_EIP)==base and m.reg_read(UC_X86_REG_ESP)==stack+8
        result=m.reg_read(UC_X86_REG_EAX);assert result==(0 if accepted else 0xffffffff)
        row=dict(label=label,source=path.relative_to(ROOT).as_posix(),inputBytes=len(data),inputSha256=SHA(data),accepted=accepted,
                 nativeReturn=result,declaredOrdinaryFilePath=True,serviceEvents=events)
        if accepted:
            decoded_pointer=get(manager+0x208);assert get(manager+0x1c)==decoded_pointer
            decoded=bytes(m.mem_read(decoded_pointer,struct.unpack_from('<I',data,0x20)[0]));(home/'decoded.bin').write_bytes(decoded)
            count=struct.unpack_from('<I',decoded,0x78)[0];assert 1<=count<=7
            at=0x94;stages=[]
            for _ in range(count):
                stage,seed,frames,payload=struct.unpack_from('<HHII',decoded,at);assert 1<=stage<=7
                table=manager+stage*0x28+0xc8
                observed=[get(table+n)for n in (0,8,16)]
                expected=[decoded_pointer+at+0xdc,decoded_pointer+at+0xdc+frames*6,decoded_pointer+at]
                assert observed==expected and frames*6<=payload and at+0xdc+payload<=len(decoded)
                stages.append(dict(stage=stage,seed=seed,frames=frames,payloadBytes=payload,headerOffset=at,inputOffset=at+0xdc,fpsOffset=at+0xdc+frames*6,actualNativePointerOffsets=[x-decoded_pointer for x in observed]))
                at+=0xdc+payload
            assert at==len(decoded)
            row.update(decodedBytes=len(decoded),decodedSha256=SHA(decoded),stages=stages,allNativeStagePointerOffsetsEqualDeclaredLayout=True)
        (home/'report.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
    result=dict(schema='th14/original-replay-file-parser/1',passed=True,originalEntryPc=0x455c20,
                executableSha256=SHA(image.data),toolSha256=SHA(Path(__file__).read_bytes()),cases=rows,
                originalInstructionBytesPatched=0,actualOriginalFileSystemExecuted=False,controlledFileAndCrtServices=True,
                originalDecryptDecompressAndStageIndexInstructionsExecuted=True,ordinaryGuiAccepted=False,
                nativePlaybackAccepted=False,completeGame=False,nativeEquivalent=False)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),validInputs=sum(r['accepted']for r in rows),negativeInputs=sum(not r['accepted']for r in rows))))
if __name__=='__main__':main()
