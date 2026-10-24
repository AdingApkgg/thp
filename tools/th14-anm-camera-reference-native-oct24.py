"""Execute original46f770 camera-variable getters without patching instructions.

Camera words and VM/stack storage are declared inputs. No native process, GPU,
audio or replay is started. The complete game is not claimed equivalent.
"""
from pathlib import Path
import hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_XMM0,UC_X86_REG_XMM1,UC_X86_REG_MXCSR

root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'))
image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
u=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,count in image.sections:
    first=base&~4095;u.mem_map(first,((base+size+4095)&~4095)-first);u.mem_write(base,image.data[raw:raw+count])
stop=0x70000000;vm=stop+0x1000;stack=stop+0x2000;u.mem_map(stop,0x4000)
word=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
inputs=[
 [17.25,-9.5,.125,3.5,-4.75,11.25,.25,.5,-.75],
 [-1000,2000,-3000,-.125,.0625,4096,1,0,-1],
 [0.,-0.,0.,-0.,0.,-0.,-0.,0.,-0.],
 [-0.,-0.,-0.,-0.,-0.,-0.,0.,-0.,1.],
 [16777216.,-16777216.,33554432.,1.,-1.,3.,.1,.2,.3],
 [1.e-37,-1.e-37,1.e-30,1.e-38,1.e-38,-1.e-30,1.e-20,-1.e-20,1.e-10],
]
rows=[]
for index,values in enumerate(inputs):
    bits=list(map(word,values));camera=bytearray(0x124)
    for offset,start in ((0,0),(0x3c,3),(0x24,6)):struct.pack_into('<3I',camera,offset,*bits[start:start+3])
    u.mem_write(0x4d9514,bytes(camera))
    for reference in range(10016,10022):
        for fraction in (0.,.75):
            u.mem_write(stack,struct.pack('<I',stop));u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,vm)
            u.reg_write(UC_X86_REG_XMM1,word(reference+fraction));u.reg_write(UC_X86_REG_MXCSR,0x1f80)
            u.emu_start(0x46f770,stop,count=100)
            assert u.reg_read(UC_X86_REG_EIP)==stop
            rows.append(dict(cameraCase=index,inputBits=bits,reference=reference,fraction=fraction,outputBits=u.reg_read(UC_X86_REG_XMM0)&0xffffffff))
h=root/'artifacts/th14/anm-camera-reference-oct24';h.mkdir(parents=True,exist_ok=True)
report=dict(observed=True,rows=rows,cases=len(rows),executableSha256=sha(image.data),getterAddress='0x46f770',instructionBytesPatched=0,toolSha256=sha(Path(__file__).read_bytes()),scope='Original camera getters10016..10021; six independent camera environments, exact and fractional variable IDs,72 calls. Camera words are inputs; original camera generation, GPU pixels and PCM not tested.',completeGame=False,nativeEquivalent=False)
(h/'native.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(observed=True,cases=len(rows),instructionBytesPatched=0)))
