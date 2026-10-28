"""Decode a specified replay using retail TH14 crypto/LZSS instruction bodies.

Fresh zero dictionary and CRT allocation/copy/free are controlled component
boundaries. No original filesystem, GPU, process scheduling or playback claim.
"""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,time
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_EAX,UC_X86_REG_EIP
R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();source=a.input.resolve(strict=True);O=a.output.resolve()
    assert O.is_relative_to(R/'artifacts/th14') and not O.exists();O.mkdir(parents=True)
    data=source.read_bytes();assert data[:6]==b't13r\x02\0' and len(data)>=0x24
    packed,unpacked=struct.unpack_from('<II',data,0x1c);declared=struct.unpack_from('<I',data,0xc)[0]
    assert declared==0x24+packed<=len(data) and packed<512*1024 and 0<unpacked<6*1024*1024
    image,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,offset,length in image.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[offset:offset+length])
    base=0x70000000;m.mem_map(base,16*1024*1024)
    src,dst,stack=base+0x1000,base+1024*1024,base+15*1024*1024;heap=[base+8*1024*1024];calls=[]
    def put(pointer,value):m.mem_write(pointer,struct.pack('<I',value&0xffffffff))
    def get(pointer):return struct.unpack('<I',m.mem_read(pointer,4))[0]
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP);result=0
        if address==0x485540:
            length=get(sp+4);result=heap[0];heap[0]+=(length+15)&~15;assert heap[0]<stack-4096;m.mem_write(result,bytes(length))
        elif address==0x487620:
            result=get(sp+4);m.mem_write(result,bytes(m.mem_read(get(sp+8),get(sp+12))))
        m.reg_write(UC_X86_REG_EAX,result);m.reg_write(UC_X86_REG_ESP,sp+4);m.reg_write(UC_X86_REG_EIP,get(sp))
    for address in (0x485540,0x487620,0x4855d2):m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    def run(address,ecx,edx,args):
        put(stack,base)
        for index,value in enumerate(args):put(stack+4+index*4,value)
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_EDX,edx)
        m.emu_start(address,base,count=50000000);assert m.reg_read(UC_X86_REG_EIP)==base
        calls.append(hex(address))
    start=time.monotonic();m.mem_write(src,data[0x24:declared]);m.mem_write(0x4f36c8,bytes(8192));m.mem_write(dst,bytes(unpacked+32))
    run(0x4028e0,src,packed,(0x5c,0xe1,0x400,packed));run(0x4028e0,src,packed,(0x7d,0x3a,0x100,packed));run(0x465840,src,packed,(dst,unpacked))
    decoded=bytes(m.mem_read(dst,unpacked))
    mirror_path=R/'tools/th-replay-container.py';ns={};exec(compile(mirror_path.read_text().partition('if __name__')[0],str(mirror_path),'exec'),ns)
    assert decoded==ns['decode_with'](data,packed,unpacked,ns['TH13'])
    count,character,subtype,difficulty=struct.unpack_from('<4I',decoded,0x78)
    assert 1<=count<=7 and character<=2 and subtype<=1 and difficulty<=4
    stages=[];offset=0x94
    for index in range(count):
        stage,seed,frames,payload=struct.unpack_from('<HHII',decoded,offset)
        assert 1<=stage<=7 and frames*6<=payload and offset+0xdc+payload<=len(decoded)
        stages.append(dict(stage=stage,seed=seed,frames=frames,payloadBytes=payload,
            headerSha256=SHA(decoded[offset:offset+0xdc]),payloadSha256=SHA(decoded[offset+0xdc:offset+0xdc+payload])))
        offset+=0xdc+payload
    assert offset==len(decoded)
    (O/'decoded.bin').write_bytes(decoded)
    result=dict(passed=True,inputBytes=len(data),inputSha256=SHA(data),packedBytes=packed,decodedBytes=len(decoded),decodedSha256=SHA(decoded),
        nativeExecutableSha256=SHA(image.data),nativeEntryPoints=calls,actualRetailInstructionBodies=True,controlledCrtBoundaries=True,
        freshZeroDictionary=True,allDecodedBytesEqualIndependentPythonMirror=True,nameHex=decoded[:8].hex(),
        stageCount=count,character=character,subtype=subtype,difficulty=difficulty,stages=stages,
        trailingBytes=len(data)-declared,trailingSha256=SHA(data[declared:]),
        mirrorSha256=SHA(mirror_path.read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),elapsedSeconds=time.monotonic()-start,
        nativeFilesystemOrPlaybackAcceptance=False,completeGame=False,nativeEquivalent=False)
    (O/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
