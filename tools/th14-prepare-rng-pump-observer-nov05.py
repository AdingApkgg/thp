"""Free one VM edge hardware slot to observe the actual earlier main pump.

The original process is not launched by this generator. No additional game
memory writes, instruction patches or thread suspension operations are added.
"""
from pathlib import Path
import argparse,ast,hashlib,json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/script-rng-read-generation-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def prepare(out):
    parent=H/'observer-pending-status/observer.py';raw=parent.read_bytes()
    assert SHA(raw)=='26727dd09ec942e04e9def563c5ec8b56e6a010912f44e4ed1b28809bb7ce596'
    component=H/'rotating-edge-component-retry3'
    proofs=[json.loads((component/n/'report.json').read_bytes())for n in ['static-control','rotating']]
    for p in proofs:
        assert not p['error']and p['exitCode']==0 and not p['unknownExceptions']and p['perThreadOrderEqual']
        assert p['toolSha256']==SHA((R/'tools/th14-rotating-edge-watch-component-nov05.py').read_bytes())
        assert p['executableSha256']==SHA((component/'build/fixture.exe').read_bytes())
        assert all(p['counts'][n]==256 for n in ['call','store','return','receipt'])
    assert proofs[0]['counts']['pump']==0 and proofs[1]['counts']['pump']==256
    source=raw.decode()
    def replace(a,b):
        nonlocal source
        assert source.count(a)==1,(a[:100],source.count(a));source=source.replace(a,b)
    replace('pending_debug_context_deferrals=[]','pending_debug_context_deferrals=[]\nrotating_main_pump_rows=[]')
    replace('        addresses[1:3]=[0x40f2a2,0x40f2a7]',
        '''        # The main thread cannot enter the next call before returning
        # from the current one. Rotate one execute slot at each actual edge.
        # Keep DR0 Player and DR3 RNG; DR1 now observes the earlier real pump.
        addresses[1:3]=[0x47d720,0x40f2a7 if stage_object_vm_active is not None else 0x40f2a2]
        if addresses[3]==0x47d720:addresses[3]=0 # no duplicate pump watch''')
    replace('def finish_stage_object_window(row,tid):',
        '''def stage_vm_watch_hit(registers,pc):
    addresses=registers['addresses'];status=registers['status']
    return bool(status&sum(1<<index for index,address in enumerate(addresses)if address==pc))

def finish_stage_object_window(row,tid):''')
    replace("bool(row['mainThreadContextAtWorkerEvent']['debugRegisters']['status']&2)",
        "stage_vm_watch_hit(row['mainThreadContextAtWorkerEvent']['debugRegisters'],0x40f2a2)")
    replace("bool(row['mainThreadContextAtWorkerEvent']['debugRegisters']['status']&4)",
        "stage_vm_watch_hit(row['mainThreadContextAtWorkerEvent']['debugRegisters'],0x40f2a7)")
    replace("debugRegisters=dict(status=struct.unpack_from('<I',main,20)[0]))",
        "debugRegisters=dict(status=struct.unpack_from('<I',main,20)[0],addresses=list(struct.unpack_from('<4I',main,4)),control=struct.unpack_from('<I',main,24)[0]))")
    replace("        if pc==0x47d720:main_resource_frames+=1;main_camera_phase='update'",
        '''        if pc==0x47d720:
            main_resource_frames+=1;main_camera_phase='update'
            if stage_object_vm_window_tid is not None:
                assert len(rotating_main_pump_rows)<8192
                pump=dict(event='main-resource-pump-with-rotating-vm-edge',pc=pc,
                    precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),
                    hostMonotonicNs=observation_clock_ns(),mainResourceFrame=main_resource_frames,
                    vmCallActive=stage_object_vm_active is not None,
                    debugAddresses=list(struct.unpack_from('<4I',b,4)),debugStatus=struct.unpack_from('<I',b,20)[0],
                    scriptRngWatchActive=script_rng_access_active,readOnly=True,providedToEngine=False)
                rotating_main_pump_rows.append(pump)
                with(home/'rotating-watch-pump-events.jsonl').open('a',encoding='utf8')as stream:stream.write(event_json(pump)+'\\n')''')
    anchor="    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print("
    replace(anchor,"    report.update(rotatingVmEdgeHardwareSlot=True,mainPumpPreservedDuringStageVmWindow=True,rotatingVmWindowPumpEvents=len(rotating_main_pump_rows),rotatingVmWindowPumpSha256=sha((home/'rotating-watch-pump-events.jsonl').read_bytes())if rotating_main_pump_rows else None,mainPumpOutsideVmWindowMayStillHaveRngWatchGap=True,additionalGameMemoryWrites=0,additionalSuspendOrResumeCalls=0)\n"+anchor)
    critical={'WriteProcessMemory','SuspendThread','ResumeThread','ContinueDebugEvent','CreateProcessW','Wow64SetThreadContext'}
    def calls(text):return sorted(ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(text))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in critical)
    assert calls(raw.decode())==calls(source);tree=ast.parse(source)
    # Exercise the exact generated address block over both edge states and
    # verify the actual-address DR6 decoder, rather than assuming slot numbers.
    install=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='install')
    slot=next(n for n in install.body if isinstance(n,ast.If)and any(isinstance(x,ast.Constant)and x.value==0x40f2a7 for x in ast.walk(n)))
    decoder=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='stage_vm_watch_hit')
    cases=[]
    for active in [None,dict(vm=1)]:
        for rng in [False,True]:
            state=dict(opt=type('Options',(),dict(stage_object_vm_window_events=True))(),stage_object_vm_window_tid=2,tid=1,
                pi=type('Process',(),dict(tid=1))(),first_snapshot=True,trace_publications=False,
                stage_object_vm_active=active,addresses=[0x44dbd0,0,0,0x47d720])
            exec(compile(ast.fix_missing_locations(ast.Module(body=[slot,decoder],type_ignores=[])),str(out/'observer.py'),'exec'),state)
            if rng:state['addresses'][3]=0x4db508
            expected=[0x44dbd0,0x47d720,0x40f2a7 if active else 0x40f2a2,0x4db508 if rng else 0]
            assert state['addresses']==expected
            for pc in [0x40f2a2,0x40f2a7]:
                assert state['stage_vm_watch_hit'](dict(addresses=expected,status=4),pc)==(expected[2]==pc)
                assert not state['stage_vm_watch_hit'](dict(addresses=expected,status=2),pc)
            cases.append(dict(activeCall=active is not None,rngWatch=rng,addresses=expected))
    assert not out.exists();out.mkdir(parents=True);(out/'observer.py').write_text(source,encoding='utf8',newline='\n')
    (out/'prepare-tool.py').write_bytes(Path(__file__).read_bytes())
    value=dict(prepared=True,parentObserverSha256=SHA(raw),observerSha256=SHA((out/'observer.py').read_bytes()),
        criticalMutationCallAstUnchanged=True,additionalGameMemoryWrites=0,additionalSuspendOrResumeCalls=0,
        ownedFixtureStaticPumpEvents=0,ownedFixtureRotatingPumpEvents=256,ownedFixtureAllCallStoreReturnReceiptEvents=256,
        ownedComponentReportSha256=[SHA((component/n/'report.json').read_bytes())for n in ['static-control','rotating']],
        addressAndDr6Cases=cases,mainPumpPreservedDuringStageVmWindow=True,mainPumpOutsideVmWindowMayHaveGap=True,
        pendingOtherThreadDebugStatusGuardUnchanged=True,unrecognizedExceptionPolicyUnchanged=True,
        originalProcessNotYetRun=True,exactIndependentSchedulingAccepted=False,completeGame=False,
        toolSha256=SHA(Path(__file__).read_bytes()))
    (out/'prepared.json').write_text(json.dumps(value,indent=2)+'\n');return value

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    v=prepare(out);print(json.dumps({k:v[k]for k in ['prepared','observerSha256','criticalMutationCallAstUnchanged','mainPumpPreservedDuringStageVmWindow','originalProcessNotYetRun']}))
