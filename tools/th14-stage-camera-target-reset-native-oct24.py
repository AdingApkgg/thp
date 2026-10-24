"""Original40d412..40d502 camera-copy/reset block, stopped before registration.

Declared Stage storage, incoming camera and stack inputs; no code patches or
replacement callees. This isolates initialization, not the whole constructor.
"""
from pathlib import Path
import hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EBX,UC_X86_REG_EIP,UC_X86_REG_MXCSR
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'));img=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(img.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
u=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,n in img.sections:
    first=base&~4095;u.mem_map(first,((base+size+4095)&~4095)-first);u.mem_write(base,img.data[raw:raw+n])
stage=0x70000000;stack=0x70010000;u.mem_map(stage,0x12000);rows=[]
for case in range(12):
    values=[float((i+1)*(case+1)*(-.75 if(i+case)&1 else 1.25))for i in range(22)];bits=list(struct.unpack('<22I',struct.pack('<22f',*values)))
    camera=bytearray(0x12c);struct.pack_into('<22I',camera,0,*bits);u.mem_write(0x4d9514,bytes(camera));u.mem_write(stage,bytes(0x43a0))
    u.reg_write(UC_X86_REG_EBP,stack+0x1000);u.reg_write(UC_X86_REG_ESP,stack+0xf00);u.reg_write(UC_X86_REG_EBX,stage);u.reg_write(UC_X86_REG_MXCSR,0x1f80)
    u.emu_start(0x40d412,0x40d502,count=1000);assert u.reg_read(UC_X86_REG_EIP)==0x40d502
    outputs=list(struct.unpack('<22I',u.mem_read(stage+0x4274,22*4)));assert outputs[18:21]==[0,0,0]
    rows.append(dict(case=case,inputBits=bits,outputBits=outputs))
h=root/'artifacts/th14/stage-camera-target-reset-oct24';h.mkdir(exist_ok=True)
(h/'native.json').write_text(json.dumps(dict(observed=True,rows=rows,executableSha256=sha(img.data),toolSha256=sha(Path(__file__).read_bytes()),instructionBytesPatched=0,scope='Original camera-copy/reset block40d412..40d502 with12 distinct incoming camera states; target offset cleared by40d4ef/40d4fc. Stops before callback registration, resource setup and later constructor work.',completeGame=False,nativeEquivalent=False),indent=2)+'\n');print('Observed12 original camera resets without instruction patches.')
