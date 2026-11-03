"""Read typed VM/template context at worker events without main-thread VM traps."""
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
    marker='    replay_store_events.append(row)';assert text.count(marker)==1
    extra='''    row['anmManagerSerial']=u32(u32(0x4f56cc)+0xff52c8)
    if main_regs['eip']==0x470097:
        assert read(0x470090,13).hex()=='8b5f280fbf43043b874c050000'
        vm=main_regs['edi'];blob=read(vm,0x5cc)
        row['mainInterpreterDispatch']=dict(pc=0x470097,vm=vm,
            file=struct.unpack_from('<H',blob,0x36)[0],script=struct.unpack_from('<H',blob,0x4aa)[0],
            handle=struct.unpack_from('<I',blob,0x540)[0],instructionPointer=struct.unpack_from('<I',blob,0x28)[0],
            rawVmHex=blob.hex(),readOnly=True,providedToEngine=False)
    if main_regs['eip']==0x40af28:
        assert read(0x40af28,2)==bytes.fromhex('f3a5')
        remaining=main_regs['ecx'];assert remaining<=0x150
        copied=(0x150-remaining)*4;destination=main_regs['ebx'];template=main_regs['esi']-copied
        assert main_regs['edi']==destination+copied and main_regs['esp']==main_regs['ebp']-12
        source_bytes=read(template,0x5cc);destination_bytes=read(destination,0x5cc)
        frame=main_regs['ebp'];requested=u32(frame+12);caller=u32(frame+4)
        copy=dict(pc=0x40af28,source=template,destination=destination,
            copiedBytes=copied,remainingDwords=remaining,totalDwords=0x150,
            requestedScript=requested,callerReturnPc=caller,
            sourceFile=struct.unpack_from('<H',source_bytes,0x36)[0],
            sourceScript=struct.unpack_from('<H',source_bytes,0x4aa)[0],
            sourceVmHex=source_bytes.hex(),destinationVmHex=destination_bytes.hex(),
            destinationPartiallyInitialized=True,readOnly=True,providedToEngine=False)
        if caller==0x47ef08:
            assert read(0x47ef03,5).hex()=='e8f8bff8ff'
            create_frame=u32(frame);parent_vm=u32(create_frame+0x10);file_object=u32(frame-8)
            assert parent_vm==u32(frame-4) and requested==u32(create_frame+12)
            parent_bytes=read(parent_vm,0x5cc)
            assert struct.unpack_from('<I',parent_bytes,0x30)[0]==file_object
            assert u32(file_object+0x10c)+requested*0x5cc==template
            instruction=struct.unpack_from('<I',parent_bytes,0x28)[0]
            copy['attachedParent']=dict(vm=parent_vm,fileObject=file_object,createFrame=create_frame,
                createCallerReturnPc=u32(create_frame+4),
                file=struct.unpack_from('<H',parent_bytes,0x36)[0],
                script=struct.unpack_from('<H',parent_bytes,0x4aa)[0],
                handle=struct.unpack_from('<I',parent_bytes,0x540)[0],instructionPointer=instruction,
                instructionHex=read(instruction,16).hex(),rawVmHex=parent_bytes.hex(),
                frameArgumentsAndSavedRegistersAgree=True,resourceAndTemplatePointersAgree=True,
                readOnly=True,providedToEngine=False)
        row['mainTemplateCopy']=copy
'''
    text=text.replace(marker,extra+marker);compile(text,str(source),'exec');source.write_bytes(text.encode())
    prepared.update(observerSha256=sha(text.encode()),preparerSha256=sha(Path(__file__).read_bytes()),
        parentPreparerSha256=sha(parent.read_bytes()),mainNormalVmCallReturnBreakpointsAdded=False,
        typedTemplateContextAt40af28=True,attachedParentReadFromVerifiedFrameArguments=True,
        typedInterpreterContextOnlyAt470097=True,nativeVmOrRngValuesProvidedToEngine=False)
    (out/'prepared.json').write_bytes((json.dumps(prepared,indent=2)+'\n').encode());print(json.dumps(prepared))


if __name__=='__main__':main()
