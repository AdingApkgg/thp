"""Real front panel families, native factories/lifetimes and draw geometry."""
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
 roots=[('front.anm',slot) for slot in range(216,232)]
 resources={name:dict((s,b) for s,_,b in importlib.import_module('th-anm-script-dump').scripts((extraction/name).read_bytes()) if 168<=s<232) for name,_ in roots}
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
  elif a==0x4854a0:pop=0
  else:return
  if a!=0x4854a0:uc.reg_write(UC_X86_REG_EAX,result)
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x48f980,0x4854af,0x4854fe,0x4854a0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
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
  data=(extraction/filename).read_bytes();offset=0;index=0;chunk=0;records=base+0x100000;source=base+0x180000;put(resource+0x11c,records)
  while True:
   ns=struct.unpack_from('<H',data,offset+4)[0];width,height=struct.unpack_from('<HH',data,offset+10)
   for i in range(ns):
    raw=struct.unpack_from('<I',data,offset+64+i*4)[0]+offset;number,x,y,w,h=struct.unpack_from('<I4f',data,raw);assert number==index
    right=struct.unpack('<f',struct.pack('<f',x+w))[0];bottom=struct.unpack('<f',struct.pack('<f',y+h))[0]
    m.mem_write(source,bytes(72));put(source+8,base+0x190000+chunk*0x100);put(base+0x190000+chunk*0x100,chunk+1);m.mem_write(source+0xc,struct.pack('<6f',x,y,right,bottom,float(height),float(width)));m.mem_write(source+0x3c,struct.pack('<2f',1.,1.));run(0x47d9e0,resource,(index,source));index+=1
   stride=struct.unpack_from('<I',data,offset+36)[0]
   if not stride:break
   offset+=stride;chunk+=1
  put(resource+0x108,index)
 rows=[]
 for resource_index,rate,width,synchronous in itertools.product(range(len(roots)),(.5,1.,1.25),(32.,128.,384.),(0,1)):
  filename,slot=roots[resource_index];bodies=resources[filename];prepare_sprites(filename);codes.clear();cursor=base+0x200000
  for script,body in bodies.items():codes[script]=cursor;m.mem_write(cursor,body);put(table+script*4,cursor);cursor+=(len(body)+15)&~15
  allocated.clear();dead.clear();m.mem_write(manager+0xfe8208,bytes(16));put(manager+0xff52c8,0);m.mem_write(0x4d8f58,struct.pack('<f',rate))
  m.mem_write(manager+0xbc8188,bytes([255])*16);put(manager+0xff52cc,0xffffffff);put(manager+0xff52d0,0);put(0x4d9964,1);put(0x4d9960,0);m.mem_write(0x4f5815,b'\0');device_state.clear();device_state.update({14:1,19:2,20:1,171:1});sampler_state.clear();sampler_state.update({1:1,2:1,5:2,6:2})
  for s in bodies:
   p=templates+s*0x5cc;m.mem_write(p,bytes(0x5cc));run(0x46f3e0,resource,(p,s))
   for o,v in ((0x548,-2),(0x54c,-1),(0x550,0xbf800000)):put(p+o,v)
   assert run(0x46fe50,p)==0
  run(0x47ed10,resource,(base+0x9000,slot,0,0,0xffffffff,0,0));handle=get(base+0x9000);assert allocated[0]==root;assert len(allocated)==4;assert run(0x47f0a0,manager,(handle,))==root
  linked=[];node=get(root+0x584)
  while node:linked.append(struct.unpack('<h',m.mem_read(get(node)+0x4aa,2))[0]);node=get(node+4)
  for p in (allocated[1],allocated[3]):m.mem_write(p+0x4bc,struct.pack('<f',width))
  initial=family_state();frames=[];events=[]
  for frame in range(110):
   label={12:2,45:3,60:8,90:1}.get(frame)
   if label is not None:run(0x47f1b0 if synchronous else 0x47f140,manager,(handle,label));events.append(dict(frame=frame,label=label,state=family_state()))
   run(0x47e5e0,manager);run(0x47e6c0,manager)
   alive=[int(p not in dead) for p in allocated]
   geometry=draw_layers();frames.append(dict(alive=alive,state=family_state(),layers=layer_state(),draws=geometry))
   if not any(alive):break
  rows.append(dict(input=[resource_index,slot,rate,width,synchronous],linked=linked,initial=initial,events=events,frames=frames))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),d3dxSha256=dll_sha,resourceHashes=resource_hashes,roots=roots,rows=rows,scope='Sixteen actual front.anm216..231 panel roots with three original children each, widths32/128/384 at child float10004, rates0.5/1/1.25, deferred/synchronous family labels2/3/8/1. Native screen RHW initialized1; actual47ed10 heap factory/registration/lookup, original47d9e0 sprite records and46f1e0 binding, real ANM scripts/children, full47e5e0/47e6c0 manager updates/destruction and every36 layers through whole47e810/478f60. Real D3DX baseline/SSE2 table. Captures original four screen vertices and texture/depth/blend/filter/address states at475f80 batch boundary, plus38 selected family state words/lifetimes/layer chains. ANM texture extents with resize factors1, opaque texture handles and D3D state/batch/flush recording sinks; controlled CRT heap/memset/cookie. No native full resource loader, texture pixels, actual GPU raster/full MSG/world/natural clear claim.')
 (ROOT/'artifacts/th14/dialogue-panel-geometry-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS native panel geometry',len(rows),sum(len(r['frames']) for r in rows),sum(len(f['draws']) for r in rows for f in r['frames']))
if __name__=='__main__':main()
