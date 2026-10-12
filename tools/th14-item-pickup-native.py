"""Actual 4390c0/4394a0 rewards below the collection line (no combo).
Popup, notify, sound and player option rebuild are controlled delivery sinks.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,ITEM,PLAYER,STACK=0x70000000,0x70001000,0x70004000,0x7003f000
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(BASE,0x40000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 events=[]
 def sink(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x457f00:events.append([0,get(sp+8),get(sp+12)])
  elif a==0x46e470:events.append([1,get(sp+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
  elif a==0x434430:events.append([2,get(sp+8)])
  elif a==0x44f970:events.append([3])
  elif a==0x46e3d0:events.append([1,get(sp+4),bits(0)])
  elif a==0x434ef0:events.append([4,get(sp+4),get(sp+8)])
  elif a==0x434fd0:events.append([5,get(sp+4),get(sp+8)])
  elif a==0x4397b0:
   p=get(sp+8);events.append([6,get(sp+4),*[get(p+j) for j in (0,4,8)],get(sp+24)])
  elif a==0x458000:
   p=get(sp+4);events.append([7,get(sp+8),get(sp+12),m.reg_read(UC_X86_REG_XMM3)&0xffffffff,*[get(p+j) for j in (0,4,8)]])
 for a,cleanup in ((0x457f00,12),(0x46e470,4),(0x434430,8),(0x44f970,0),(0x46e3d0,8),(0x434ef0,8),(0x434fd0,8),(0x4397b0,24),(0x458000,12)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 cases=[]
 for kind in (1,2,3,8):
  for character in range(3):
   for y in (148.00002,160.75,300.25,400,472,800):
    for variant in range(8):
     m.mem_write(BASE,bytes(0x3e000));events.clear();power=(-1,0,39,40,159,160,161,2147483647)[variant];score=(0,999999900,999999999,-1)[variant%4];point=(0,100,17700,123499,999999,1000000,-100,-2147483648)[variant]
     for p,v in ((0x4db67c,PLAYER),(0x4db550,BASE+0x28000),(0x4f5828,character),(0x4f5858,power),(0x4f585c,160),(0x4f5860,40),(0x4f5830,score),(0x4f584c,point),(0x4f5848,2147483647),(0x4f5880,0),(0x4f5878,0),(PLAYER+0x5e4,bits(y)),(ITEM+0xbac,bits(17.25)),(ITEM+0xbb0,bits(400)),(ITEM+0xbf0,1)):put(p,v)
     put(0x4f5854,1000000)
     put(STACK,BASE);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,ITEM)
     m.emu_start({1:0x4390c0,2:0x4394a0,3:0x439300,8:0x439220}[kind],BASE,count=10000);assert m.reg_read(UC_X86_REG_EIP)==BASE
     cases.append(dict(input=[kind,character,bits(y),power,score,point],result=[get(p) for p in (0x4f5858,0x4f5830,0x4f584c,0x4f5848,0x4f5880,0x4f5878)],events=events[:]))
 fragments=[]
 for kind,entry in ((4,0x447bb0),(5,0x447b70),(6,0x447d00),(7,0x447cc0)):
  for lives in (-1,0,7,8,9):
   for life_fragments in (-2,-1,0,1,2,3,7,8,11):
    for bombs in (-2147483648,-1,0,7,8,9,2147483647):
     for bomb_fragments in (-2147483648,-1,0,6,7,8,11,2147483647):
      m.mem_write(BASE,bytes(0x3e000));events.clear();initial=[lives,life_fragments,0,bombs,bomb_fragments]
      put(0x4db550,BASE+0x28000)
      for i,value in enumerate(initial):put(0x4f5864+i*4,value)
      put(STACK,BASE);put(STACK+4,0);m.reg_write(UC_X86_REG_ESP,STACK);m.emu_start(entry,BASE,count=10000);assert m.reg_read(UC_X86_REG_EIP)==BASE
      fragments.append(dict(kind=kind,input=initial,result=[get(0x4f5864+i*4) for i in range(5)],events=events[:]))
 for awards in (47,48,49):
  for lives in (0,7,8):
   for life_fragments in (0,2,3,8,11):
    m.mem_write(BASE,bytes(0x3e000));events.clear();initial=[lives,life_fragments,awards,0,0]
    put(0x4db550,BASE+0x28000)
    for i,value in enumerate(initial):put(0x4f5864+i*4,value)
    put(STACK,BASE);put(STACK+4,0);m.reg_write(UC_X86_REG_ESP,STACK);m.emu_start(0x447bb0,BASE,count=10000);assert m.reg_read(UC_X86_REG_EIP)==BASE
    fragments.append(dict(kind=4,input=initial,result=[get(0x4f5864+i*4) for i in range(5)],events=events[:]))
 combo_pickups=[]
 for kind in (1,2,3,8):
  for character in range(3):
   for y in (0,128,128.00002,148,148.00002,400):
    for state in (1,3):
     for variant in range(8):
      m.mem_write(BASE,bytes(0x3e000));events.clear();power=(-1,0,39,40,159,160,161,2147483647)[variant];score=(0,999999900,999999999,-1)[variant%4];point=(0,100,17700,123499,999999,1000000,-100,-2147483648)[variant]
      count,total=(2147483647,2147483597) if variant%2 else (0,0)
      for p,v in ((0x4db67c,PLAYER),(0x4db550,BASE+0x28000),(0x4f5828,character),(0x4f5858,power),(0x4f585c,160),(0x4f5860,40),(0x4f5830,score),(0x4f584c,point),(0x4f5848,2147483647),(0x4f5880,count),(0x4f5878,total),(0x4f5884,8),(PLAYER+0x5e0,bits(-33.25)),(PLAYER+0x5e4,bits(y)),(PLAYER+0x5e8,bits(3.5)),(ITEM+0xbac,bits(17.25)),(ITEM+0xbb0,bits(400)),(ITEM+0xbf0,state)):put(p,v)
      for j,v in enumerate((bits(2.25),bits(3.75),bits(-1.5))):put(0x4f5888+j*4,v)
      put(0x4f5854,1000000)
      put(STACK,BASE);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,ITEM);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
      m.emu_start({1:0x4390c0,2:0x4394a0,3:0x439300,8:0x439220}[kind],BASE,count=10000);assert m.reg_read(UC_X86_REG_EIP)==BASE
      combo_pickups.append(dict(input=[kind,character,bits(y),state,power,score,point,count,total],result=[get(p) for p in (0x4f5858,0x4f5830,0x4f584c,0x4f5848,0x4f5880,0x4f5878,0x4f5888,0x4f588c,0x4f5890,0x4f5884)],events=events[:]))
 settlements=[]
 for count in (-1,0,4,5,19,20,29,30,39,40,49,50,59,60,2147483647):
  for total in (-2147483648,-1001,-1,0,1,19,10001,2147483647):
   for timer in (-1,0,1,2,8):
    for dialogue in (0,1):
     m.mem_write(BASE,bytes(0x3e000));events.clear()
     for p,v in ((0x4db550,BASE+0x28000),(BASE+0x28194,dialogue),(0x4f5880,count),(0x4f5878,total),(0x4f5884,timer),(0x4f5830,999999990),(0x4f5888,bits(-33.25)),(0x4f588c,bits(100.5)),(0x4f5890,bits(3.5))):put(p,v)
     m.reg_write(UC_X86_REG_ESP,STACK-0x100);m.reg_write(UC_X86_REG_XMM4,0);m.reg_write(UC_X86_REG_XMM5,bits(2))
     m.emu_start(0x438dad,0x43907b,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x43907b
     settlements.append(dict(input=[count,total,timer,dialogue],result=[get(p) for p in (0x4f5880,0x4f5878,0x4f5884,0x4f5830)],events=events[:]))
 out=ROOT/'artifacts/th14/item-pickup-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,fragments=fragments,comboPickups=combo_pickups,settlements=settlements))+'\n',encoding='utf8');print(f'{len(cases)} ordinary pickup, {len(fragments)} life/bomb reward, {len(combo_pickups)} combo pickup, {len(settlements)} settlement cases.')
if __name__=='__main__':main()
