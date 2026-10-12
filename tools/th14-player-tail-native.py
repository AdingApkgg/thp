"""Own constructor fields, complete stage reset and common clock/fire/blink tails.

ANM lookup, HUD, option reconstruction, shot allocation and shot update delivery
are controlled. The firing timer itself executes the complete retail450fb0.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
 base,stack,end=0x70000000,0x700ff000,0x700fe000;m.mem_map(base,0x100000)
 header,hud,enemy,control=base+0x20000,base+0x22000,base+0x24000,base+0x26000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 calls=[]
 def hook(machine,a,size,user):
  if a==0x450fb0:calls.append('fire')
  elif a==0x434ef0:
   sp=m.reg_read(UC_X86_REG_ESP);calls.append([get(sp+4),get(sp+8)])
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x47f0a0,4),(0x434ef0,8),(0x44f970,0),(0x450ed0,4),(0x451380,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
  m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x450fb0,end=0x450fb0)
 def reset(rate=1.):
  m.mem_write(base,bytes(0x28000));calls.clear()
  for p,v in ((0x4db67c,base),(0x4db550,hud),(0x4db544,enemy),(0x4db558,control),(base+0x688,header),(0x4d8f58,bits(rate)),(0x4f583c,1000)):
   put(p,v)
 def timer(off,n,rate=True,previous=None,fractional=None):
  for j,v in enumerate((n-1 if previous is None else previous,n,bits(float(n) if fractional is None else fractional),0x4d8f58 if rate else 0,1)):put(base+off+j*4,v)
 def run(a,until):
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,stack-0x100)
  m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ECX,base)
  m.reg_write(UC_X86_REG_XMM3,img.u32(0x4c19f8));m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(a,until,count=100000)
  except Exception:print('native failure',hex(m.reg_read(UC_X86_REG_EIP)));raise
  assert m.reg_read(UC_X86_REG_EIP)==until
 bounds=(0x630,0x63c,0x1835c,0x18368,0x18374,0x18380,0x1838c,0x18398)
 parameters=[]
 for character in range(3):
  reset();put(0x4f5828,character);put(base+0x5e4,bits(400.))
  run(0x44c681,0x44c9dc)
  parameters.append(dict(character=character,result=[get(header+o) for o in (4,12,8)]+[get(base+o) for o in (0x648,0x64c,0x650,0x654,0x658,0x65c,0x660,0x664,0x668)]+[get(base+o+j*4) for o in bounds for j in range(3)]))
 stages=[]
 for flags,x,y,fragments in itertools.product((0,2,4,8,0x10,0x12,0xffffffff),(-321,0,23552),(51200,55300),(-1,7,65537)):
  reset();put(base+0x182d4,flags);put(base+0x5ec,x);put(base+0x5f0,y)
  for off in (0x68c,0x6a0,0x6b4,0x18338):timer(off,73)
  for o in (0x1834c,0x18350,0x18354,0x18358,0x184b4,0x184b8,0x184bc,0xde14,0x18300):put(base+o,37)
  put(base+0x18308,bits(3.));put(0x4f5864,2);put(0x4f5868,fragments)
  run(0x44cc10,end)
  stages.append(dict(args=[flags,x,y,fragments],result=[get(base+0x684)]+[get(base+off+j*4) for off in (0x68c,0x6a0,0x6b4,0x18338) for j in range(3)]+[get(base+0x183a8+j*4) for j in range(66)]+[get(base+o) for o in (0x182d4,0x1834c,0x18350,0x18354,0x18358,0x184b4,0x184b8,0x184bc,0x18300,0x18308)],events=list(calls)))
 tails=[]
 # Each environment independently covers HUD, manager/count, game-thread gate.
 for env,flags,age,rate,life,schedule in itertools.product(range(5),(0,4,0x10,0x14,8,0x80),(-1,0,18,19,20,59),(.5,1.,1.25),(1,2,4),(-1,0,7,14)):
  reset(rate);timer(0x68c,59);timer(0x6a0,7);timer(0x6b4,age);timer(0x18338,schedule)
  put(base+0x684,life);put(base+0x182d4,flags);put(base+0xde0c,0x1234);put(base+0xde10,1)
  put(hud+0x194,int(env==1));put(0x4db544,0 if env==2 else enemy);put(enemy+0xd8,int(env!=3));put(control+0x80,0x4000 if env==4 else 0);put(0x4d6a90,1)
  run(0x44e8d5,0x44ebda)
  tails.append(dict(args=[env,flags,age,bits(rate),life,schedule],result=[get(base+o+j*4) for o in (0x68c,0x6a0,0x6b4,0x18338) for j in range(3)]+[get(base+0xde0c),get(base+0xde10)&255,get(0x4f583c)],fire='fire' in calls))
 blinks=[]
 for invincible,frame,previous,mode,rate in itertools.product((0,1,2,20),(0,1,2,3,59,60),(0,1),(0,1,2,3),(.5,1.,1.25)):
  reset(rate);timer(0x182c0,invincible);timer(0x68c,frame,previous=frame if previous else frame-1)
  put(base+0x2c,0x12345678&~0x60000|mode<<17);put(base+0x54c,0x87654321)
  run(0x44e0fa,0x44e1ac)
  blinks.append(dict(args=[invincible,frame,previous,mode,bits(rate)],result=[get(base+0x2c),get(base+0x54c)]+[get(base+0x182c0+j*4) for j in range(3)]))
 out=ROOT/'artifacts/th14/player-tail-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),parameters=parameters,stages=stages,tails=tails,blinks=blinks))+'\n',encoding='utf8')
 print(f'{len(parameters)} parameter sets, {len(stages)} complete stage resets, {len(tails)} clock/fire tails, {len(blinks)} blinks')
if __name__=='__main__':main()
