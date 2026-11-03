"""Read current pool VM candidates from registers/stack at worker store events."""
from pathlib import Path
import argparse,hashlib,importlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    sys.path.insert(0,str(R/'tools'));img=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(img.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    signatures={0x47f10f:'69c9e4050000',0x47f115:'80bc31b806000000',0x47f11f:'3984311c060000'}
    for pc,signature in signatures.items():assert img.read(pc,len(signature)//2).hex()==signature
    parent=R/'tools/th14-prepare-replay-rng-post-vm-observer-nov04.py'
    subprocess.run([sys.executable,'-X','utf8',str(parent),'--output',str(out)],cwd=R,check=True,capture_output=True)
    previous=(out/'prepared.json').read_bytes();prepared=json.loads(previous);source=out/'observer.py';text=source.read_text(encoding='utf8')
    assert sha(source.read_bytes())==prepared['observerSha256'];(out/'post-vm-parent-prepared.json').write_bytes(previous)
    marker='    replay_store_events.append(row)';assert text.count(marker)==1
    extra='''    manager=u32(0x4f56cc);pool_base=manager+0xdc;stride=0x5e4;aliases={}
    def candidate(value,alias):
        delta=value-pool_base
        if delta<0 or delta%stride or delta//stride>=8191:return
        aliases.setdefault(value,[]).append(alias)
    for register in ('edi','esi','ebx','edx','ecx','eax','ebp','esp'):candidate(main_regs[register],register)
    stack=bytes.fromhex(row['mainThreadContextAtWorkerDebugEvent']['stackHex'])
    for offset in range(0,len(stack),4):candidate(struct.unpack_from('<I',stack,offset)[0],'esp+'+str(offset))
    frames=[];frame=main_regs['ebp'];frame_error=None
    for depth in range(4):
        if frame&3 or not main_regs['esp']<=frame<main_regs['esp']+0x10000:break
        try:frame_raw=read(frame,32)
        except (AssertionError,OSError)as error:frame_error=str(error);break
        saved,returned=struct.unpack_from('<II',frame_raw);frames.append(dict(frame=frame,savedFrame=saved,returnPc=returned,rawFrameHex=frame_raw.hex()))
        for offset in range(0,32,4):candidate(struct.unpack_from('<I',frame_raw,offset)[0],'frame'+str(depth)+'+'+str(offset))
        if saved<=frame:break
        frame=saved
    candidates=[]
    for vm,names in aliases.items():
        raw=read(vm,stride);slot=(vm-pool_base)//stride
        candidates.append(dict(vm=vm,slot=slot,aliases=names,rawPoolEntryHex=raw.hex(),
            poolUsed=raw[0x5dc],handle=struct.unpack_from('<I',raw,0x540)[0],
            storedSlot=struct.unpack_from('<I',raw,0x544)[0],file=struct.unpack_from('<H',raw,0x36)[0],
            script=struct.unpack_from('<H',raw,0x4aa)[0],instructionPointer=struct.unpack_from('<I',raw,0x28)[0]))
    row['mainPoolVmCandidates']=dict(manager=manager,poolBase=pool_base,stride=stride,capacity=8191,
        candidates=candidates,frameChain=frames,frameReadError=frame_error,
        boundedRegisterStackCandidates=True,onlyActualWorkerStopMemoryRead=True,
        currentExecutingVmIdentityNotAssumed=True,heapVmNotCoveredByPoolFormula=True,
        readOnly=True,providedToEngine=False)
'''
    text=text.replace(marker,extra+marker);compile(text,str(source),'exec');source.write_bytes(text.encode())
    prepared.update(observerSha256=sha(text.encode()),preparerSha256=sha(Path(__file__).read_bytes()),poolContextParentPreparerSha256=sha(parent.read_bytes()),
        poolLookupInstructionSignatures={hex(pc):signature for pc,signature in signatures.items()},nativePoolOrigin=0xdc,nativePoolStride=0x5e4,
        poolContextsReadAtExistingWorkerStopsOnly=True,additionalMainThreadBreakpoints=False,heapVmNotCoveredByPoolFormula=True)
    (out/'prepared.json').write_bytes((json.dumps(prepared,indent=2)+'\n').encode());print(json.dumps(prepared),flush=True)


if __name__=='__main__':main()
