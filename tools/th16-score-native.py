"""Own4493c0 character defaults and complete43e250 high-score insertion."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x50000);bank,replay,stack,ret=0x70001000,0x70010000,0x7004d000,0x7004e000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x477920:
   target,value,length=(get(sp+n) for n in (4,8,12));machine.mem_write(target,bytes([value&255])*length);machine.reg_write(UC_X86_REG_EAX,target)
  elif a==0x47a09e:machine.mem_write(get(sp+4),struct.pack('<Q',0x123456789abcdef0))
 for a in (0x477920,0x47a09e):m.mem_write(a,b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def run(a):
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bank);m.emu_start(a,ret,count=30000);assert m.reg_read(UC_X86_REG_EIP)==ret
 run(0x4493c0);initial=bytes(m.mem_read(bank,0x5318));cases=[]
 for difficulty,score,stage,continues,ratio,season in itertools.product((0,1,5),(0,9999,10000,50000,50001,100000,100001,0x7fffffff,0x80000000,0xffffffff),(1,7,9),(0,257),(0,.125,1),(0,3)):
  m.mem_write(bank,initial)
  for rank in range(60):m.mem_write(bank+0x10+rank*32+15,bytes([rank+8]))
  for p,v in ((0x4a57b4,difficulty),(0x4a57b0,score),(0x4a5790,stage),(0x4a57b8,continues),(0x4a57ac,season),(0x4a6dc8,replay)):put(p,v)
  m.mem_write(replay+0x20,struct.pack('<dd',ratio,1.0));run(0x43e250)
  cases.append(dict(difficulty=difficulty,score=score,stage=stage,continues=continues,ratio=ratio,season=season,rank=struct.unpack('<i',struct.pack('<I',m.reg_read(UC_X86_REG_EAX)))[0],rows=bytes(m.mem_read(bank+0x10,60*32)).hex()))
 out=ROOT/'artifacts/th16/score-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),initial=initial.hex(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} own TH16 score insertions and full character initialization')
if __name__=='__main__':main()
