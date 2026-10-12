"""Retail float-reference helper and its actual FNINIT side effects."""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
 assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in image.sections:
  begin=base&~4095;m.mem_map(begin,((base+size+4095)&~4095)-begin);m.mem_write(base,image.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x20000);vm=base+0x1000;stack=base+0x1f000
 values=[0,.75,10000,10004,10010,10011,10012,10022,10027,10028,10029,10030,10031,10032,10033,10034,10035]
 rows=[]
 for control in (0x7f,0x37f):
  for seed in (0,0xbeef,65535):
   for value in values:
    m.mem_write(vm,bytes(0x700));m.mem_write(vm+0x4ac,struct.pack('<i',7));m.mem_write(vm+0x4bc,struct.pack('<f',.25));m.mem_write(vm+0x4e0,struct.pack('<ffi',1.75,-2.5,31))
    m.mem_write(0x4db508,struct.pack('<HHI',seed,0,0));m.mem_write(0x4db510,struct.pack('<HHI',12345,0,0));m.mem_write(0x4f5815,b'\0')
    m.mem_write(stack,struct.pack('<I',base));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,vm);m.reg_write(UC_X86_REG_XMM1,struct.unpack('<I',struct.pack('<f',value))[0]);m.reg_write(UC_X86_REG_FPCW,control);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    m.emu_start(0x46f770,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
    rows.append(dict(control=control,seed=seed,value=value,postControl=m.reg_read(UC_X86_REG_FPCW),result=m.reg_read(UC_X86_REG_XMM0)&0xffffffff,rng=list(struct.unpack('<4I',m.mem_read(0x4db508,16)))))
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,rows=rows,toolSha256=sha(Path(__file__).read_bytes()),executableSha256=sha(image.data),scope='Whole retail46f770 float-reference helper, actual403470/4034b0 RNG and FNINIT,17 reference/literal values times3 seeds times2 initial controls. Exact returned SSE float bits, two RNG states and post FPCW. No GPU, OS or whole game claim.')
 (ROOT/'artifacts/th14/anm-texture-precision-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS retail reference precision',len(rows))
if __name__=='__main__':main()
