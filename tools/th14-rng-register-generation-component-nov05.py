"""Check values retained by original RNG instructions across a later seed write.

Original x86 instructions execute in an isolated emulator with declared
synthetic register/memory inputs. This proves a decoding contract, not an
original process interleaving, ordinary scheduling or complete gameplay.
"""
from pathlib import Path
import argparse, hashlib, importlib, json, struct, sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESI, UC_X86_REG_EIP

R=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def verify():
    sys.path.insert(0,str(R/'tools'))
    image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,address,size,start,length in image.sections:
        low=address&~4095;m.mem_map(low,((address+size+4095)&~4095)-low)
        m.mem_write(address,image.data[start:start+length])
    seed_address=0x4db508
    cases=[
        ('mix16',0x4032c5,0x4032c8,'663306','xorAX'),
        ('mix32',0x403336,0x403339,'663306','xorAX'),
        ('mix32Alternate',0x4033c6,0x4033c9,'663306','xorAX'),
        ('returnReload16',0x4032fd,0x403300,'668b06','AX'),
        ('store16',0x4032e0,0x4032e3,'66890e','CX'),
        ('store32',0x403373,0x403376,'66890e','CX'),
        ('store32Alternate',0x403403,0x403406,'66890e','CX'),
    ]
    assert image.read(0x456123,6).hex()=='66a308b54d00'
    events=[];active=False
    def memory(machine,access,address,size,value,user):
        if active and address<=seed_address<address+size:
            events.append(dict(access=access,address=address,size=size,value=value,
                               before=bytes(m.mem_read(seed_address,2)).hex()))
    m.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,memory)
    rows=[];global_snapshot_wrong=0
    for name,pc,after,opcode,kind in cases:
        assert image.read(pc,after-pc).hex()==opcode
        for original in [0,1,0x1234,0x8000,0x9630,0xffff]:
            for worker in [0,1,0x5678,0xaaaa,0xffff]:
                m.mem_write(seed_address,struct.pack('<H',original))
                m.reg_write(UC_X86_REG_ESI,seed_address)
                m.reg_write(UC_X86_REG_EAX,0x9630 if kind=='xorAX' else 0xdeadbeef)
                m.reg_write(UC_X86_REG_ECX,0xa5a50000|original)
                events.clear();active=True;m.emu_start(pc,after,count=1);active=False
                assert m.reg_read(UC_X86_REG_EIP)==after and len(events)==1
                own=m.context_save();ax=m.reg_read(UC_X86_REG_EAX)&0xffff;cx=m.reg_read(UC_X86_REG_ECX)&0xffff
                recovered=(ax^0x9630)if kind=='xorAX'else ax if kind=='AX'else cx
                assert recovered==original
                trapped_event=dict(events[0])
                # Execute the actual worker script-seed store after the main
                # instruction, then restore its stopped register context only.
                # The global seed deliberately remains the worker generation.
                m.reg_write(UC_X86_REG_EAX,worker)
                m.emu_start(0x456123,0x456129,count=1)
                assert m.reg_read(UC_X86_REG_EIP)==0x456129
                m.context_restore(own)
                observed=struct.unpack('<H',m.mem_read(seed_address,2))[0]
                assert observed==worker
                ax=m.reg_read(UC_X86_REG_EAX)&0xffff;cx=m.reg_read(UC_X86_REG_ECX)&0xffff
                recovered=(ax^0x9630)if kind=='xorAX'else ax if kind=='AX'else cx
                assert recovered==original
                if kind=='CX':assert trapped_event['value']&0xffff==original
                else:assert int.from_bytes(bytes.fromhex(trapped_event['before']),'little')==original
                global_snapshot_wrong+=observed!=original
                rows.append(dict(kind=name,instructionPc=pc,trapResumePc=after,originalSeed=original,
                                 laterWorkerSeed=worker,recoveredFromStoppedRegisters=recovered,
                                 globalSeedAtLaterObservation=observed,globalSnapshotWrong=observed!=original))
    assert len(rows)==210 and global_snapshot_wrong>0
    return dict(schema='th14/rng-register-generation-component/1',passed=True,cases=len(rows),
        mainRegisterRecoveriesEqual=len(rows),laterGlobalSnapshotWrong=global_snapshot_wrong,
        originalInstructionBytesUnmodified=True,realOriginalProcess=False,syntheticInputs=True,
        explicitControlledEmulatorInterleaving=True,exactOriginalScheduleRecovered=False,
        instructionCases=[dict(kind=n,pc=p,after=a,bytes=b,recovery=k)for n,p,a,b,k in cases],
        originalExecutableSha256=SHA(image.data),rows=rows,physicalAudioDevicesOpened=0,
        wholeRngFunctionAccepted=False,ordinaryIndependentTimingAccepted=False,completeGame=False,
        toolSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
    result=verify();(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ['passed','cases','mainRegisterRecoveriesEqual','laterGlobalSnapshotWrong','wholeRngFunctionAccepted','ordinaryIndependentTimingAccepted']}))
