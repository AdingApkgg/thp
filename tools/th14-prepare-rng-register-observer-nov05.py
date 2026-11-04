"""Prepare a bounded stage3 main-thread script RNG read/write hardware watch.

DR3 temporarily replaces main resource-pump observation, never Player or VM
edges. Stopped-register values are diagnostic outputs only. No RNG/counter,
instruction or thread suspend writes are added.
"""
from pathlib import Path
import argparse, ast, hashlib, json

R=Path(__file__).resolve().parents[1]
P=R/'artifacts/th14/reimub-hard-full-context-nov05/next-observer-context-audit/observer.py'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def prepare(out,profile):
    path=P if profile=='selective'else R/'artifacts/th14/reimub-hard-full-context-nov05/observer.py'
    parent=path.read_bytes()
    normalized_parent=parent.replace(b'\r\n',b'\n')
    if profile=='selective':
        assert SHA(parent)=='b8e959b85f3a9047465599ebf4827ee6dffdf7aba52b48e9ef1591300e59394a'
        parent_note=json.loads((P.parent/'prepared.json').read_bytes())
        assert SHA(normalized_parent)==parent_note['observerSha256']=='a3e963aaffbb82bf4f82dc8b9e8405d31b7717327de441a13f13421f34c0e3a3'
    else:assert SHA(parent)=='9891a90f16a67b61019b354cb737c9b22964ea6c296ef6830cac495c65204246'
    component=R/'artifacts/th14/script-rng-read-generation-nov05/component/report.json'
    proof=json.loads(component.read_bytes());assert proof['passed']and proof['cases']==210 and proof['laterGlobalSnapshotWrong']==189
    assert proof['toolSha256']==SHA((R/'tools/th14-rng-register-generation-component-nov05.py').read_bytes())
    source=normalized_parent.decode()
    def replace(old,new):
        nonlocal source
        assert source.count(old)==1,(old[:90],source.count(old));source=source.replace(old,new)
    replace('pending_worker_rng=set()', '''pending_worker_rng=set()
script_rng_access_active=False;script_rng_access_armed=False;script_rng_restore_receipt=False
script_rng_access_rows=[];script_rng_post_restore_accesses=0;script_rng_arm=None''')
    handler='''def script_rng_access_snapshot(pc,tid,b):
    global script_rng_access_active,script_rng_post_restore_accesses
    assert tid==pi.tid and len(script_rng_access_rows)<512
    regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
    contract={0x4032c8:('mix16',0x4032c5,'663306','xorAX'),0x403339:('mix32',0x403336,'663306','xorAX'),
        0x4033c9:('mix32Alternate',0x4033c6,'663306','xorAX'),0x403300:('returnReload16',0x4032fd,'668b06','AX'),
        0x4032e3:('store16',0x4032e0,'66890e','CX'),0x403376:('store32',0x403373,'66890e','CX'),
        0x403406:('store32Alternate',0x403403,'66890e','CX')}.get(pc)
    recovered=None;decoded=None
    if contract and regs['esi']==0x4db508:
        name,instruction,code,kind=contract;assert read(instruction,pc-instruction).hex()==code
        recovered=((regs['eax']&65535)^0x9630)if kind=='xorAX'else(regs['eax']if kind=='AX'else regs['ecx'])&65535
        decoded=dict(kind=name,instructionPc=instruction,instructionBytes=code,recovery=kind)
    if script_rng_restore_receipt:script_rng_post_restore_accesses+=1
    row=dict(event='main-script-rng-seed-access',ordinal=len(script_rng_access_rows)+1,pc=pc,threadId=tid,
        hostMonotonicNs=observation_clock_ns(),precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),
        registers=regs,rngHexAtObservation=read(0x4db508,16).hex(),watchAddress=0x4db508,watchBytes=2,
        debugAddresses=list(struct.unpack_from('<4I',b,4)),debugStatus=struct.unpack_from('<I',b,20)[0],debugControl=struct.unpack_from('<I',b,24)[0],
        instructionContract=decoded,valueRetainedByTrappedInstruction=recovered,
        instructionValueDecoded=decoded is not None,globalSnapshotIsNotInstructionValue=True,
        globalsCopyReceiptAlreadySeen=script_rng_restore_receipt,postRestoreReceiptAccessOrdinal=script_rng_post_restore_accesses,
        dataReadOrWriteHardwareTrap=True,debuggerPausesAffectTiming=True,crossThreadInstructionOrderNotAsserted=True,
        exactOriginalScheduleRecovered=False,gameValuesProvidedToEngine=False,readOnly=True)
    script_rng_access_rows.append(row)
    with(home/'script-rng-access-events.jsonl').open('a',encoding='utf8')as stream:stream.write(event_json(row)+'\\n')
    if script_rng_restore_receipt and script_rng_post_restore_accesses>=64:script_rng_access_active=False
    storage_budget()

'''
    replace('def install(tid,current=False):',handler+'def install(tid,current=False):')
    replace("    for index,address in enumerate(addresses):struct.pack_into('<I',b,4+4*index,address)",
            "    if script_rng_access_active and tid==pi.tid:addresses[3]=0x4db508\n    for index,address in enumerate(addresses):struct.pack_into('<I',b,4+4*index,address)")
    replace("    if current:struct.pack_into('<I',b,192,struct.unpack_from('<I',b,192)[0]|0x10000)",
            "    if script_rng_access_active and tid==pi.tid:struct.pack_into('<I',b,24,struct.unpack_from('<I',b,24)[0]|0x70000000)\n    if current:struct.pack_into('<I',b,192,struct.unpack_from('<I',b,192)[0]|0x10000)")
    replace('def replay_store_snapshot(pc,tid,b):',
            'def replay_store_snapshot(pc,tid,b):\n    global script_rng_restore_receipt')
    replace("    if pc==0x456135:\n        row['mainThreadPcAtWorkerEvent']", "    if pc==0x456135 and row['stage']==3:script_rng_restore_receipt=True\n    if pc==0x456135:\n        row['mainThreadPcAtWorkerEvent']")
    # snapshot() is already embedded from the replay cursor helper; this is the
    # actual observer's main event dispatcher, not the cursor helper function.
    dispatch='def event_snapshot(pc,tid,b):'
    if dispatch not in source:
        candidates=[n for n in ast.walk(ast.parse(source))if isinstance(n,ast.FunctionDef)and any(isinstance(x,ast.Constant)and x.value=='sleep60-before-call'for x in ast.walk(n))]
        assert len(candidates)==1
        dispatch='def '+candidates[0].name+'(pc,tid,b):'
    replace(dispatch,dispatch+'\n    global script_rng_access_active,script_rng_access_armed,script_rng_arm')
    anchor='            if opt.worker_rng_events and tid!=pi.tid:pending_worker_rng.add(tid)'
    replace(anchor,anchor+'''
            if tid!=pi.tid and row['stage']==3 and not script_rng_access_armed:
                script_rng_access_active=script_rng_access_armed=True
                script_rng_arm=dict(event='arm-stage3-script-seed-read-write-watch',workerPc=pc,
                    precedingPlayerCallbacks=callback_count,stage=3,hostMonotonicNs=observation_clock_ns(),
                    mainResourcePumpObservationTemporarilyReplaced=True,playerAndVmEdgesPreserved=True,
                    watchAddress=0x4db508,watchBytes=2,hardwareOnly=True,readOnly=True,providedToEngine=False)
                (home/'script-rng-watch-arm.json').write_text(event_json(script_rng_arm)+'\\n')
                if pi.tid in threads:install(pi.tid)''')
    anchor="                    if pc in targets or camera_write_hit or camera_read_hit or (serial_watch_manager and struct.unpack_from('<I',b,20)[0]&2) or (ev.tid in pending_publications and pc==pending_publications[ev.tid]['publishPc']):"
    replace(anchor,"                    script_rng_hit=ev.tid==pi.tid and bool(struct.unpack_from('<I',b,20)[0]&8)and struct.unpack_from('<I',b,16)[0]==0x4db508 and struct.unpack_from('<I',b,24)[0]&0xf0000000==0x70000000\n"+anchor.replace('pc in targets or','script_rng_hit or pc in targets or'))
    replace('                        if pc in (0x4552cd,0x45521b):','                        if script_rng_hit:\n                            script_rng_access_snapshot(pc,ev.tid,b)\n                        elif pc in (0x4552cd,0x45521b):')
    replace("    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print(",
            "    report.update(scriptRngRegisterAccessEvents=len(script_rng_access_rows),scriptRngAccessWatchArmed=script_rng_access_armed,scriptRngAccessWatchStillActive=script_rng_access_active,scriptRngPostRestoreReceiptAccesses=script_rng_post_restore_accesses,scriptRngAccessSha256=sha((home/'script-rng-access-events.jsonl').read_bytes())if script_rng_access_rows else None,scriptRngAccessValuesProvidedToEngine=False,mainResourcePumpObservationHasDeclaredStage3WatchGap=True,scriptRngDecodedRegisterValues=sum(row['instructionValueDecoded']for row in script_rng_access_rows),scriptRngRegisterValueCrossThreadScheduleAccepted=False)\n    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print(")
    # Verify that no new calls capable of writing game memory, patching code,
    # creating processes or altering explicit thread suspend counts appeared.
    critical={'WriteProcessMemory','SuspendThread','ResumeThread','ContinueDebugEvent','CreateProcessW','Wow64SetThreadContext'}
    def calls(text):
        return sorted(ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(text))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in critical)
    assert calls(parent.decode())==calls(source)
    ast.parse(source);out.mkdir(parents=True)
    path=out/'observer.py';path.write_text(source,encoding='utf8',newline='\n')
    (out/'prepare-tool.py').write_bytes(Path(__file__).read_bytes())
    result=dict(prepared=True,observerSha256=SHA(path.read_bytes()),parentObserverSha256=SHA(parent),
        parentProfile=profile,parentPreparedDigestWasNormalizedTextNotRawFile=profile=='selective',parentNormalizedTextSha256=SHA(normalized_parent),
        parentSelectiveContextAuditOnlyPreviouslyPrepared=profile=='selective',componentSha256=SHA(component.read_bytes()),
        watchedStage=3,maximumAccessEvents=512,stopAfterGlobalsCopyReceiptAccesses=64,
        onlyMainDr3TemporarilyReplaced=True,mainResourcePumpObservationHasDeclaredGap=True,
        playerAndStageVmEdgesPreserved=True,criticalMutationCallAstUnchanged=True,
        additionalGameMemoryWrites=0,additionalSuspendOrResumeCalls=0,
        instructionValuesAreOutputsOnly=True,exactIndependentSchedulingAccepted=False,
        originalProcessNotYetRun=True,completeGame=False,toolSha256=SHA(Path(__file__).read_bytes()))
    (out/'prepared.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--parent',choices=['original','selective'],default='original');a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    value=prepare(out,a.parent);print(json.dumps({k:value[k]for k in ['prepared','observerSha256','criticalMutationCallAstUnchanged','originalProcessNotYetRun']}))
