"""Actual retail45f5a0 Replay draw, with controlled CRT/calendar/ASCII sink."""
import hashlib,importlib,itertools,json,re,struct,time
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,sup,calendar,stack=0x70000000,0x70001000,0x70010000,0x70030000,0x7003f000;m.mem_map(base,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def flt(p):return struct.unpack('<f',m.mem_read(p,4))[0]
 def string(p):return bytes(m.mem_read(p,255)).split(b'\0')[0].decode('latin1')
 requests=[]
 def formatted(fmt,args):
  values=[]
  for match in re.finditer(r'%(?:[-+ #0]*\d*(?:\.\d+)?l?)([dsucf%])',fmt):
   kind=match[1]
   if kind=='%':continue
   if kind=='f':values.append(struct.unpack('<d',m.mem_read(args,8))[0]);args+=8
   elif kind=='s':values.append(string(get(args)));args+=4
   elif kind=='u':values.append(get(args));args+=4
   else:values.append(struct.unpack('<i',m.mem_read(args,4))[0]);args+=4
  return fmt%tuple(values)
 def hook(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x4865c2:
   stamp=struct.unpack('<q',m.mem_read(get(sp+4),8))[0];t=time.gmtime(stamp)
   m.mem_write(calendar,struct.pack('<9i',t.tm_sec,t.tm_min,t.tm_hour,t.tm_mday,t.tm_mon-1,t.tm_year-1900,(t.tm_wday+1)%7,t.tm_yday-1,0));uc.reg_write(UC_X86_REG_EAX,calendar)
  elif a==0x40bb10:
   p=get(sp+8);text=formatted(string(get(sp+12)),sp+16)
   requests.append(dict(text=text.encode('latin1').hex(),position=[flt(p+i*4) for i in range(3)],color=get(sup+0x191b0),shadow=get(sup+0x191c4),font=get(sup+0x191c8),scale=[flt(sup+0x191b4),flt(sup+0x191b8)]))
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4)
 m.hook_add(UC_HOOK_CODE,hook);catalog=[]
 for index in range(75):
  if index%5==0:catalog.append(None);continue
  entry=0x70040000+index*0x800;decoded=entry+0x300;mask=(1,4,64,127,85,42)[index%6];header=bytearray(0x94);stage_headers=bytearray(7*0xdc)
  header[:9]=f'R{index:06d} '.encode()+b'\0';header[10]=2 if index%3==0 else 0
  struct.pack_into('<Q',header,12,1700000000+index*60);struct.pack_into('<I',header,0x14,(0,1234567,0x7fffffff,0x80000000)[index%4]);struct.pack_into('<f',header,0x74,index/4)
  struct.pack_into('<6I',header,0x7c,index%3,index%2,index%5,index%9,index%3,index%120)
  m.mem_write(decoded,bytes(header));put(entry+0x1c,decoded);m.mem_write(entry+0x220,b'th14_udABCD.rpy\0')
  for st in range(1,8):
   offset=(st-1)*0xdc;struct.pack_into('<H',stage_headers,offset,st);struct.pack_into('<I',stage_headers,offset+0x1c,(0,2345678,0x7fffffff,0x80000000)[st%4]);struct.pack_into('<I',stage_headers,offset+0x24,st%3)
   if mask&(1<<(st-1)):
    stage=0x70080000+index*0x700+offset;m.mem_write(stage,bytes(stage_headers[offset:offset+0xdc]));put(entry+0x100+(st-1)*0x28,stage)
  catalog.append(dict(header=header.hex(),mask=mask,stages=stage_headers.hex(),pointer=entry))
 rows=[]
 cases=[(2,15,15.25,selected,page,page*25+17) for page,selected in itertools.product(range(3),range(25))]
 cases += [(4,timer,timer+.25,selected,page,page*25+row) for page,row,timer,selected in itertools.product(range(3),(1,17,24),(0,1,5,9,10,15),range(7))]
 for state,timer,fraction,selected,page,file in cases:
  m.mem_write(menu,bytes(0x6000));m.mem_write(sup,bytes(0x19200));put(0x4db520,sup);put(menu+0x24,state);put(menu+0x28,selected);put(menu+0x1d8,page);put(menu+0x2b8,timer);m.mem_write(menu+0x2bc,struct.pack('<f',fraction));put(menu+0x5aec,file)
  for index,entry in enumerate(catalog):put(menu+0x5af4+index*4,entry['pointer'] if entry else 0)
  put(sup+0x191b0,0xffffffff);m.mem_write(sup+0x191b4,struct.pack('<2f',1,1));requests.clear();put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x45f5a0,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
  assert len(requests)==(25 if state==2 else 8 if timer>=10 else 1)
  rows.append(dict(state=state,timer=timer,fraction=fraction,selected=selected,page=page,file=file,requests=requests[:]))
 for entry in catalog:
  if entry:del entry['pointer']
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),catalog=catalog,rows=rows,scope='Actual retail45f5a0 full Replay draw callback; 75-entry catalog with empty, normal and SpellPr recordings, six loadouts, five difficulties, all reach labels, sparse/full stage masks and signed score edge cases. Three pages/all 25 cursor rows plus fractional stage-selection animation and seven selected stages. CRT printf/calendar (UTC), valid metadata suppliers and ASCII sink controlled; excludes file enumeration, glyph/GPU/audio and native playback.')
 (ROOT/'artifacts/th14/title-replay-text-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} retail Replay layouts; {sum(len(r["requests"]) for r in rows)} ASCII requests')
if __name__=='__main__':main()

