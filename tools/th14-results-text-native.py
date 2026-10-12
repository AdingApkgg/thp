"""Actual461030 Results ASCII requests; CRT formatting/calendar and queue are controlled."""
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
 for selection,difficulty,unranked in itertools.product(range(6),range(5),(0,1)):
  ordinal=len(rows);selected=ordinal%10;name_selected=(0,88,89,90)[ordinal%4];length=(0,8)[ordinal%2]
  m.mem_write(base,bytes(0x7e000));put(0x4db68c,score);put(0x4db520,sup);put(menu+0x24,2);put(menu+0x28,selected);put(menu+0x59f8,unranked);put(menu+0x5a00,name_selected);put(menu+0x59f4,length);m.mem_write(menu+0x59e8,b'ABCDEFGH\0')
  for p,v in ((0x4f5828,selection//2),(0x4f582c,selection%2),(0x4f5834,difficulty)):put(p,v)
  m.mem_write(sup+0x191b4,struct.pack('<2f',1,1));data=bytearray(280)
  for rank in range(10):
   offset=rank*28;score_value=(0,1234567,0x7fffffff,0x80000000)[rank%4];stamp=1700000000+rank*60 if rank%2 else 0
   struct.pack_into('<IBB',data,offset,score_value,rank%9,rank%3);data[offset+6:offset+15]=f'R{rank:02d}     '.encode()+b'\0';struct.pack_into('<Qf',data,offset+16,stamp,float(rank)/4)
  m.mem_write(score+8+selection*0x5298+0x10+difficulty*0x118,bytes(data));requests.clear()
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x461030,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
  assert len(requests)==(10 if unranked else 103)
  rows.append(dict(selection=selection,difficulty=difficulty,unranked=unranked,selected=selected,nameSelected=name_selected,length=length,records=bytes(data).hex(),requests=requests[:]))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Actual retail461030 Results draw callback: all ten ranking rows, saved-name/underscore and91 character cells, native positions/colors/shadow/font/scale. CRT printf formatting and calendar supplier controlled (UTC), ASCII queue delivery controlled; no glyph/GPU or host timezone equivalence.')
 (ROOT/'artifacts/th14/results-text-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} retail Results text layouts; {sum(len(r["requests"]) for r in rows)} ASCII requests')
if __name__=='__main__':main()
