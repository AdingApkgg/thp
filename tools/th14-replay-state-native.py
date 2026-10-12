"""TH14 own456050 playback stage restore and own44c600 live power step."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x100000);manager,record,player,sheet,stack=base+0x1000,base+0x2000,base+0x4000,base+0x30000,base+0xff000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 headers=[]
 for stage,seed,variant in itertools.product((1,3,7),(0,1,0x9630,0xffff),range(8)):
  h=bytearray(0xdc);struct.pack_into('<HH',h,0,stage,seed);struct.pack_into('<ii',h,12,-4096+variant*125,51200-variant*519)
  values=[(variant*0x197731+index*0x10204081)&0xffffffff for index in range(28)];struct.pack_into('<28I',h,0x14,*values)
  for i in range(20):struct.pack_into('<I',h,0x88+i*4,(i*0xdeaddead+variant)&0xffffffff)
  headers.append((f'synthetic/{stage}/{seed}/{variant}',bytes(h)))
 ns={};exec(compile((ROOT/'tools/th-replay-container.py').read_text(encoding='utf8').partition('if __name__')[0],'container','exec'),ns)
 for p in ns['demo_files'](14):
  data,packed,unpacked=ns['fields'](p);decoded=ns['decode_with'](data,packed,unpacked,ns['TH13']);headers.append((p.name,decoded[0x94:0x170]))
 cases=[]
 for (name,h),visual_calls in itertools.product(headers,(0,97,0x80000000,0xffffffff)):
  stage,seed=struct.unpack_from('<HH',h);m.mem_write(manager,bytes(0x320));m.mem_write(record,h);put(manager+0x10,1);put(manager+stage*40+0xd8,record);put(0x4db688,manager);put(0x4f58a4,stage)
  m.mem_write(0x4f5828,bytes([0x5a])*0x70);put(0x4db510,0x1234);put(0x4db508,0x5678);put(0x4db50c,visual_calls);put(0x4db514,97);put(stack,base);m.reg_write(UC_X86_REG_ESP,stack)
  m.emu_start(0x456050,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
  games=[get(0x4f5828+n*4) for n in range(28)];assert bytes(m.mem_read(0x4f5828,0x70))==h[0x14:0x84]
  cases.append(dict(name=name,visualCalls=visual_calls,header=h.hex(),globals=games,rng=[get(0x4db510)&65535,get(0x4db508)&65535,get(0x4db514),get(0x4db50c)]))
 # 435ed0 selects first construction or existing-controller stage entry.
 # Resource/manager construction is a controlled boundary here; 456050 is real.
 for address in (0x454e60,0x40d8a0,0x42fd00,0x416510,0x438430,0x43a4c0,0x448270,0x457900,0x42eb30):
  m.mem_write(address,b'\xb8\x01\x00\x00\x00\xc3')
 routes=[];controller=base+0x50000;service=base+0x60000;h=headers[0][1];stage=struct.unpack_from('<H',h)[0]
 for flags,visual_calls in itertools.product((0,1,2,3,0x40,0x41,0x42,0x43),(0,97,0x80000000,0xffffffff)):
  m.mem_write(manager,bytes(0x320));m.mem_write(record,h);put(manager+0x10,1);put(manager+stage*40+0xd8,record)
  put(0x4db688,manager);put(0x4f58a4,stage);put(0x4f58b8,flags);put(0x4db69c,service);put(service+4,service+0x1000);put(0x4db550,controller)
  put(0x4db508,0x5678);put(0x4db50c,visual_calls);put(0x4db510,0x1234);put(0x4db514,97);put(stack,base)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBX,controller)
  m.emu_start(0x435ed0,0x435f50,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x435f50
  routes.append(dict(flags=flags,first=not bool(flags&2),visualCalls=visual_calls,header=h.hex(),visual=[get(0x4db508)&65535,get(0x4db50c)]))
 power=[]
 for selection,raw in itertools.product(range(6),(40,80,100,200)):
  m.mem_write(sheet,bytes(0xe0));put(sheet+0x20,4);put(sheet+0x24,raw);put(player+0x688,sheet);m.reg_write(UC_X86_REG_ECX,sheet);m.reg_write(UC_X86_REG_EDI,player);m.reg_write(UC_X86_REG_ESP,stack)
  m.emu_start(0x44c600,0x44c628,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x44c628
  power.append(dict(selection=selection,rawStep=raw,output=[get(sheet+0x24),get(0x4f585c),get(0x4f5860)]))
 (ROOT/'artifacts/th14/replay-state-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,routes=routes,power=power),separators=(',',':'))+'\n',encoding='utf8')
 print(f'{len(cases)} own playback stage snapshots / {len(power)} live power-step stores')
if __name__=='__main__':main()
