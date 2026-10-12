"""Execute retail TH14 SHT loader; replace only archive read with a supplied file."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text(encoding='utf-8'))
BASE,DATA,PLAYER,STACK,RETURN=0x70000000,0x70010000,0x70080000,0x700ff000,0x700fe000
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,n in image.sections:
    first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[raw:raw+n])
m.mem_map(BASE,0x100000)
m.mem_write(0x402b00,b'\xb8'+struct.pack('<I',DATA)+b'\xc2\x04\x00')
get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
files=[]
for n in range(6):
    name=image.cstring(image.u32(0x4d9f20+n*4));b=(Path(archive['extraction'])/name).read_bytes()
    assert hashlib.sha256(b).hexdigest()==next(r['sha256'] for r in archive['decoded'] if r['name']==name)
    m.mem_write(DATA,b);m.mem_write(STACK,struct.pack('<II',RETURN,0));m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,PLAYER)
    m.emu_start(0x44ecc0,RETURN,count=100000)
    assert m.reg_read(UC_X86_REG_EIP)==RETURN and m.reg_read(UC_X86_REG_EAX)==0
    assert get(PLAYER+0x688)==DATA
    groups=[]
    for g in range(struct.unpack_from('<H',b,2)[0]):
        p=get(DATA+0xe0+g*4);start=p;records=[]
        while struct.unpack('<b',m.mem_read(p,1))[0]>=0:
            records.append(bytes(m.mem_read(p,0x58)).hex());p+=0x58
        groups.append(dict(offset=start-DATA,records=records))
    files.append(dict(name=name,sha256=hashlib.sha256(b).hexdigest(),header=bytes(m.mem_read(DATA,0xe0)).hex(),groups=groups))
tables={}
for offset,base in ((0x28,0x4d5954),(0x2c,0x4d592c),(0x30,0x4db684),(0x34,0x4d5904)):
    table={}
    for f in files:
        b=(Path(archive['extraction'])/f['name']).read_bytes()
        for g in f['groups']:
            for r in range(len(g['records'])):
                index=struct.unpack_from('<I',b,g['offset']+r*0x58+offset)[0]
                table[str(index)]=get(base+index*4)
    tables[str(offset)]=table
out=ROOT/'artifacts/th14/sht-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(image.data).hexdigest(),files=files,callbackTables=tables),indent=2)+'\n',encoding='utf-8')
print(f'Observed {len(files)} native SHT loads, {sum(len(g["records"]) for f in files for g in f["groups"])} shot records.')
