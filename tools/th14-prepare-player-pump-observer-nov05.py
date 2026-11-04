"""Observe the earlier pump after the VM window closes, using a DR0 mux.

Only while the bounded RNG watch is active: after an observed Player wait for
the pump, and after an observed pump wait for Player. Original dispatch order
is an explicit assumption, not proved by the owned two-thread component.
All camera/VM/data slots and the pending-debug-status guard remain intact.
"""
from pathlib import Path
import argparse,ast,hashlib,json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/script-rng-read-generation-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def prepare(out):
    parent=H/'observer-rotating-pump/observer.py';raw=parent.read_bytes()
    assert SHA(raw)=='4595cf23b509c917cf881aa420b5629307aacb7f07c793a51482e9b14b254754'
    own=H/'player-pump-component-retry1'
    for name in ['static-control','rotating']:
        p=json.loads((own/name/'report.json').read_bytes())
        assert p['exitCode']==0 and not p['error']and not p['unknownExceptions']and p['perThreadOrderEqual']
        assert p['toolSha256']==SHA((R/'tools/th14-player-pump-watch-component-nov05.py').read_bytes())
        assert p['executableSha256']==SHA((own/'build/fixture.exe').read_bytes())
        assert all(p['counts'][key]==256 for key in ['call','store','return','receipt'])
        assert p['counts']['pump']==(256 if name=='rotating'else 0)
    source=raw.decode()
    def replace(a,b):
        nonlocal source
        assert source.count(a)==1,(a[:100],source.count(a));source=source.replace(a,b)
    replace('rotating_main_pump_rows=[]','rotating_main_pump_rows=[]\nplayer_pump_mux_rows=[]')
    replace('    if script_rng_access_active and tid==pi.tid:addresses[3]=0x4db508',
        '''    if script_rng_access_active and tid==pi.tid:
        addresses[3]=0x4db508
        # Existing phase is set at actual pump/Player events, not by a timer.
        # Do not let the end of the VM window remove the next pump boundary.
        addresses[0]=0x47d720 if main_camera_phase=='draw'else 0x44dbd0''')
    helper='''def record_player_pump_mux(pc,tid,b):
    if not script_rng_access_active or tid!=pi.tid:return
    assert pc in (0x47d720,0x44dbd0)and len(player_pump_mux_rows)<4096
    addresses=list(struct.unpack_from('<4I',b,4));status=struct.unpack_from('<I',b,20)[0]
    matching=sum(1<<index for index,address in enumerate(addresses)if address==pc)
    assert status&matching
    row=dict(event='rng-watch-main-pump'if pc==0x47d720 else'rng-watch-player-entry',
        pc=pc,threadId=tid,precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),
        hostMonotonicNs=observation_clock_ns(),phaseBeforeBoundary=main_camera_phase,
        debugAddresses=addresses,debugStatus=status,matchingHardwareBits=matching,
        stageVmWindowActive=stage_object_vm_window_tid is not None,
        readOnly=True,providedToEngine=False,originalDispatchOrderAssumed=True,
        allUnobservedCallsNotClaimed=True)
    player_pump_mux_rows.append(row)
    with(home/'player-pump-mux-events.jsonl').open('a',encoding='utf8')as stream:stream.write(event_json(row)+'\\n')

'''
    replace('def event_snapshot(pc,tid,b):',helper+'def event_snapshot(pc,tid,b):')
    replace("        if pc==0x47d720:\n            main_resource_frames+=1;main_camera_phase='update'",
        "        if pc==0x47d720:\n            record_player_pump_mux(pc,tid,b)\n            main_resource_frames+=1;main_camera_phase='update'")
    replace("                        elif pc==0x44dbd0:\n                            main_camera_phase='draw'",
        "                        elif pc==0x44dbd0:\n                            record_player_pump_mux(pc,ev.tid,b)\n                            main_camera_phase='draw'")
    anchor="    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print("
    replace(anchor,"    report.update(playerPumpDr0MultiplexedDuringRngWatch=True,playerPumpMuxEvents=len(player_pump_mux_rows),playerPumpMuxSha256=sha((home/'player-pump-mux-events.jsonl').read_bytes())if player_pump_mux_rows else None,playerPumpMuxOriginalDispatchOrderAssumed=True,allPlayerOrPumpCallsProvenObserved=False,mainPumpAtFirstRngAccessMustBeCheckedSeparately=True)\n"+anchor)
    critical={'WriteProcessMemory','SuspendThread','ResumeThread','ContinueDebugEvent','CreateProcessW','Wow64SetThreadContext'}
    def calls(text):return sorted(ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(text))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in critical)
    assert calls(raw.decode())==calls(source)
    tree=ast.parse(source);install=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='install')
    block=next(n for n in install.body if isinstance(n,ast.If)and any(isinstance(x,ast.Constant)and x.value==0x4db508 for x in ast.walk(n)))
    cases=[]
    for enabled in [False,True]:
        for main in [False,True]:
            for phase in ['update','draw']:
                state=dict(script_rng_access_active=enabled,tid=1 if main else 2,pi=type('Process',(),dict(tid=1))(),main_camera_phase=phase,addresses=[0x44dbd0,0x40dae9,0x4d9544,0])
                before=list(state['addresses'])
                exec(compile(ast.fix_missing_locations(ast.Module(body=[block],type_ignores=[])),str(out/'observer.py'),'exec'),state)
                expected=list(before)
                if enabled and main:expected[0]=0x47d720 if phase=='draw'else 0x44dbd0;expected[3]=0x4db508
                assert state['addresses']==expected and expected[1:3]==before[1:3]
                cases.append(dict(enabled=enabled,main=main,phase=phase,addresses=expected))
    assert not out.exists();out.mkdir(parents=True);(out/'observer.py').write_text(source,encoding='utf8',newline='\n')
    (out/'prepare-tool.py').write_bytes(Path(__file__).read_bytes())
    value=dict(prepared=True,parentObserverSha256=SHA(raw),observerSha256=SHA((out/'observer.py').read_bytes()),
        criticalMutationCallAstUnchanged=True,additionalGameMemoryWrites=0,additionalSuspendOrResumeCalls=0,
        pendingOtherThreadHardwareStatusGuardUnchanged=True,exceptionPolicyUnchanged=True,
        playerPumpSlotOnlyWhileRngWatchActive=True,cameraAndVmSlotsUnchanged=True,
        addressCases=cases,ownedConcurrentPumpCallStoreReturnReceiptEventsEach=256,
        ownedComponentReportsSha256=[SHA((own/name/'report.json').read_bytes())for name in ['static-control','rotating']],
        originalDispatchOrderAssumed=True,allPlayerOrPumpCallsProvenObserved=False,
        originalProcessNotYetRun=True,completeGame=False,toolSha256=SHA(Path(__file__).read_bytes()))
    (out/'prepared.json').write_text(json.dumps(value,indent=2)+'\n');return value

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    v=prepare(out);print(json.dumps({k:v[k]for k in ['prepared','observerSha256','criticalMutationCallAstUnchanged','cameraAndVmSlotsUnchanged','originalProcessNotYetRun']}))
