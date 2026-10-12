"""Actual460740 Player Data draw callback; CRT/calendar and queue controlled."""
import hashlib,importlib,itertools,json,re,struct,time
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,score,sup,calendar,stack=0x70000000,0x70001000,0x70010000,0x70050000,0x70070000,0x7007f000;m.mem_map(base,0x80000)
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
 m.hook_add(UC_HOOK_CODE,hook);rows=[]
 for selection,difficulty,page in itertools.product(range(6),range(5),range(4)):
  ordinal=len(rows);m.mem_write(base,bytes(0x7e000));put(0x4db68c,score);put(0x4db520,sup);put(menu+0x24,2);put(menu+0x28,selection);put(menu+0x100,difficulty);put(menu+0x1d8,page);m.mem_write(sup+0x191b4,struct.pack('<2f',1,1));data=bytearray(280)
  for rank in range(10):
   offset=rank*28;score_value=(0,1234567,0x7fffffff,0x80000000)[rank%4];stamp=1700000000+rank*60 if rank%2 else 0
   struct.pack_into('<IBB',data,offset,score_value,rank%9,rank%3);data[offset+6:offset+15]=f'R{rank:02d}     '.encode()+b'\0';struct.pack_into('<Qf',data,offset+16,stamp,float(rank)/4)
  character=score+8+selection*0x5298;m.mem_write(character+0x10+difficulty*0x118,bytes(data));stats=[(0,0x7fffffff,0xffffffff)[ordinal%3],(0,59,60,3599,3600,215999,216000,0x7fffffff,0xffffffff)[ordinal%9],(0,0x7fffffff,0xffffffff)[ordinal%3]]
  for offset,value in zip((0x7b8,0x7bc,0x7c0+difficulty*4),stats):put(character+offset,value)
  requests.clear();put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x460740,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base;assert len(requests)==(3 if page else 13)
  rows.append(dict(selection=selection,difficulty=difficulty,page=page,records=bytes(data).hex(),stats=stats,requests=requests[:]))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Actual retail460740 Records draw callback: ten rankings on overview and three play-count/time/clear-count rows on every page, all text bytes/position/colors/shadow/font/scale. CRT printf/calendar supplier controlled (UTC); signed frame-time division and integer edge cases exercised. No glyph/GPU/host timezone equivalence.')
 (ROOT/'artifacts/th14/records-text-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} retail Player Data layouts; {sum(len(r["requests"]) for r in rows)} ASCII requests')
if __name__=='__main__':main()
