"""Run complete retail TH16 update on stopped VMs with a controlled callback."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000);vm=0x70001000;stack=0x7001e000;captured=[]
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 f=lambda p,v:m.mem_write(p,struct.pack('<f',v))
 m.mem_write(0x47499b,b'\xc3')
 current_status=[0]
 def callback(machine,address,size,user):captured.append(get(0x4a5788));machine.reg_write(UC_X86_REG_EAX,current_status[0]&0xffffffff)
 m.mem_write(0x407330,b'\xc3')
 m.hook_add(UC_HOOK_CODE,callback,begin=0x407330,end=0x407330)
 rates=(0.,-0.,.125,.5,1.,1.5,2.,-.25);slowdowns=(0.,-0.,.125,.5,1.,1.5,-.5);rows=[]
 for ri,rate in enumerate(rates):
  for si,slow in enumerate(slowdowns):
   for length in range(1,5):
    for independent in range(16):
     for force in (0,1):
      for status in (0,1,-1):
       for i in range(4):
        p=vm+i*0x1000;m.mem_write(p,bytes(0x700));put(p+0x28,0xffffffff);put(p+0x534,((independent>>i)&1)<<16);put(p+0x5ac,p+0x1000 if i+1<length else 0);f(p+0x5b4,slow if i+1==length else .25*(i+1))
       put(vm+0x534,get(vm+0x534)|(force<<9));put(vm+0x5c4,1);put(stack,0x70000000);f(0x4a5788,rate);captured.clear();current_status[0]=status
       m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,vm);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
       m.emu_start(0x45f980,0x70000000,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x70000000;assert len(captured)==1
       rows.append([ri,si,length,independent,force,status,captured[0],get(0x4a5788),m.reg_read(UC_X86_REG_EAX)])
 out=ROOT/'artifacts/th16/rate-native.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),scope='Complete45f980 update on stopped VMs and actual406340 parent walk, 1..4 nodes, all independence masks, force-rate bit9 and seven slowdown values/eight incoming rates. Selector1 callback is a controlled rate recorder returning0/1/-1; security cookie is a sink. Compare callback effective rate and final restored global rate/return. No real particle callback, script/animation tail, cycles, interpolation, rendering or full gameplay claim.',rates=rates,slowdowns=slowdowns,rows=rows),separators=(',',':'))+'\n');print(len(rows),'native TH16 effective-rate cases')
if __name__=='__main__':main()
