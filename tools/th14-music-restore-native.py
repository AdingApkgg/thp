"""Retail end-menu music filename/time capture and Continue restore requests."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,stack=0x70000000,0x70001000,0x7001f000;m.mem_map(base,0x20000)
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 def text(p):return bytes(m.mem_read(p,32)).split(b'\0')[0].decode('ascii')
 events=[];cursor=0
 def sink(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x44beb0:m.reg_write(UC_X86_REG_XMM0,cursor)
  elif a==0x445690:events.append(['end-track',text(get(sp+8))])
  elif a==0x46ef90:events.append(['restore-track',get(sp+4),get(sp+8),text(get(sp+12))])
  elif a==0x481ee0:events.append(['seek',m.reg_read(UC_X86_REG_XMM1)&0xffffffffffffffff])
  elif a==0x46e5e0:m.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x44beb0,0),(0x445690,8),(0x44c070,0),(0x46ef90,12),(0x46e5e0,0),(0x481ee0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 tracks=json.loads((ROOT/'runtimes/th14/th14_web/assets/sdl-native/music-verification.json').read_text())
 rows=[]
 for track,seconds in itertools.product(tracks,(0.,1.25,17.875,359.125)):
  m.mem_write(menu,bytes(0x1000));m.mem_write(0x4f9e00,track['name'].removesuffix('.wav').encode()+b'\0');events.clear()
  cursor=struct.unpack('<Q',struct.pack('<d',seconds))[0];m.reg_write(UC_X86_REG_ESI,menu);m.reg_write(UC_X86_REG_ESP,stack)
  m.emu_start(0x449e6c,0x449ea5,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x449ea5
  saved=text(menu+0x2e4);saved_cursor=struct.unpack('<Q',m.mem_read(menu+0x2dc,8))[0]
  m.reg_write(UC_X86_REG_EDI,menu);m.reg_write(UC_X86_REG_ESP,stack)
  m.emu_start(0x44aef0,0x44af2c,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x44af2c
  assert saved==track['name'].removesuffix('.wav') and saved_cursor==cursor
  assert events==[['end-track','th128_08'],['restore-track',2,0xffffffff,saved],['seek',cursor]],events
  rows.append(dict(track=saved,seconds=seconds,cursorBits=str(cursor),events=[[str(x) if isinstance(x,int) and x>0xffffffff else x for x in e] for e in events]))
 out=ROOT/'artifacts/th14/music-restore-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows))+'\n',encoding='utf8')
 print(f'{len(rows)} retail music capture/restore requests')
if __name__=='__main__':main()
