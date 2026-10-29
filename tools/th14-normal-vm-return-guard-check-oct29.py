"""Exercise the actual observer return handler using the retained failure order.

Only the event handler AST is executed. Process/context/memory services are
declared test inputs; this never starts or controls an original process.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse,ast,hashlib,json,struct

R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    native=a.native.resolve(strict=True);out=a.output.resolve()
    assert native.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')and not out.exists()
    report=json.loads((native/'report.json').read_bytes());assert report['error']=='AssertionError()'
    rows=[json.loads(line)for line in (native/'normal-vm-window-events.jsonl').read_text().splitlines()]
    entry=rows[-1];assert entry['pc']==0x47e65b
    restored=next(row for row in report['transitionEvents']if row.get('normalVmCallWindowAtSeedRestore',{}).get('activeCall')==entry)
    assert restored['mainThreadPcAtWorkerEvent']==0x47e660 and restored['hostMonotonicNs']>entry['hostMonotonicNs']
    out.mkdir(parents=True)
    # This thin declared fixture contains only fields the handler reads. It is
    # not an observed full VM and is never supplied to a game implementation.
    blob=bytearray(0x5cc)
    for at,value,fmt in [(0x36,entry['file'],'H'),(0x4aa,entry['script'],'H'),(0x540,entry['handle'],'I')]:struct.pack_into('<'+fmt,blob,at,value)
    exe=(native/'work/th14.exe').read_bytes();assert SHA(exe)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    pe=struct.unpack_from('<I',exe,60)[0];opt=pe+24;base=struct.unpack_from('<I',exe,opt+28)[0];table=opt+struct.unpack_from('<H',exe,pe+20)[0]
    def instruction(pc,size):
        for at in range(table,table+40*struct.unpack_from('<H',exe,pe+6)[0],40):
            vs,va,length,offset=struct.unpack_from('<IIII',exe,at+8)
            if va<=pc-base<va+max(vs,length):return exe[offset+pc-base-va:offset+pc-base-va+size]
        raise AssertionError(hex(pc))
    def read(address,size):
        if address in (0x47e65b,0x47e660):return instruction(address,size)
        if address==entry['vm']and size==len(blob):return bytes(blob)
        if address==0x4db508 and size==16:return bytes.fromhex(restored['rngHex'])
        raise AssertionError((hex(address),size))
    producer=R/'tools/th14-native-campaign-observer-oct25.py';source=producer.read_bytes();tree=ast.parse(source)
    handler=next(node for node in tree.body if isinstance(node,ast.FunctionDef)and node.name=='event_snapshot')
    namespace=dict(struct=struct,json=json,time=SimpleNamespace(monotonic_ns=lambda:restored['hostMonotonicNs']+1),
        read=read,u32=lambda address:entry['stage']if address==0x4f58a4 else None,home=out,
        pi=SimpleNamespace(tid=entry['threadId']),opt=SimpleNamespace(normal_vm_window_events=True),
        targets={0x47e65b:'normal-vm-before-original-call',0x47e660:'normal-vm-after-original-return'},
        normal_vm_window_tid=entry['workerThreadId'],normal_vm_active=entry,normal_vm_closing_restore=restored['hostMonotonicNs'],
        normal_vm_events=list(rows),callback_count=entry['precedingPlayerCallbacks'],storage_budget=lambda:None)
    exec(compile(ast.Module(body=[handler],type_ignores=[]),str(producer),'exec'),namespace)
    context=bytearray(716);struct.pack_into('<I',context,160,entry['vm']);struct.pack_into('<I',context,172,entry['vm'])
    invoke=lambda pc:namespace['event_snapshot'](pc,entry['threadId'],context)
    invoke(0x47e660)
    assert namespace['normal_vm_window_tid']is None and namespace['normal_vm_active']is None and namespace['normal_vm_closing_restore']is None
    after=namespace['normal_vm_events'][-1]
    assert after['callEntryOrdinal']==entry['ordinal']and after['returnPcAlreadyObservedAtSeedRestore']and after['restoreEventDeliveredEarlier']
    assert after['restoreObservationHostNs']==restored['hostMonotonicNs']
    rejected=[]
    for name in ['disarmed-before-call','mismatched-return-owner']:
        namespace['normal_vm_window_tid']=None if name=='disarmed-before-call'else entry['workerThreadId']
        namespace['normal_vm_active']=dict(entry,vm=entry['vm']+4)
        count=len(namespace['normal_vm_events'])
        try:invoke(0x47e65b if name=='disarmed-before-call'else 0x47e660)
        except AssertionError:rejected.append(name)
        else:raise AssertionError(name+' accepted')
        assert len(namespace['normal_vm_events'])==count
    namespace.update(normal_vm_window_tid=entry['workerThreadId'],normal_vm_active=None,normal_vm_closing_restore=None)
    invoke(0x47e65b);invoke(0x47e660)
    assert namespace['normal_vm_window_tid']==entry['workerThreadId']and namespace['normal_vm_active']is None and namespace['normal_vm_closing_restore']is None
    result=dict(passed=True,actualObserverHandlerAst=True,retainedOriginalNegativeOrderUsed=True,
        returnPcAlreadyObserved=0x47e660,pendingReturnDrained=True,nextWindowCallPairPassed=True,rejected=rejected,
        syntheticContextAndThinMemoryServices=True,newOriginalProcessRuns=0,originalMemoryWrites=0,gameImplementationInvoked=False,
        producerSha256=SHA(source),toolSha256=SHA(Path(__file__).read_bytes()),
        retainedReportSha256=SHA((native/'report.json').read_bytes()),retainedEdgesSha256=SHA((native/'normal-vm-window-events.jsonl').read_bytes()),
        privateControlLogSha256=SHA((out/'normal-vm-window-events.jsonl').read_bytes()),completeGame=False,nativeEquivalent=False)
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
