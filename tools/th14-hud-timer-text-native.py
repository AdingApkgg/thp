"""Retail4318b6..431a29 timer decimal queue; CRT/ASCII delivery controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,sup,hud,manager,digit,stack=0x70000000,0x70001000,0x70021000,0x70022000,0x70023000,0x7002f000;m.mem_map(base,0x30000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 requests=[]
 def hook(uc,a,size,data):
  if a!=0x40bb10:return
  sp=uc.reg_read(UC_X86_REG_ESP);p=get(sp+8);fmt=bytes(uc.mem_read(get(sp+12),16)).split(b'\0')[0].decode()
  value=struct.unpack('<i',uc.mem_read(sp+16,4))[0];text=fmt%value if '%' in fmt else fmt
  requests.append(dict(text=text,words=[get(p+i*4) for i in range(3)]+[get(sup+off) for off in (0x191b0,0x191b4,0x191b8,0x191c8,0x191cc)]))
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4)
 m.hook_add(UC_HOOK_CODE,hook);rows=[]
 for gate,seconds,hundredths,position,color in itertools.product(range(5),(-1,0,99),(-1,0,9,99,100),((0,0),(192,56),(-32.25,159.99),(300.125,320.25)),(0,0x8040c0ff,0xffffffff)):
  m.mem_write(base,bytes(0x2e000));requests.clear()
  for p,v in ((0x4db520,sup),(0x4db544,0 if gate==1 else manager),(manager+0x5c,0 if gate==2 else 1),(manager+0x9c,1 if gate==3 else 0),(hud+0x194,1 if gate==4 else 0),(hud+0x19c,seconds),(hud+0x1a0,hundredths),(hud+0x98,digit),(digit+0x534,color),(sup+0x191b4,0x3f800000),(sup+0x191b8,0x3f800000)):put(p,v)
  m.mem_write(digit+0x3c,struct.pack('<2f',*position));m.reg_write(UC_X86_REG_EBX,hud);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,stack-0x100);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x4318b6,0x431a29,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x431a29
  rows.append(dict(gate=gate,seconds=seconds,hundredths=hundredths,position=position,color=color,requests=requests[:]))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Full retail4318b6..431a29 decimal timer drawing block. Manager/boss presence, managerflag1/dialogue/negative-second gates; first-digit animated script X/Y and color; dot and %.2d bytes, position/scale/color/font4/pass2 words exact. CRT formatting and ASCII delivery controlled; native vertex/GPU/audio and real ANM movement excluded.')
 (ROOT/'artifacts/th14/hud-timer-text-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} original timer text layouts')
if __name__=='__main__':main()
