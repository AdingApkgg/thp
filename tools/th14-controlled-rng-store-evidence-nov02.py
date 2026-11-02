"""Verify an actual controlled original RNG cached-read/store interleave."""
from pathlib import Path
import argparse,ast,hashlib,importlib,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');N=home/'native';bindings={}
    def raw(path):
        p=path.resolve(strict=True);assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    run=load(N/'report.json');plan=load(N/'controlled-schedule-plan.json');prepared=load(home/'preflight.json');end=load(home/'process-end.json')
    assert end['observerExitCode']==end['expectedDiagnosticExitCode']==1 and end['actualMastersZero']and end['guardStop']is None
    assert run['childExited']and not run['error']and run['callbacks']==34000 and run['diagnosticPrefixOnly']and not run['observedForcedReplayEndMenu']
    assert run['threadSchedulingControlled']and run['controlledScheduleComplete']and run['controlledPostStoreObserved']and not run['hardwareBreakpointsOnly']
    assert run['controlledExactMainSeedStorePc']==plan['mainHoldPc']==0x403373 and plan['mainAfterStorePc']==0x403376
    assert run['controlledExactGlobalsCopyCompletePc']==plan['workerGlobalsCopyCompletePc']==0x456135
    assert run['controlledVmWindowKind']=='rng-before-seed-store'
    assert run['instructionBytesPatched']==run['rngOrCounterWrites']==0 and not run['inputInjected']
    assert run['gameStateWordWrites']==1 and run['caseInitialization']['attractBitClearOnly']
    first=load(N/'untouched-first-player.json');notices=run['debugErrors'];assert len(notices)==10
    assert all(x['code']==0xe06d7363 and x['firstChance']==1 and x['callbacks']==0 and x['hostMonotonicNs']<first['hostMonotonicNs']for x in notices)
    source=raw(N/'observer-source.py');assert SHA(source)==run['sourceSha256']==prepared['sourceSha256']==SHA(raw(R/'tools/th14-controlled-rng-store-observer-nov02.py'))
    base=raw(R/'tools/th14-controlled-nested-instruction-observer-nov02.py');assert SHA(base)==prepared['baseSourceSha256']=='69594e58d2ea32a558df35320d41c6cf5ebd38a814f964e678dc8883935fa1a4'
    def mutations(code):return[ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(code))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in('WriteProcessMemory','SuspendThread','ResumeThread','Wow64SetThreadContext')]
    assert mutations(source)==mutations(base)
    assert b'status=0x80010001'in source
    quiet=load(home/'native-silence-verified.json');assert quiet['verifiedActualNativeMasterLevelsZero']and quiet['nativePid']==run['pid']
    assert quiet['processStartSha256']==SHA(raw(N/'process-start.json'))
    assert len(quiet['samples'])==2 and all(all(s[k]==0 for k in('musicConfig','effectsConfig','musicMaster','effectsMaster'))for s in quiet['samples'])
    rows=[json.loads(x)for x in raw(N/'controlled-schedule-events.jsonl').decode().splitlines()]
    assert rows==run['controlledScheduleEvents']and len(rows)==7
    assert[x['event']for x in rows]==['hold-worker-before-original-sleep','suspend-main-before-rng-seed-store','resume-worker-to-execute-original-sleep','seed-restored-while-main-held','globals-copy-complete-before-main-resume','resume-main-after-globals-copy','main-original-seed-store-completed']
    assert all(a['hostMonotonicNs']<b['hostMonotonicNs']for a,b in zip(rows,rows[1:]))
    worker,main,worker_resume,restored,copied,main_resume,written=rows
    assert worker['pc']==0x435b0f and worker['originalInstructionBytes']=='ffd0'
    assert main['pc']==0x403373 and main['originalInstructionBytes']=='66890e'
    assert worker['stage']==main['stage']==copied['stage']==written['stage']==3 and worker['threadId']!=main['threadId']
    for hold,resume in((worker,worker_resume),(main,main_resume)):
        assert hold['addedSuspendCount']==1 and resume['ownIncrementOnly']and hold['threadId']==resume['threadId']
        assert resume['previousSuspendCount']==hold['previousSuspendCount']+1 and resume['restoredSuspendCount']==hold['previousSuspendCount']
        assert not hold['gameplayValuesWritten']and hold['schedulerInterventionDeclared']
        assert 0<resume['hostMonotonicNs']-hold['hostMonotonicNs']<=5_000_000_000
    assert plan['maximumHoldSeconds']==5 and plan['oneMainSuspendIncrementOnly']and plan['oneWorkerSuspendIncrementOnly']
    assert restored['pc']==0x456133 and restored['mainStillHeld']and restored['originalSeedRestoreExecuted']
    assert copied['pc']==0x456135 and copied['mainHeldAtPc']==0x403373 and copied['originalRepMovsdCompleted']
    assert written['pc']==0x403376 and written['threadId']==main['threadId']and written['originalSeedStoreExecuted']
    assert all(x['precedingPlayerCallbacks']==main['precedingPlayerCallbacks']for x in rows[1:])
    regs=main['registers'];assert regs['esi']==0x4db508 and regs['edx']==0x6553
    state=lambda row:struct.unpack('<HHIHHI',bytes.fromhex(row['rngHex']))
    before,after_worker,after_main=map(state,(main,copied,written))
    assert after_main[0]==written['cachedSeedStoreWord']==main['cachedSeedStoreWord']==regs['ecx']&0xffff
    assert before[2]==after_worker[2]==after_main[2] and after_worker[0]!=after_main[0]
    assert after_worker[3:]==after_main[3:]and after_main[5]==0
    image,*_=importlib.import_module('th-anm-handlers').handlers(14)
    assert SHA(image.data)==run['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    for pc,expected in[(0x403373,'66890e'),(0x456123,'66a308b54d00'),(0x456133,'f3a5'),(0x40b140,'558bec83ec10'),(0x46ff1d,'8bcfffd0')]:assert image.read(pc,len(bytes.fromhex(expected)))==bytes.fromhex(expected)
    # The cached mixed word is independently re-executed from original code.
    seed_read=((regs['edi']+0x6553)&0xffff)^0x9630
    m=Uc(UC_ARCH_X86,UC_MODE_32);m.mem_map(0x400000,0x100000);m.mem_map(0x100000,0x10000)
    m.mem_write(0x403310,image.read(0x403310,0x8b));m.mem_write(0x4db508,struct.pack('<HHI',seed_read,0,(before[2]-2)&0xffffffff))
    m.reg_write(UC_X86_REG_ESP,0x108000);m.reg_write(UC_X86_REG_ECX,0x4db508)
    m.emu_start(0x403310,0x403373,count=100)
    for name,reg in [('edi',UC_X86_REG_EDI),('esi',UC_X86_REG_ESI),('ebx',UC_X86_REG_EBX),('edx',UC_X86_REG_EDX),('ecx',UC_X86_REG_ECX),('eax',UC_X86_REG_EAX)]:
        assert(m.reg_read(reg)&0xffff if name=='ecx'else m.reg_read(reg))==(regs[name]&0xffff if name=='ecx'else regs[name]),name
    assert struct.unpack('<HHI',bytes(m.mem_read(0x4db508,8)))==(seed_read,0,before[2])
    # Frame-pointer positions and actual return PCs identify the ribbon
    # pre-update callback, without inferring its file/script or live VM identity.
    stack=bytes.fromhex(main['stackHex']);sp=main['stackAddress'];assert sp==regs['esp']
    word=lambda address:struct.unpack_from('<I',stack,address-sp)[0]
    assert word(sp+12)==0x4034bc and word(regs['ebp']+4)==0x40b209
    callback_frame=word(regs['ebp']);assert word(callback_frame+4)==0x46ff21
    for pc,target in[(0x4034b7,0x403310),(0x40b204,0x4034b0)]:
        code=image.read(pc,5);assert code[0]==0xe8 and pc+5+struct.unpack_from('<i',code,1)[0]==target
    assert word(sp)==word(sp+4)  # Ribbon callback retains its geometry in EDI/ESI.
    for name in('selected-state.u32','player-host-monotonic.u64','snapshot-plan.json','seed-store-instruction-events.jsonl','transition-events.jsonl'):raw(N/name)
    return dict(verifiedControlledOriginalRngStoreBoundary=True,capturedCallbacks=34000,diagnosticPrefixOnly=True,
        precedingPlayerCallbacks=main['precedingPlayerCallbacks'],originalMainPc=0x403373,originalAfterStorePc=0x403376,
        globalsCopyCompleteHostNs=copied['hostMonotonicNs'],nativeRngFunctionIndependentlyExecuted=True,
        restoredSeedOverwrittenByPreviouslyComputedMainValue=True,scriptCounterPreservedAcrossWorkerRestore=True,
        originalRibbonPreUpdateCallChainProved=True,targetEffect=8,targetBoundary=3,liveVmFileOrScriptIdentityClaimed=False,
        originalInstructionsPatched=0,additionalGameWrites=0,oneOwnSuspendIncrementPerThread=True,
        startupFirstChanceNoticesRetained=10,coldStartupAccepted=False,exceptionCauseClassified=False,
        ordinaryIndependentThreadTimingAcceptance=False,nativeValuesProvidedToEngine=False,
        completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
