"""Read actual Application-written TH14 files using the original x86 codecs.

No original process is launched or controlled. Unicorn executes the unmodified
decryptor, LZSS, score loader and score writer with declared CRT boundaries.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EDI

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();source=args.save.resolve(strict=True);out=args.output.resolve()
    assert source.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
    out.mkdir(parents=True)
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,address,size,offset,length in img.sections:
        first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first);m.mem_write(address,img.data[offset:offset+length])
    base=0x71000000;m.mem_map(base,0x1000000)
    packed_at,decoded_at,manager,header,stack,ret=base+0x1000,base+0x100000,base+0x200000,base+0x240000,base+0xffd000,base+0xffe000
    heap=[base+0x400000]
    def put(pointer,value):m.mem_write(pointer,struct.pack('<I',value&0xffffffff))
    def get(pointer):return struct.unpack('<I',m.mem_read(pointer,4))[0]
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP);value=0
        if address==0x485540:
            length=get(sp+4);value=heap[0];heap[0]+=(length+15)&~15;assert heap[0]<stack;m.mem_write(value,bytes(length))
        elif address==0x487620:
            value=get(sp+4);m.mem_write(value,bytes(m.mem_read(get(sp+8),get(sp+12))))
        elif address==0x48f980:
            value=get(sp+4);m.mem_write(value,bytes([get(sp+8)&255])*get(sp+12))
        m.reg_write(UC_X86_REG_EAX,value);m.reg_write(UC_X86_REG_ESP,sp+4);m.reg_write(UC_X86_REG_EIP,get(sp))
    for address in [0x485540,0x487620,0x48f980,0x4855d2]:m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    def run(address,ecx,edx=0,arguments=(),stop=ret):
        put(stack,ret)
        for index,value in enumerate(arguments):put(stack+4+index*4,value)
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_EDX,edx)
        for _ in range(30):
            m.emu_start(address,stop,count=100000000)
            if m.reg_read(UC_X86_REG_EIP)==stop:return
            address=m.reg_read(UC_X86_REG_EIP)
        raise AssertionError('Native codec instruction budget exhausted')
    def unpack(data,offset,packed,unpacked,passes):
        assert 0<packed<0xf0000 and 0<unpacked<0x100000 and offset+packed<=len(data)
        heap[0]=base+0x400000;m.mem_write(packed_at,data[offset:offset+packed]);m.mem_write(decoded_at,bytes(unpacked));m.mem_write(0x4f36c8,bytes(8192))
        for key,step,block in passes:run(0x4028e0,packed_at,packed,(key,step,block,packed))
        run(0x465840,packed_at,packed,(decoded_at,unpacked))
        return bytes(m.mem_read(decoded_at,unpacked))
    replay=(source/'replay/th14_01.rpy').read_bytes();assert replay[:6]==b't13r\x02\x00'
    packed,unpacked=struct.unpack_from('<II',replay,0x1c);declared=struct.unpack_from('<I',replay,0xc)[0];assert declared==0x24+packed
    decoded=unpack(replay,0x24,packed,unpacked,[(0x5c,0xe1,0x400),(0x7d,0x3a,0x100)])
    count,character,subtype,difficulty=struct.unpack_from('<4I',decoded,0x78);assert(count,character,subtype,difficulty)==(1,2,1,0)
    stage,seed=struct.unpack_from('<HH',decoded,0x94);frames,payload=struct.unpack_from('<II',decoded,0x98)
    (out/'replay-decoded.bin').write_bytes(decoded)
    assert stage==1 and frames==128 and payload==frames*6+5 and len(decoded)==0x94+0xdc+payload,(stage,frames,payload,len(decoded))
    inputs=decoded[0x94+0xdc:0x94+0xdc+frames*6];fps=decoded[-5:]
    assert inputs[:-6]==bytes(127*6)and inputs[-6:]==b'\xff'*6 and len(fps)==5
    score=(source/'scoreth14.dat').read_bytes();assert struct.unpack_from('<4I',score)==(0x31344854,len(score),5,0x100)
    packed,unpacked=struct.unpack_from('<II',score,16);assert unpacked==0x24654 and len(score)==24+packed
    score_decoded=unpack(score,24,packed,unpacked,[(0xac,0x35,0x10)])
    position=0
    for index in range(8):
        kind,checksum,length=struct.unpack_from('<3I',score_decoded,position)
        assert(kind,length)==((0x15243,0x5298)if index<7 else(0x15453,0x42c))
        record=score_decoded[position:position+length];assert sum(record[8:])&0xffffffff==checksum
        if index<7:assert struct.unpack_from('<I',record,12)[0]==index
        else:assert record[12:20]==b'A       '
        position+=length
    assert position==len(score_decoded)
    m.mem_write(header,score);put(manager,header);put(0x4db68c,manager);m.mem_write(manager+8,b'\x5a'*len(score_decoded));m.mem_write(0x4f36c8,bytes(8192));heap[0]=base+0x400000
    run(0x456de0,manager)
    loaded=bytes(m.mem_read(manager+8,len(score_decoded)));assert loaded==score_decoded
    heap[0]=base+0x400000;run(0x456f60,manager,stop=0x457086)
    rewritten=bytes(m.mem_read(header,24))+bytes(m.mem_read(m.reg_read(UC_X86_REG_EDI),get(header+16)));assert rewritten==score
    (out/'score-decoded.bin').write_bytes(score_decoded)
    result=dict(verifiedFiniteNativeCodecEvidence=True,replay=dict(bytes=len(replay),sha256=SHA(replay),decodedBytes=len(decoded),decodedSha256=SHA(decoded),stageCount=count,character=character,subtype=subtype,difficulty=difficulty,stage=stage,seed=seed,frames=frames,gameplayFrames=127,terminalSentinels=1,fpsSamples=5,inputBytes=len(inputs),allGameplayInputsZero=True),score=dict(bytes=len(score),sha256=SHA(score),decodedBytes=len(score_decoded),decodedSha256=SHA(score_decoded),allEightRecordChecksumsValid=True,originalFullLoaderBytesEqual=True,originalFullWriterBytesEqual=True,lastName='A       '),nativeExecutableSha256=SHA(img.data),toolSha256=SHA(Path(__file__).read_bytes()),originalProcessLaunched=False,instructionBytesPatched=0,controlledBoundaries=['CRT malloc/free/memcpy/memset','zero-filled codec dictionary at independent file startup'],scope='Original x864028e0 and465840 read the actual Application-written replay and score;456de0 loads all149076 score bytes and456f60 rewrites the whole score identically. Normalized input fixture recorded127 idle frames, then one six-byte terminal sentinel and five FPS samples. No original full replay playback, ordinary original UI, OS persistence, physical input, GPU/audio or browser equivalence.',completeGame=False,nativeEquivalent=False)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
