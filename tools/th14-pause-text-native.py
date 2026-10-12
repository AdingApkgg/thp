"""Execute retail4485d0 plus448440; calendar/ASCII/ANM lookup are boundaries."""
import hashlib,importlib,itertools,json,re,struct,time
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,sup,score,calendar,stack=0x70000000,0x70001000,0x70010000,0x70040000,0x700d0000,0x700ff000;m.mem_map(base,0x100000)
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
  sp=uc.reg_read(UC_X86_REG_ESP);cleanup=0
  if a==0x4865c2:
   stamp=struct.unpack('<q',m.mem_read(get(sp+4),8))[0];t=time.gmtime(stamp)
   m.mem_write(calendar,struct.pack('<9i',t.tm_sec,t.tm_min,t.tm_hour,t.tm_mday,t.tm_mon-1,t.tm_year-1900,(t.tm_wday+1)%7,t.tm_yday-1,0));uc.reg_write(UC_X86_REG_EAX,calendar)
  elif a==0x40bb10:
   p=get(sp+8);text=formatted(string(get(sp+12)),sp+16)
   requests.append(dict(text=text.encode('latin1').hex(),position=[flt(p+i*4) for i in range(3)],color=get(sup+0x191b0),shadow=get(sup+0x191c4),font=get(sup+0x191c8),scale=[flt(sup+0x191b4),flt(sup+0x191b8)]))
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,0);cleanup=4
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook);catalog=[]
 for index in range(25):
  if index%5==0:catalog.append(None);continue
  header=bytearray(0x94);header[:9]=f'R{index:06d} '.encode()+b'\0';header[10]=2 if index%3==0 else 0
  struct.pack_into('<Q',header,12,1700000000+index*60);struct.pack_into('<6I',header,0x7c,index%3,index%2,index%5,index%9,index%3,index%120)
  catalog.append(dict(header=header.hex()))
 rows=[];cases=[]
 cases += [(state,17,selected,0,0,0,0,0) for state,selected in itertools.product((9,17,26),(0,12,24))]
 cases += [(state,timer,selected,length,glyph,0,spell,0) for state,timer,selected,length,glyph,spell in itertools.product((10,18,27),(0,1,5,9,10,15),(0,12,24),(0,8),(0,88,89,90),(0,1))]
 cases += [(state,17,selected,length,glyph,unranked,0,selection*5+difficulty) for state,selected,length,glyph,unranked,selection,difficulty in itertools.product((19,28),(0,9),(0,8),(0,88,89,90),(0,1),range(6),range(5))]
 cases += [(15,17,0,0,0,0,0,n) for n in (0,1,3,5)]
 records=bytearray(280)
 for rank in range(10):
  offset=rank*28;struct.pack_into('<IBB',records,offset,(0,1234567,0x7fffffff,0x80000000)[rank%4],rank%9,rank%3)
  records[offset+6:offset+15]=f'R{rank:02d}     '.encode()+b'\0';struct.pack_into('<Qf',records,offset+16,1700000000+rank*60 if rank%2 else 0,rank/4)
 for state,timer,selected,length,glyph,unranked,spell,variant in cases:
  m.mem_write(base,bytes(0xfe000));requests.clear();selection,difficulty=divmod(variant,5)
  for p,v in ((0x4db520,sup),(0x4db68c,score),(0x4f56cc,base),(menu+4,state),(menu+0x14,timer),(menu+0x38,selected),(menu+0x110,glyph),(menu+0x1f0,length),(menu+0x1f8,unranked),(0x4f5828,selection//2),(0x4f582c,selection%2),(0x4f5834,difficulty),(0x4f58a4,selected%9),(0x4f58c8,variant),(sup+0x191b0,0xffffffff)):put(p,v)
  m.mem_write(menu+0x2cc,b'ABCDEFGH\0');m.mem_write(sup+0x191b4,struct.pack('<2f',1,1));m.mem_write(score+8+selection*0x5298+0x10+difficulty*0x118,bytes(records))
  for index,entry in enumerate(catalog):
   if entry:
    p=base+0x70000+index*0x400;m.mem_write(p+0x200,bytes.fromhex(entry['header']));put(p+0x1c,p+0x200);put(menu+0x204+index*4,p)
  current=base+0xb0000;header=bytearray.fromhex(catalog[3 if spell else 1]['header']);header[10]=2 if spell else 0;m.mem_write(current+0x200,bytes(header));put(current+0x1c,current+0x200);put(0x4db688,current)
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x4485d0,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
  rows.append(dict(state=state,timer=timer,selected=selected,length=length,glyph=glyph,unranked=unranked,selection=selection,difficulty=difficulty,stage=selected%9,credits=variant,header=bytes(header).hex(),requests=requests[:]))
 result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),catalog=catalog,records=records.hex(),rows=rows,scope='Complete retail4485d0 draw callback and448440 name-grid helper for all three replay-slot/name contexts, normal/compact ranking and Credit display.25 slots include empty/normal/SpellPr entries; all six loadouts/five difficulties/unsigned score bits/dated and empty rows; single-precision name transition,0/8 length and special glyph cells. ANM lookup (absent overlay), CRT formatting/calendar (UTC) and ASCII sink controlled; no child alpha propagation, file scan, save controls, font/GPU or host timezone equivalence.')
 (ROOT/'artifacts/th14/pause-text-native.json').write_text(json.dumps(result,separators=(',',':'))+'\n',encoding='utf-8');print(f'PASS {len(rows)} retail Pause layouts / {sum(len(r["requests"]) for r in rows)} ASCII requests')
if __name__=='__main__':main()
