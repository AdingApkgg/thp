"""Retail430033..430122 countdown changes; animation/audio services controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,game,first,second,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x7001f000;m.mem_map(base,0x20000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 labels=[];sounds=[];sprites=[]
 def hook(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x4113e0:labels.append([0 if uc.reg_read(UC_X86_REG_ECX)==first else 1,get(sp+4)]);cleanup=4
  elif a==0x46e3d0:sounds.append(get(sp+4));cleanup=8
  elif a==0x46f1e0:sprites.append([0 if get(sp+4)==first else 1,get(sp+8)]);cleanup=8
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook);rows=[]
 for seconds,previous,resources in itertools.product(range(100),(-1,0,1,4,5,9,10,30,99,100),range(4)):
  m.mem_write(base,bytes(0x1e000));labels.clear();sounds.clear();sprites.clear()
  for p,v in ((game+0x98,first),(game+0x9c,second),(game+0x19c,seconds),(game+0x1a4,previous),(first+0x30,resources&1),(second+0x30,resources&2)):put(p,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,game);m.emu_start(0x430033,0x43014e,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x43014e
  rows.append(dict(seconds=seconds,previous=previous,resources=resources,labels=list(labels),sounds=list(sounds),sprites=list(sprites),after=get(game+0x1a4)))
 result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Retail430033..430122 within valid visible boss countdown branch. All seconds0..99, previous -1/0/1/4/5/9/10/30/99/100 and both digit-resource presence bits. Exact interruption labels7/8/9, warning sounds11/12, sprites239+digit and previous_seconds writes; animation interrupt/sprite binding/audio services controlled. Excludes earlier visibility/colour/scaling branches, ANM execution, glyph pixels and full HUD callback.')
 (ROOT/'artifacts/th14/hud-timer-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} original countdown change cases')
if __name__=='__main__':main()
