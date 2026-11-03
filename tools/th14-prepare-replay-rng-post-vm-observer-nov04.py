"""Retain verified post-script VM contexts at the existing worker store stops."""
from pathlib import Path
import argparse, hashlib, importlib, json, subprocess, sys
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    sys.path.insert(0,str(R/'tools'));img=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(img.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    signatures={0x473c8c:'83be50030000007411',0x473253:'0f2ec49ff6c444'}
    for pc,signature in signatures.items():assert img.read(pc,len(signature)//2).hex()==signature
    parent=R/'tools/th14-prepare-replay-rng-template-observer-nov04.py'
    subprocess.run([sys.executable,'-X','utf8',str(parent),'--output',str(out)],cwd=R,check=True,capture_output=True)
    previous=(out/'prepared.json').read_bytes();prepared=json.loads(previous);source=out/'observer.py';text=source.read_text(encoding='utf8')
    assert sha(source.read_bytes())==prepared['observerSha256'];(out/'template-parent-prepared.json').write_bytes(previous)
    marker='    replay_store_events.append(row)';assert text.count(marker)==1
    extra='''    vm_register={0x473c93:'esi',0x473253:'ecx'}.get(main_regs['eip'])
    if vm_register is not None:
        signatures={0x473c8c:'83be50030000007411',0x473253:'0f2ec49ff6c444'}
        for address,signature in signatures.items():assert read(address,len(signature)//2).hex()==signature
        vm=main_regs[vm_register];blob=read(vm,0x5cc);frames=[];frame=main_regs['ebp']
        for depth in range(4):
            if frame&3 or not main_regs['esp']<=frame<main_regs['esp']+0x10000:break
            frame_bytes=read(frame,32);saved,returned=struct.unpack_from('<II',frame_bytes)
            frames.append(dict(frame=frame,savedFrame=saved,returnPc=returned,rawFrameHex=frame_bytes.hex()))
            if saved<=frame:break
            frame=saved
        row['mainAnimationVmAtWorkerStore']=dict(pc=main_regs['eip'],register=vm_register,vm=vm,
            file=struct.unpack_from('<H',blob,0x36)[0],script=struct.unpack_from('<H',blob,0x4aa)[0],
            handle=struct.unpack_from('<I',blob,0x540)[0],instructionPointer=struct.unpack_from('<I',blob,0x28)[0],
            rawVmHex=blob.hex(),frameChain=frames,normalCallReturnInFrameChain=any(x['returnPc']==0x47e660 for x in frames),
            snapshotAtThisWorkerEventOnly=True,readOnly=True,providedToEngine=False)
'''
    text=text.replace(marker,extra+marker);compile(text,str(source),'exec');source.write_bytes(text.encode())
    prepared.update(observerSha256=sha(text.encode()),preparerSha256=sha(Path(__file__).read_bytes()),
        postVmParentPreparerSha256=sha(parent.read_bytes()),postScriptVmRegisters={'0x473c93':'esi','0x473253':'ecx'},
        executableSignatures={hex(pc):signature for pc,signature in signatures.items()},
        boundedFrameChainDepth=4,noAdditionalMainThreadBreakpoints=True,nativeValuesProvidedToEngine=False)
    (out/'prepared.json').write_bytes((json.dumps(prepared,indent=2)+'\n').encode());print(json.dumps(prepared),flush=True)


if __name__=='__main__':main()
