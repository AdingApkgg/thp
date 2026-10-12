"""Full411e70 basic bullet update, controlled collision/ANM/retirement boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x2000000);bullet,anm,file,sprites,stack,ret=0x70001000,0x70010000,0x70004000,0x70006000,0x71ffd000,0x71ffe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def fput(p,v):m.mem_write(p,struct.pack('<f',v))
 events=[];anm_result=0
 def boundary(machine,address,size,user):
  if address==0x4124b0:events.append('collision');machine.reg_write(UC_X86_REG_EAX,0)
  elif address==0x45f980:events.append('animation');machine.reg_write(UC_X86_REG_EAX,anm_result)
  elif address==0x412670:events.append('retire')
 for address,cleanup in ((0x4124b0,4),(0x45f980,0),(0x412670,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 put(0x4c0f48,anm);put(anm+0x184f4f0,file);put(file+0x11c,sprites);put(0x490eb0,0x4a5788)
 cases=[];locations=((-220,40),(220,40),(0,-100),(0,470),(-192,224),(192,224),(0,-64),(0,448),(0,224),(7.125,9.25))
 for state in (1,2,3,4):
  for rate in (0,.25,.5,.99,1,1.01,1.5,2):
   for anm_result in (0,1):
    for n in range(160):
     position=[*locations[n%10],.1];velocity=[-1.25+n*.125,2.5-n*.0625,.125];lifetime=(0,7,8,9)[n%4];delay=n%3;grace=n%7;integer=n%2
     m.mem_write(bullet,bytes(0x2000));
     if n>=40:
      put(bullet+0xca8,1);fput(bullet+0xc38,2.25);fput(bullet+0xc3c,.3)
     age=(-1,0,15,16,17,18,2147483647,-2147483648)[n%8] if n>=80 else 0
     fraction=float(age)+.25 if n>=80 else 0
     if n>=80:
      put(bullet+0xc68,1);put(bullet+0xc60,1);put(bullet+0xfa0,33);put(bullet+0xfa4,age);fput(bullet+0xfa8,fraction)
     fput(0x4a5788,rate);put(bullet+0x20,3 if n!=39 else 11);put(bullet+0x24,delay);put(bullet+0xc58,grace);put(bullet+0xc72,state);put(bullet+0x4c8,integer)
     put(bullet+0x1450,lifetime);put(bullet+0x1464,17);fput(bullet+0x1468,17.5);fput(bullet+0x141c,1.5)
     for j,v in enumerate(position):fput(bullet+0xc20+j*4,v)
     for j,v in enumerate(velocity):fput(bullet+0xc2c+j*4,v)
     fput(sprites+0x38,17);fput(sprites+0x34,36)
     put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);events.clear();m.emu_start(0x411e70,ret,count=20000)
     assert m.reg_read(UC_X86_REG_EIP)==ret
     cases.append(dict(state=state,rate=rate,animationResult=anm_result,n=n,age=age,fraction=fraction,position=position,velocity=velocity,lifetime=lifetime,delay=delay,grace=grace,integer=integer,flags=3 if n!=39 else 11,output=[get(bullet+o) for o in (0xc20,0xc24,0xc28,0x24,0xc58,0xc72,0x1460,0x1464,0x1468,0xc2c,0xc30,0xc34,0xc68,0xc60,0xfa0,0xfa4,0xfa8,0xfd0)],events=list(events),result=m.reg_read(UC_X86_REG_EAX)))
 out=ROOT/'artifacts/th16/bullet-step-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8');print(f'{len(cases)} native TH16 zero/ETEX1 bullet updates')
if __name__=='__main__':main()
