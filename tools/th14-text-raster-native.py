"""Retail467ba0 scratch pixels with real Windows GDI and controlled host boundaries."""
import ctypes as C,hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 arena=0x70000000;m.mem_map(arena,0xc0000);pixels=arena+0x10000;rect=arena+0x1000;text=arena+0x2000;texture=arena+0x3000;vtable=arena+0x4000;stack=arena+0xbf000
 gdi=C.WinDLL('gdi32',use_last_error=True)
 def fn(name,result,args):f=getattr(gdi,name);f.restype=result;f.argtypes=args;return f
 ptr=C.c_void_p;integer=C.c_int;u32=C.c_uint32
 create_dc=fn('CreateCompatibleDC',ptr,[ptr]);dib=fn('CreateDIBSection',ptr,[ptr,ptr,u32,C.POINTER(ptr),ptr,u32]);select=fn('SelectObject',ptr,[ptr,ptr]);create_font=fn('CreateFontA',ptr,[integer]*5+[u32]*8+[C.c_char_p]);color=fn('SetTextColor',u32,[ptr,u32]);mode=fn('SetBkMode',integer,[ptr,integer]);draw=fn('TextOutA',integer,[ptr,integer,integer,C.c_char_p,integer]);flush=fn('GdiFlush',integer,[]);delete_object=fn('DeleteObject',integer,[ptr]);delete_dc=fn('DeleteDC',integer,[ptr])
 info=bytearray(108);struct.pack_into('<IiiHHII',info,0,108,1024,-128,1,16,3,1024*128*2);struct.pack_into('<IIII',info,40,0xf00,0xf0,0xf,0xf000)
 info_buf=C.create_string_buffer(bytes(info));bits=ptr();bitmap=dib(None,info_buf,0,C.byref(bits),None,0);assert bitmap and bits.value;dc=create_dc(None);assert dc;old_bitmap=select(dc,bitmap)
 font_rows=json.loads((ROOT/'artifacts/th14/font-initialization-native.json').read_text())['rows'][0]['fonts'];fonts=[]
 for row in font_rows:fonts.append(create_font(*row['args'],bytes.fromhex(row['face'])))
 assert all(fonts);old_font=select(dc,fonts[0]);selected=1;uploads=[]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def sint(v):return C.c_int32(v).value
 shims={0x4b1030:(arena+0x5000,'select',8),0x4b101c:(arena+0x5010,'color',8),0x4b1020:(arena+0x5020,'mode',8),0x4b1018:(arena+0x5030,'draw',20),0x4b12e0:(arena+0x5040,'upload',40)}
 for iat,(address,name,pop) in shims.items():put(iat,address)
 calls={a:(name,pop) for a,name,pop in shims.values()};calls[arena+0x5050]=('surface',12);calls[0x48f980]=('memset',0);calls[0x4854a0]=('cookie',0)
 calls.update({0x485540:('malloc',0),0x487620:('memcpy',0),0x4855d2:('free',0)})
 trail=[];boundary_calls=[]
 def hook(uc,a,n,u):
  nonlocal selected
  trail.append(a)
  if len(trail)>80:del trail[0]
  if a not in calls:return
  name,pop=calls[a];sp=uc.reg_read(UC_X86_REG_ESP);result=0
  boundary_calls.append([name,hex(get(sp))])
  if name=='select':
   requested=get(sp+8);result=selected
   if 1<=requested<=8:select(dc,fonts[requested-1]);selected=requested
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
 for address in calls:m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
 def invalid(uc,access,address,size,value,user):
  sp=uc.reg_read(UC_X86_REG_ESP);print('Unmapped raster boundary',hex(address),'PC',hex(uc.reg_read(UC_X86_REG_EIP)),'return',hex(get(sp)),'calls',boundary_calls[-20:],'trail',[hex(a) for a in trail[-8:]]);return False
 m.hook_add(UC_HOOK_MEM_INVALID,invalid)
 for address,value in ((0x4d9ae8,26),(0x4d9aec,1024),(0x4d9af0,128),(0x4d9af4,1024*128*2),(0x4d9af8,2048),(0x4d9afc,1),(0x4d9b08,pixels),(texture,vtable),(vtable+0x48,arena+0x5050)):put(address,value)
 for address,handle in zip((0x4fd61c,0x4fd62c,0x4fd620,0x4fd630,0x4fd624,0x4fd628,0x4fd634,0x4fd638),range(1,9)):put(address,handle)
 output=ROOT/'artifacts/th14/text-raster-native';output.mkdir(exist_ok=True);rows=[]
 try:
  for font in (*range(8),-1,8):
   for profile in range(8):
    height=(16,17,20,17,23,17,32,17)[profile];offset=(-3,0,4,2,3,0,-1,17)[profile];foreground=(0x123456,0xffffff,0x817364,0x334455,0xfa3721,0,0x63e581,0x182944)[profile];outline=(0x654321,0,0x192633,0x778899,0x741999,0,0xffffff,0x5f12c4)[profile];spacing=(0,0,0,12,19,0,0,11)[profile];shadow=profile not in (2,7);plain=(b'Text012: iWj',bytes.fromhex('938c95fb'),b'Text012: iWj',bytes.fromhex('938c95fb'),b'Odd',b'',bytes.fromhex('b1b2b3dedf'),bytes.fromhex('926e97ec9361817596b2917a8176'))[profile]
    m.mem_write(pixels,bytes(1024*128*2));m.mem_write(text,plain+b'\0');m.mem_write(rect,struct.pack('<iiii',0,0,512,32));put(stack,arena)
    for i,v in enumerate((height,foreground,outline,text,texture,font,spacing,int(shadow)),1):put(stack+i*4,v)
    m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,rect);m.reg_write(UC_X86_REG_EDX,offset*2&0xffffffff);uploads.clear();m.emu_start(0x467ba0,arena,count=50000000);assert m.reg_read(UC_X86_REG_EIP)==arena,(font,profile,hex(m.reg_read(UC_X86_REG_EIP)));assert len(uploads)==1
    raw=bytes(m.mem_read(pixels,1024*128*2));name=f'font{font}-profile{profile}.bin';(output/name).write_bytes(raw);rows.append(dict(font=font,height=height,offset=offset,color=foreground,outline=outline,spacing=spacing,plain=not shadow,text=plain.hex(),file='artifacts/th14/text-raster-native/'+name,sha256=hashlib.sha256(raw).hexdigest(),upload=uploads[0]))
 finally:
  select(dc,old_font)
  for font in fonts:delete_object(font)
  select(dc,old_bitmap);delete_object(bitmap);delete_dc(dc)
 (ROOT/'artifacts/th14/text-raster-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Actual retail467ba0 and 467020/466eb0/466b10 scratch processing, actual host Windows GDI TextOutA/CreateFontA. Allocation, memcpy, free, surface upload and resource/COM delivery controlled. Not a GPU or other-system-font proof.'),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} retail text scratch images')
if __name__=='__main__':main()
