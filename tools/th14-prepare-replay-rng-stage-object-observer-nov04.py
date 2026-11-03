"""Observe the actual detached Stage object VM call/return during worker wait."""
from pathlib import Path
import argparse,hashlib,importlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    sys.path.insert(0,str(R/'tools'));img=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(img.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert img.read(0x40f290,23).hex()=='0fbf7e0669ffcc05000003b9080200008bcfe8a90b0600'
    assert img.read(0x40f2a7,4).hex()=='837f2800'
    parent=R/'tools/th14-prepare-replay-rng-store-vm-observer-nov04.py'
    subprocess.run([sys.executable,'-X','utf8',str(parent),'--output',str(out)],cwd=R,check=True,capture_output=True)
    previous=(out/'prepared.json').read_bytes();prepared=json.loads(previous);source=out/'observer.py';text=source.read_text(encoding='utf8')
    assert sha(source.read_bytes())==prepared['observerSha256'];(out/'normal-edge-parent-prepared.json').write_bytes(previous)
    text=text.replace('0x47e65b','0x40f2a2').replace('0x47e660','0x40f2a7')
    text=text.replace('normal_vm','stage_object_vm').replace('normal-vm','stage-object-vm').replace('normalVm','stageObjectVm')
    old="call=read(0x40f2a2,7)";assert text.count(old)==1;text=text.replace(old,"call=read(0x40f2a2,5)")
    old="and call[5:]==b'\\x85\\xc0'";assert text.count(old)==1;text=text.replace(old,"and read(0x40f2a7,4)==bytes.fromhex('837f2800')")
    old="vm=struct.unpack_from('<I',b,160)[0]";assert text.count(old)==1;text=text.replace(old,"vm=struct.unpack_from('<I',b,156)[0]")
    marker="        if getattr(opt,'worker_active_vm_snapshot',False):row['rawVmHexAtCallEdge']=blob.hex()";assert text.count(marker)==1
    extra='''        frame=struct.unpack_from('<I',b,180)[0];primitive=struct.unpack_from('<I',b,160)[0]
        owner=u32(frame-4);object_index=u32(frame-8);object_address=u32(frame-12);array=u32(owner+0x208)
        assert vm>=array and (vm-array)%0x5cc==0
        animation=(vm-array)//0x5cc;primitive_header=read(primitive,8)
        assert animation==struct.unpack_from('<h',primitive_header,6)[0]
        cursor=object_address+0x1c;primitive_index=0
        while cursor!=primitive:
            header=read(cursor,8);kind,length=struct.unpack_from('<hh',header)
            assert kind>=0 and length>=8 and primitive_index<256 and cursor<primitive
            cursor+=length;primitive_index+=1
        row['stageObjectContext']=dict(owner=owner,array=array,objectIndex=object_index,
            primitiveIndex=primitive_index,animationIndex=animation,objectAddress=object_address,
            primitiveAddress=primitive,rawPrimitiveHex=primitive_header.hex(),rawOwnerPrefixHex=read(owner,32).hex(),
            rawCallerFrameHex=read(frame-12,44).hex(),actualVmArrayAndPrimitiveIndexAgree=True,
            currentExecutingObjectIdentityObserved=True,readOnly=True,providedToEngine=False)
'''
    text=text.replace(marker,marker+'\n'+extra);compile(text,str(source),'exec');source.write_bytes(text.encode())
    prepared.update(observerSha256=sha(text.encode()),preparerSha256=sha(Path(__file__).read_bytes()),stageObjectParentPreparerSha256=sha(parent.read_bytes()),
        stageObjectVmCallPc=0x40f2a2,stageObjectVmReturnPc=0x40f2a7,
        objectAndPrimitiveAndAnimationIndicesObserved=True,normalVmIdentityObservedAtActualCallEdges=False,
        extraHardwareBreakpointsBoundedToWorkerWait=True,originalInstructionsPatched=False,nativeValuesProvidedToEngine=False)
    (out/'prepared.json').write_bytes((json.dumps(prepared,indent=2)+'\n').encode());print(json.dumps(prepared),flush=True)


if __name__=='__main__':main()
