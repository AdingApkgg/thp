"""Execute the original VM call with a declared synthetic pre-update callback."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ESI
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    output=a.output.resolve();assert output.is_relative_to(R/'artifacts/th14')and not output.exists()
    sys.path.insert(0,str(R/'tools'));img=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(img.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    profiles=[]
    for initial in(0,1,0xffffffff):
        m=Uc(UC_ARCH_X86,UC_MODE_32)
        for _,address,size,offset,count in img.sections:
            first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first);m.mem_write(address,img.data[offset:offset+count])
        base=0x70000000;callback=base+0x1000;marker=base+0x4e0;m.mem_map(base,0x20000)
        # A synthetic callback changes a marker, without touching retail code.
        m.mem_write(callback,bytes.fromhex('ff81e004000031c0c3'));m.mem_write(marker,struct.pack('<I',initial))
        m.mem_write(base+0x5b8,struct.pack('<I',callback));m.mem_write(base+0x28,struct.pack('<I',base+0x2000))
        m.mem_write(base+0x18,struct.pack('<I',0x100000));m.mem_write(0x4d8f58,struct.pack('<f',1))
        m.reg_write(UC_X86_REG_ESI,base);m.reg_write(UC_X86_REG_ESP,base+0x1f000)
        events=[]
        def observe(machine,pc,size,data):
            if pc in(0x47e65b,callback):events.append(dict(pc=pc,marker=struct.unpack('<I',machine.mem_read(marker,4))[0]))
        m.hook_add(UC_HOOK_CODE,observe);m.emu_start(0x47e659,0x47e660,count=20000)
        after=struct.unpack('<I',m.mem_read(marker,4))[0]
        assert events==[dict(pc=0x47e65b,marker=initial),dict(pc=callback,marker=initial)]and after==(initial+1)&0xffffffff
        profiles.append(dict(initial=initial,beforeCall=initial,afterReturn=after,events=events))
    result=dict(verifiedOriginalPreUpdateInsideVmCall=True,profiles=profiles,originalInstructionsUnmodified=True,
        syntheticVmStackCallbackAndMarker=True,ordinaryGameTimingAccepted=False,completeGame=False,nativeEquivalent=False,
        executableSha256=sha(img.data),toolSha256=sha(Path(__file__).read_bytes()))
    output.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result),flush=True)


if __name__=='__main__':main()
