"""Exercise actual observer AST with the retained worker-before-call delivery.

This controls debugger/context services and a thin VM fixture. No original
process, game implementation, scheduling, or native memory writes are used.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse,ast,hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    native=a.native.resolve(strict=True);out=a.output.resolve();assert native.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
    run=json.loads((native/'report.json').read_bytes());assert run['error']=='AssertionError()'and run['childExited']
    restored=next(r for r in run['transitionEvents']if r.get('normalVmCallWindowAtSeedRestore',{}).get('mainPcAtRestore')==0x47e65b)
    assert restored['normalVmCallWindowAtSeedRestore']['activeCall']is None
    actual_main=restored['mainThreadContextAtWorkerEvent'];assert actual_main['debugRegisters']['status']&2
    assert actual_main['debugRegisters']['addresses'][1:3]==[0x47e65b,0x47e660]
    rows=[json.loads(x)for x in (native/'normal-vm-window-events.jsonl').read_text().splitlines()]
    assert len(rows)==restored['normalVmCallWindowAtSeedRestore']['observedEdges']and rows[-1]['pc']==0x47e660
    main_tid=rows[-1]['threadId'];worker_tid=restored['threadId'];out.mkdir(parents=True)
    exe=(native/'work/th14.exe').read_bytes();assert SHA(exe)==run['executableSha256']
    pe=struct.unpack_from('<I',exe,60)[0];optional=pe+24;base=struct.unpack_from('<I',exe,optional+28)[0];table=optional+struct.unpack_from('<H',exe,pe+20)[0]
    def instruction(pc,count):
        for at in range(table,table+40*struct.unpack_from('<H',exe,pe+6)[0],40):
            size,va,length,offset=struct.unpack_from('<IIII',exe,at+8)
            if va<=pc-base<va+max(size,length):return exe[offset+pc-base-va:offset+pc-base-va+count]
        raise AssertionError(hex(pc))
    registers=['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp']
    def context(values,debug=None):
        b=bytearray(716);struct.pack_into('<11I',b,156,*[values[k]for k in registers])
        if debug:
            struct.pack_into('<4I',b,4,*debug['addresses']);struct.pack_into('<I',b,20,debug['status']);struct.pack_into('<I',b,24,debug['control'])
        return b
    main=context(actual_main['registers'],actual_main['debugRegisters']);worker=context(restored['registers'])
    vm=actual_main['registers']['esi'];assert actual_main['registers']['ecx']==vm
    blob=bytearray(0x5cc)
    # These identity fields only make the actual call/return handler readable.
    # They are declared, not a recovered VM snapshot from the failed event.
    for at,value,fmt in [(0x36,2,'H'),(0x4aa,17,'H'),(0x540,0x12345678,'I')]:struct.pack_into('<'+fmt,blob,at,value)
    def read(address,count):
        if address in (0x47e65b,0x47e660,0x456133):return instruction(address,count)
        if address==actual_main['registers']['esp']:return bytes.fromhex(actual_main['stackHex'])[:count]
        if address==0x4db508 and count==16:return bytes.fromhex(restored['rngHex'])
        if address==restored['registers']['esi']-0x12 and count==2:return struct.pack('<H',restored['restoredReplaySeed'])
        if address==vm and count==len(blob):return bytes(blob)
        raise AssertionError((hex(address),count))
    control=0x71000000;words={0x4db558:control,control+0x14:restored['stageFrame'],0x4f58a4:restored['stage']}
    installed=[];source=(ROOT/'tools/th14-native-campaign-observer-oct25.py').read_bytes();tree=ast.parse(source)
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ['event_snapshot','worker_vm_snapshot']];assert len(functions)==2
    ns=dict(struct=struct,json=json,time=SimpleNamespace(monotonic_ns=lambda:restored['hostMonotonicNs']+1),read=read,u32=lambda address:words[address],
        pi=SimpleNamespace(tid=main_tid),threads={main_tid:1},context=lambda _:main,home=out,
        opt=SimpleNamespace(worker_rng_events=True,worker_main_context=True,worker_main_stack_bytes=512,normal_vm_window_events=True,worker_active_vm_snapshot=True),
        targets={0x47e65b:'normal-vm-before-original-call',0x47e660:'normal-vm-after-original-return',0x456133:'replay-seeds-restored-before-globals-copy'},
        pending_worker_rng={worker_tid},normal_vm_window_tid=worker_tid,normal_vm_active=None,normal_vm_closing_restore=None,
        normal_vm_events=list(rows),callback_count=restored['precedingPlayerCallbacks'],transition_events=[],install=lambda tid:installed.append(tid))
    exec(compile(ast.Module(body=functions,type_ignores=[]),'actual-observer-handler','exec'),ns)
    ns['event_snapshot'](0x456133,worker_tid,worker)
    assert ns['normal_vm_window_tid']==worker_tid and ns['normal_vm_active']is None and not installed
    assert ns['normal_vm_closing_restore']==dict(boundary='call-entry-pending',hostMonotonicNs=restored['hostMonotonicNs']+1)
    seed=ns['transition_events'][-1]['normalVmCallWindowAtSeedRestore'];assert seed['callEntryDeliveryPending']and seed['callWatchStatusBitAtRestore']and not seed['activeVmSnapshot']['observedCallActive']
    for pc in [0x47e65b,0x47e660]:
        struct.pack_into('<I',main,184,pc);ns['event_snapshot'](pc,main_tid,main)
        if pc==0x47e65b:
            assert ns['normal_vm_active']is not None and ns['normal_vm_window_tid']==worker_tid
            assert ns['normal_vm_events'][-1]['callEntryDrainedAfterSeedRestore']
    assert ns['normal_vm_window_tid']is ns['normal_vm_active']is ns['normal_vm_closing_restore']is None
    after=ns['normal_vm_events'][-1]
    assert after['callEntryPendingAtSeedRestore']and not after['returnPcAlreadyObservedAtSeedRestore']and after['restoreEventDeliveredEarlier']
    assert after['restoreObservationHostNs']==restored['hostMonotonicNs']+1
    result=dict(passed=True,actualObserverHandlerAst=True,retainedWorkerBeforeCallEntryOrder=True,
        actualMainCallPc=0x47e65b,actualMainCallDrStatusBitObserved=True,pendingEntryAndReturnDrained=True,
        watchesNotDisarmedBeforePendingEntry=True,noPreRestoreActiveVmInvented=True,
        thinVmIdentityAndContextServicesControlled=True,newOriginalProcesses=0,originalMemoryWrites=0,gameImplementationInvoked=False,
        producerSha256=SHA(source),toolSha256=SHA(Path(__file__).read_bytes()),retainedReportSha256=SHA((native/'report.json').read_bytes()),
        completeGame=False,nativeEquivalent=False)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
