"""Execute retail455180 and its actual41e710 keyboard edge/count update."""
from pathlib import Path
import hashlib,importlib,itertools,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,n in img.sections:
 first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
base=0x70000000;m.mem_map(base,0x100000);manager,header,inputs,fps,stack=base+0x1000,base+0x3000,base+0x4000,base+0x5000,base+0xff000
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];rows=[]
for previous,held,stored_press,stored_release in itertools.product([0,1,521,1561,0x80000],[0,1,8,520,521,1561,32,64],[0,1,0xffff],[0,8,0xffff]):
 m.mem_write(manager,bytes(0x320));m.mem_write(0x4d6878,bytes(0x240));put(0x4db558,1);put(0x4d6a90,previous);put(manager+0x218,6);put(header+4,2);slot=manager+6*40;put(slot+0xd8,header);put(slot+0xcc,inputs);put(slot+0xd4,fps);put(slot+0xdc,0);m.mem_write(inputs,struct.pack('<3H',held,stored_press,stored_release));m.mem_write(fps,b'\x3c\x3d');put(stack,base)
 m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager);m.emu_start(0x455180,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
 result=[get(0x4d6a90),get(0x4d6a94),get(0x4d6a9c),get(0x4d6aa0)];expected=[held,previous,(held^previous)&held,(held^previous)&(~held&0xffffffff)];assert result==expected
 assert get(slot+0xdc)==1 and get(slot+0xcc)==inputs+6;assert m.mem_read(manager+0x20c,1)==b'\x3c'
 rows.append(dict(previous=previous,held=held,storedPressed=stored_press,storedReleased=stored_release,result=result))
out=ROOT/'artifacts/th14/replay-input-edges';out.mkdir(exist_ok=True);report=dict(passed=True,completeGame=False,nativeEquivalent=False,cases=rows,nativeExecutableSha256=hashlib.sha256(img.data).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual455180 playback input reader and actual41e710 count/edge update; arbitrary saved edge words are overwritten from current/previous normalized held masks. Controlled manager, replay payload, FPS bytes and keyboard starting state; no OS input or full gameplay claim.')
(out/'native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS',len(rows),'retail playback edge cases; saved edge words overridden')
