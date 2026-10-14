"""Untouched original pooled-VM destroy preserves all160 capture record bytes."""
import hashlib,json,struct,importlib.util
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
ROOT=Path(__file__).resolve().parents[1];HELPER=ROOT/'tools/th14-loading-lifecycle-evidence-check.py'
sha=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('queue_destroy_image',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);image=helper.Image();md=Cs(CS_ARCH_X86,CS_MODE_32)
MANAGER,STACK,RETURN=0x2000000,0x7ff000,0x710000;SLOTS=[0x20,0x48,0x70,0x98];rows=[]
for indices in [[0,-1,-1,-1],[0,1,2,25],[-1,0,1,25],[-2,0,1,25]]:
    u=image.machine();u.mem_map(MANAGER,0x1000000);vm=MANAGER+0xdc
    record_bytes=b''.join(struct.pack('<10i',index,*range(101,110)) for index in indices)
    for i,offset in enumerate(SLOTS):u.mem_write(MANAGER+offset,record_bytes[i*40:i*40+40])
    # Ordinary pooled VM; no callback, geometry allocation or child list.
    helper.word(u,vm+0x544,0);helper.word(u,vm+0x5c0,0);helper.word(u,vm+0x5b4,0)
    helper.word(u,MANAGER+0xfe820c,vm+0x570);helper.word(u,MANAGER+0xfe8208,vm+0x570)
    helper.word(u,STACK,RETURN);helper.word(u,STACK+4,vm);u.reg_write(UC_X86_REG_ECX,MANAGER);u.reg_write(UC_X86_REG_ESP,STACK)
    calls=[];capture_writes=[];instructions=[]
    def bounded(guest,address,size,unused):
        if address==RETURN:guest.emu_stop();return
        ins=next(md.disasm(bytes(guest.mem_read(address,size)),address,count=1));instructions.append(hex(address))
        if ins.mnemonic=='call':calls.append(hex(address));guest.emu_stop()
    def writes(guest,access,address,size,value,unused):
        if any(MANAGER+offset<=address<MANAGER+offset+40 for offset in SLOTS):capture_writes.append(dict(address=hex(address),instruction=hex(guest.reg_read(UC_X86_REG_EIP)),bytes=size,value=value))
    u.hook_add(UC_HOOK_CODE,bounded);u.hook_add(UC_HOOK_MEM_WRITE,writes);u.emu_start(0x47eb50,RETURN,count=1000)
    assert u.reg_read(UC_X86_REG_EIP)==RETURN and not calls and not capture_writes
    after=b''.join(bytes(u.mem_read(MANAGER+offset,40)) for offset in SLOTS);assert after==record_bytes
    assert struct.unpack('<I',u.mem_read(MANAGER+0xfe820c,4))[0]==0
    assert struct.unpack('<I',u.mem_read(MANAGER+0xfe8208,4))[0]==0
    assert bytes(u.mem_read(0x47eb50,0x184))==image.bytes(0x47eb50,0x184)
    rows.append(dict(indices=indices,declaredPooledVm=hex(vm),entry='0x47eb50',stop=hex(RETURN),before160BytesHex=record_bytes.hex(),after160BytesHex=after.hex(),captureRecordWrites=capture_writes,callsExecuted=calls,executedInstructions=instructions,registryHeadsRemoved=True))
prior_path=ROOT/'docs/porting/th14-staged-loader-capture-queue-verified-oct14.json';prior=json.loads(prior_path.read_bytes());assert prior['captureQueueEvidencePassed']
assert [r['instruction'] for r in prior['constructorPrefix']['writes']]==['0x47a958','0x47a95f','0x47a966','0x47a96d']
data=image.bytes(0x47eb50,0x184)
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,actualRetailProcessesStarted=0,originalCodeUnmodified=True,fullOrdinaryPooledVmDestroyCases=rows,captureRecordsComparedBytes=4*160,originalConstructorInitializationBound=True,constructorProofSha256=sha(prior_path.read_bytes()),helperSha256=sha(HELPER.read_bytes()),executableSha256=helper.EXPECTED_EXE_SHA,originalDestroyUnit=dict(address='0x47eb50',bytes=len(data),hex=data.hex(),sha256=sha(data)),toolSha256=sha(Path(__file__).read_bytes()),scope='Complete original pooled-VM destroy47eb50 executes with declared real pool address, zero optional destructor callback/geometry/child list, and synthetic pending capture records. No callee patch, service shim, retail process, GPU or scheduler timing. All160 record bytes remain identical despite registry unlink/recycling. This proves that this ordinary VM retirement is not capture cancellation; it does not prove every special destruction/resource-clear path. New manager constructor prefix separately initializes four first-file fields to-1. Therefore portable VM clear should preserve requests until explicit postDraw/headless target retirement, not clear them per stage.')
path=ROOT/'docs/porting/th14-deferred-capture-vm-clear-verified-oct14.json';path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({'diagnosticEvidenceVerified':True,'ordinaryPooledVmDestroyCases':len(rows),'captureRecordsComparedBytes':640,'captureWrites':0}))
