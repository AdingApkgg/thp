"""Own43de50/43df20 and42c600; complete visibility helpers, controlled VM tick."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x40000);gui,root,bar,levels,child1,child2,nodes,stack,ret=0x70000000,0x70001000,0x70002000,0x70003000,0x70004000,0x70005000,0x70006000,0x7003d000,0x7003e000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 events=[]
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x46efa0:machine.reg_write(UC_X86_REG_EAX,{123:root,2:bar,3:levels,0:0}.get(get(sp+4),0))
  elif a==0x46f510:machine.reg_write(UC_X86_REG_EAX,bar if get(sp+4)==115 else levels)
  else:events.append([0,int(machine.reg_read(UC_X86_REG_ECX)==levels),get(machine.reg_read(UC_X86_REG_ECX)+0x490)]);machine.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x46efa0,4),(0x46f510,8),(0x45f980,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(0x4a6dcc,gui);put(gui+0x10c,123);put(bar+0x538,2);put(levels+0x538,3);put(levels+0x58c,nodes);put(nodes,child1);put(nodes+4,nodes+16);put(nodes+16,child2)
 costs=(0,100,130,160,200,250,300);thresholds=(0,100,230,390,590,840,1140)
 for n,v in enumerate(costs):put(0x4a5810+n*4,v)
 for n,v in enumerate(thresholds):put(0x4a5838+n*4,v)
 def call(addr,args=()):
  put(stack,ret)
  for n,v in enumerate(args):put(stack+4+n*4,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(addr,ret,count=5000);assert m.reg_read(UC_X86_REG_EIP)==ret
 counts=(-2147483648,-1,0,99,100,229,230,389,390,589,590,839,840,1139,1140,2147483647)
 collection=[];gauges=[]
 for count,maximum in itertools.product(counts,(0,100,1140,2147483647)):
  put(0x4a5808,count);put(0x4a580c,maximum);call(0x43de50,(16,));collection.append(dict(count=count,maximum=maximum,result=m.reg_read(UC_X86_REG_EAX),output=get(0x4a5808)))
  call(0x43df20);collection[-1]['progress']=m.reg_read(UC_X86_REG_XMM0)&0xffffffff
 for count,maximum,active,flags in itertools.product(counts,(100,1140),(0,1,2),(0,7,0x80000003)):
  put(0x4a5808,count);put(0x4a580c,maximum);put(gui+0x114,active);put(bar+0x530,flags);put(levels+0x530,flags);put(child1+0x530,flags);put(child2+0x530,flags);put(bar+0x490,99);put(levels+0x490,99);events.clear();call(0x42c600)
  gauges.append(dict(count=count,maximum=maximum,active=active,flags=flags,output=[get(bar+0x70),get(bar+0x530),get(levels+0x530),get(child1+0x530),get(child2+0x530),get(bar+0x490),get(levels+0x490),get(gui+0x114)],events=list(events)))
 rewards=[];release=0x70007000;put(0x4a6da4,release)
 def score_boundary(machine,a,size,user):events.append(get(machine.reg_read(UC_X86_REG_ESP)+4))
 m.mem_write(0x43e080,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,score_boundary,begin=0x43e080,end=0x43e080)
 for kind,point,maximum,energy in itertools.product(range(9,15),(-2147483648,-1,0,999,10000,100000,2147483647),(0,100000,2147483647),(-1,0,.25,500)):
  put(0x4a57d8,point);put(0x4a57e0,maximum);put(release+0xdc,bits(energy));m.reg_write(UC_X86_REG_ECX,kind);m.reg_write(UC_X86_REG_ESP,stack);events.clear();m.emu_start(0x42fe0d,0x42fe97,count=5000);assert m.reg_read(UC_X86_REG_EIP)==0x42fe97
  rewards.append(dict(kind=kind,point=point,maximum=maximum,energy=energy,output=[get(0x4a57d8),get(release+0xdc),events[0]]))
 (ROOT/'artifacts/th16/season-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),collection=collection,gauges=gauges,rewards=rewards),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(collection)} season collections;{len(gauges)} gauges;{len(rewards)} cancel rewards')
if __name__=='__main__':main()
