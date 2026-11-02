"""Execute both original CRT free entry paths to a synthetic HeapFree boundary."""
from pathlib import Path
import argparse, hashlib, importlib, json, struct, sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools'))
image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert image.read(0x4854fe,5).hex() == 'e9cf000000'
assert image.read(0x4855d2,9).hex() == '558bec837d0800742d'
assert image.read(0x4855e6,6).hex() == 'ff15e8114b00'
pe = struct.unpack_from('<I',image.data,0x3c)[0]
directory = image.image_base + struct.unpack_from('<I',image.data,pe+0x18+0x68)[0]
resolved = None
for j in range(200):
    oft,_,_,name,first = struct.unpack('<5I',image.read(directory+j*20,20))
    if not any([oft,name,first]): break
    dll=image.cstring(image.image_base+name); thunk=image.image_base+(oft or first)
    for k in range(1000):
        value=image.u32(thunk+k*4)
        if not value: break
        if image.image_base+first+k*4 == 0x4b11e8:
            assert not value&0x80000000 and resolved is None
            resolved=(dll,image.cstring(image.image_base+value+2))
assert resolved == ('KERNEL32.dll','HeapFree')
direct = [0x4029d3,0x402aeb,0x407506,0x40b7ef,0x40b80c]
for call in direct:
    data=image.read(call,5)
    assert data[0]==0xe8 and (call+5+int.from_bytes(data[1:],'little',signed=True))&0xffffffff==0x4855d2
cases=[]
for entry in (0x4854fe,0x4855d2):
    for pointer in (0x70002000,0):
        m=Uc(UC_ARCH_X86,UC_MODE_32)
        for _,va,size,offset,count in image.sections:
            page=va&~4095
            m.mem_map(page,((va+size+4095)&~4095)-page)
            m.mem_write(va,image.data[offset:offset+count])
        m.mem_map(0x70000000,0x100000)
        stack=0x700ff000; sentinel=0x70001000; heap=0x70003000; stub=0x70004000
        m.mem_write(0x4b11e8,struct.pack('<I',stub));m.mem_write(0x4dafec,struct.pack('<I',heap))
        m.mem_write(stack,struct.pack('<2I',sentinel,pointer));m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(entry,stub if pointer else sentinel,count=100)
        if pointer:
            assert m.reg_read(UC_X86_REG_EIP)==stub
            sp=m.reg_read(UC_X86_REG_ESP)
            assert struct.unpack('<4I',m.mem_read(sp,16))==(0x4855ec,heap,0,pointer)
            m.reg_write(UC_X86_REG_EAX,1);m.reg_write(UC_X86_REG_ESP,sp+16)
            m.emu_start(0x4855ec,sentinel,count=100)
        assert m.reg_read(UC_X86_REG_EIP)==sentinel
        cases.append(dict(entry=hex(entry),syntheticNullPointer=not bool(pointer),heapFreeBoundaryReached=bool(pointer),returnedToSyntheticCaller=True))
result=dict(verifiedOriginalCommonFreeSite=True,originalExecutableSha256=sha(image.data),wrapperJumpsToCommonEntry=True,directCallExamples=[hex(x) for x in direct],heapFreeImport='KERNEL32.dll!HeapFree',actualOriginalInstructionsExecuted=True,cases=cases,operatingSystemHeapFreeExecuted=False,freeSuccessInRealProcessProved=False,originalFullHeapHistoryProved=False,nativeValuesProvidedToEngine=False,productionCodeChanged=False,completeGame=False,nativeEquivalent=False,toolSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-crt-common-free-site-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(R/'artifacts/th14');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check: assert out.read_bytes()==data
else: assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
