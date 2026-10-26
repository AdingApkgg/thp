"""Run original camera producer and ordered Scene-copy instructions as two contexts.

Enumerates finite instruction-boundary schedules; it cannot infer an unrecorded
real thread schedule, fix campaign gates or provide native values to the engine.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import itertools
import json
import struct
import sys

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,required=True)
    parser.add_argument('--summary',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();home=args.home.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')
    if not args.check:home.mkdir(exist_ok=False)
    sys.path.insert(0,str(ROOT/'tools'));Image=importlib.import_module('th12-pe').Image
    bindings={}
    def read(path):
        raw=path.read_bytes()
        if path.is_relative_to(ROOT):bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw))
        return raw
    image=Image('H:/Games/th/14/th14.exe');dll=Image('C:/Windows/SysWOW64/d3dx9_43.dll')
    assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert SHA(dll.data)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for source in [image,dll]:
        for _,address,size,raw,count in source.sections:
            page=address&~4095;m.mem_map(page,((address+size+4095)&~4095)-page)
            m.mem_write(address,source.data[raw:raw+count])
    BASE,STACK,RETURN,CAMERA,DEVICE,TABLE,SCENE,WORKER_STACK=0x70000000,0x700ff000,0x700fe000,0x4d9514,0x70002000,0x70003000,0x70005000,0x700ed000
    m.mem_map(BASE,0x100000);m.mem_map(0,4096)
    def put(address,value):m.mem_write(address,struct.pack('<I',value&0xffffffff))
    def word(address):return struct.unpack('<I',m.mem_read(address,4))[0]
    matrices=[]
    def matrix_sink(machine,pc,size,data):
        sp=machine.reg_read(UC_X86_REG_ESP)
        matrices.append((word(sp+8),bytes(m.mem_read(word(sp+12),64))))
        machine.reg_write(UC_X86_REG_EAX,0)
    m.mem_write(RETURN+0x100,b'\xc2\x0c\x00')
    m.hook_add(UC_HOOK_CODE,matrix_sink,begin=RETURN+0x100,end=RETURN+0x100)
    put(DEVICE,TABLE);put(TABLE+0xb0,RETURN+0x100);put(0x4d8f68,DEVICE);put(0x4f56cc,0)
    def prepare(stack,owner,args=()):
        m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),RETURN,*args))
        for reg in [UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]:m.reg_write(reg,0)
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_EFLAGS,2)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    # Same pinned real-DLL dispatch bootstrap as the existing vector oracle.
    m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));prepare(STACK,0,[0x101ca068])
    m.emu_start(0x101bc521,RETURN,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
    pe=struct.unpack_from('<I',dll.data,0x3c)[0];directory=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0]
    functions,names,ordinals=[dll.image_base+dll.u32(directory+o)for o in (28,32,36)];exports={}
    for index in range(dll.u32(directory+24)):
        name=dll.read(dll.image_base+dll.u32(names+index*4),128).split(b'\0')[0].decode()
        ordinal=struct.unpack('<H',dll.read(ordinals+index*2,2))[0];exports[name]=dll.image_base+dll.u32(functions+ordinal*4)
    for slot,name in [(0x4b12ec,'D3DXMatrixLookAtLH'),(0x4b12e8,'D3DXMatrixPerspectiveFovLH'),(0x4b12b8,'D3DXVec3Normalize')]:put(slot,exports[name])

    writes=[];copy_reads=[];target_writes=None;role=None
    def watch_write(machine,access,address,size,value,user):
        if role!='producer' or not(CAMERA+0x30<=address<CAMERA+0x3c):return
        assert address+size<=CAMERA+0x3c
        writes.append(dict(pc=machine.reg_read(UC_X86_REG_EIP),offset=address-CAMERA-0x30,size=size,
            raw=(value&((1<<(size*8))-1)).to_bytes(size,'little').hex()))
    def watch_read(machine,access,address,size,value,user):
        if role!='worker':return
        assert machine.reg_read(UC_X86_REG_EIP)==0x40d445 and size==4
        assert address==CAMERA+4*len(copy_reads)
        copy_reads.append(dict(offset=address-CAMERA,raw=bytes(machine.mem_read(address,4)).hex(),producerStoresCompleted=len(writes)))
    def pause_after_stores(machine,pc,size,user):
        if role=='producer' and target_writes is not None and len(writes)>=target_writes:machine.emu_stop()
    m.hook_add(UC_HOOK_MEM_WRITE,watch_write,begin=CAMERA+0x30,end=CAMERA+0x3b)
    m.hook_add(UC_HOOK_MEM_READ,watch_read,begin=CAMERA,end=CAMERA+0x12b)
    m.hook_add(UC_HOOK_CODE,pause_after_stores)
    expected_stores=[(0x446590,0,8),(0x44659d,8,4),(0x101bcaa0,0,4),(0x101bcaa4,4,4),(0x101bcaa9,8,4)]
    native=ROOT/'artifacts/th14/retail-sakuyab-easy-exact-camera-hardware-oct26'
    report=json.loads(read(native/'report.json'));raw=read(native/'world-camera.raw')
    assert report['callbacks']==106903 and SHA(raw)==report['worldCameraSha256']and len(raw)==106903*0x124
    assert report['hardwareBreakpointsOnly']and report['instructionBytesPatched']==report['rngOrCounterWrites']==0
    events=[json.loads(line)for line in read(native/'scene-camera-copy-events.jsonl').splitlines()]
    afters=[row for row in events if row['event']=='scene-camera-copy-after'];assert [row['stage']for row in afters]==[2,3,4,5,6]
    orders=list(itertools.combinations_with_replacement(range(6),3));assert len(orders)==56
    cases=[]
    for after in afters:
        before=next(row for row in events if row['stage']==after['stage']and row['event']=='scene-camera-copy-before')
        callback=after['precedingPlayerCallbacks'];assert callback==before['precedingPlayerCallbacks']
        assert before['pc']==0x40d435 and after['pc']==0x40d447 and before['threadId']==after['threadId']
        camera=raw[(callback-1)*0x124:callback*0x124]+bytes(8);assert len(camera)==300
        # First run obtains the actual producer stores, without worker reads.
        role=None;m.mem_write(CAMERA,camera);prepare(STACK,0,[CAMERA]);writes.clear();matrices.clear()
        role='producer';target_writes=None;m.emu_start(0x446400,RETURN,count=1000000)
        assert m.reg_read(UC_X86_REG_EIP)==RETURN
        baseline_writes=writes.copy();final=bytes(m.mem_read(CAMERA+0x30,12))
        assert [(w['pc'],w['offset'],w['size'])for w in writes]==expected_stores
        states=[camera[0x30:0x3c]]
        for w in writes:
            state=bytearray(states[-1]);state[w['offset']:w['offset']+w['size']]=bytes.fromhex(w['raw']);states.append(bytes(state))
        assert states[-1]==final
        outputs=[];matches=[]
        for order in orders:
            role=None;m.mem_write(CAMERA,camera);m.mem_write(SCENE+0x4274,bytes(300))
            prepare(STACK,0,[CAMERA]);m.reg_write(UC_X86_REG_EIP,0x446400);producer=m.context_save()
            prepare(WORKER_STACK,0);m.reg_write(UC_X86_REG_EBX,SCENE)
            m.emu_start(0x40d435,0x40d445,count=10)
            assert m.reg_read(UC_X86_REG_EIP)==0x40d445 and m.reg_read(UC_X86_REG_ECX)==75
            worker=m.context_save();writes.clear();copy_reads.clear();matrices.clear()
            for lane,rank in enumerate(order):
                if rank>len(writes):
                    role='producer';target_writes=rank;m.context_restore(producer)
                    m.emu_start(m.reg_read(UC_X86_REG_EIP),RETURN,count=1000000);producer=m.context_save()
                    assert len(writes)==rank
                role='worker';m.context_restore(worker)
                while len(copy_reads)<13+lane:
                    m.emu_start(0x40d445,0x40d447,count=1)
                worker=m.context_save()
            role='worker';m.context_restore(worker);m.emu_start(0x40d445,0x40d447,count=100)
            assert m.reg_read(UC_X86_REG_EIP)==0x40d447 and len(copy_reads)==75
            assert m.reg_read(UC_X86_REG_ESI)==CAMERA+300 and m.reg_read(UC_X86_REG_EDI)==SCENE+0x4274+300
            assert m.reg_read(UC_X86_REG_ECX)==0
            copied=bytes(m.mem_read(SCENE+0x4274,300));assert copied==b''.join(bytes.fromhex(row['raw'])for row in copy_reads)
            right=copied[0x30:0x3c]
            independent=b''.join(states[rank][lane*4:(lane+1)*4]for lane,rank in enumerate(order))
            assert right==independent
            assert [row['producerStoresCompleted']for row in copy_reads[12:15]]==list(order)
            role='producer';target_writes=None;m.context_restore(producer)
            m.emu_start(m.reg_read(UC_X86_REG_EIP),RETURN,count=1000000)
            assert m.reg_read(UC_X86_REG_EIP)==RETURN and writes==baseline_writes
            assert bytes(m.mem_read(CAMERA+0x30,12))==final
            if right.hex()==after['copiedRightHex']:matches.append(list(order))
            outputs.append(dict(order=list(order),copiedRight=right.hex(),copiedBufferSha256=SHA(copied)))
        assert matches
        cases.append(dict(stage=after['stage'],callback=callback,sourceCameraSha256=SHA(camera),producerStores=baseline_writes,
            states=[state.hex()for state in states],actualRetainedCopyRight=after['copiedRightHex'],matchingSchedules=matches,outputs=outputs))
    mixed=next(row for row in cases if row['stage']==4)
    assert mixed['callback']==48006 and mixed['matchingSchedules']==[[3,3,3],[3,3,4]]
    assert mixed['actualRetainedCopyRight']==mixed['states'][3]
    assert mixed['actualRetainedCopyRight']not in[mixed['states'][0],mixed['states'][2],mixed['states'][5]]
    detail=dict(schema='th14/camera-instruction-interleaving/1',cases=cases)
    detail_raw=(json.dumps(detail,indent=2)+'\n').encode()
    if args.check:assert(home/'cases.json').read_bytes()==detail_raw
    else:(home/'cases.json').write_bytes(detail_raw)
    bindings[(home/'cases.json').relative_to(ROOT).as_posix()]=dict(bytes=len(detail_raw),sha256=SHA(detail_raw))
    summary=dict(verifiedFiniteOriginalInstructionSchedules=True,caseCount=len(cases),orderedSchedulesPerCase=56,
        actualProducerAndSceneCopyExecutions=280,actualCopiedDwords=280*75,sceneCopyBytesPerExecution=300,
        allInstructionCopiesEqualIndependentStoreModel=True,allProducerFinalRightWordsUnchangedBySchedules=True,
        instructionStores=[dict(pc=hex(pc),offset=offset,bytes=size)for pc,offset,size in expected_stores],
        stage4RetainedMixedCopyReproduced=True,stage4Callback=48006,stage4MatchingSchedules=mixed['matchingSchedules'],
        stage4MixedCopyDiffersFromOldRawAndFinalControls=True,matchedRetainedStages=[row['stage']for row in cases],
        actualRealThreadScheduleIdentified=False,recordedInputsOnlyAtComponentBoundary=True,nativeValuesProvidedToGameEngine=False,
        originalProcessOrHardwareDeviceLaunched=False,productionCodeChanged=False,campaignCameraFailureClosed=False,
        originalExecutableSha256=SHA(image.data),d3dxSha256=SHA(dll.data),toolSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,
        completeGame=False,nativeEquivalent=False,browserAcceptance=False,
        scope='Original446400 plus pinned real x86 D3DX code, and original40d435..40d447 ordered75-dword Scene copy. Separate complete CPU contexts share camera memory under56 explicitly controlled instruction-boundary schedules per recorded input. Device SetTransform is a declared sink. This finite store model treats the raw8-byte instruction as one transaction; subinstruction hardware tearing is not asserted. Reproduces retained mixed right values but cannot identify unrecorded real copy timing or accept a campaign, original ordinary UI, pixels, audio or browser.')
    output=args.summary.resolve()if args.summary else home/'verified.json'
    assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    if args.check:assert json.loads(output.read_bytes())==summary
    else:output.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({key:summary[key]for key in ['caseCount','actualProducerAndSceneCopyExecutions','actualCopiedDwords','stage4RetainedMixedCopyReproduced','stage4MatchingSchedules','actualRealThreadScheduleIdentified','campaignCameraFailureClosed']}))


if __name__=='__main__':main()
