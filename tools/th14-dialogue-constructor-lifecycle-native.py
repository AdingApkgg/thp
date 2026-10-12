"""Full original dialogue constructor with real text ANM factories and lifetimes."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x800000);resource=base+0x3000;table=base+0x6000;templates=base+0x10000;stack=base+0x700000;root=base+0x300000;manager=0x71000000;m.mem_map(manager,0x1000000)
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());extraction=Path(archive['extraction']);codes={}
 roots=[('text.anm',0)]
 resources={name:dict((s,b) for s,_,b in importlib.import_module('th-anm-script-dump').scripts((extraction/name).read_bytes()) if s in (0,1)) for name,_ in roots}
 resource_hashes={name:hashlib.sha256((extraction/name).read_bytes()).hexdigest() for name in resources}
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 allocated=[];dead=set()
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);result=0
  if a==0x48f980:result=get(sp+4);m.mem_write(result,bytes([get(sp+8)&255])*get(sp+12));pop=0
  elif a==0x4854af:
   result=root+0x1000*len(allocated);m.mem_write(result,bytes(0x700));allocated.append(result);pop=0
  elif a==0x4854fe:dead.add(get(sp+4));pop=0
  elif a in (0x41b880,0x43ac00,0x424cb0,0x4350b0):pop={0x41b880:4,0x43ac00:8,0x424cb0:0,0x4350b0:0}[a]
  elif a==0x4854a0:pop=0
  else:return
  if a!=0x4854a0:uc.reg_write(UC_X86_REG_EAX,result)
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x48f980,0x4854af,0x4854fe,0x4854a0,0x41b880,0x43ac00,0x424cb0,0x4350b0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(0x4db520,base+0xd0000);put(0x4f56cc,manager);put(resource+0x120,table);put(resource+0x10c,templates)

 def run(address,owner,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_EBP,0);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(address,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 offsets=(0x534,0x538,0x24,0x54c,0x550,0x3c,0x40,0x44,0x60,0x64,0x4a0,0x4bc,0x4c0,0x78,0x7c)
 def state(p):
  slot=struct.unpack('<h',m.mem_read(p+0x4aa,2))[0];return [get(p+0x34)&0xffff,*[get(p+o) for o in offsets],get(p+0x528)&0xffff,get(p+0x1c)&0xa00,get(p+0x18)&1,get(p+0x28)-codes[slot] if get(p+0x28) else 0xffffffff,int(get(p+0x594)==root),slot,*[get(p+o) for o in (0x80,0x84,0x3b8,0x3bc,0x3c0,0x3c4,0x3c8,0x3cc,0x3d0,0x3d4,0x3e0,0x3f4,0x460,0x474,0x420,0x434)]]
 def family_state():return [state(p) if p not in dead else [0]*38 for p in allocated]
 def layer_state():
  result=[]
  for layer in range(36):
   p=get(manager+0xfe8218+layer*0x5cc+0x590);chain=[]
   while p:chain.append(allocated.index(p));assert len(chain)<=len(allocated);p=get(p+0x590)
   result.append(chain)
  return result
 def prepare_sprites(filename):
  data=(extraction/filename).read_bytes();offset=0;index=0;records=base+0x100000;source=base+0x180000;put(resource+0x11c,records)
  while True:
   ns=struct.unpack_from('<H',data,offset+4)[0];width,height=struct.unpack_from('<HH',data,offset+10)
   for i in range(ns):
    raw=struct.unpack_from('<I',data,offset+64+i*4)[0]+offset;number,x,y,w,h=struct.unpack_from('<I4f',data,raw);assert number==index
    right=struct.unpack('<f',struct.pack('<f',x+w))[0];bottom=struct.unpack('<f',struct.pack('<f',y+h))[0]
    m.mem_write(source,bytes(72));m.mem_write(source+0xc,struct.pack('<6f',x,y,right,bottom,float(height),float(width)));m.mem_write(source+0x3c,struct.pack('<2f',1.,1.));run(0x47d9e0,resource,(index,source));index+=1
   stride=struct.unpack_from('<I',data,offset+36)[0]
   if not stride:break
   offset+=stride
  put(resource+0x108,index)
 rows=[]
 for rate,synchronous,sequence in itertools.product((.5,1.,1.25),(0,1),range(3)):
  resource_index=0
  filename,slot=roots[resource_index];bodies=resources[filename];prepare_sprites(filename);codes.clear();cursor=base+0x200000
  for script,body in bodies.items():codes[script]=cursor;m.mem_write(cursor,body);put(table+script*4,cursor);cursor+=(len(body)+15)&~15
  allocated.clear();dead.clear();m.mem_write(manager+0xfe8208,bytes(16));put(manager+0xff52c8,0);m.mem_write(0x4d8f58,struct.pack('<f',rate))
  for s in bodies:
   p=templates+s*0x5cc;m.mem_write(p,bytes(0x5cc));run(0x46f3e0,resource,(p,s))
   for o,v in ((0x548,-2),(0x54c,-1),(0x550,0xbf800000)):put(p+o,v)
   assert run(0x46fe50,p)==0
  d=base+0x410000;instruction=base+0x420000;m.mem_write(d,bytes(0x200));m.mem_write(instruction,bytes(64));put(0x4d967c,resource);m.mem_write(0x4f5815,b'\0');run(0x431a70,d,(instruction,));assert len(allocated)==4
  handles=[get(d+0x58+i*4) for i in range(4)]
  for handle,p in zip(handles,allocated):assert run(0x47f0a0,manager,(handle,))==p
  linked=[];constructor=[get(d+o) for o in (0x1a0,0x1a4,0x1ac,0x194,0x198,0x19c)]+[int(get(p+0x5bc)!=0) for p in allocated]
  initial=family_state();frames=[];events=[]
  for frame in range(160):
   label=({12:2,45:3,60:2,100:1} if sequence==1 else {12:2,25:9,45:3,60:2,100:1} if sequence==2 else {}).get(frame)
   if label is not None:
    for handle in handles:run(0x47f1b0 if synchronous else 0x47f140,manager,(handle,label))
    events.append(dict(frame=frame,label=label,state=family_state()))

   run(0x47e5e0,manager);run(0x47e6c0,manager)
   alive=[int(p not in dead) for p in allocated]
   frames.append(dict(alive=alive,state=family_state(),layers=layer_state()))
   if not any(alive):break
  rows.append(dict(input=[rate,synchronous,sequence],constructor=constructor,linked=linked,initial=initial,events=events,frames=frames))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resourceHashes=resource_hashes,roots=roots,rows=rows,scope='Whole original431a70 Dialogue constructor with actual text.anm0/1 templates, actual47d9e0 sprite records and46f1e0 binding, full47fcb0 heap allocation and original40af00/46fe50 first updates/47e890 registration/47f0a0 lookup/47f140 second-line7. Four real text ANM roots0/0/1/1 with21x21/plain/callback initialization; rates0.5/1/1.25 and none/deferred/synchronous label sequences2/3/9/1, actual full manager updates/destruction and36 layer chains. Captures38 state words per live line, lifetime, label instant and10 constructor state words. CRT heap/memset/cookie and world/HUD/input services41b880/43ac00/424cb0/4350b0 controlled, native texture extents from ANM headers with resize1; full resource loader, draw callbacks/GDI/GPU/full MSG/world not claimed.')
 (ROOT/'artifacts/th14/dialogue-constructor-lifecycle-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS native dialogue constructor lifecycle',len(rows),sum(len(r['frames']) for r in rows))
if __name__=='__main__':main()
