"""Retail score and bonus factories, complete pool update and score glyph delivery."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,obj,pos,player,resource,atlas,ascii,stack,end=0x70000000,0x70001000,0x70002000,0x70003000,0x70005000,0x70006000,0x70010000,0x7003f000,0x70040000
 m.mem_map(base,0x50000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 def f(p):return struct.unpack('<f',m.mem_read(p,4))[0]
 def entry(p):
  words=[get(p+4*n) for n in range(18)];words[11]=int(words[11]!=0);return words
 def pool():return [entry(obj+0x5e4+72*n) for n in range(18)]
 def reset():
  m.mem_write(obj,bytes(0xaf4));put(0x4db694,obj);put(0x4db67c,player);put(0x4db520,ascii);put(0x4f56cc,base+0x45000)
  put(obj+0x10,resource);put(resource+0x11c,atlas);put(obj+0x34,0x1c0000);put(0x4d916c,0);put(0x4d9960,0)
  put(ascii+0x191b4,bits(1));put(ascii+0x191b8,bits(1))
  for n in range(18):
   p=obj+0x5e4+n*72;put(p+0x34,0x12345678+n);put(p+0x38,0xabcdef00+n)
 def call(address,args=(),multiplier=0,owner=None):
  put(stack,end)
  for n,v in enumerate(args):put(stack+4+4*n,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj if owner is None else owner);m.reg_write(UC_X86_REG_XMM3,bits(multiplier))
  m.emu_start(address,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
 glyphs=[];queued=[];bonus_glyphs=[]
 def hook(uc,a,size,user):
  if a==0x4756e0:
   vm=get(m.reg_read(UC_X86_REG_ESP)+4)
   if vm==ascii+0x14:bonus_glyphs.append([(get(ascii+0x40)-atlas)//72,get(ascii+0x50),get(ascii+0x54),get(ascii+0x548),int(bool(get(ascii+0x30)&0x400))])
   else:glyphs.append([ (get(vm+0x2c)-atlas)//72,get(vm+0x59c),get(vm+0x5a0),get(vm+0x534)])
  if a==0x40caf0:put(ascii+0x40,get(m.reg_read(UC_X86_REG_ESP)+4))
  if a==0x40bb10:
   sp=m.reg_read(UC_X86_REG_ESP);q=get(sp+8);fmt=get(sp+12)
   text=bytes(m.mem_read(fmt,32)).split(b'\0')[0].decode()
   if text=='BONUS %.1f':text=text%struct.unpack('<d',m.mem_read(sp+16,8))[0]
   elif text=='%d':text=text%struct.unpack('<i',m.mem_read(sp+16,4))[0]
   queued.append(dict(text=text,position=[get(q+4*n) for n in range(3)],color=get(ascii+0x191b0),font=get(ascii+0x191c8),passIndex=get(ascii+0x191cc),shadow=get(ascii+0x191c4),horizontal=get(ascii+0x191d4),vertical=get(ascii+0x191d8)))
 for a,cleanup in ((0x475eb0,0),(0x476100,20),(0x4756e0,8),(0x40bb10,0),(0x40caf0,4)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
 m.hook_add(UC_HOOK_CODE,hook)
 factories=[]
 for bonus,cursor,value,flags,blocked in itertools.product((False,True),(0,9,10),(0,1,1234567890,-1,-2147483648),(0,0xabc00001),(0,2,5)):
  if not bonus and blocked:continue
  reset();put(obj+0x14,cursor)
  for n in range(18):
   p=obj+0x5e4+72*n;put(p+0x30,flags);put(p+0x2c,0x4d8f58 if flags else 0)
  for n in range(blocked):m.mem_write(obj+0x98c+72*n+0x3c,b'\x01')
  initial=pool();xyz=[bits(-200 if cursor==0 else 200),bits(-20 if cursor==0 else 99.5),bits(3)]
  for n,v in enumerate(xyz):put(pos+4*n,v)
  call(0x458000 if bonus else 0x457f00,(pos,value,0xa5345678),1.2)
  factories.append(dict(bonus=bonus,cursor=cursor,value=value,blocked=blocked,initial=initial,position=xyz,color=0xa5345678,multiplier=bits(1.2),result=pool(),nextCursor=get(obj+0x14)))
 timelines=[]
 for value,rate in itertools.product((0,12,1234567,-1),(.3,.5,.99,1,1.01,1.25)):
  reset();put(0x4d8f58,bits(rate));m.mem_write(pos,struct.pack('<3f',12.25,99.5,2));call(0x457f00,(pos,value,0xa5345678));call(0x458000,(pos,value,0xa5345678),1.2)
  initial=pool();states=[]
  put(player+0x5e0,bits(-50.25));put(player+0x5e4,bits(210.5))
  for frame in range(280):
   call(0x4579c0);words=pool();glyphs.clear();queued.clear();call(0x457ae0)
   bonus_glyphs.clear()
   for q in queued:
    request=base+0x30000;m.mem_write(request,bytes(0x138));m.mem_write(request,q['text'].encode()+b'\0')
    for n,v in enumerate(q['position']):put(request+0x100+4*n,v)
    for off,v in ((0x10c,q['color']),(0x110,bits(1)),(0x114,bits(1)),(0x120,q['font']),(0x124,q['shadow']),(0x128,q['passIndex']),(0x130,q['horizontal']),(0x134,q['vertical'])):put(request+off,v)
    put(ascii+0x191e4,resource);put(ascii+0x191dc,9);put(0x4f7a6c,bits(1));call(0x40bf20,(request,),owner=ascii)
   states.append(dict(words=words,glyphs=glyphs.copy(),requests=queued.copy(),bonusGlyphs=bonus_glyphs.copy()))
   if all(not w[15]&255 for w in words):break
  timelines.append(dict(value=value,rate=rate,initial=initial,states=states,player=[bits(-50.25),bits(210.5),0]))
 glyph_cases=[]
 for value,age,distance in itertools.product((0,1,12,1234567,2147483647,-1),(1,7,8,35,36,39,40,43,44,48,51,52,55,56,59,60,61),(0,63.999996185302734,64,64.00000762939453,127.99999237060547,128,128.00001525878906)):
  reset();put(0x4d8f58,bits(1));m.mem_write(pos,struct.pack('<3f',0,99.5,2));call(0x457f00,(pos,value,0xa5345678))
  p=obj+0x5e4;put(p+0x20,age-1);put(p+0x24,age);put(p+0x28,bits(age))
  put(player+0x5e0,bits(distance));put(player+0x5e4,bits(99.5));glyphs.clear();queued.clear();call(0x457ae0)
  glyph_cases.append(dict(value=value,age=age,player=[bits(distance),bits(99.5),0],initial=pool(),glyphs=glyphs.copy()))
 out=ROOT/'artifacts/th14/score-popup-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),factories=factories,timelines=timelines,glyphCases=glyph_cases)),encoding='utf-8')
 print('native popups:',len(factories),'factories,',len(timelines),'timelines /',sum(len(r['states']) for r in timelines),'frames')
if __name__=='__main__':main()
