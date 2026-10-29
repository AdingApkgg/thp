"""Observe the original first-signature allocation call before the ASCII call.

Reuses the startup main-thread DR0 slot; no software breakpoint or additional
simultaneous hardware breakpoint is installed. All native values stay private.
"""
from pathlib import Path
import argparse, ast, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    assert out.is_relative_to(ROOT/'artifacts/th14') and not out.exists()
    base = ROOT/'tools/th14-native-campaign-observer-oct25.py'; raw = base.read_bytes()
    s = raw.decode().replace('\r\n','\n'); patches = []

    def replace(old,new,label):
        nonlocal s
        assert s.count(old)==1,label
        s=s.replace(old,new); patches.append(label)

    replace('root=Path(__file__).resolve().parents[1]', 'root=Path('+repr(str(ROOT))+')', 'privateWorkspaceRoot')
    replace('ascii_create_invocations=[]', "ascii_create_invocations=[];signature_create_invocations=[]\ntargets[0x4446a1]='startup-signature-first-allocation-call'", 'signatureStorageAndTarget')
    replace('if first_snapshot is None and tid==pi.tid and not ascii_create_invocations:addresses[0]=0x44477a',
            'if first_snapshot is None and tid==pi.tid and not ascii_create_invocations:addresses[0]=0x44477a if signature_create_invocations else 0x4446a1', 'reuseStartupDr0')
    old='                        elif pc==0x44477a:'
    new='''                        elif pc==0x4446a1:
                            assert ev.tid==pi.tid and not signature_create_invocations and first_snapshot is None
                            regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
                            manager=u32(0x4f56cc);supervisor=u32(0x4db668);resource=u32(manager+0xbc7b10)
                            assert resource==regs['ebx'] and supervisor==regs['edi'] and u32(resource)==1
                            assert u32(supervisor+0x604)==1 and u32(supervisor+0x60c)==0
                            assert read(pc,5).hex()=='e80ab60300'
                            row=dict(event=targets[pc],pc=pc,threadId=ev.tid,hostMonotonicNs=time.monotonic_ns(),
                                mainResourceFrame=main_resource_frames,precedingPlayerCallbacks=callback_count,
                                stage=u32(0x4f58a4),readOnly=True,actualCallInstruction=True,callTarget=0x47fcb0,
                                originalInstructionBytes=read(pc,5).hex(),signatureState=1,signatureDraws=0,
                                originalResourceSlot=1,registers=regs,
                                debugRegisters=dict(zip(['dr0','dr1','dr2','dr3','dr6','dr7'],struct.unpack_from('<6I',b,4))),
                                nativeValuesProvidedToEngine=False,explicitThreadSchedulingControl=False)
                            signature_create_invocations.append(row)
                            (home/'signature-create-call-events.json').write_text(json.dumps(dict(readOnly=True,actualCallInstruction=True,rows=signature_create_invocations),indent=2)+'\\n')
''' + old
    replace(old,new,'readActualSignatureAllocationCall')
    replace('diagnosticPrefixOnly=False,asciiBeginObserved','diagnosticPrefixOnly=True,asciiBeginObserved','finitePrefixScope')
    replace("    (home/'report.json').write_text", "    report.update(signatureCreateInvocations=signature_create_invocations,signatureCreationObservedAtActualCallInstruction=bool(signature_create_invocations),additionalSimultaneousBreakpoints=0,explicitThreadSchedulingControl=False,diagnosticStopReason='maximumCallbacks'if callback_count>=opt.maximum_callbacks else 'naturalEnd'if complete else 'errorOrBudget',fullReplayAccepted=False)\n    (home/'report.json').write_text",'signatureReport')
    replace('if error or not complete:raise SystemExit(1)','if error or (not complete and callback_count<opt.maximum_callbacks):raise SystemExit(1)','declaredPrefixExit')
    ast.parse(s); out.mkdir(parents=True); generated=s.encode(); (out/'observer.py').write_bytes(generated)
    proof=dict(baseObserverPath=base.relative_to(ROOT).as_posix(),baseObserverSha256=SHA(raw),generatedObserverSha256=SHA(generated),preparerSha256=SHA(Path(__file__).read_bytes()),exactCompositionSteps=patches,signatureCallPc=0x4446a1,signatureAllocationCallTarget=0x47fcb0,reusesStartupDr0=True,additionalSimultaneousBreakpoints=0,originalProcessLaunched=False,nativeValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False)
    (out/'prepared.json').write_text(json.dumps(proof,indent=2)+'\n'); print(json.dumps(proof))


if __name__=='__main__': main()
