"""Retail ending image commands, real first ANM update; allocation/binding/registry controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x40000)
 vm,owner,resource,old,created,code,msg,staff,supervisor,stack=(base+n for n in (0x1000,0x2000,0x3000,0x4000,0x5000,0x6000,0x7000,0x9000,0x10000,0x3f000))
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def floats(p,*values):m.mem_write(p,struct.pack('<'+'f'*len(values),*values))
 bindings=[];loads=[];text_handles={};texts=[];interrupts=[];music_files=[]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);this=uc.reg_read(UC_X86_REG_ECX)
  if a==0x47fcb0:uc.reg_write(UC_X86_REG_EAX,created);pop=0
  elif a==0x40af00:
   assert this==resource and get(sp+4)==created;bindings.append(get(sp+8));pop=8
   put(created+0x18,7);put(created+0x1c,0x800000);put(created+0x28,code);put(created+0x38,code);put(created+0x30,resource)
   put(created+0x554,0x4d8f58);put(created+0x558,1);floats(created+0x60,1,1,1,1);floats(created+0x4e0,1,3.1415927410125732);put(created+0x4e8,65536);put(created+0x580,created)
  elif a==0x47e890:
   assert get(sp+8)==created;out=get(sp+4);put(out,200);uc.reg_write(UC_X86_REG_EAX,out);pop=8
  elif a==0x47f6e0:
   if get(this)==100:put(old+0x1c,get(old+0x1c)|32)
   put(this,0);pop=0
  elif a==0x47d090:loads.append(get(sp+4));uc.reg_write(UC_X86_REG_EAX,resource);pop=8
  elif a==0x47f140:
   if text_handles:interrupts.append([get(sp+4),get(sp+8)])
   pop=8
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,text_handles.get(get(sp+4),0));pop=4
  elif a==0x47db50:
   p=get(sp+32);b=bytearray()
   while m.mem_read(p,1)!=b'\0':b.extend(m.mem_read(p,1));p+=1;assert len(b)<512
   handle=next(h for h,v in text_handles.items() if v==get(sp+8));texts.append(dict(handle=handle,args=[get(sp+o) for o in (12,16,20,24,28)],bytes=b.hex()));pop=0
  elif a==0x445690:
   assert get(sp+4)==0;p=get(sp+8);b=bytearray()
   while m.mem_read(p,1)!=b'\0':b.extend(m.mem_read(p,1));p+=1
   music_files.append(b.decode('ascii'));pop=8
  elif a==0x46ef90:pop=12
  elif a==0x41f990:
   p=get(sp+4);assert bytes(m.mem_read(p,10))==b'staff.msg\0';uc.reg_write(UC_X86_REG_EAX,staff);pop=4
  elif a==0x48f980:
   p=get(sp+4);m.mem_write(p,bytes([get(sp+8)&255])*get(sp+12));uc.reg_write(UC_X86_REG_EAX,p);pop=0
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 def reset():
  m.mem_write(base,bytes(0x3e000));bindings.clear();loads.clear();text_handles.clear();texts.clear();interrupts.clear();music_files.clear();put(0x4db540,owner);put(owner+0x18,vm);put(0x4db520,supervisor);floats(0x4d8f58,1);m.mem_write(0x4f5815,b'\0')
  for offset in (4,0x18,0x2c):put(vm+offset,0xffffffff);put(vm+offset+12,0x4d8f58);put(vm+offset+16,1)
  put(vm+0x54,msg);put(vm+0x74,1);put(vm+0x7c,0xffffff)
 def call(a,this):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,this);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(a,base,count=50000);assert m.reg_read(UC_X86_REG_EIP)==base
 def cmd(op,*args):return struct.pack('<hHhH',op,8+4*len(args),0,0)+b''.join(struct.pack('<I',v&0xffffffff) for v in args)
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 loader=[]
 for slot in range(4):
  reset();put(vm+0xec,slot);put(vm+0x70,msg);put(vm+0x74,5);m.mem_write(msg,b'e01.anm\0');call(0x420c50,vm)
  assert len(loads)==1;loader.append(dict(slot=slot,fileId=loads[0],flags=get(vm+0x74),resourcePresent=get(vm+0x80+slot*4)==resource))
 rows=[]
 for op,difficulty,file,slot,program in itertools.product((8,15,16,17),range(4),range(4),(0,7,15),range(3)):
  reset();put(0x4f5834,difficulty);put(vm+0x80+file*4,resource);put(vm+0x90+slot*4,100)
  m.mem_write(msg,struct.pack('<HBBiii',0,op,12,slot,file,1)+struct.pack('<HBB',65535,0,0))
  b=b''
  if program:b+=cmd(304,8 if program==1 else 28)
  if program==2:b+=cmd(400,*map(bits,(3.25,-7.5,9.125)))+cmd(401,*map(bits,(.25,-.5,2.25)))+cmd(404,*map(bits,(2.5,-3.25)))
  m.mem_write(code,b+cmd(2)+cmd(-1));call(0x420260,vm)
  rows.append(dict(op=op,difficulty=difficulty,file=file,slot=slot,program=program,offset=get(vm+0x54)-msg,retired=bool(get(old+0x1c)&32),handle=get(vm+0x90+slot*4),bindings=bindings[:],vm=[get(created+o) for o in (0x24,0x1c,0x59c,0x5a0,0x5a4,0x3c,0x40,0x44,0x50,0x60,0x64)] if bindings else []))
 for r in rows:
  if r['vm']:r['vm'][1]&=0x60220
 text_rows=[]
 for op,line,color,plain in itertools.product((3,4),range(5),(0,0x123456,0xffffff,0xff123456),(b'',b'A',b'Ending line',bytes.fromhex('938c95fb'),bytes(range(1,128)))):
  reset();put(vm+0x78,line);put(vm+0x7c,color)
  for i in range(5):text_handles[100+i]=old+i*0x700;put(vm+0x40+i*4,100+i)
  encoded=bytearray();key=0x77;step=7
  for c in plain+b'\0':encoded.append(c^key);key=(key+step)&255;step=(step+16)&255
  n=len(encoded) if op==3 else 0
  m.mem_write(msg,struct.pack('<HBB',0,op,n)+(bytes(encoded) if op==3 else b'')+struct.pack('<HBB',65535,0,0));call(0x420260,vm)
  final_interrupts=[0]*5
  for h,label in interrupts:final_interrupts[h-100]=label
  text_rows.append(dict(op=op,line=line,color=color,plain=plain.hex(),offset=get(vm+0x54)-msg,finalLine=get(vm+0x78),texts=texts[:],interrupts=final_interrupts))
 music_rows=[]
 for path,initial in itertools.product(('bgm/th14_16','bgm/th14_17'),(0,2,0x10,0xff)):
  reset();put(0x4db68c,supervisor);put(0x4d916c,0);m.mem_write(supervisor+0x24230,bytes([initial])*0x42c);b=path.encode('ascii')+b'\0'
  m.mem_write(msg,struct.pack('<HBB',0,10,len(b))+b+struct.pack('<HBB',65535,0,0));call(0x420260,vm)
  assert music_files==[path];music_rows.append(dict(path=path,initial=initial,settings=bytes(m.mem_read(supervisor+0x24230,0x42c)).hex()))
 switches=[]
 for time,wait,line,flags,schedule,rate in itertools.product((0,40),(0,9),(0,4),(1,3),(0,5),(.5,1,1.25)):
  reset();floats(0x4d8f58,rate);put(vm+0x18,time-1);put(vm+0x1c,time);floats(vm+0x20,time);put(vm+0x2c,wait-1);put(vm+0x30,wait);floats(vm+0x34,wait);put(vm+0x78,line);put(vm+0x74,flags);put(vm+0x7c,0x123456)
  for i in range(5):put(vm+0x40+i*4,100+i)
  for i in range(16):put(vm+0x90+i*4,100+i)
  for i in range(4):put(vm+0x80+i*4,resource)
  m.mem_write(msg,struct.pack('<HBB',0,12,10)+b'staff.msg\0'+struct.pack('<HBB',65535,0,0));m.mem_write(staff,struct.pack('<IIHBBI',0,8,schedule,9,4,0x654321)+struct.pack('<HBB',65535,0,0));call(0x420260,vm)
  switches.append(dict(time=time,wait=wait,line=line,flags=flags,schedule=schedule,rate=rate,offset=get(vm+0x54)-staff,finalFlags=get(vm+0x74),finalLine=get(vm+0x78),color=get(vm+0x7c),timers=[get(vm+off+i*4) for off in (4,0x18,0x2c) for i in range(3)],handles=[get(vm+0x40+i*4) for i in range(5)]+[get(vm+0x80+i*4) for i in range(4)]+[get(vm+0x90+i*4) for i in range(16)]))
 (ROOT/'artifacts/th14/ending-animation-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),loader=loader,rows=rows,textRows=text_rows,musicRows=music_rows,switches=switches),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} retail ending image cases, {len(loader)} resource slots, {len(text_rows)} text cases, {len(music_rows)} BGM cases, {len(switches)} staff switches')
if __name__=='__main__':main()
