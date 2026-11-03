"""Add observed normal-VM identity and template-copy progress to store events."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists()
    parent=R/'tools/th14-prepare-replay-rng-store-observer-nov04.py'
    subprocess.run([sys.executable,'-X','utf8',str(parent),'--output',str(out)],cwd=R,check=True,capture_output=True)
    before=(out/'prepared.json').read_bytes();prepared=json.loads(before);source=out/'observer.py';text=source.read_text(encoding='utf8')
    assert sha(source.read_bytes())==prepared['observerSha256'];(out/'parent-prepared.json').write_bytes(before)
    old='assert opt.worker_rng_events and opt.worker_main_context and not opt.normal_vm_window_events'
    assert text.count(old)==1;text=text.replace(old,'assert opt.worker_rng_events and opt.worker_main_context and opt.normal_vm_window_events and opt.worker_active_vm_snapshot')
    marker='    replay_store_events.append(row)';assert text.count(marker)==1
    extra='''    row['normalVmCallAtWorkerStore']=dict(observedCall=normal_vm_active,
        actualNormalCallEdgeWatched=True,mainCallEntryPc=0x47e65b,mainCallReturnPc=0x47e660,
        mainReturnEdgePending=main_regs['eip']==0x47e660,mainCallEdgePending=main_regs['eip']==0x47e65b,
        snapshot=worker_vm_snapshot(normal_vm_active),providedToEngine=False)
    if main_regs['eip']==0x40af28:
        assert read(0x40af28,2)==bytes.fromhex('f3a5')
        remaining=main_regs['ecx'];assert remaining<=0x150
        copied=(0x150-remaining)*4;destination=main_regs['ebx'];template=main_regs['esi']-copied
        assert main_regs['edi']==destination+copied and main_regs['esp']==main_regs['ebp']-12
        source_bytes=read(template,0x5cc);destination_bytes=read(destination,0x5cc)
        row['mainTemplateCopy']=dict(pc=0x40af28,source=template,destination=destination,
            copiedBytes=copied,remainingDwords=remaining,totalDwords=0x150,
            requestedScript=u32(main_regs['ebp']+12),callerReturnPc=u32(main_regs['ebp']+4),
            sourceFile=struct.unpack_from('<H',source_bytes,0x36)[0],
            sourceScript=struct.unpack_from('<H',source_bytes,0x4aa)[0],
            sourceVmHex=source_bytes.hex(),destinationVmHex=destination_bytes.hex(),
            destinationPartiallyInitialized=True,readOnly=True,providedToEngine=False)
'''
    text=text.replace(marker,extra+marker);compile(text,str(source),'exec');source.write_bytes(text.encode())
    prepared.update(observerSha256=sha(text.encode()),preparerSha256=sha(Path(__file__).read_bytes()),
                    parentPreparerSha256=sha(parent.read_bytes()),normalVmIdentityObservedAtActualCallEdges=True,
                    templateCopyProgressObservedOnlyAtOriginal40af28=True,templateSourceAndPartialDestinationCaptured=True,
                    nativeVmOrRngValuesProvidedToEngine=False)
    (out/'prepared.json').write_bytes((json.dumps(prepared,indent=2)+'\n').encode());print(json.dumps(prepared))


if __name__=='__main__':main()
