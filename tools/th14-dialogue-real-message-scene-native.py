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
 base=0x70000000;m.mem_map(base,0x2000000);resource=base+0x3000;table=base+0x6000;templates=base+0x10000;stack=base+0x700000;root=base+0x300000;manager=0x73000000;m.mem_map(manager,0x1000000)
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());extraction=Path(archive['extraction']);codes={}
 file_names=['text.anm','front.anm','pl00.anm','st01enm.anm','st01logo.anm']
 resources={name:dict((script,body) for script,_,body in importlib.import_module('th-anm-script-dump').scripts((extraction/name).read_bytes()) if name!='front.anm' or script in range(168,232)) for name in file_names}
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
 dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/d3dx9_43.dll');dll_sha=hashlib.sha256(dll.data).hexdigest();assert dll_sha=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
 for _,b,size,raw,n in dll.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,dll.data[raw:raw+n])
 device,vtable,camera=base+0xd1000,base+0xd2000,base+0xd3000;vertex_buffer,vertex_table,vertex_data=base+0xd4000,base+0xd5000,base+0xd6000;draws=[];device_state={};sampler_state={};texture_handle=0
 def sink(uc,a,n,u):
  nonlocal texture_handle
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==base+0x100:device_state[get(sp+8)]=get(sp+12)
  elif a==base+0x110:assert get(sp+8)==0;sampler_state[get(sp+12)]=get(sp+16)
  elif a==base+0x120:assert get(sp+8)==0;texture_handle=get(sp+12)
  elif a==base+0x170:put(get(sp+24),vertex_buffer)
  elif a==base+0x180:put(get(sp+16),vertex_data)
  elif a==0x475f80:
   p=get(sp+4);draws.append(dict(vertices=[list(struct.unpack('<4fI2f',m.mem_read(p+i*28,28))) for i in range(4)],material=[texture_handle,device_state[14],device_state[19],device_state[20],device_state[171],sampler_state[5],sampler_state[6],sampler_state[1],sampler_state[2]]))
 for a,cleanup in ((base+0x100,12),(base+0x110,16),(base+0x120,12),(base+0x130,16),(base+0x140,8),(base+0x170,28),(base+0x180,20),(base+0x190,4),(base+0x1a0,20),(0x475eb0,0),(0x475f80,4)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 put(device,vtable)
 put(vtable+0x68,base+0x170);put(vtable+0x190,base+0x1a0);put(vertex_buffer,vertex_table);put(vertex_table+0x2c,base+0x180);put(vertex_table+0x30,base+0x190)
 for offset,a in ((0xe4,base+0x100),(0x114,base+0x110),(0x104,base+0x120),(0x10c,base+0x130),(0x164,base+0x140)):put(vtable+offset,a)
 put(0x4d8f68,device);put(0x4d9640,camera)
 for i,v in enumerate((0,0,640,480)):put(camera+0xe0+i*4,v)
 m.mem_write(0x4f7a6c,struct.pack('<f',1.))
 for p,v in ((0x4f7a88,320),(0x4f7a8c,16),(0x4f7a80,320),(0x4f7a84,16)):put(p,v)
 # The selected quad helpers overwrite position/color/UV but retain RHW in
 # the Supervisor's shared screen vertex buffer. Supply its screen default.
 for i in range(4):m.mem_write(0x4fd224+i*28,struct.pack('<f',1.))
 m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));run(0x101bc521,manager,(0x101ca068,))
 pe=struct.unpack_from('<I',dll.data,0x3c)[0];directory=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0];count=dll.u32(directory+24);functions,names,ordinals=[dll.image_base+dll.u32(directory+offset) for offset in (28,32,36)];exports={}
 for i in range(count):
  name=dll.read(dll.image_base+dll.u32(names+4*i),128).split(b'\0')[0].decode('ascii');ordinal=struct.unpack('<H',dll.read(ordinals+2*i,2))[0];exports[name]=dll.image_base+dll.u32(functions+4*ordinal)
 for iat,name in ((0x4b12d4,'D3DXMatrixMultiply'),(0x4b12d8,'D3DXMatrixRotationX'),(0x4b12f8,'D3DXMatrixRotationY'),(0x4b12cc,'D3DXMatrixRotationZ')):put(iat,exports[name])
 try:run(0x47b9f0,manager)
 except Exception:
  print('native init diagnostic',hex(m.reg_read(UC_X86_REG_EIP)),hex(m.reg_read(UC_X86_REG_ESP)),m.mem_read(m.reg_read(UC_X86_REG_ESP),32).hex());raise
 def draw_layers():
  draws.clear()
  for layer in range(36):assert run(0x47e810,manager,(layer,))==1
  return list(draws)
 offsets=(0x534,0x538,0x24,0x54c,0x550,0x3c,0x40,0x44,0x60,0x64,0x4a0,0x4bc,0x4c0,0x78,0x7c)
 def state(p):
  slot=struct.unpack('<h',m.mem_read(p+0x4aa,2))[0];return [get(p+0x34)&0xffff,*[get(p+o) for o in offsets],get(p+0x528)&0xffff,get(p+0x1c)&0xa00,get(p+0x18)&1,get(p+0x28)-codes[(get(p+0x30),slot)] if get(p+0x28) else 0xffffffff,int(get(p+0x594)==root),slot,*[get(p+o) for o in (0x80,0x84,0x3b8,0x3bc,0x3c0,0x3c4,0x3c8,0x3cc,0x3d0,0x3d4,0x3e0,0x3f4,0x460,0x474,0x420,0x434)]]
 def family_state():return [state(p) if p not in dead else [0]*38 for p in allocated]
 def layer_state():
  result=[]
  for layer in range(36):
   p=get(manager+0xfe8218+layer*0x5cc+0x590);chain=[]
   while p:chain.append(allocated.index(p));assert len(chain)<=len(allocated);p=get(p+0x590)
   result.append(chain)
  return result

 descriptors={};texture_base=0
 for i,name in enumerate(file_names):
  origin=base+0x1000000+i*0x100000;data=(extraction/name).read_bytes();chunk=0;number=1
  while (stride:=struct.unpack_from('<I',data,chunk+36)[0]):number+=1;chunk+=stride
  descriptors[name]=dict(resource=origin,table=origin+0x2000,templates=origin+0x10000,sprites=origin+0x80000,raw=origin+0x90000,texture_info=origin+0xa0000,code=origin+0xb0000,texture_base=texture_base,textures=number)
  texture_base+=number;put(origin,{'text.anm':0,'front.anm':5,'pl00.anm':7,'st01enm.anm':10,'st01logo.anm':6}[name]);put(origin+0x120,origin+0x2000);put(origin+0x10c,origin+0x10000)
 def prepare_sprites(filename):
  desc=descriptors[filename];data=(extraction/filename).read_bytes();offset=0;index=0;chunk=0;resource=desc['resource'];records=desc['sprites'];source=desc['raw'];put(resource+0x11c,records)
  while True:
   ns=struct.unpack_from('<H',data,offset+4)[0];width,height=struct.unpack_from('<HH',data,offset+10)
   for i in range(ns):
    raw=struct.unpack_from('<I',data,offset+64+i*4)[0]+offset;number,x,y,w,h=struct.unpack_from('<I4f',data,raw);assert number==index
    right=struct.unpack('<f',struct.pack('<f',x+w))[0];bottom=struct.unpack('<f',struct.pack('<f',y+h))[0];holder=desc['texture_info']+chunk*0x100
    m.mem_write(source,bytes(72));put(source+8,holder);put(holder,desc['texture_base']+chunk+1);m.mem_write(source+0xc,struct.pack('<6f',x,y,right,bottom,float(height),float(width)));m.mem_write(source+0x3c,struct.pack('<2f',1.,1.));run(0x47d9e0,resource,(index,source));index+=1
   stride=struct.unpack_from('<I',data,offset+36)[0]
   if not stride:break
   offset+=stride;chunk+=1
  put(resource+0x108,index)
 text_resource=descriptors['text.anm']['resource'];front_resource=descriptors['front.anm']['resource']
 writes=[];sounds=[]
 def cstr(p):
  result=bytearray()
  while m.mem_read(p,1)!=b'\0':result+=m.mem_read(p,1);p+=1;assert len(result)<2048
  return bytes(result)
 def service(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x47db50:
   args=[get(sp+i*4) for i in range(1,9)];vm=args[1];writes.append(dict(line=allocated.index(vm),color=args[2],font=struct.unpack('<i',struct.pack('<I',args[4]))[0],offset=struct.unpack('<i',struct.pack('<I',args[5]))[0],spacing=struct.unpack('<i',struct.pack('<I',args[6]))[0],text=cstr(args[7]).hex(),plain=get(vm+0x1c)&0x800));put(vm+0x18,get(vm+0x18)|1);pop=0
  elif a==0x445710:uc.reg_write(UC_X86_REG_EAX,0);pop=8
  elif a==0x435590:uc.reg_write(UC_X86_REG_EAX,0);pop=4
  elif a==0x46e3d0:sounds.append(get(sp+4));pop=8
  elif a==0x486016:uc.reg_write(UC_X86_REG_EAX,int(cstr(get(sp+4)).split(b',')[0]));pop=0
  elif a==0x486040:uc.reg_write(UC_X86_REG_EAX,get(sp+4)+cstr(get(sp+4)).index(bytes([get(sp+8)&255])));pop=0
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x47db50,0x435590,0x46e3d0,0x486016,0x486040,0x445710):m.hook_add(UC_HOOK_CODE,service,begin=a,end=a)

 rows=[];msg_file='st01a.msg';msg=(extraction/msg_file).read_bytes();msg_sha=hashlib.sha256(msg).hexdigest();entry=0;start=struct.unpack_from('<I',msg,4+entry*8)[0];stop=struct.unpack_from('<I',msg,12+entry*8)[0];program=msg[start:stop]
 for rate in (1.,):
  codes.clear()
  for name in file_names:
   desc=descriptors[name];prepare_sprites(name);cursor=desc['code']
   for script,body in resources[name].items():codes[(desc['resource'],script)]=cursor;m.mem_write(cursor,body);put(desc['table']+script*4,cursor);cursor+=(len(body)+15)&~15
  allocated.clear();dead.clear();m.mem_write(manager+0xfe8208,bytes(16));put(manager+0xff52c8,0);m.mem_write(0x4d8f58,struct.pack('<f',rate))
  m.mem_write(manager+0xbc8188,bytes([255])*16);put(manager+0xff52cc,0xffffffff);put(manager+0xff52d0,0);put(0x4d9964,1);put(0x4d9960,0);device_state.clear();device_state.update({14:1,19:2,20:1,171:1});sampler_state.clear();sampler_state.update({1:1,2:1,5:2,6:2})
  for name in file_names:
   desc=descriptors[name]
   for script in resources[name]:
    p=desc['templates']+script*0x5cc;m.mem_write(p,bytes(0x5cc));run(0x46f3e0,desc['resource'],(p,script))
    for o,v in ((0x548,-2),(0x54c,-1),(0x550,0xbf800000)):put(p+o,v)
    assert run(0x46fe50,p)==0,(name,script)
  d=base+0x410000;instruction=base+0x420000;m.mem_write(d,bytes(0x200));m.mem_write(instruction,program);put(0x4d967c,text_resource);m.mem_write(0x4f5815,b'\0');run(0x431a70,d,(instruction,));assert len(allocated)==4;enemy=base+0x430000;put(0x4db550,enemy);put(enemy+0x194,d);put(enemy+0x2a4,front_resource);put(enemy+0x148,descriptors['st01logo.anm']['resource']);player=base+0x450000;put(0x4db67c,player);put(player+0x10,descriptors['pl00.anm']['resource']);animations=base+0x460000;put(0x4db544,animations)
  for file in range(16):put(animations+0xa0+file*4,descriptors['st01enm.anm']['resource'])
  put(0x4f5828,0);put(0x4f58a4,1);put(0x4db69c,0x4d5988+0xcc)
  for addr in (0x4d6a90,0x4d6a9c,0x4d6a30,0x4d6a0c):put(addr,0)
  initial=family_state();frames=[];writes.clear();sounds.clear()
  for frame in range(6000):
   pressed=0x80001 if frame%60==0 else 0;put(0x4d6a9c,pressed);writes.clear()
   try:status=run(0x432390,d)
   except Exception:print('real-MSG diagnostic',frame,hex(m.reg_read(UC_X86_REG_EIP)),hex(get(d+0x158)-instruction));raise
   assert status in (0,1)
   run(0x47e5e0,manager);run(0x47e6c0,manager);quad=draw_layers()
   selected=[get(d+o) for o in (0x184,0x180,0x188,0x18c,0x190,0x194,0x198,0x19c,0x1a0,0x1a4,0x1ac,0x1b4,8,12,0x1c,0x20,0x30,0x34)]+[get(d+0x158)-instruction,int(get(d+0x6c)!=0),len(sounds)]
   frames.append(dict(input=[0,pressed],status=status,dialogue=selected,writes=list(writes),alive=[int(p not in dead) for p in allocated],state=family_state(),layers=layer_state(),draws=quad))
   if status:break
  assert frames[-1]['status']==1
  rows.append(dict(input=[1,0,entry,rate],program=program.hex(),initial=initial,frames=frames))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),d3dxSha256=dll_sha,resourceHashes=resource_hashes,messageFile=msg_file,messageSha256=msg_sha,descriptors=descriptors,rows=rows,toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual st01a.msg entry0, retail431a70 and whole432390/432400, real text/front/player/enemy/logo ANM templates/sprites/factories/manager/destructor/full36-layer drawing and real text follow callbacks. Literal text device47db50 records requests/dirty bit; CRT/HUD/world/input/sound/music controlled, confirmation every60 frames, shared screen RHW1. Texture dimensions/header resize1 and opaque handles controlled, no original complete loader/GDI/GPU/fullworld/natural-clear claim.')
 (ROOT/'artifacts/th14/dialogue-real-message-scene-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS native real MSG scene',len(rows),sum(len(r['frames']) for r in rows),max(len(f['state']) for r in rows for f in r['frames']))
if __name__=='__main__':main()
