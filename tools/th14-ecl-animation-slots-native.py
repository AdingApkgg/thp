"""Observe original 422500 loading each stage's ANIM include block."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,n in img.sections:
    start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
base=0x70000000;manager=base+0x1000;code=base+0xa000;stack=base+0x1f000;supervisor=0x71000000
m.mem_map(base,0x20000);m.mem_map(supervisor,0xc00000)
def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
def string(p):return bytes(m.mem_read(p,128)).split(b'\0')[0].decode('ascii')
calls=[]
def boundary(machine,address,size,user):
    if address==0x47cff0:
        sp=m.reg_read(UC_X86_REG_ESP);index=get(sp+4);calls.append(dict(file=index,name=string(get(sp+8))));m.reg_write(UC_X86_REG_EAX,base+0x4000+(index-10)*0x1000)
    else:m.reg_write(UC_X86_REG_EAX,supervisor)
for address,cleanup in ((0x47cff0,8),(0x47ff50,0)):
    m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
rows=[]
for stage in range(1,8):
    data=(ROOT/f'artifacts/archive-differential/th14-ppPprY/st{stage:02}.ecl').read_bytes();at=data.index(b'ANIM');count=struct.unpack_from('<I',data,at+4)[0];end=at+8
    for n in range(count):end=data.index(b'\0',end)+1
    block=data[at:end];block+=bytes(-len(block)%4)+b'ECLI'+bytes(4)
    m.mem_write(base,bytes(0x10000));m.mem_write(code,block);calls.clear();put(0x4f56cc,supervisor);put(0x4db544,manager);put(0x4d9684,0x180)
    put(stack,base);put(stack+4,code);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base+0x2000);m.emu_start(0x422500,base,count=100000)
    assert m.reg_read(UC_X86_REG_EIP)==base
    slots=[n for n in range(6) if get(manager+0xa0+n*4)]
    assert len(slots)==len(calls)
    for row,slot in zip(calls,slots):row['enemySlot']=slot
    rows.append(dict(stage=stage,animations=calls[:]))
(ROOT/'artifacts/th14/ecl-animation-slots-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),stages=rows),indent=2)+'\n',encoding='utf-8')
print('Observed all seven TH14 ECL animation include lists and native file/manager slots.')
