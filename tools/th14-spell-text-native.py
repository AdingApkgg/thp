"""Full41c9c0 bonus/history queue and40bf20 glyph layout; lookup/CRT/atlas sinks controlled."""
import hashlib,importlib,itertools,json,re,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,SUP,SPELL,VM,SCORE,RESOURCE,ATLAS,REQUEST,STACK,RETURN=(0x70000000+n for n in (0,0x1000,0x20000,0x22000,0x30000,0x60000,0x61000,0x70000,0x8f000,0x90000))
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(BASE,0xa0000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def signed(p):return struct.unpack('<i',m.mem_read(p,4))[0]
 def flt(p):return struct.unpack('<f',m.mem_read(p,4))[0]
 def string(p):return bytes(m.mem_read(p,256)).split(b'\0')[0].decode('ascii')
 queued=[];glyphs=[]
 def hook(uc,a,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x40bb10:
   fmt=string(get(sp+12));count=len(re.findall(r'%(?:\d+)?(?:\.\d+)?d',fmt));text=fmt%tuple(signed(sp+16+i*4) for i in range(count)) if count else fmt;p=get(sp+8)
   queued.append(dict(text=text,position=[flt(p+i*4) for i in range(3)],color=get(SUP+0x191b0),scale=[flt(SUP+0x191b4),flt(SUP+0x191b8)],font=get(SUP+0x191c8),shadow=get(SUP+0x191c4),passIndex=get(SUP+0x191cc),horizontal=get(SUP+0x191d4),vertical=get(SUP+0x191d8)))
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,VM if get(sp+4)==1 else 0)
  elif a==0x40caf0:put(SUP+0x40,get(sp+4))
  elif a==0x4756e0:glyphs.append(dict(sprite=(get(SUP+0x40)-ATLAS)//72,x=flt(SUP+0x50),y=flt(SUP+0x54),color=get(SUP+0x548),filtered=bool(get(SUP+0x30)&0x400)))
 for a,cleanup in ((0x40bb10,0),(0x47f0a0,4),(0x40caf0,4),(0x476100,20),(0x4756e0,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[];bonuses=(0,1,99,999,1000,999999,1000000,99999999,2147483647,-1,-2147483648)
 for selection,flags,run,captures,attempts in itertools.product(range(6),(0,1,3),(0,0x10,0x20,0x30),(-1,0,9,99,100,99999,2147483647),(-1,0,9,99,100,99999,2147483647)):
  n=len(rows);alpha=(0,80,255)[n%3];live=(0,1,3)[n//3%3];bonus=bonuses[n%len(bonuses)];id=(0,2,52,63,119,174)[n%6];m.mem_write(BASE,bytes(0x8e000));queued.clear();glyphs.clear()
  for p,v in ((0x4db520,SUP),(0x4f56cc,BASE+0x500),(0x4db68c,SCORE),(0x4f5828,selection//2),(0x4f582c,selection%2),(0x4f58b8,run),(SPELL+0x7c,flags),(SPELL+0x78,id),(SPELL+0x80,bonus),(SPELL+0x1c,live),(VM+0x534,alpha<<24|0x102030),(SUP+0x191b0,0xffffffff),(SUP+0x191b4,0x3f800000),(SUP+0x191b8,0x3f800000),(SUP+0x191d4,1),(SUP+0x191d8,1)):put(p,v)
  record=SCORE+0x980+selection*0x5298+id*0x9c
  for off,val in ((0x80,captures),(0x84,attempts),(0x88,attempts),(0x8c,captures)):put(record+off,val)
  put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,SPELL);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x41c9c0,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
  for q in queued[:]:
   m.mem_write(REQUEST,bytes(0x138));m.mem_write(REQUEST,q['text'].encode()+b'\0');m.mem_write(REQUEST+0x100,struct.pack('<3fI2f',*q['position'],q['color'],*q['scale']))
   for off,v in ((0x120,q['font']),(0x124,q['shadow']),(0x128,q['passIndex']),(0x130,q['horizontal']),(0x134,q['vertical'])):put(REQUEST+off,v)
   put(SUP+0x191e4,RESOURCE);put(RESOURCE+0x11c,ATLAS);put(SUP+0x191dc,9);m.mem_write(0x4f7a6c,struct.pack('<f',1));put(STACK,RETURN);put(STACK+4,REQUEST);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,SUP);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
   m.emu_start(0x40bf20,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
  rows.append(dict(selection=selection,flags=flags,runFlags=run,captures=captures,attempts=attempts,alpha=alpha,live=live,bonus=bonus,id=id,handleAfter=get(SPELL+0x1c),requests=queued[:],glyphs=glyphs[:]))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Full41c9c0 bonus/history text, original40bf20 glyph layout; six selections, active/capture flags, run0/10/20/30 record source, signed bonus/count thresholds, alpha0/80/255 and absent/live/stale title roots. Lookup/CRT/ASCII queue/atlas/GPU are controlled boundaries. Supervisor initial RGBwhite/scales1/left alignment are controlled; only VM alpha is copied by native text routine. Covers request/glyph words at resolution1, not native full resource, VM retirement lifecycle or pixels.')
 (ROOT/'artifacts/th14/spell-text-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} original spell bonus/history layouts')
if __name__=='__main__':main()
