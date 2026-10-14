"""Bound original TH14 deferred screen-copy queue semantics without a game process.

Synthetic mapped owners/texture tables are declared. No host/game function is
patched or simulated; every external/cookie/flush boundary stops before call.
"""
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT/'tools/th14-loading-lifecycle-evidence-check.py'
OUTPUT = ROOT/'docs/porting/th14-staged-loader-capture-queue-verified-oct14.json'
MANAGER, CONTROLLER, RESOURCE, TEXTURES, STACK, RETURN = 0x2000000, 0x600000, 0x620000, 0x630000, 0x7ff000, 0x710000
SLOTS = [0x20, 0x48, 0x70, 0x98]
SHA = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('capture_image', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    image = helper.Image()
    imports = image.imports()
    assert imports[0x4b12bc]['function'] == 'D3DXLoadSurfaceFromSurface'
    md = Cs(CS_ARCH_X86, CS_MODE_32)

    def new_machine(indices):
        machine = image.machine()
        machine.mem_map(MANAGER, 0x1000000)
        helper.word(machine, 0x4f56cc, MANAGER)
        helper.word(machine, 0x4db558, CONTROLLER)
        for offset, index in zip(SLOTS, indices):
            machine.mem_write(MANAGER+offset, struct.pack('<10I', index & 0xffffffff, *range(101,110)))
        for slot in range(26):
            helper.word(machine, MANAGER+0xbc7b0c+slot*4, RESOURCE)
        helper.word(machine, RESOURCE+0x124, TEXTURES)
        machine.mem_write(0x4db510, struct.pack('<HHI', 49408, 0, 66446))
        helper.word(machine, 0x4d9684, 0)
        helper.word(machine, 0x4d9658, 0)
        writes = []

        def observe_write(uc, access, address, size, value, user):
            if address in {MANAGER+x for x in SLOTS}:
                writes.append(dict(instruction=hex(uc.reg_read(UC_X86_REG_EIP)),
                                   offset=hex(address-MANAGER), bytes=size,
                                   before=struct.unpack('<i',uc.mem_read(address,4))[0],
                                   value=value & 0xffffffff))
        machine.hook_add(UC_HOOK_MEM_WRITE, observe_write)
        return machine, writes

    def run(machine, entry, stop, owner=MANAGER, arguments=(), registers=None):
        machine.mem_write(STACK, struct.pack('<'+'I'*(len(arguments)+1),RETURN,*arguments))
        machine.reg_write(UC_X86_REG_ESP, STACK)
        machine.reg_write(UC_X86_REG_ECX, owner)
        for register, value in (registers or {}).items():
            machine.reg_write(register, value)
        called = []

        def bounded(uc, address, size, user):
            if address == stop:
                uc.emu_stop()
                return
            instruction = next(md.disasm(bytes(uc.mem_read(address,size)),address,count=1))
            if instruction.mnemonic == 'call':
                called.append(hex(address))
                uc.emu_stop()
        hook = machine.hook_add(UC_HOOK_CODE,bounded)
        machine.emu_start(entry, RETURN, count=2000)
        machine.hook_del(hook)
        assert machine.reg_read(UC_X86_REG_EIP)==stop, (hex(entry),hex(machine.reg_read(UC_X86_REG_EIP)),called)
        assert called == [], called
        assert list(struct.unpack('<HHI',machine.mem_read(0x4db510,8))) == [49408,0,66446]
        return dict(entry=hex(entry),stop=hex(stop),callInstructionsExecuted=0,
                    gameplayRngUnchanged=[49408,0,66446],instructionBudget=2000)

    def indices(machine):
        return [struct.unpack('<i',machine.mem_read(MANAGER+x,4))[0] for x in SLOTS]

    machine,writes = new_machine([7,8,9,10])
    constructor = run(machine,0x47a923,0x47a977,registers={UC_X86_REG_EDI:MANAGER})
    assert indices(machine)==[-1]*4
    assert [r['instruction'] for r in writes] == ['0x47a958','0x47a95f','0x47a966','0x47a96d']
    constructor.update(declaredPrefix='After actual constructor memset; excludes allocation, full constructor and callback registration.',writes=writes)

    enqueues = []
    arrangements = [[-1]*4,[0,-1,2,-1],[0,1,-2,-1],[0,1,2,-1],[0,1,2,3],[-2147483648,1,2,3]]
    for before in arrangements:
        for resource_slot in (0,1,25):
            machine,writes = new_machine(before)
            arguments=[resource_slot,2,32,16,384,448,3,5,128,128]
            row=run(machine,0x44bdd0,RETURN,arguments=arguments)
            free=next((n for n,v in enumerate(before) if v<0),None)
            expected=before.copy()
            if free is not None:
                expected[free]=resource_slot
                assert list(struct.unpack('<10I',machine.mem_read(MANAGER+SLOTS[free],40)))==arguments
                assert len(writes)==1 and writes[0]['instruction']=='0x44bdf5'
            else:
                assert writes==[]
            assert indices(machine)==expected
            assert machine.reg_read(UC_X86_REG_EAX)==0
            row.update(before=before,arguments=arguments,firstFreeSlot=free,after=expected,writes=writes,
                       fullQueueReturnsZeroWithoutWrite=free is None)
            enqueues.append(row)

    retirements=[]
    for before in ([-1]*4,[0,-1,-1,-1],[0,1,2,25],[-1,1,2,25],[-2,0,1,25]):
        machine,writes = new_machine(before)
        # Each pending slot targets texture index 0 whose declared COM handle is null.
        for offset in SLOTS:
            helper.word(machine,MANAGER+offset+4,0)
        row=run(machine,0x4690d0,0x4691ea)
        expected=[v if v<0 else -1 for v in before]
        assert indices(machine)==expected
        assert len(writes)==sum(v>=0 for v in before)
        assert all(r['instruction']=='0x4691d1' and r['value']==0xffffffff for r in writes)
        row.update(declaredTextureHandle=0,before=before,after=expected,writes=writes,
                   cookieCallNotExecuted=True,gpuCallsNotExecuted=True)
        retirements.append(row)

    # GetSurfaceLevel's nonzero HRESULT branch is separately initialized after
    # the COM call. It proves error retirement, not a simulated service return.
    failure_branches=[]
    for error in (1,0x80004005):
        machine,writes=new_machine([0,-1,-1,-1])
        row=run(machine,0x469145,0x4691d8,registers={UC_X86_REG_EAX:error,UC_X86_REG_ESI:MANAGER+0x28})
        assert indices(machine)[0]==-1 and len(writes)==1
        row.update(declaredHRESULT=hex(error),writes=writes,
                   precedingCOMCallNotExecutedOrSimulated=True)
        failure_branches.append(row)

    # The actual table lookup chooses the given resource/texture. Stop before
    # flush and before GetSurfaceLevel; no GPU result is invented.
    machine,writes=new_machine([25,-1,-1,-1])
    helper.word(machine,MANAGER+0x24,2)
    helper.word(machine,TEXTURES+2*24,0x640000)
    helper.word(machine,0x640000,0x650000)
    target_prefix=run(machine,0x4690d0,0x46911b)
    assert machine.reg_read(UC_X86_REG_ECX)==MANAGER
    target_prefix.update(resourceSlot=25,textureSlot=2,textureHandle='0x640000',flushCallNotExecuted=True)
    lookup_prefix=run(machine,0x469120,0x469142,registers={UC_X86_REG_EDI:MANAGER,UC_X86_REG_ESI:MANAGER+0x28,UC_X86_REG_EBP:0x7fe000})
    sp=machine.reg_read(UC_X86_REG_ESP)
    assert struct.unpack('<3I',machine.mem_read(sp,12))==(0x640000,0,0x7fdfd8)
    lookup_prefix.update(declaredPostFlushEntry=True,COMArguments=['0x640000',0,'0x7fdfd8'],getSurfaceLevelCallNotExecuted=True)

    # Execute a real null-target consumer between two genuine wait prefixes.
    # No Sleep executes; the consumer itself produces the negative field.
    machine,writes=new_machine([0,-1,-1,-1])
    helper.word(machine,MANAGER+0x24,0)
    before_wait=run(machine,0x435ab0,0x435af2,registers={UC_X86_REG_EBX:CONTROLLER})
    consume=run(machine,0x4690d0,0x4691ea)
    after_wait=run(machine,0x435af4,0x435b0f,registers={UC_X86_REG_EBX:CONTROLLER})
    assert struct.unpack('<I',machine.mem_read(machine.reg_read(UC_X86_REG_ESP),4))[0]==60
    wait_chain=dict(before=before_wait,actualConsumer=consume,after=after_wait,writes=writes,
                    sleepCallsExecuted=0,threadTimeGenerated=False)
    machine,_=new_machine([-1,0,1,25])
    first_only=run(machine,0x435ab0,0x435b0f,registers={UC_X86_REG_EBX:CONTROLLER})
    first_only.update(declaredSlots=[-1,0,1,25],otherSlotsRemainPending=True,
                      allSlotsEmptyIsNotTheNativePredicate=True)

    addresses=[0x47a958,0x47a95f,0x47a966,0x47a96d,0x44bdd5,0x44bdd8,0x44bddb,
               0x44bdde,0x44bde1,0x44bdef,0x44bdf5,0x44be91,0x44be94,0x44be96,
               0x4690e3,0x4690e9,0x4690ee,0x4690f1,0x4690ff,0x469109,0x469142,
               0x469145,0x46919d,0x4691c5,0x4691ce,0x4691d1,0x4691d8,0x46ab87,
               0x44a080,0x44b220,0x435acf,0x435af9,
               0x46a45d,0x46a468,0x46a487,0x46a493,0x46a8d1,0x46aae7]
    instructions=[]
    for address in addresses:
        i=next(md.disasm(image.bytes(address,15),address,count=1))
        instructions.append(dict(address=hex(address),bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str))
    engine_path=ROOT/'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'
    engine=json.loads(engine_path.read_text())
    assert len(engine['sourceHashes'])==265
    for name,digest in engine['sourceHashes'].items():
        assert SHA(ROOT/'runtimes/th12/th12_web'/name)==digest,name
    result=dict(diagnosticOnly=True,captureQueueEvidencePassed=True,completeGame=False,
                nativeEquivalent=False,productionChanged=False,actualRetailProcessesStarted=0,
                constructorPrefix=constructor,enqueues=enqueues,nullTargetRetirements=retirements,
                independentlyDeclaredFailureBranches=failure_branches,textureLookupPrefixes=[target_prefix,lookup_prefix],
                realConsumerWaitChain=wait_chain,firstSlotOnlyWait=first_only,originalInstructions=instructions,
                copyImport=dict(iat='0x4b12bc',**imports[0x4b12bc]),
                guardMeaningProven=True,
                guardMeaning='ANM manager+20 is the signed ANM resource-slot index of the first of four deferred screen-to-texture copy requests, each40 bytes; negative means the request slot is free. It is not a pending-job count or general ANM lifetime/GPU resource fence. The loader tests only the first slot.',
                recordFields=['resourceSlot','textureSlot','targetX','targetY','targetWidth','targetHeight','sourceX','sourceY','sourceWidth','sourceHeight'],
                consumer='4690d0 uses the original resource table at manager+bc7b0c, 24-byte texture table at resource+124, GetSurfaceLevel(0), D3DXLoadSurfaceFromSurface with source Supervisor+1b4/4d9114, texture AddDirtyRect and surface Release. It retires the request at4691d1 even when texture is absent or GetSurfaceLevel fails.',
                consumerDispatch='Render-loop draw queue4013b0 at46a45d and flush475eb0 at46a468 precede device-vtable+a8 call46a487 and pacing46a4c0 at46a493. Both pacing routes call46ab70 (46a8d1/46aae7), whose first call46ab87 is4690d0. Queue consumption is after the draw queue, not the CPU resource loader or callback update queue.',
                currentHostCapture=dict(path='runtimes/th12/th12_web/cpp/sdl/Application.cpp',sha256=SHA(ROOT/'runtimes/th12/th12_web/cpp/sdl/Application.cpp'),
                                        behavior='Current pause capture_requested handling calls backend.resample after session.update and before the subsequent draw method. It clears its bool after the resample returns; no shared four-slot deferred capture index is published to core.'),
                callInstructionsExecuted=0,hostOrGameCallShims=0,sleepCallsExecuted=0,nativeThreadTimeGenerated=False,
                sourceFilesVerified=265,sourceHashes=engine['sourceHashes'],executableSha256=hashlib.sha256(image.data).hexdigest(),
                verifierSha256=SHA(Path(__file__)),helperSha256=SHA(HELPER),engineManifestSha256=SHA(engine_path),
                scope='Unchanged original constructor initialization block, complete queue enqueue function, complete four-slot null-target consumer body stopped before cookie call, independent error branch, and actual texture-table/wait prefixes. Declared synthetic owners, indices and null handles; no actual GPU copy, successful COM/D3DX operation, full constructor/scene, native process or scheduler timing. The resource/texture/rectangle semantics and request retirement are proven; hardware completion and whole-game equivalence are not.')
    OUTPUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(captureQueueEvidencePassed=True,enqueues=len(enqueues),nullTargetConsumers=len(retirements),
                          failureBranches=len(failure_branches),sourceFilesVerified=265,hostCalls=0,guardMeaningProven=True)))


if __name__=='__main__':
    main()
