"""Prepare fixed Player/Supervisor1/pump/RNG watches after the startup prefix.

This profile deliberately gives up main-thread camera/VM/controller watches.
Worker watches and all game/process mutations retain their existing bodies.
Supervisor1 is an observed callback-pass boundary, not a claimed physical frame.
"""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,struct,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
P=R/'artifacts/th14/script-rng-read-generation-nov05/observer-player-pump/observer.py'
def prepare(out):
    raw=P.read_bytes();assert SHA(raw)=='f215b4fae98ac88c1cd94576f99ccb31484d157497cf14e7bfd89e22f79a8884'
    component=R/'artifacts/th14/frame-entry-audit-retry1-nov05/component/stable/report.json';proof=json.loads(component.read_bytes())
    assert proof['passed']and proof['counts']==dict(entry=256,pump=256,player=224,store=224)and proof['omittedPlayerPasses']==32
    assert proof['toolSha256']==SHA((R/'tools/th14-fixed-frame-watch-component-nov05.py').read_bytes())
    sys.path.insert(0,str(R/'tools'));image=__import__('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert image.read(0x444e70,5)==b'\x68'+struct.pack('<I',0x444890)
    assert image.read(0x444e9c,3)==bytes.fromhex('6a0150')
    assert image.read(0x4448cd,5)==b'\xe8'+struct.pack('<i',0x47d720-0x4448d2)
    source=raw.decode()
    def replace(a,b):
        nonlocal source
        assert source.count(a)==1,(a[:100],source.count(a));source=source.replace(a,b)
    replace('player_pump_mux_rows=[]','player_pump_mux_rows=[]\nsupervisor_pass_rows=[];supervisor_pass_ordinal=0;latest_supervisor_pass=None')
    replace('targets.update({0x456115:',"targets.update({0x444890:'supervisor-priority1-entry'})\ntargets.update({0x456115:")
    helper='''def record_supervisor_pass_boundary(pc,tid,b):
    global supervisor_pass_ordinal,latest_supervisor_pass
    if tid!=pi.tid or first_snapshot is None or callback_count<opt.publication_cutoff:return
    addresses=list(struct.unpack_from('<4I',b,4));status=struct.unpack_from('<I',b,20)[0]
    # The cutoff's last Player can still have the previous startup watches.
    if addresses[:3]!=[0x44dbd0,0x444890,0x47d720]:return
    assert pc in (0x44dbd0,0x444890,0x47d720)
    matching=sum(1<<index for index,address in enumerate(addresses)if address==pc)
    assert status&matching and len(supervisor_pass_rows)<200000
    if pc==0x444890:supervisor_pass_ordinal+=1
    row=dict(event={0x444890:'supervisor-priority1-entry',0x47d720:'supervisor-resource-pump',0x44dbd0:'player-entry'}[pc],
        pc=pc,threadId=tid,hostMonotonicNs=observation_clock_ns(),precedingPlayerCallbacks=callback_count,
        supervisorPassOrdinal=supervisor_pass_ordinal,stage=u32(0x4f58a4),debugAddresses=addresses,debugStatus=status,
        matchingHardwareBits=matching,hardwareWatchesNotMultiplexed=True,readOnly=True,providedToEngine=False,
        physicalFrameIdentityNotClaimed=True,receiptTimeIsNotInstructionExecutionTime=True)
    supervisor_pass_rows.append(row)
    encoded=event_json(row)
    if pc==0x444890:latest_supervisor_pass={key:row[key]for key in ['pc','threadId','hostMonotonicNs','precedingPlayerCallbacks','supervisorPassOrdinal','debugEventSequence']}
    with(home/'supervisor-pass-events.jsonl').open('a',encoding='utf8')as stream:stream.write(encoded+'\\n')

'''
    replace('def event_snapshot(pc,tid,b):',helper+'def event_snapshot(pc,tid,b):')
    replace('    if pc==0x45a0f0:',"    if pc==0x444890:\n        record_supervisor_pass_boundary(pc,tid,b);return\n    if pc==0x45a0f0:")
    replace('            record_player_pump_mux(pc,tid,b)','            record_supervisor_pass_boundary(pc,tid,b)')
    replace('                            record_player_pump_mux(pc,ev.tid,b)','                            record_supervisor_pass_boundary(pc,ev.tid,b)')
    replace("    if script_rng_restore_receipt:script_rng_post_restore_accesses+=1", "    if script_rng_restore_receipt:script_rng_post_restore_accesses+=1")
    replace("        registers=regs,rngHexAtObservation=read(0x4db508,16).hex(),watchAddress=0x4db508,watchBytes=2,",
        "        registers=regs,rngHexAtObservation=read(0x4db508,16).hex(),watchAddress=0x4db508,watchBytes=2,latestObservedSupervisorPass=latest_supervisor_pass,")
    override='''    if first_snapshot is not None and not trace_publications and tid==pi.tid:
        # Stable execution watches never rely on Player/pump alternation.
        # Main-thread camera/VM/controller/EOF slots are explicitly given up.
        addresses=[0x44dbd0,0x444890,0x47d720,0x4db508 if script_rng_access_active else 0]
        watch_camera_write=False;watch_camera_read=False
'''
    replace("    for index,address in enumerate(addresses):struct.pack_into('<I',b,4+4*index,address)",override+"    for index,address in enumerate(addresses):struct.pack_into('<I',b,4+4*index,address)")
    anchor="    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print("
    replace(anchor,"""    report.update(supervisorPassBoundaryPc=0x444890,supervisorPassWatchStartsAfterPublications=opt.publication_cutoff,
        supervisorPassBoundaryEvents=len(supervisor_pass_rows),supervisorEntryEvents=supervisor_pass_ordinal,
        supervisorPassEventsSha256=sha((home/'supervisor-pass-events.jsonl').read_bytes())if supervisor_pass_rows else None,
        supervisorPlayerPumpWatchesFixed=True,mainCameraVmControllerWatchesGivenUpAfterPrefix=True,
        rotatingVmEdgeHardwareSlot=False,playerPumpDr0MultiplexedDuringRngWatch=False,
        playerPumpMuxOriginalDispatchOrderAssumed=False,controllerSlotRotatesAfterObservedCameraWrite=False,
        mainResourcePumpObservationHasDeclaredStage3WatchGap=False,mainPumpOutsideVmWindowMayStillHaveRngWatchGap=False,
        physicalFrameEntryRecovered=False,originalInstructionExecutionTimestampsRecovered=False)
"""+anchor)
    critical={'WriteProcessMemory','SuspendThread','ResumeThread','ContinueDebugEvent','CreateProcessW','Wow64SetThreadContext'}
    def calls(s):return sorted(ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(s))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in critical)
    assert calls(raw.decode())==calls(source)
    install=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='install')
    block=next(n for n in install.body if isinstance(n,ast.If)and any(isinstance(x,ast.Constant)and x.value==0x444890 for x in ast.walk(n)))
    cases=[]
    for first,prefix,main,active in __import__('itertools').product([False,True],repeat=4):
        before=[0x44dbd0,0x436bed,0x4d9544,0]
        state=dict(first_snapshot={}if first else None,trace_publications=prefix,tid=1 if main else 2,pi=type('Process',(),dict(tid=1))(),
            script_rng_access_active=active,addresses=list(before),watch_camera_write=True,watch_camera_read=True)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[block],type_ignores=[])),str(out/'observer.py'),'exec'),state)
        expected=[0x44dbd0,0x444890,0x47d720,0x4db508 if active else 0]if first and not prefix and main else before
        assert state['addresses']==expected
        if first and not prefix and main:assert not state['watch_camera_write']and not state['watch_camera_read']
        cases.append(dict(firstSnapshot=first,startupPrefix=prefix,mainThread=main,rngActive=active,addresses=expected))
    assert not out.exists();out.mkdir(parents=True);(out/'observer.py').write_text(source,encoding='utf8',newline='\n');(out/'prepare-tool.py').write_bytes(Path(__file__).read_bytes())
    result=dict(prepared=True,parentObserverSha256=SHA(raw),observerSha256=SHA((out/'observer.py').read_bytes()),
        ownedFixedSlotComponentSha256=SHA(component.read_bytes()),addressCases=cases,criticalMutationCallAstUnchanged=True,
        pendingOtherThreadHardwareStatusGuardUnchanged=True,additionalGameMemoryWrites=0,additionalSuspendOrResumeCalls=0,
        supervisorEntryPc=0x444890,callbackPriority=1,mainWatchesGivenUp=['camera','stage-vm','controller-flags','eof'],
        originalInstructionBindings=[dict(pc=pc,bytes=size,sha256=SHA(image.read(pc,size)))for pc,size in [(0x444e70,0x42),(0x444890,0xae)]],
        originalProcessNotYetRun=True,physicalFrameEntryProven=False,toolSha256=SHA(Path(__file__).read_bytes()),completeGame=False)
    (out/'prepared.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists();r=prepare(out)
    print(json.dumps({k:r[k]for k in ['prepared','observerSha256','criticalMutationCallAstUnchanged','supervisorEntryPc','callbackPriority','originalProcessNotYetRun']}))
