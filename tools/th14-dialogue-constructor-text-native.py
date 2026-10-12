"""Full original dialogue constructor with real text ANM factories and lifetimes."""
import ctypes as C,hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_INVALID
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
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*[v&0xffffffff for v in args]));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_EBP,0);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(address,base,count=50000000);assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/d3dx9_43.dll');dll_sha=hashlib.sha256(dll.data).hexdigest();assert dll_sha=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
 for _,b,size,raw,n in dll.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,dll.data[raw:raw+n])
 device,vtable,camera=base+0xd1000,base+0xd2000,base+0xd3000;vertex_buffer,vertex_table,vertex_data=base+0xd4000,base+0xd5000,base+0xd6000;draws=[];device_state={};sampler_state={};texture_handle=0
 def sink(uc,a,n,u):
  nonlocal texture_handle
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==base+0x100:device_state[get(sp+8)]=get(sp+12)
  elif a==base+0x110:assert get(sp+8)==0;sampler_state[get(sp+12)]=get(sp+16)
  elif a==base+0x120:assert get(sp+8)==0;texture_handle=(get(sp+12)-(base+0x560000))//0x100+1
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
 arena=base+0x500000;pixels=arena+0x10000;rect=arena+0x1000;text=arena+0x2000;texture=arena+0x3000;vtable=arena+0x4000
 gdi=C.WinDLL('gdi32',use_last_error=True)
 def fn(name,result,args):f=getattr(gdi,name);f.restype=result;f.argtypes=args;return f
 ptr=C.c_void_p;integer=C.c_int;u32=C.c_uint32
 create_dc=fn('CreateCompatibleDC',ptr,[ptr]);dib=fn('CreateDIBSection',ptr,[ptr,ptr,u32,C.POINTER(ptr),ptr,u32]);select=fn('SelectObject',ptr,[ptr,ptr]);create_font=fn('CreateFontA',ptr,[integer]*5+[u32]*8+[C.c_char_p]);color=fn('SetTextColor',u32,[ptr,u32]);mode=fn('SetBkMode',integer,[ptr,integer]);draw=fn('TextOutA',integer,[ptr,integer,integer,C.c_char_p,integer]);flush=fn('GdiFlush',integer,[]);delete_object=fn('DeleteObject',integer,[ptr]);delete_dc=fn('DeleteDC',integer,[ptr])
 info=bytearray(108);struct.pack_into('<IiiHHII',info,0,108,1024,-128,1,16,3,1024*128*2);struct.pack_into('<IIII',info,40,0xf00,0xf0,0xf,0xf000)
 info_buf=C.create_string_buffer(bytes(info));bits=ptr();bitmap=dib(None,info_buf,0,C.byref(bits),None,0);assert bitmap and bits.value;dc=create_dc(None);assert dc;old_bitmap=select(dc,bitmap)
 font_rows=json.loads((ROOT/'artifacts/th14/font-initialization-native.json').read_text())['rows'][0]['fonts'];fonts=[]
 for row in font_rows:fonts.append(create_font(*row['args'],bytes.fromhex(row['face'])))
 assert all(fonts);old_font=select(dc,fonts[0]);selected=1;uploads=[];deliveries=[]
 def sint(v):return C.c_int32(v).value
 shims={0x4b1030:(arena+0x5000,'select',8),0x4b101c:(arena+0x5010,'color',8),0x4b1020:(arena+0x5020,'mode',8),0x4b1018:(arena+0x5030,'draw',20),0x4b12e0:(arena+0x5040,'upload',40)}
 for iat,(address,name,pop) in shims.items():put(iat,address)
 calls={a:(name,pop) for a,name,pop in shims.values()};calls[0x4859cd]=('format',0);calls[arena+0x5050]=('surface',12);
 calls.update({0x485540:('malloc',0),0x487620:('memcpy',0),0x4855d2:('free',0)})
 trail=[];boundary_calls=[]
 def raster_hook(uc,a,n,u):
  nonlocal selected
  trail.append(a)
  if len(trail)>80:del trail[0]
  if a not in calls:return
  name,pop=calls[a];sp=uc.reg_read(UC_X86_REG_ESP);result=0
  boundary_calls.append([name,hex(get(sp))])
  if name=='select':
   requested=get(sp+8);result=selected
   if 1<=requested<=8:select(dc,fonts[requested-1]);selected=requested
  elif name=='format':m.mem_write(get(sp+4),plain+b'\0');result=len(plain)
  elif name=='color':result=color(dc,get(sp+8))
  elif name=='mode':result=mode(dc,sint(get(sp+8)))
  elif name=='draw':
   raw=bytes(m.mem_read(pixels,1024*128*2));C.memmove(bits,raw,len(raw));data=bytes(m.mem_read(get(sp+16),get(sp+20)));assert draw(dc,sint(get(sp+8)),sint(get(sp+12)),data,len(data));assert flush();m.mem_write(pixels,C.string_at(bits,1024*128*2));result=1
  elif name=='memset':p=get(sp+4);m.mem_write(p,bytes([get(sp+8)&255])*get(sp+12));result=p
  elif name=='malloc':
   assert get(sp+4)<=0x30000;result=arena+0x80000
  elif name=='memcpy':
   result=get(sp+4);m.mem_write(result,bytes(m.mem_read(get(sp+8),get(sp+12))))
  elif name=='surface':put(get(sp+12),0)
  elif name=='upload':
   destination=[sint(get(get(sp+12)+i*4)) for i in range(4)];source=[sint(get(get(sp+32)+i*4)) for i in range(4)];uploads.append(dict(destination=destination,source=source,format=get(sp+20),pitch=get(sp+24),filter=get(sp+36),colorKey=get(sp+40)))
  uc.reg_write(UC_X86_REG_EAX,result&0xffffffff);uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for address in calls:m.hook_add(UC_HOOK_CODE,raster_hook,begin=address,end=address)
 def invalid(uc,access,address,size,value,user):
  sp=uc.reg_read(UC_X86_REG_ESP);print('Unmapped raster boundary',hex(address),'PC',hex(uc.reg_read(UC_X86_REG_EIP)),'return',hex(get(sp)),'calls',boundary_calls[-20:],'trail',[hex(a) for a in trail[-8:]]);return False
 m.hook_add(UC_HOOK_MEM_INVALID,invalid)
 for address,value in ((0x4d9ae8,26),(0x4d9aec,1024),(0x4d9af0,128),(0x4d9af4,1024*128*2),(0x4d9af8,2048),(0x4d9afc,1),(0x4d9b08,pixels),(texture,vtable),(vtable+0x48,arena+0x5050)):put(address,value)
 for address,handle in zip((0x4fd61c,0x4fd62c,0x4fd620,0x4fd630,0x4fd624,0x4fd628,0x4fd634,0x4fd638),range(1,9)):put(address,handle)

 def observe_delivery(uc,address,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP);args=[get(sp+i*4) for i in range(1,9)]
  deliveries.append(dict(height=args[0],color=args[1],outline=args[2],font=sint(args[5]),spacing=args[6],shadow=args[7],offset=sint(uc.reg_read(UC_X86_REG_EDX))))
 m.hook_add(UC_HOOK_CODE,observe_delivery,begin=0x467ba0,end=0x467ba0)
 output=ROOT/'artifacts/th14/dialogue-constructor-text';output.mkdir(exist_ok=True);rows=[]
 for font,profile,alignment in itertools.product((*range(8),-1,8),range(3),range(3)):
  filename='text.anm';bodies=resources[filename];prepare_sprites(filename);codes.clear();cursor=base+0x200000
  for script,body in bodies.items():codes[script]=cursor;m.mem_write(cursor,body);put(table+script*4,cursor);cursor+=(len(body)+15)&~15
  allocated.clear();dead.clear();m.mem_write(manager+0xfe8208,bytes(16));put(manager+0xff52c8,0);m.mem_write(0x4d8f58,struct.pack('<f',1.))
  m.mem_write(manager+0xbc8188,bytes([255])*16);put(manager+0xff52cc,0xffffffff);put(manager+0xff52d0,0);put(0x4d9964,1);put(0x4d9960,0);device_state.clear();device_state.update({14:1,19:2,20:1,171:1});sampler_state.clear();sampler_state.update({1:1,2:1,5:2,6:2})
  for s in bodies:
   p=templates+s*0x5cc;m.mem_write(p,bytes(0x5cc));run(0x46f3e0,resource,(p,s))
   for o,v in ((0x548,-2),(0x54c,-1),(0x550,0xbf800000)):put(p+o,v)
   assert run(0x46fe50,p)==0
  d=base+0x410000;instruction=base+0x420000;m.mem_write(d,bytes(0x200));m.mem_write(instruction,bytes(64));put(0x4d967c,resource);m.mem_write(0x4f5815,b'\0');run(0x431a70,d,(instruction,));assert len(allocated)==4;enemy=base+0x430000;put(0x4db550,enemy);put(enemy+0x194,d)
  initial=family_state();writes=[]
  # Replace only opaque texture objects with COM upload boundaries, preserving
  # the actual sprite records/UV/extents produced by47d9e0 and46f1e0.
  for chunk in range(4):
   obj=base+0x560000+chunk*0x100;put(base+0x190000+chunk*0x100,obj);put(obj,vtable)
  for line,vm in enumerate(allocated):
   foreground=(0x123456,0xffffff,0x817364)[profile];offset=(-3,2,17)[profile];spacing=(0,12,20)[profile];plain=(b'Text012: iWj',bytes.fromhex('938c95fb'),bytes.fromhex('926e97ec9361817596b2917a8176'))[profile]
   m.mem_write(pixels,bytes(1024*128*2));uploads.clear();deliveries.clear()
   args=(0,vm,foreground,0,font,offset,spacing//2,arena+0x5000) if alignment==0 else (0,vm,foreground,0,font,spacing//2,arena+0x5000)
   run((0x47db50,0x47dc40,0x47dd70)[alignment],manager,args)
   assert len(uploads)==1 and len(deliveries)==1,(font,profile,alignment,line,uploads,deliveries)
   raw=bytes(m.mem_read(pixels,1024*128*2));name=f'case{len(rows)}-line{line}.bin';(output/name).write_bytes(raw)
   writes.append(dict(line=line,delivery=deliveries[0],upload=uploads[0],file=name,sha256=hashlib.sha256(raw).hexdigest(),finalFlags=get(vm+0x18)))
  written=family_state();frames=[]
  for i in range(4):run(0x47f140,manager,(get(d+0x58+i*4),2))
  for frame in range(13):
   run(0x47e5e0,manager);run(0x47e6c0,manager);frames.append(dict(state=family_state(),draws=draw_layers()))
  rows.append(dict(input=[font,profile,alignment],color=foreground,offset=offset,spacing=spacing,text=plain.hex(),initial=initial,written=written,writes=writes,frames=frames))
 select(dc,old_font)
 for font in fonts:delete_object(font)
 select(dc,old_bitmap);delete_object(bitmap);delete_dc(dc)
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),d3dxSha256=dll_sha,resourceHashes=resource_hashes,rows=rows,toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual431a70 constructor and real text.anm0/1 script/sprite factories, four21x21/plain lines; complete47db50/47dc40/47dd70 text wrappers and467ba0 raster with actual host GDI fonts. Formatter returns controlled literal CP932 bytes, CRT allocation/copies and COM surface/upload controlled. Actual36-layer draws over13 subsequent animation frames, absent panel callback, controlled screen RHW1 and D3D state/batch sinks. Does not claim full resource loader/fullMSG/world/original32bitCOM/GPU equivalence.')
 (output/'scratch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS actual constructor text writes',len(rows),sum(len(r['writes']) for r in rows))
if __name__=='__main__':main()
