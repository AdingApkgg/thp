"""Retail TH16 score/stock helpers and ordinary pickup dispatch; delivery controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x40000);item,player,stack,ret=0x70000000,0x70010000,0x7003d000,0x7003e000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 events=[]
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x45e150:events.extend([0,get(sp+4),0,0])
  elif a==0x45e1f0:events.extend([0,get(sp+4),machine.reg_read(UC_X86_REG_XMM2)&0xffffffff,1])
  elif a==0x44a460:
   p=get(sp+4);events.extend([1,get(p),get(p+4),get(p+8),get(sp+8),get(sp+12)])
  elif a==0x42c280:events.extend([2,get(sp+4),get(sp+8)])
  elif a==0x42c390:events.extend([3,get(sp+4),get(sp+8)])
  elif a==0x42bcf0:events.extend([4,get(sp+8)])
  elif a==0x4440e0:events.extend([5])
 for a,cleanup in ((0x45e150,8),(0x45e1f0,4),(0x44a460,12),(0x42c280,8),(0x42c390,8),(0x42bcf0,8),(0x4440e0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 offsets=(0x4a57b0,0x4a57e4,0x4a57d8,0x4a57f4,0x4a57f8,0x4a57fc,0x4a5800,0x4a5804,0x4a57d4,0x4a5860,0x4a5868,0x4a5870,0x4a5874,0x4a5878)
 def reset(score=0,difficulty=1,extend=0,lives=2,fragments=0,bombs=3,bomb_fragments=0,power=0,point=1000000,maximum=10000000):
  for a in offsets:put(a,0)
  for a,v in ((0x4a57b0,score),(0x4a57b4,difficulty),(0x4a57fc,extend),(0x4a57f4,lives),(0x4a57f8,fragments),(0x4a5800,bombs),(0x4a5804,bomb_fragments),(0x4a57e4,power),(0x4a57e8,400),(0x4a57ec,100),(0x4a57d8,point),(0x4a57e0,maximum)):put(a,v)
  events.clear()
 def call(a,ecx=0,args=(),stop=ret):
  put(stack,ret)
  for n,v in enumerate(args):put(stack+4+n*4,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.emu_start(a,stop,count=20000);assert m.reg_read(UC_X86_REG_EIP)==stop
 def output():return [get(a) for a in offsets]
 scores=[]
 for score,amount,difficulty,extend,lives in itertools.product((0,499999,999999,3999999,99999999,999999990),(0,-9,9,10,100,10000000,2000000000),(1,4),(0,1,5),(0,7,8,9)):
  if ((score+int(amount/10))&0xffffffff)>=1000000000:continue
  reset(score,difficulty,extend,lives,123);call(0x43e080,args=(amount,));scores.append(dict(score=score,amount=amount,difficulty=difficulty,extend=extend,lives=lives,fragments=123,output=output(),events=list(events)))
 stocks=[]
 for kind,count,fragments in itertools.product((0,1,2),(-2147483648,-1,0,7,8,9,2147483647),(-2147483648,-1,0,4,5,2147483647)):
  reset(lives=count,fragments=fragments,bombs=count,bomb_fragments=fragments);call((0x43df70,0x43dfb0,0x43dff0)[kind],args=(0,));stocks.append(dict(kind=kind,count=count,fragments=fragments,awarded=int(kind==0 and count<8),output=output(),events=list(events)))
 pickups=[];put(0x4a6ef8,player)
 for kind,power,point,character,y,state in itertools.product(range(1,9),(0,99,100,399,400,401),(0,1000010,2147483647),range(4),(100.,128.,148.,400.),(1,4)):
  reset(power=power,point=point);put(0x4a57a4,character)
  for n,v in enumerate((0,y,2)):put(player+0x610+n*4,bits(v))
  for n,v in enumerate((17.25,61.5,2)):put(item+0xc08+n*4,bits(v))
  put(item+0xc50,state);put(item+0xc54,kind);put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,item)
  m.emu_start(0x42fd84,0x42fe9d,count=20000);assert m.reg_read(UC_X86_REG_EIP)==0x42fe9d
  pickups.append(dict(kind=kind,power=power,point=point,character=character,y=y,state=state,output=output(),events=list(events)))
 (ROOT/'artifacts/th16/item-rewards-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),scores=scores,stocks=stocks,pickups=pickups),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(scores)} score/extend; {len(stocks)} stocks; {len(pickups)} ordinary pickups')
if __name__=='__main__':main()
